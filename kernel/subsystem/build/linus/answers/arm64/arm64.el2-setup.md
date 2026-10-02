- `init_el2_state` users: `init_kernel_el` in `arch/arm64/kernel/head.S` and
  `__kvm_init_el2_state` in `arch/arm64/kvm/hyp/nvhe/hyp-init.S`;
  `arch/arm64/kernel/hyp-stub.S` does not run it.
- `init_kernel_el` callers: `primary_entry`, `secondary_holding_pen`,
  `secondary_entry` and `cpu_resume`.
- `__kvm_init_el2_state`: runs `init_el2_state` then `finalise_el2_state`;
  called from `__kvm_hyp_init_cpu`, and from `___kvm_hyp_init` only when
  `HCR_E2H` is set.
- `sctlr_el2`: set inside `init_el2_state` by `__init_el2_sctlr`, not left to
  the caller.
- `hcr_el2`: set by the caller before the macro, with `init_el2_hcr` in
  `init_kernel_el` and `__kvm_hyp_init_cpu`, and with `msr_hcr_el2` in
  `___kvm_hyp_init`; `__check_hvhe` in `__init_el2_timers` and
  `__init_el2_cptr` reads the `HCR_E2H` bit it leaves.
- `init_el2_state` can run with `HCR_E2H` set (a VHE-only CPU, or the hVHE
  replay), so a register whose layout depends on it needs `__check_hvhe`.
- Left to `init_kernel_el` outside the macro: `elr_el2` before it, and after
  it `vbar_el2`, `spsr_el2`, and `sctlr_el1` or `SYS_SCTLR_EL12`.
- Left to `finalise_el2_state`, which honours ID overrides through
  `check_override`:

| Feature | Registers |
|---|---|
| MPAM | `SYS_MPAM2_EL2`, `SYS_MPAMHCR_EL2` |
| GCS | `SYS_GCSCR_EL1`, `SYS_GCSCRE0_EL1` |
| SVE | `CPTR_EL2_TZ` or `CPACR_EL1_ZEN`, `SYS_ZCR_EL2` |
| SME | `CPTR_EL2_TSM` or `CPACR_EL1_SMEN`, `SCTLR_ELx_ENTP2`, `SYS_SMCR_EL2`, `SYS_SMPRIMAP_EL2` |

- `check_override` in the nVHE object: reads a symbol named after the
  register with the suffix `_el1_sys_val`, for example
  `id_aa64pfr0_el1_sys_val`, instead of the override; a new register there
  needs that variable in `arch/arm64/kvm/hyp/nvhe/sys_regs.c`, set in
  `arch/arm64/kvm/arm.c`.
- `finalise_el2_state` runs on every `HVC_FINALISE_EL2`, before
  `__finalise_el2` decides whether to switch to VHE.
- `__finalise_el2` requires the EL2 MMU off: bit 0 of `sctlr_el2` set returns
  `HVC_STUB_ERR` and the kernel stays at EL1.
- `__finalise_el2` copies `sp_el1`, and through the `_EL12` aliases
  `SYS_CPACR_EL12`, `SYS_VBAR_EL12`, `SYS_TCR_EL12`, `SYS_TTBR0_EL12`,
  `SYS_TTBR1_EL12`, `SYS_MAIR_EL12`, then `REG_TCR2_EL12` if TCRX is present,
  and `REG_PIRE0_EL12` and `REG_PIR_EL12` only if both TCRX and S1PIE are.
- `enter_vhe` copies `SYS_SCTLR_EL12` and then writes
  `INIT_SCTLR_EL1_MMU_OFF` to it.
- `tpidr_el1`: not copied by `__finalise_el2`; `cpu_copy_el2regs()`, the
  `.cpu_enable` of `ARM64_HAS_VIRT_HOST_EXTN`, copies it to `tpidr_el2` while
  `alternative_is_applied()` is false for that cap.
- An EL1 register that `HCR_E2H` redirects to EL2 and that is programmed
  before `finalise_el2`, in `__cpu_setup()` or `__enable_mmu`, needs its own
  copy in `__finalise_el2`; otherwise the value stays in the EL1 register
  after the switch.
- `__finalise_el2` also undoes nVHE-only state: it clears
  `MDCR_EL2_E2PB_MASK` and `MDCR_EL2_E2TB_MASK`.
- There is no HCRX_HOST_FLAGS in this tree; the `SYS_HCRX_EL2` boot value is
  built in `__init_el2_hcrx`.
