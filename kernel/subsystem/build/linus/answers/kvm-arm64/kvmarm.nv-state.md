- `is_hyp_ctxt()` in `arch/arm64/include/asm/kvm_emulate.h`: returns
  `vcpu_is_el2(vcpu) || (e2h && tge) || tge`, so virtual `HCR_EL2.TGE` alone
  makes a non-EL2 mode a hypervisor context; E2H is not required.
- `kvm_inject_nested()` and `kvm_hyp_handle_eret()`: treat `PSR_MODE_EL0t`
  as host EL0 only when `vcpu_el2_e2h_is_set()` and `vcpu_el2_tge_is_set()`
  both hold.
- `HCR_EL2`: not VNCR-backed in this tree. It is a plain `enum vcpu_sysreg`
  entry between `__SANITISED_REG_START__` and `__VNCR_START__`, stored in
  `sys_regs[]`.
- `NVHCR_EL2`: the `VNCR()` entry at page offset 0x078 (`VNCR_NVHCR_EL2` in
  `arch/arm64/include/asm/vncr_mapping.h`). There is no VNCR_HCR_EL2.
- `__compute_hcr()` in `arch/arm64/kvm/hyp/vhe/switch.c`, in hyp context:
  copies `HCR_EL2` into `NVHCR_EL2` before entry.
- `fixup_nv_guest_exit()`: copies `NVHCR_EL2` back into `HCR_EL2` on every
  exit taken with `VCPU_IN_HYP_CONTEXT` set, so `is_hyp_ctxt()` reads KVM's
  copy as of the last exit.
- With `ARM64_HAS_NV3` and `vcpu_el2_e2h_is_set()`: both copies use the
  hardware register `SYS_NVHCR_EL2` instead of the page slot.
- `SCTLR_EL2`, `TCR_EL2`, `TTBR0_EL2`, `TTBR1_EL2`, `VBAR_EL2`, `ESR_EL2`,
  `FAR_EL2`, `ELR_EL2`, `SPSR_EL2`: plain `sys_regs[]` entries, not
  VNCR-backed. `locate_register()` in `arch/arm64/kvm/sys_regs.c` maps them
  to the hardware EL1 register while in hyp context with `SYSREGS_ON_CPU`
  set.
- `vncr_array`: a `u64 *` field of `struct kvm_cpu_context`, one page from
  `kvm_vcpu_init_nested()`. There is no struct of that name.
- `VCPU_IN_HYP_CONTEXT`: per-CPU host data flag, set or cleared by
  `__compute_hcr()` on each entry of an NV vCPU. It is not per-vCPU state.
- `fixup_nv_guest_exit()`: uses the flag to turn EL1t/EL1h in the saved
  PSTATE back into EL2t/EL2h, then `BUG_ON()`s if the flag and
  `is_hyp_ctxt()` disagree.
- `__compute_hcr()` in hyp context: sets `HCR_NV | HCR_NV2 | HCR_AT |
  HCR_TTLB`; `HCR_NV1` only when `vcpu_el2_e2h_is_set()` is false.
- Names absent from this tree: vcpu_mode_el2, get_el2_to_el1_mapping,
  __vcpu_put_sysregs, __vcpu_load_sysregs, compute_hcr. The jobs are done by
  `vcpu_is_el2()`, `locate_register()`, `__vcpu_put_switch_sysregs()`,
  `__vcpu_load_switch_sysregs()` and `__compute_hcr()`.
- `kvm_inject_el2_exception()`: only calls `kvm_pend_exception()` and, for
  sync and SError, writes `ESR_EL2`. `enter_exception64()` in
  `arch/arm64/kvm/hyp/exception.c`, reached from `__kvm_adjust_pc()`, writes
  `ELR_EL2`, `SPSR_EL2`, PC and PSTATE.
- `kvm_inject_nested()` from vEL2, or from EL0 with E2H and TGE: pends the
  exception and returns, with no put/load; the state changes at the next
  `__kvm_adjust_pc()`.
- `kvm_inject_nested()` from any other mode: `__kvm_adjust_pc()`,
  `kvm_arch_vcpu_put()`, pend, `__kvm_adjust_pc()` again,
  `kvm_arch_vcpu_load()`, all with preemption disabled.
- `kvm_emulate_nested_eret()`: does `kvm_arch_vcpu_put()` and
  `kvm_arch_vcpu_load()` itself, even for a return that stays at vEL2. The
  exception is a failed ERETAx with FPACCOMBINE and no illegal return: it
  injects with `kvm_inject_nested_sync()` and returns first.
- `kvm_hyp_handle_eret()` declines, leaving the slow path, when:
  - `ARM64_HAS_NV3` and `vcpu_el2_e2h_is_set()`
  - `is_nested_ctxt()`
  - the target mode is not EL2t, EL2h, or EL0t with E2H and TGE
  - ERETAx fails `kvm_auth_eretax()` or the vCPU lacks ptrauth
