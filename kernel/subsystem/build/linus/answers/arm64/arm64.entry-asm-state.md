- `kernel_ventry` for EL0: only recovers x30 from `tpidrro_el0` (64-bit) or
  zeroes it (32-bit), and only when entered through `tramp_ventry`;
  Spectre-BHB mitigation is in `tramp_ventry`.
- `kernel_entry` writes no PAN, UAO, BTI or MTE tag-check control; its only
  PSTATE write is `SET_PSTATE_DIT(1)`, for `\el == 0` under `ARM64_HAS_DIT`.
- Also EL0 only, for example: `NO_SYSCALL` stored at `S_SYSCALLNO`, and
  `FRAME_META_TYPE_FINAL` instead of `FRAME_META_TYPE_PT_REGS`.
- Shadow call stack on EL0 entry: `scs_load_current_base`, not
  `scs_load_current`; x18 restarts at the task's SCS base.
- SW PAN from EL0: `__swpan_entry_el0` always runs
  `__uaccess_ttbr0_disable`.
- SW PAN from EL1: `__swpan_entry_el1` disables TTBR0 only if it was
  enabled, and records which in `PSR_PAN_BIT` of the saved SPSR.
- State installed only for `\el == 0` stays current for EL1 entries because
  `cpu_switch_to()` switches it: `sp_el0`, the kernel PAC key
  (`ptrauth_keys_install_kernel`) and x18.
- Per-task kernel state added to the EL0 branch needs the same at context
  switch.
- `__sdei_asm_handler`: does not use `kernel_entry`; it reloads `sp_el0`
  from `__entry_task` and switches stacks, and performs none of the other
  EL0 entry steps.
- Writes sharing the one `isb`: `SYS_APIAKEYLO_EL1` and `SYS_APIAKEYHI_EL1`
  from `__ptrauth_keys_install_kernel_nosync`, the `SCTLR_ELx_ENIA` write
  to `sctlr_el1`, and `SYS_GCR_EL1` from `mte_set_kernel_gcr`; that `isb`
  is patched in only under `ARM64_MTE` or `ARM64_HAS_ADDRESS_AUTH`.
- `disable_step_tsk` and `__uaccess_ttbr0_disable` carry their own `isb`.
- The EL1 path of `kernel_entry` has no `isb` outside `__swpan_entry_el1`;
  a new write needed for EL1 entries must synchronise itself.
