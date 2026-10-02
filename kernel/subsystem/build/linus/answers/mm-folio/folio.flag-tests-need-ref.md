- `folio_flags()` and `const_folio_flags()`: make no poison check, so no
  `folio_test_*()` accessor runs `PF_POISONED_CHECK()`; of the flag accessors,
  only the page accessors (through their policy) and `PageHead()` do, and only
  with `CONFIG_DEBUG_VM_PGFLAGS`.
- Tail pointer through a folio accessor: with `CONFIG_DEBUG_VM_PGFLAGS`,
  `folio_flags()` asserts `compound_info & 1` is clear, and for index 1 that
  `PG_head` is set.
- Tail pointer through a page test accessor: no assertion on the tail;
  `PF_HEAD` and `PF_NO_TAIL` read the head, `PF_ANY` and `PF_NO_COMPOUND` read
  the page given.
- `PagePoisoned()`: true only for a memmap that `page_init_poison()` filled,
  at memmap allocation and in `remove_pfn_range_from_zone()`
  (`mm/memory_hotplug.c`).
- `page_init_poison()`: empty without `CONFIG_DEBUG_VM`, and the `vm_debug`
  boot parameter can turn it off, see `setup_vm_debug()` in `mm/debug.c`.
- Freed page: no check fires on a flag test; `__free_pages_prepare()` clears
  `PAGE_FLAGS_CHECK_AT_PREP`, which is every flag except `PG_hwpoison`, from
  the word.
- `free_page_is_bad()` and `check_new_pages()` in `mm/page_alloc.c`: run only
  when the `check_pages_enabled` static key is on, which is the default with
  `CONFIG_DEBUG_VM`.
- `snapshot_page()` in `mm/util.c`: copies the page and its folio into a
  `struct page_snapshot` with no reference; `__dump_page()`,
  `stable_page_flags()` and `get_kpage_count()` work on the copy.
- `snapshot_page_is_faithful()`: false when the copy fell back to treating the
  page as a single page.
