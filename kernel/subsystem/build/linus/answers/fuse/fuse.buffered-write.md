- `fuse_perform_write()`: always sends synchronous WRITEs.
- Writeback cache on: `fuse_cache_write_iter()` calls
  `iomap_file_buffered_write()` with `fuse_iomap_ops` and
  `fuse_iomap_write_ops`; it does not call `generic_file_write_iter()`, and
  there is no fuse_write_begin or fuse_write_end in this tree.
- `inode_lock()`: taken by `fuse_cache_write_iter()` itself, in both modes.
- Partial write to a non-uptodate range, writeback cache on:
  `fuse_iomap_read_folio_range()` reads the missing range synchronously.
- `fuse_fill_write_pages()`: never reads from the server.
- Uptodate on the write-through path: `fuse_fill_write_pages()` marks a
  folio uptodate at copy time when the whole folio was copied;
  `fuse_send_write_pages()` changes no uptodate state, whatever the reply.
- Folio locks across the WRITE: uptodate folios are unlocked before the
  send; only a last, non-uptodate folio stays locked
  (`ia->write.folio_locked`).
- `fc->handle_killpriv_v2` set and `setattr_should_drop_suidgid()` true:
  `writeback` stays false, so the write goes through `fuse_perform_write()`
  even with the writeback cache on.
- `IOCB_DIRECT` in `fuse_cache_write_iter()`: `generic_file_direct_write()`
  first; what is left goes through `fuse_perform_write()`, also with the
  writeback cache on.
- Dirty times: there is no FUSE_I_MTIME_DIRTY here; `fuse_write_inode()`
  calls `fuse_flush_times()` each time the VFS writes the inode.
