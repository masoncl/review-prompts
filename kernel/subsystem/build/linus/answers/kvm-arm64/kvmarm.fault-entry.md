- Names: kvm_inject_dabt(), kvm_inject_pabt() and kvm_inject_vabt() are not in
  this tree. `kvm_inject_sea()` in `arch/arm64/kvm/inject_fault.c` takes an
  `iabt` flag; `kvm_inject_sea_dabt()` and `kvm_inject_sea_iabt()` are inline
  wrappers in `arch/arm64/include/asm/kvm_emulate.h`.
- Before the lookup, translation fault, two IPA ranges:
  - `fault_ipa >= BIT_ULL(get_kvm_ipa_limit())`: `kvm_inject_size_fault()`.
  - at or above the `VTCR_EL2_IPA()` size but below that limit:
    `kvm_inject_sea()`.
- `kvm_handle_guest_sea()`: returns 1 with nothing injected when
  `apei_claim_sea()` claims the abort; otherwise `kvm_inject_serror()`, or a
  `KVM_EXIT_ARM_SEA` exit when `KVM_ARCH_FLAG_EXIT_SEA` is set and
  `host_owns_sea()` is false.
- `kvm->srcu`: taken before the nested walk, not just around the memslot
  lookup.
- Nested walk: `-EAGAIN` from `kvm_walk_nested_s2()` returns 1 with no
  injection; any other failure of it or of `kvm_s2_handle_perm_fault()`
  injects with `kvm_inject_s2_fault()`.
- Missing syndrome: tested in `io_mem_abort()` in `arch/arm64/kvm/mmio.c`,
  after the lookup. It injects (`kvm_inject_sea_dabt()`) only for a protected
  VM; otherwise `KVM_EXIT_ARM_NISV` or `-ENOSYS`.
- Cache-maintenance skip (`kvm_incr_pc()`): only when `kvm_is_error_hva(hva)`.
  A CMO that hits the write-to-read-only-slot case goes on to
  `io_mem_abort()`.
- Final dispatch order: `kvm_vm_is_protected()` selects `pkvm_mem_abort()`
  first; only otherwise `kvm_slot_has_gmem()` chooses between `gmem_abort()`
  and `user_mem_abort()`.
- Exclusive/atomic FSC: `esr_fsc_is_excl_atomic_fault()` passes the
  "Unsupported FSC" filter. `kvm_inject_dabt_excl_atomic()` has one caller,
  `kvm_s2_fault_compute_prot()`, so it runs after the lookup and only on the
  `user_mem_abort()` path.
