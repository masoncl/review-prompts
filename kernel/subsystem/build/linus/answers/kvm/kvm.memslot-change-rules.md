- `KVM_MEM_READONLY`: toggling it on an existing slot is `-EINVAL` on every
  architecture.
- `KVM_MEM_GUEST_MEMFD`: `-EINVAL` if the new flags have it, and `-EINVAL`
  if old and new flags differ in it; both tests are in
  `kvm_set_memory_region()`.
- Existing guest_memfd slot: every request with `memory_size != 0` fails,
  an identical one too, as the test runs before the "nothing to change"
  return.
- Flag validation: `check_memory_region_flags()`; there is no
  kvm_check_memory_region_flags() here.
- Same `base_gfn`, size, `userspace_addr` and flags: returns 0, picks no
  `enum kvm_mr_change` value, does not call `kvm_set_memslot()`.
- Different `base_gfn` plus a flag change: classified `KVM_MR_MOVE`.
