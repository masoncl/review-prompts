- `hugetlb_alloc_folio()` in `mm/hugetlb.c`: the VMA-less core of
  `alloc_hugetlb_folio()`, which is its only caller.
- `hugetlb_alloc_folio()`: has no stub without `CONFIG_HUGETLB_PAGE` in
  `include/linux/hugetlb.h`.

| Function | Reservations | Cgroup | Pool counters |
|---|---|---|---|
| `alloc_hugetlb_folio()` | reserve map, subpool, `hugetlb_set_folio_subpool()`; turns `map_chg` and `gbl_chg` into `alloc_flags` | charges nothing itself | none itself; `hugetlb_acct_memory()` only on the failure and race paths |
| `hugetlb_alloc_folio()` | no reserve map, no subpool; `resv_huge_pages--` and restore-reserve flag only with `HUGETLB_ALLOC_USE_GLOBAL_RESERVATIONS` | hugetlb cgroup usage and `mem_cgroup_charge_hugetlb()` always; rsvd only with `HUGETLB_ALLOC_CHARG_CGROUP_RSVD` | `dequeue_hugetlb_folio()`, else surplus via `alloc_buddy_hugetlb_folio()` |
| `alloc_hugetlb_folio_nodemask()` | dequeues only if `available_huge_pages()` | none | fallback `alloc_migrate_hugetlb_folio()`: `nr_huge_pages` only, `HPG_temporary`, not surplus |
| `alloc_hugetlb_folio_reserve()` | `resv_huge_pages--`; sets neither the restore-reserve flag nor the folio's subpool | none | dequeue only |
| `alloc_surplus_hugetlb_folio()` | none | none | `account_new_hugetlb_folio()` and `surplus_huge_pages++` itself, under `hugetlb_lock`; NULL once `surplus_huge_pages` reaches `nr_overcommit_huge_pages` |
| `alloc_fresh_hugetlb_folio()` | none | none | none; the caller calls `account_new_hugetlb_folio()` under `hugetlb_lock` |
| `alloc_pool_huge_folio()` | none | none | none; `prep_and_add_allocated_folios()` accounts and enqueues |

- dequeue_hugetlb_folio_vma(), alloc_buddy_hugetlb_folio_with_mpol() and
  prep_new_hugetlb_folio(): not in this tree.
- `hugetlb_alloc_folio()` with `HUGETLB_ALLOC_USE_GLOBAL_RESERVATIONS`:
  dequeues even when `available_huge_pages()` is 0; if dequeue returns NULL,
  the surplus folio still gets the flag and the `resv_huge_pages--`.
- `hugetlb_alloc_folio()` without that flag: dequeues only if
  `available_huge_pages()` is non-zero; the test is in its own body.
- Pool growth in `set_max_huge_pages()`: uses `alloc_pool_huge_folio()`, not
  `alloc_fresh_hugetlb_folio()`.
- `alloc_hugetlb_folio()` and `hugetlb_alloc_folio()` in `mm/hugetlb.c`:
  return `ERR_PTR()` on failure, never NULL.
- `alloc_hugetlb_folio_nodemask()` and `alloc_hugetlb_folio_reserve()`: return
  NULL on failure.
- `alloc_hugetlb_folio_reserve()` user `memfd_alloc_folio()`: sets the folio's
  subpool itself, after `hugetlb_add_to_page_cache()`.
