- Large-folio check: the only one is
  `VM_BUG_ON_PGFLAGS(n > 0 && !test_bit(PG_head, ...))` in `folio_flags()` and
  `const_folio_flags()`, compiled in only with `CONFIG_DEBUG_VM_PGFLAGS`;
  there is no `VM_BUG_ON_FOLIO()` in the accessors.
- `PF_SECOND` and `FOLIO_PF_SECOND`: defined, but no accessor in this tree is
  declared with them; all three second-page flags use
  `FOLIO_FLAG(name, FOLIO_SECOND_PAGE)`.
- `PF_SECOND`: takes `&page[1]` of the page it is given after asserting
  `PageHead(page)`; it does not look up the head.
- Bit choice: not one of the low 8 bits, which hold the order
  (`folio_large_order()` reads `_flags_1 & 0xff`), and not a bit whose page
  accessor is `PF_ANY`, since those are set on a tail page's own word, as
  `SetPageAnonExclusive()` does with `PG_owner_2`.
- `PAGE_FLAGS_SECOND` in `include/linux/page-flags.h`: a new second-page flag
  must be added to it; `__free_pages_prepare()` clears the mask from `page[1]`
  before the tail pages are checked against `PAGE_FLAGS_CHECK_AT_FREE`.
- Accessor forms: only atomic test, set and clear exist for `large_rmappable`,
  `partially_mapped` and `has_hwpoisoned`; no non-atomic form is declared.
- Order byte: `folio_set_order()` in `mm/internal.h` and `folio_reset_order()`
  in `include/linux/mm.h` rewrite it with a plain read-modify-write of
  `_flags_1`, which can lose an atomic flag update made to that word at the
  same time; `__split_folio_to_order()` calls `folio_set_order()` with the
  refcount frozen.
- **Potentially unsafe usage**: using a second-page accessor with no folio
  reference.
  - Unsafe: when nothing stops a split or a free, after which `page[1]` is
    another folio's head or a free page.
  - Safe: with a reference held; `__folio_freeze_and_split_unmapped()` in
    `mm/huge_memory.c` must win `folio_ref_freeze()` before
    `__split_folio_to_order()` runs.
  - Safe: at refcount 0 with the `deferred_split_lru` list lock held and the
    folio still on the list, as `deferred_split_isolate()` and
    `__folio_unqueue_deferred_split()` do; `__folio_put()` and
    `folios_put_refs()` call `folio_unqueue_deferred_split()`, which takes
    that lock, before the pages are freed.
  - Safe: at refcount 0 in the path that dropped the last reference, before
    it frees the pages, as `__folio_put()` does through
    `folio_unqueue_deferred_split()`; `folio_try_get()` and
    `folio_ref_freeze()` both fail on a zero count.
  - Safe: on the copy made by `snapshot_page()`, as `stable_page_flags()` in
    `fs/proc/page.c` does; the second page is inside the
    `struct page_snapshot`.
