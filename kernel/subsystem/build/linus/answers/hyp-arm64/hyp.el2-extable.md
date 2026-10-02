- `__kvm_unexpected_el2_exception()` in
  `arch/arm64/kvm/hyp/include/hyp/switch.h`: does not read ESR_EL2; any
  synchronous exception or SError whose ELR_EL2 equals an entry's instruction
  address is recovered.
- Table entries are `struct kvm_exception_table_entry`, not
  `struct exception_table_entry`; the table is unsorted and scanned linearly.
- Marking: `_kvm_extable` in assembly, `__KVM_EXTABLE()` in inline asm; both
  are in `arch/arm64/include/asm/kvm_asm.h`.
- Users in this tree: only `__kvm_at()` and the SError window in `__guest_exit`
  (`abort_guest_exit_start`, `abort_guest_exit_end`); there is no
  ___kvm_hyp_call and no __kvm_get_mdcr_el2.
- Fixup code runs after the EL2 exception has overwritten ELR_EL2, SPSR_EL2
  and ESR_EL2; it must restore what later code reads, as `__kvm_at()` does for
  SPSR and ELR and the `9997` fixup in `arch/arm64/kvm/hyp/entry.S` does for
  all three.
- A marked instruction is not recovered while `__kvm_hyp_host_vector` is
  installed: `__kvm_at()` is also reached there, through `__get_fault_info()`
  from `handle_host_mem_abort()`, and a fault on it panics.
