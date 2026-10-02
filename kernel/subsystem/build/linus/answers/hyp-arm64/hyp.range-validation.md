- There is no addr_is_allowed_memory() in this tree.

| Helper | Checks | Leaves unchecked |
|---|---|---|
| `pfn_range_is_valid()` | range lies below `BIT(kvm_phys_shift() - PAGE_SHIFT)` of the host stage-2, without overflow | `nr_pages` of 0 passes; whether it is memory |
| `check_range_allowed_memory()` | start and `end - 1` in one `struct kvm_mem_range`; a memblock region; not `MEMBLOCK_NOMAP` | who owns the pages, including hyp-owned ones |
| `range_is_memory()` | start is memory and `end - 1` is in the same region | `MEMBLOCK_NOMAP` |
| `addr_is_memory()` | one address is in a memblock region | `MEMBLOCK_NOMAP` |

- `check_range_allowed_memory()`: `-EINVAL` when the range leaves its
  region, `-EPERM` when it is not memory or is `MEMBLOCK_NOMAP`.
- `pfn_range_is_valid()`: called by the functions that take `nr_pages`
  with a pfn. `__pkvm_host_share_hyp()`, `__pkvm_host_unshare_hyp()` and
  `__pkvm_host_donate_guest()` do not call it.
- Those three rely on `check_range_allowed_memory()` inside
  `__host_check_page_state_range()`.
- `check_range_allowed_memory()` also runs, under `WARN_ON()`, on the
  address read from a guest PTE: `get_valid_guest_pte()` and
  `__check_host_shared_guest()`.
- `range_is_memory()`: gates `host_stage2_set_owner_locked()` (for
  `PKVM_ID_HOST`) and `host_stage2_set_owner_metadata_locked()` with
  `-EPERM`; `host_stage2_force_pte_cb()` uses it to pick the expected prot.
- `__pkvm_hyp_donate_host()`: `__hyp_check_page_state_range()` runs before
  any memory check; the function has no hypercall handler, EL2 code
  supplies the pfn.
