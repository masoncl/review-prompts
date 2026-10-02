- `fuse_read_folio()` and `fuse_readahead()`: both go through iomap,
  `iomap_read_folio()` and `iomap_readahead()`, with `fuse_iomap_ops` and
  `fuse_iomap_read_ops`.
- `fuse_iomap_read_folio_range_async()`: the one read hook for both; with
  `ctx->rac` NULL it calls `fuse_do_readfolio()` synchronously, despite its
  name; with `ctx->rac` set it calls `fuse_handle_readahead()`.
- Unit of a read: a byte range of a folio, not a folio;
  `fuse_do_readfolio()` takes `off` and `len`, and each batch entry carries
  its range in `struct fuse_folio_desc`.
- `fuse_do_readfolio()`: does not mark the folio uptodate, unlock it or
  touch atime; on success `fuse_iomap_read_folio_range_async()` finishes
  the range with `iomap_finish_folio_read()`, and `fuse_read_folio()` calls
  `fuse_invalidate_atime()`.
- `fuse_read_folio()` when READ fails: returns 0 and leaves the folio not
  uptodate; it returns `-EIO` only for `fuse_is_bad()`.
- Failed readahead: there is no folio error flag;
  `iomap_finish_folio_read()` with an error ends the read with the folio not
  uptodate.
- `fuse_readahead()`: does not walk the window; `iomap_readahead()` does,
  and `fuse_readahead()` only sends the batch left in `data.ia`.
- `fuse_short_read()`: zeroes nothing; the tail is zeroed by
  `fuse_copy_folio()` in `fs/fuse/dev.c` because the READ sets
  `page_zeroing`; on virtio-fs `virtio_fs_request_complete()` does it.
