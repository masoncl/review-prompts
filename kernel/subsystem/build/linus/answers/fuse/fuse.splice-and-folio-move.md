- `page_replace`: set only by `fuse_send_readpages()` in `fs/fuse/file.c`,
  the readahead path; `fuse_do_readfolio()` does not set it, so its reply is
  copied.
- Pipe buffer: `fuse_try_move_folio()` tests
  `buf->len == folio_size(oldfolio)`; it does not test `buf->offset`.
- Previous buffer: `fuse_copy_folio()` tries a move only when `cs->len` is 0,
  so the data must start at a pipe buffer boundary.
- Large stolen folio: `folio_test_large(newfolio)` falls back to the copy.
- `fuse_check_folio()`: rejects a mapped folio, a non-NULL `mapping`, or any
  flag in `PAGE_FLAGS_CHECK_AT_PREP` outside the set it lists; `PG_lru`,
  `PG_active`, `PG_workingset`, `PG_reclaim`, `PG_waiters`, `PG_locked`,
  `PG_referenced`, `LRU_GEN_MASK` and `LRU_REFS_MASK` are tolerated.
- `fuse_check_folio()`: makes no reference count test; the sole-owner test
  is in the pipe's `try_steal` operation, for example
  `generic_pipe_buf_try_steal()`.
- Uptodate: `fuse_try_move_folio()` clears it on the stolen folio before the
  check, so it never causes a fallback.
- Abort: `lock_request()` runs before `replace_page_cache_folio()`; on
  `-ENOENT` the page cache is unchanged, the stolen folio is unlocked and the
  function returns `-ENOENT`.
- No `FR_ABORTED` test follows the replace.
- On success the request stays locked and `cs->len` is 0.
- Old folio: no test for a changed slot or truncation; the folio lock held by
  the read path is what keeps it in the mapping.
- New folio: stays locked after the move; `fuse_readpages_end()` ends the
  read through `iomap_finish_folio_read()` on `ap->folios[i]`.
- **Unsafe usage**: setting `page_replace` on a request whose folios are not
  locked page cache folios with a reference owned by the folio array.
  - Safe: `fuse_send_readpages()`, whose folios come locked from readahead
    with a `folio_get()` from `fuse_handle_readahead()`;
    `replace_page_cache_folio()` asserts both folios locked with
    `VM_BUG_ON_FOLIO()`, and `fuse_try_move_folio()` unlocks the old folio
    and drops the array's reference.
- **Unsafe usage**: using a folio pointer saved before the request, after a
  `page_replace` request has ended.
  - Safe: read the folio back from `ap->folios[i]`, as `fuse_readpages_end()`
    does; `fuse_try_move_folio()` stores the new folio there.
