- Guaranteed by the enum itself: every register declared after a marker is
  numerically at or above it, and `NR_SYS_REGS` is above every entry; inside
  the VNCR block the numbers follow the page offsets in
  `arch/arm64/include/asm/vncr_mapping.h`, not the declaration order.
- There is no grouping by "loaded on the CPU"; EL1 registers are split between
  the plain block and the VNCR block.
- `set_sysreg_masks()` in `arch/arm64/kvm/nested.c`: has `BUILD_BUG_ON()` for a
  register below `__SANITISED_REG_START__`; a register that gets RES0/RES1
  masks must be declared after that marker.
- Pointer-auth keys: each `HI` entry must directly follow its `LO` entry; the
  `stp`/`ldp` pairs in `arch/arm64/include/asm/kvm_ptrauth.h` rely on it.
- Code that selects by name: `locate_register()` and `locate_direct_register()`
  in `arch/arm64/kvm/sys_regs.c`; `__copy_vcpu_state()` in
  `arch/arm64/kvm/hyp/nvhe/hyp-main.c`, which skips the timer registers with one
  `case` each.
- **Unsafe usage**: `<`, `>` or `case A ... B` between two named
  `enum vcpu_sysreg` registers.
  - Safe: comparison against `__SANITISED_REG_START__`, `__VNCR_START__` or
    `NR_SYS_REGS`, as `___ctxt_sys_reg()` and `__kvm_get_sysreg_resx()` do; the
    `MARKER()` and `VNCR()` macros define that order.
  - Safe: one `case` per register, as `__copy_vcpu_state()` does.
- **Potentially unsafe usage**: base register plus index.
  - Unsafe: when nothing makes the family's numbers consecutive, for example
    VNCR entries whose page offsets are not 8 bytes apart.
  - Safe: `PMEVCNTR0_EL0 + idx` and `PMEVTYPER0_EL0 + idx`, as
    `counter_index_to_reg()` and `counter_index_to_evtreg()` in
    `arch/arm64/kvm/pmu-emul.c` do; the enum reserves the slots with
    `PMEVCNTR30_EL0 = PMEVCNTR0_EL0 + 30`.
  - Safe: `ICH_LRN()`, `ICH_AP0RN()`, `ICH_AP1RN()` in
    `arch/arm64/kvm/vgic/vgic-v3-nested.c`; the offsets in
    `arch/arm64/include/asm/vncr_mapping.h` are 8 bytes apart.
- **Potentially unsafe usage**: a loop over every number from a marker to
  `NR_SYS_REGS`.
  - Unsafe: when the body assumes each number is a register; the range has
    holes.
  - Safe: when the body is harmless on a hole, as the loop at the end of
    `kvm_init_nv_sysregs()` is: it rewrites each slot with its own masked
    value.
