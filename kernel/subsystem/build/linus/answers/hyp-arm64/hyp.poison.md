- Host decision point: `is_spurious_el1_translation_fault()` in
  `arch/arm64/mm/fault.c`, reached from `__do_kernel_fault()`; it calls
  `pkvm_force_reclaim_guest_page()` in `arch/arm64/kvm/pkvm.c`.
- The host reclaims only when all of these hold:
  - the abort carries `ESR_ELx_S1PTW`, set by `host_inject_mem_abort()`
  - it is an EL1 data abort reported as a translation fault
  - `fixup_exception()` found no fixup; it runs first
  - `AT S1E1R` on the address succeeds, which gives the physical address
- `pkvm_force_reclaim_guest_page()`: 0 and `-EAGAIN` both count as handled
  and the access is retried; any other result ends in
  `die_kernel_fault()`, for which `__do_kernel_fault()` picks the message
  "access to hypervisor-protected memory" when `is_pkvm_stage2_abort()` is
  true and no earlier branch (permission fault, address below `PAGE_SIZE`)
  matched.
- `__pkvm_host_force_reclaim_page_guest()` returns `-EAGAIN` when the
  page's host state is no longer `PKVM_NOPAGE`, or the VM handle is gone.
- `__pkvm_host_force_reclaim_page_guest()` returns `-EPERM` when the
  annotation's owner is not `PKVM_ID_GUEST`, or the guest's state for the
  page is not `PKVM_PAGE_OWNED`.
- Order of updates:
  1. `kvm_pgtable_stage2_annotate()` writes
     `KVM_GUEST_INVALID_PTE_TYPE_POISONED` into the guest entry, with no
     memcache; its error is returned.
  2. `hyp_poison_page()` clears the page.
  3. `host_stage2_set_owner_locked()` with `PKVM_ID_HOST`, asserted.
- Guest's next access: EL2 injects nothing; the stage-2 fault exits to the
  host and reaches `pkvm_mem_abort()`.
- `pkvm_pgtable_stage2_map()`: finds the `struct pkvm_mapping` still in
  the tree and issues the `__pkvm_vcpu_in_poison_fault` hypercall; any
  non-zero result becomes `-EFAULT`, zero becomes `-EAGAIN`.
- `kvm_handle_guest_abort()` returns that `-EFAULT`, which ends `KVM_RUN`.
- `__pkvm_vcpu_in_poison_fault()`: reads the faulting IPA from the vCPU's
  fault registers at EL2, not from the host.
- After a forced reclaim the host keeps its `struct pkvm_mapping` and its
  pin on the page until teardown.
