- Data in flight: the page-cache folio itself is in the WRITE; there is no
  temporary copy, no fi->writepages tree and no
  fuse_wait_on_page_writeback in this tree.
- Names: the file is taken with `fuse_write_file_get()`; the test for
  sending the pending request is `fuse_folios_need_send()`.
- `fuse_iomap_writeback_range()`: does no per-folio accounting;
  `iomap_writeback_folio()` starts folio writeback before it calls the hook.
- `fuse_writepage_finish()`: only calls `iomap_finish_folio_write()` per
  entry and wakes `fi->page_waitq`; it updates no statistics.
- Writeback ending with no reply: `fuse_send_writepage()` finishes the
  request at `out_free` when it lies wholly beyond the crop size or when
  queuing fails.
- Request blocked by `FUSE_NOWRITE`: it sits on `fi->queued_writes` and its
  folios stay under writeback until the release.
- Two kinds of wait: `folio_wait_writeback()` waits for one folio;
  `fuse_sync_writes()` waits for `fi->writectr`, that is for sent requests.
- `folio_wait_writeback()` under `fs/fuse/`: `fuse_page_mkwrite()`,
  `fuse_send_write_pages()` and `fuse_launder_folio()`.
- `fuse_page_mkwrite()`: waits unconditionally; it does not call
  `folio_wait_stable()`.
- `fuse_sync_writes()` callers: `fuse_fsync()`, `fuse_direct_io()` and
  `fuse_writeback_range()`.
- `fuse_flush()`: does not call `fuse_sync_writes()`; it waits through
  `write_inode_now(inode, 1)`.
- Buffered write with the writeback cache on: `folio_wait_stable()` waits
  only with `AS_STABLE_WRITES`; nothing under `fs/fuse/` sets it, but
  `setup_bdev_super()` sets `SB_I_STABLE_WRITES` for a fuseblk mount on a
  device with stable writes.
