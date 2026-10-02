- `FOPEN_CACHE_DIR` without a server reply: `fuse_file_open()` in
  `fs/fuse/file.c` defaults a directory to
  `FOPEN_KEEP_CACHE | FOPEN_CACHE_DIR` when `fc->no_opendir` is set or
  `FUSE_OPENDIR` returns `-ENOSYS`.
- `FOPEN_KEEP_CACHE` on a directory: only decides whether `fuse_dir_open()`
  calls `invalidate_inode_pages2()`; the mtime, iversion and epoch tests do
  not look at it.
- `fi->rdc.epoch`: a third key beside `mtime` and `iversion`; recorded when
  caching starts and compared with `fc->epoch`.
- Validity test in `fuse_readdir_cached()`: runs only when `ctx->pos` is 0; a
  reader in mid-stream does not test for a directory change.
- mtime refresh at position 0: `fuse_update_attributes()` is called only with
  `fc->auto_inval_data`.
- `fuse_rdc_reset()`: static in `fs/fuse/readdir.c`, called only from
  `fuse_readdir_cached()`; it resets the `rdc` fields and removes no pages.
- `fuse_dir_changed()`: does not touch `rdc`; it bumps the iversion, which the
  next reader at position 0 compares.
- `FUSE_NOTIFY_INVAL_INODE` on a directory with offset >= 0: drops the cached
  pages of the given range, so the next cached read of one of them hits the
  missing-page reset.
- Version mismatch between `ff->readdir.version` and `fi->rdc.version`: the
  stream restarts at the start of the cache and scans for `ctx->pos`; it does
  not by itself switch to an uncached read.
- `ff->readdir`: holds `pos`, `cache_off` and `version` only; it has no lock
  member in this tree.
