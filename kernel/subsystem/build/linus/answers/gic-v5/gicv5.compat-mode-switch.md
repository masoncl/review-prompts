- Control: `ICH_VCTLR_EL2_V3`; `__vgic_v5_compat_mode_disable()` clears it and
  issues `isb()`, `__vgic_v3_compat_mode_enable()` sets it.
- Write site: first statement of `__vgic_v5_restore_vmcr_apr()` in
  `arch/arm64/kvm/hyp/vgic-v5-sr.c`.
- When it runs: at vCPU load, from `vgic_v5_load()` through `kvm_call_hyp()`;
  not at each guest entry.
- `vgic_v5_load()`: returns early when `gicv5_vpe.resident` is true, so V3 is
  cleared once per load and put pair.
- `__vgic_v5_compat_mode_disable()`: has no cpucap test; only
  `__vgic_v3_compat_mode_enable()` tests `ARM64_HAS_GICV5_CPUIF`.
- Putting a GICv3 vCPU: nothing clears V3; apart from the boot write, only
  `__vgic_v5_compat_mode_disable()` clears it.
- Boot value: `arch/arm64/include/asm/el2_setup.h` writes only
  `ICH_VCTLR_EL2_En`, so V3 starts clear.
- **Potentially unsafe usage**: writing a GICv5-layout `ICH_*_EL2` register in
  a function that does not itself clear `ICH_VCTLR_EL2_V3`.
  - Unsafe: on a path that can run before `vgic_v5_load()` has run for this
    vCPU on this CPU, or with no `isb()` after the clear; a GICv3 vCPU loaded
    earlier leaves V3 set.
  - Safe: in the same function after the clear and `isb()`, as
    `__vgic_v5_restore_vmcr_apr()` does for `SYS_ICH_VMCR_EL2` and
    `SYS_ICH_APR_EL2`.
  - Safe: at guest entry of a GICv5 vCPU, as `__vgic_v5_restore_ppi_state()`
    does; `kvm_vgic_load()` has already called `vgic_v5_load()`.
