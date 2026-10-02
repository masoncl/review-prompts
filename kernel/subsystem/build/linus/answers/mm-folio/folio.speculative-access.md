- Page-level tests before the reference: `PageLRU()` and other `PF_HEAD` tests
  resolve the head themselves and do not assert on a tail.
- `folio_test_lru()` and the other `folio_test_*()` flag tests before the
  reference: they go through `const_folio_flags()`, which under
  `CONFIG_DEBUG_VM_PGFLAGS` asserts that the folio is not a tail.
  `isolate_migratepages_block()` uses `PageLRU(page)` before the reference
  and `folio_test_lru(folio)` only after it.
- Two ways to take the reference, with different rechecks:

| Reference taken on | Helper | Recheck `page_folio(page) == folio` |
|---|---|---|
| `page_folio(page)` | `folio_try_get()` | required; see `damon_get_folio()` |
| the scanned page itself | `folio_get_nontail_page()` | none; the folio is that page; see `isolate_migratepages_block()` |

- `folio_get_nontail_page()` in `include/linux/mm.h`: returns NULL when the
  scanned page's own `_refcount` is 0, so a tail PFN yields nothing rather
  than a reference on its head.
- `isolate_migratepages_block()` after the reference: rechecks
  `folio_test_lru()`, then `folio_test_clear_lru()`, then the order under the
  lruvec lock; it never compares `page_folio(page)`.
- `damon_get_folio()` in `mm/damon/ops-common.c`: reads only `page_folio()`
  before `folio_try_get()` and tests everything else after it.
- `split_huge_pages_all()` in `mm/huge_memory.c`: a zone walker also rechecks
  `folio_zone(folio)` after the reference.
- Scanner that never takes a reference: use `snapshot_page()` in `mm/util.c`,
  which copies the page and folio and retries on an inconsistent copy; see
  `stable_page_flags()` in `fs/proc/page.c`.
- There is no page_order_unsafe() here; `buddy_order_unsafe()` in
  `mm/page_alloc.h` does that.
