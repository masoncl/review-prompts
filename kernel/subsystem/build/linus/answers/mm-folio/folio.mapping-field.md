- Flag names: there is no PAGE_MAPPING_KSM or PAGE_MAPPING_MOVABLE in the
  code here; the only names are `FOLIO_MAPPING_ANON` (0x1),
  `FOLIO_MAPPING_ANON_KSM` (0x2), `FOLIO_MAPPING_KSM` (both bits) and
  `FOLIO_MAPPING_FLAGS` (mask of both), in `include/linux/page-flags.h`.
- `FOLIO_MAPPING_ANON_KSM` is bit 1 alone, not the KSM encoding; a KSM folio
  is `(mapping & FOLIO_MAPPING_FLAGS) == FOLIO_MAPPING_KSM`.
- Movable-ops pages: nothing is encoded in `mapping`; they are found with
  `page_has_movable_ops()` (`PG_movable_ops` plus page type), and the ops
  come from `page_movable_ops()` in `mm/migrate.c`.
- `folio_test_anon()`: true for KSM folios too; `folio_anon_vma()` returns
  NULL for KSM.
- `folio_mapping()` test order: slab, then swap cache, then flag bits. An
  anon folio in the swap cache therefore returns `&swap_space`, not NULL.
- `folio_mapping()` does no masking: any bit of `FOLIO_MAPPING_FLAGS` gives
  NULL; `folio_raw_mapping()` in `mm/internal.h` is the helper that masks.
- `swap_address_space()` in `mm/swap.h`: ignores its argument and returns the
  single `swap_space`, whose initialiser sets only `a_ops`
  (`mm/swap_state.c`), so `->host` is NULL; without `CONFIG_SWAP` it returns
  NULL.
- Swap-cache folio, raw field: an anon folio keeps its tagged anon_vma; a
  shmem folio has NULL (`shmem_delete_from_page_cache()`), so NULL plus
  `folio_test_swapcache()` is not truncation; `get_futex_key()` tests for
  this.
- Tail pages: `page->mapping` is `TAIL_MAPPING`, not NULL
  (`prep_compound_tail()` in `mm/internal.h`), except in tails 1 and 2, and
  tail 3 of a hugetlb folio, where `struct folio` fields overlay the word;
  see `free_tail_page_prepare()` in `mm/page_alloc.c`.
- DAX folio: NULL with non-zero `folio->share` means shared by several files;
  see `dax_folio_is_shared()` in `fs/dax.c`.
- Anon pointer lifetime: the anon_vma in `mapping` is trusted only while
  `folio_mapped()`; `folio_get_anon_vma()` and `folio_lock_anon_vma_read()`
  in `mm/rmap.c` also warn, with `CONFIG_DEBUG_VM`, if the folio is not
  locked.
- NULL on a looked-up folio is not only truncation:
  `replace_page_cache_folio()`, `collapse_file()` and
  `shmem_delete_from_page_cache()` also clear it.
- `move_to_new_folio()` clears it too, on a non-anon source, but migration
  fails while the lookup's reference is held (`folio_ref_freeze()` in
  `__folio_migrate_mapping()`).
- NULL after those paths: the data is still in the file under another folio
  or a swap entry, so a lookup retries instead of treating the index as a
  hole, as `__filemap_get_folio_mpol()` and `filemap_fault()` do.
- `FGP_LOCK` lookups (`filemap_lock_folio()`, `FGP_WRITEBEGIN`): the recheck
  and retry are already done in `__filemap_get_folio_mpol()` in
  `mm/filemap.c`; `__filemap_get_folio()` is an inline wrapper in
  `include/linux/pagemap.h`.
- Callers that lock separately get no recheck from the lookup; the literal
  pattern is in `invalidate_inode_pages2_range()`.
  `truncate_inode_pages_range()` has no compare of its own;
  `find_lock_entries()` and `truncate_inode_folio()` do it.
- The folio lock is the lock the clearing paths share: `page_cache_delete()`
  also holds the `i_pages` lock, but `move_to_new_folio()` and
  `collapse_file()` clear the field with only the folio lock.
- **Potentially unsafe usage**: dereferencing `folio->mapping` as a
  `struct address_space *` on a folio held only by a reference.
  - Unsafe: when nothing excludes removal; the field can become NULL between
    the test and the use, and may be a tagged anon or KSM pointer.
  - Safe: folio locked and `folio->mapping == mapping` checked after locking,
    as `filemap_fault()` does; the clearing paths assert the folio lock (for
    example `page_cache_delete()`).
  - Safe: `PG_writeback` set; `truncate_inode_pages_range()` waits for
    writeback, `find_lock_entries()` skips such folios and
    `migrate_folio_unmap()` waits or gives up. `__folio_end_writeback()`
    relies on this.
  - Safe: a page of the folio is mapped and the page table lock is held, as
    `zap_present_folio_ptes()` calling `folio_mark_dirty()`;
    `truncate_cleanup_folio()` unmaps before removal and
    `filemap_unaccount_folio()` asserts the folio is unmapped.
  - Safe: one `READ_ONCE()` under RCU or with IRQs off, NULL and flag bits
    tested, used only to read the `struct address_space` or inode, as
    `gup_fast_folio_allowed()` and `get_futex_key()` do. This relies on
    `destroy_inode()` in `fs/inode.c`, which uses `call_rcu()` unless the
    filesystem has `->destroy_inode` and no `->free_inode`.
