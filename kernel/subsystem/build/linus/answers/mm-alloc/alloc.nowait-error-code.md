- `__filemap_get_folio_mpol()` with `FGP_NOWAIT`: returns `ERR_PTR(-EAGAIN)`
  when the allocation or `filemap_add_folio()` fails with `-ENOMEM`; no
  other error is rewritten.
- Mask rewrite: `gfp &= ~GFP_KERNEL; gfp |= GFP_NOWAIT`, so `__GFP_IO` and
  `__GFP_FS` are cleared as well; it happens only in the `FGP_CREAT` branch.
- Callers that pass the code up: `iomap_write_begin()` in
  `fs/iomap/buffered-io.c` and `prepare_one_folio()` in `fs/btrfs/file.c`
  return `PTR_ERR(folio)`.
- Callers that discard the code: those that use `FGP_NOWAIT` for an optional
  extra folio skip it on any `IS_ERR()` result, for example in
  `fs/squashfs/file.c`, `fs/ubifs/file.c`, `fs/nfs/dir.c`.
- `pagecache_get_page()` in `mm/folio-compat.c`: turns every error into
  `NULL`, so `grab_cache_page_nowait()` callers never see `-EAGAIN`.
