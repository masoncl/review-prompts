- guest_memfd: no special case; `kvm_check_memslot_overlap()` receives only
  the set, the id and the gfn range, never the flags.
- gfn overlap: `kvm_set_memory_region()` returns `-EEXIST`.
