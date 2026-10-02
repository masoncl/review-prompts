- `update_sctlr_el1()`: writes with `sysreg_clear_set()`; the `isb()` after it
  runs even when `sysreg_clear_set()` skipped the write.
- `set_sctlr_el1`: an assembler macro in `arch/arm64/include/asm/assembler.h`,
  used by `__enable_mmu` and `enter_vhe`; `update_sctlr_el1()` does not use it.
- `__mte_enable_kernel()`: `isb()` directly after the `sysreg_clear_set()` of
  `SCTLR_EL1_TCF_MASK`; `mte_enable_kernel_store_only()` has the same shape.
- `cpu_enable_pan()`: no `isb()` in the body; it clears `SCTLR_EL1_SPAN` with
  `sysreg_clear_set()` and then runs `set_pstate_pan(1)`.
- `init_el2_state` macros with no `isb` of their own, for example
  `__init_el2_fgt` and `__init_el2_hstr`: covered by a later `isb`, not by the
  `eret`.
  - `init_el2` in `arch/arm64/kernel/head.S`: `isb` after `msr vbar_el2`,
    which follows `init_el2_state`.
  - `___kvm_hyp_init` in `arch/arm64/kvm/hyp/nvhe/hyp-init.S`: `isb` after
    `msr tcr_el2`, which follows both calls of `__kvm_init_el2_state`.
  - Comment above `init_kernel_el()`: ERET is not relied on, because
    `SCTLR_ELx_EOS` may be clear.
- There is no __init_el2_hcr here; `init_el2_hcr` in
  `arch/arm64/include/asm/el2_setup.h` writes through the `msr_hcr_el2`
  assembler macro, which always ends in `isb`.
- Caller of `sysreg_clear_set_hcr()` that needs the barrier: adds `isb()`, as
  `__vgic_v3_get_gic_config()` does.
- Writes left without an `isb()`, and the reason the tree gives:

| Code | Write | Reason |
|---|---|---|
| `cpu_enable_mpam()` | `SYS_MPAM0_EL1` | comment: left to the ERET to EL0; the `SYS_MPAM1_EL1` write before it gets `isb()` |
| `permission_overlay_switch()` | `SYS_POR_EL0` | comment: a spurious overlay fault is tolerated |
| `mte_check_tfsr_el1()` | `SYS_TFSR_EL1` | comment: no indirect read follows the direct write |
| `cpu_enable_mte()` | `SCTLR_ELx_ATA`, `SCTLR_EL1_ATA0` | `mte_cpu_setup()` ends in `local_flush_tlb_all()`, which has `isb()`, before `mte_clear_page_tags()` runs |
