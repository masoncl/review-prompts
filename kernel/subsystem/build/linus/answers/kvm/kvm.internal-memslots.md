- `KVM_INTERNAL_MEM_SLOTS`: 3 on x86, 1 on s390
  (`KVM_S390_UCONTROL_MEMSLOT`), 0 elsewhere.

| Limit | User slot | Internal slot |
|---|---|---|
| `npages <= KVM_MEM_MAX_NR_PAGES` | enforced | exempt |
| `mem->flags` non-zero | allowed if `check_memory_region_flags()` passes | `-EINVAL` |
| `kvm_is_visible_memslot()` | true unless `KVM_MEMSLOT_INVALID` | false |
| dirty-log and dirty-ring lookups | reachable | rejected by id |
| alignment and `access_ok()` on `userspace_addr` | enforced | enforced |
| counted in `kvm->nr_memslot_pages` | yes | yes |

- Dirty-log id test: `id >= KVM_USER_MEM_SLOTS` in `kvm_get_dirty_log()`,
  `kvm_get_dirty_log_protect()`, `kvm_clear_dirty_log_protect()` and
  `kvm_reset_dirty_gfn()`.
- `KVM_CAP_NR_MEMSLOTS`: reports `KVM_USER_MEM_SLOTS`.
- s390 ucontrol VM: `s390_kvm_mmu_prepare_memory_region()` rejects every
  slot with `id < KVM_USER_MEM_SLOTS`, so only the internal slot exists.
