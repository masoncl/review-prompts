- `do_page_fault()` access chain, in order: `is_el0_instruction_abort()`,
  `is_gcs_fault()`, `is_write_abort()`, else read; `vm_flags` has no value
  before the chain.
- EL1 instruction abort: not matched by `is_el0_instruction_abort()`; it falls
  through to `is_write_abort()`, which tests no EC, and else to the read case;
  it gets no `FAULT_FLAG_INSTRUCTION`.
- Read case: `VM_READ | VM_WRITE`, plus `VM_EXEC` only when `ARM64_HAS_EPAN` is
  absent.
- There is no esr_is_gcs_fault() here; `is_gcs_fault()` in
  `arch/arm64/mm/fault.c` does that, and it matches EL0 and EL1 data aborts
  (`esr_is_data_abort()`).
- `is_el1_permission_fault()`: matches EL1 data aborts and EL1 instruction
  aborts.
- TTBR0 address with `is_el1_permission_fault()` true: dies at once only for an
  EL1 instruction abort or when `insn_may_access_user()` is false.
- `insn_may_access_user()` true: the fault goes on to the VMA lookup and
  `handle_mm_fault()`; `fixup_exception()` runs only if that path ends at
  `no_context`.
- `insn_may_access_user()` in `arch/arm64/mm/extable.c`: any entry type at
  `regs->pc` other than `EX_TYPE_UACCESS_CPY` passes,
  `EX_TYPE_KACCESS_ERR_ZERO` included.
- `EX_TYPE_UACCESS_CPY` entries: pass only when `ESR_ELx_WNR` matches
  `EX_DATA_UACCESS_WRITE`, so a fault on the kernel side of a user copy fails
  `insn_may_access_user()`; `ex_handler_uaccess_cpy()` refuses the fixup on
  the same test.
- `is_pkvm_stage2_abort()` (`ESR_ELx_S1PTW` with `is_pkvm_initialized()`):
  tested after the die-at-once test and before the VMA lookup; kernel mode
  goes to `no_context`, user mode gets `SEGV_ACCERR`.
- `do_mem_abort()` in kernel mode, handler returned non-zero (`do_bad()`):
  `die_kernel_fault()` with `inf->name`; `fixup_exception()` is not tried.
- `do_sea()` in kernel mode: `arm64_notify_die()` calls `die()`;
  `fixup_exception()` is not tried, even at a uaccess instruction.
- `fault_from_pkey()`: runs before `handle_mm_fault()`, after the
  `vma->vm_flags & vm_flags` test passes, on both lookup paths.
- `ESR_ELx_Overlay`: not read for the pkey decision; only `data_abort_decode()`
  prints it.
- `is_invalid_gcs_access()`: called in `do_page_fault()` after
  `lock_vma_under_rcu()` succeeds and before the `vm_flags` test.
- Faults without `FAULT_FLAG_USER`: jump to `lock_mmap` and never take the
  `lock_vma_under_rcu()` path.
