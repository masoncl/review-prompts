- **Unsafe usage**: passing `filemap_add_folio()` a folio that is locked or
  that another task can already reach.
  - Unsafe: `filemap_add_folio()` sets and (on failure) clears the lock bit
    with non-atomic `__folio_set_locked()` and `__folio_clear_locked()`.
  - Safe: a freshly allocated, unlocked folio, as `filemap_create_folio()`
    does.
  - Safe: `__filemap_add_folio()` on a folio the caller locked itself, as
    `hugetlb_add_to_page_cache()` does; `__filemap_add_folio()` asserts
    locked.
- Folio must not be memcg-charged already: `commit_charge()` in
  `mm/memcontrol.c` has `VM_BUG_ON_FOLIO(folio_memcg_charged(folio))`.
- `filemap_add_folio()` failure: folio comes back unlocked, uncharged,
  `folio->mapping` NULL, refcount as on entry, and `folio->index` left set
  when `__filemap_add_folio()` ran; the caller must not call
  `folio_unlock()`, and `filemap_create_folio()` only does `folio_put()`.
- `mem_cgroup_charge()` failure: its error is returned before the lock bit is
  touched.
- `AS_KERNEL_FILE` mapping: the charge is made with `root_mem_cgroup` active,
  and success raises `NR_KERNEL_FILE_PAGES`; `filemap_unaccount_folio()`
  lowers it.
- Stats: `__filemap_add_folio()` raises `NR_FILE_PAGES` and `NR_FILE_THPS`
  only; `NR_SHMEM` is never touched, since swapbacked folios are asserted out.
- `workingset_refault()`: skipped when `gfp` has `__GFP_WRITE`.
- Success path: `WARN_ON_ONCE(folio_test_active(folio))` before the LRU add.
- `__filemap_add_folio()` direct callers: `hugetlb_add_to_page_cache()` is
  the only one besides `filemap_add_folio()`; that path does no memcg charge,
  no LRU add and no refault handling.
- shmem: does not call `__filemap_add_folio()`; it has
  `shmem_add_to_page_cache()` in `mm/shmem.c`.
