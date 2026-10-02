- `page_is_unmovable()` in `mm/page_isolation.c`: holds neither
  `hugetlb_lock` nor a reference.
- `page_is_unmovable()`: calls `size_to_hstate(PAGE_SIZE << order)`, with
  `order` read once by `compound_order()` and rejected above
  `MAX_FOLIO_ORDER`; a NULL hstate counts as unmovable.
- Setting the type: `init_new_hugetlb_folio()` calls `__folio_set_hugetlb()`
  without `hugetlb_lock`, on a frozen folio not yet in a pool.
- Clearing the type: every `__folio_clear_hugetlb()` call is under
  `hugetlb_lock`, so a positive test stays positive while the lock is held.
- `remove_hugetlb_folio()`: clears the type itself unless the folio is
  vmemmap-optimised; an optimised folio keeps it until after its vmemmap is
  restored, for example in `__update_and_free_hugetlb_folio()`.
- Under `hugetlb_lock`, type set and refcount 0: the folio is in the pool
  only if `HPG_freed` is set; otherwise it is being allocated or freed.
- `HPG_freed` clear with refcount 0: `dissolve_free_hugetlb_folio()` and
  `alloc_and_dissolve_hugetlb_folio()` drop the lock and retry.
- Taking a reference from a PFN: `folio_isolate_hugetlb()` and
  `get_hwpoison_hugetlb_folio()` do it under `hugetlb_lock`, after testing the
  type and `HPG_migratable`; `get_hwpoison_hugetlb_folio()` does not need
  `HPG_migratable` when `unpoison` is true. There is no
  isolate_hugetlb() here.
- After the reference is taken: recheck `page_folio(page)`, because demotion
  can change the folio; see `__get_hwpoison_page()` and `do_migrate_range()`.
- Lockless reads of `HPG_*` flags: usable as a hint only;
  `scan_movable_pages()` in `mm/memory_hotplug.c` bounds `folio_nr_pages()`
  and lets the caller revalidate.
- **Unsafe usage**: `folio_hstate()` on a folio after `remove_hugetlb_folio()`.
  - Safe: carry `h` from before the removal, as `free_huge_folio()` does when
    it calls `update_and_free_hugetlb_folio()`; `folio_hstate()` asserts the
    type with `VM_BUG_ON_FOLIO()`.
  - Safe: `size_to_hstate(folio_size(folio))`, as `free_hpage_workfn()` does.
