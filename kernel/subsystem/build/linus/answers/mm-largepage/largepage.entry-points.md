| Job | Start reading from | Name or path that differs in this tree |
|---|---|---|
| Fault in an anonymous PMD-sized folio | `do_huge_pmd_anonymous_page()` | Mapping helper is `map_anon_folio_pmd_pf()`; `map_anon_folio_pmd_nopf()` is the form `mm/khugepaged.c` uses. |
| Split a huge PMD | `__split_huge_pmd()` | It calls `split_huge_pmd_locked()`, which calls `__split_huge_pmd_locked()`. With the PMD lock already held, enter at `split_huge_pmd_locked()`, as `mm/rmap.c` does; it has `VM_WARN_ON_ONCE()` for an address that is not PMD-aligned. |
| Split a large folio, uniform | `__split_huge_page_to_list_to_order()` in `mm/huge_memory.c` | `split_huge_page_to_list_to_order()` is an inline wrapper in `include/linux/huge_mm.h`. Both reach `__folio_split()`. |
| Split a large folio, non-uniform | `folio_split()` | No function named try_folio_split or try_folio_split_to_order exists; `folio_split_or_unmap()` in `mm/truncate.c` calls `folio_split()` directly. |
| Split an already unmapped anonymous folio | `folio_split_unmapped()` | Does not go through `__folio_split()`; calls `__folio_freeze_and_split_unmapped()` itself. |
| Collapse, both callers | `collapse_single_pmd()` | Called by `collapse_scan_mm_slot()` for khugepaged and by `madvise_collapse()`. There is no khugepaged_scan_mm_slot(). |
| Collapse, anonymous | `collapse_scan_pmd()` | There is no hpage_collapse_scan_pmd(). It calls `mthp_collapse()`, the only caller of `collapse_huge_page()`, which takes an `order` and can build a folio smaller than PMD size. |
| Collapse, file and shmem | `collapse_scan_file()`, then `collapse_file()` | There is no hpage_collapse_scan_file(). |
| Allocate a hugetlb folio | `alloc_hugetlb_folio()` | It does reservation and subpool accounting, then calls `hugetlb_alloc_folio()`, which charges cgroups and calls `dequeue_hugetlb_folio()` or `alloc_buddy_hugetlb_folio()`. There is no dequeue_hugetlb_folio_vma() or alloc_buddy_hugetlb_folio_with_mpol(). |
| Reserve hugetlb pages at mmap | `hugetlb_reserve_pages()` | Called from `hugetlbfs_file_mmap()`, installed as `.mmap` in `hugetlbfs_file_operations`. There is no hugetlbfs_file_mmap_prepare(). |
| Handle a hardware memory error | `memory_failure()` | hugetlb branch is `try_memory_failure_hugetlb()`; there is no memory_failure_hugetlb(). `memory_failure()` goes on to normal page handling only when it returns `-ENOENT`. |
