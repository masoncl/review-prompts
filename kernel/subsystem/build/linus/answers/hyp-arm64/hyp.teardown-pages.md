| Page kind | Way back to the host |
|---|---|
| Protected guest page | `__pkvm_host_reclaim_page_guest()`, per page |
| Non-protected guest page | `__pkvm_host_unshare_guest()`, per mapping |
| Stage-2 tables and PGD | `reclaim_pgtable_pages()` into `stage2_teardown_mc` |
| vCPU memcache pages | popped, pushed to `stage2_teardown_mc` |
| Hyp vCPU and hyp VM | `teardown_donated_memory()` into `teardown_mc` |

- `__pkvm_reclaim_dying_guest_page` arguments: handle and gfn only; EL2
  takes the physical address from the guest stage-2 entry in
  `get_valid_guest_pte()`.
- `__pkvm_host_reclaim_page_guest()`, guest state `PKVM_PAGE_OWNED`: page
  zeroed by `hyp_poison_page()`, then unmapped and given to the host.
- `__pkvm_host_reclaim_page_guest()`, guest state `PKVM_PAGE_SHARED_OWNED`:
  not zeroed, then unmapped and given to the host.
- `__pkvm_host_reclaim_page_guest()`, any other guest state,
  `PKVM_PAGE_SHARED_BORROWED` included: `-EPERM`.
- `-EHWPOISON` from `get_valid_guest_pte()`:
  `__pkvm_host_reclaim_page_guest()` turns it into 0, so the host drops its
  pin on a page that was force-reclaimed earlier.
- Host choice: `__pkvm_pgtable_stage2_reclaim()` in `arch/arm64/kvm/pkvm.c`
  walks `pgt->pkvm_mappings`; on success it unpins the page and frees the
  mapping, on failure it warns and keeps both.
- PGD: part of `hyp_vm->pool` since `kvm_guest_prepare_stage2()`; not
  returned by `teardown_donated_memory()`.
- There is no pkvm_pgtable_stage2_destroy here;
  `pkvm_pgtable_stage2_destroy_range()` does the per-range work.
