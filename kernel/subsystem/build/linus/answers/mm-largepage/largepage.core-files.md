| Job | File in this tree | Easy to miss |
|---|---|---|
| hugetlb sysfs | `mm/hugetlb_sysfs.c` | Exists; built with `mm/hugetlb.c` under `CONFIG_HUGETLBFS`. |
| hugetlb sysctl | `mm/hugetlb_sysctl.c` | Exists. `__nr_hugepages_store_common()`, which the sysfs and sysctl stores both call, is in `mm/hugetlb.c`. |
| hugetlb private header | `mm/hugetlb_internal.h` | Exists; included only by `mm/hugetlb.c` and the two files above. |
| rmap calls, PTE, PMD and PUD level | `mm/rmap.c` for add and remove; `include/linux/rmap.h` for dup and share | The dup and share forms, for example `folio_try_dup_anon_rmap_ptes()` and `folio_try_share_anon_rmap_pmd()`, are inline in the header. The single-PTE forms such as `folio_add_anon_rmap_pte()` are macros in `include/linux/rmap.h`. The level type is `enum pgtable_level` in `include/linux/pgtable.h`; there is no enum rmap_level. |
| rmap calls, hugetlb | `mm/rmap.c` and `include/linux/rmap.h` | `hugetlb_add_anon_rmap()` and `hugetlb_add_new_anon_rmap()` are in `mm/rmap.c`; the other hugetlb rmap helpers are inline in the header. |
| Large folio swap-in, anonymous | `mm/memory.c` and `mm/swap_state.c` | There is no alloc_swap_folio(). `do_swap_page()` picks orders with `thp_swapin_suitable_orders()`; `swapin_sync()` allocates in `swap_cache_alloc_folio()`. Only on `SWP_SYNCHRONOUS_IO` devices; `swapin_readahead()` reads order 0. |
| Large folio swap-in, shmem | `mm/shmem.c` | `shmem_swap_alloc_folio()`, called from `shmem_swapin_folio()`; it calls the same `swapin_sync()`. |
