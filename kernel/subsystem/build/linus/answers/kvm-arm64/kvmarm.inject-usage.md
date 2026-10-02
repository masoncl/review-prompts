- There is no kvm_inject_dabt() or kvm_inject_pabt() here; `kvm_inject_sea()`
  with `kvm_inject_sea_dabt()` and `kvm_inject_sea_iabt()` does that job.
- `kvm_inject_sea()` and `kvm_inject_serror_esr()`: assert `vcpu->mutex` with
  `lockdep_assert_held()`.
- `kvm_inject_sea()`, `kvm_inject_serror_esr()`, `kvm_inject_s2_fault()`:
  return `int` and may do a put/load through `kvm_inject_nested()`; abort
  handlers return the value of `kvm_inject_sea()` and `kvm_inject_serror()`.
- **Unsafe usage**: calling `kvm_incr_pc()` and `kvm_pend_exception()` for
  the same exit; each has a `WARN_ON()` of the other's flag, and
  `INCREMENT_PC` is a bit of `EXCEPT_MASK`, so the target is corrupted or the
  increment is lost.
  - Safe: one or the other; `kvm_handle_mmio_return()` tests
    `kvm_pending_external_abort()` before `kvm_incr_pc()`.
  - Safe: committing in between with `__kvm_adjust_pc()`, as
    `kvm_inject_nested()` does on its put/load path before it pends the EL2
    exception; its direct-inject path pends without committing.
- Host order: `exception_target_el()` is always EL1 without NV; with NV it
  picks the ESR and FAR register from `*vcpu_cpsr()`; `inject_abt64()` pends
  first, then writes FAR and ESR with `vcpu_write_sys_reg()`.
- Patching the ESR: inject, then read back, modify and write with
  `vcpu_read_sys_reg()` and `vcpu_write_sys_reg()`, as
  `kvm_inject_size_fault()` and `kvm_inject_dabt_excl_atomic()` do.
- Hyp order with sysregs live, `inject_sync64()` in
  `arch/arm64/kvm/hyp/nvhe/sys_regs.c`:
  - read ELR_EL2 and SPSR_EL2 into `*vcpu_pc()` and `*vcpu_cpsr()`;
  - copy VBAR_EL1 and SCTLR_EL1 to memory, since `enter_exception64()` reads
    them;
  - `kvm_pend_exception()`, then `__kvm_adjust_pc()`;
  - write ESR_EL1, then ELR_EL1 and SPSR_EL1 from ELR_EL2 and SPSR_EL2;
  - only then write the new PC and PSTATE to ELR_EL2 and SPSR_EL2.
- Injecting abort handlers, for example: `kvm_handle_guest_abort()` in
  `arch/arm64/kvm/mmu.c` and `io_mem_abort()` in `arch/arm64/kvm/mmio.c`.
