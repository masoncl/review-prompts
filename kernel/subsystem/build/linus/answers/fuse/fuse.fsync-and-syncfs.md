- Bucket count: taken by `fuse_writepage_add_to_bucket()`, called from
  `fuse_writepage_args_setup()`; there is no fuse_sync_bucket_get or
  fuse_sync_bucket_inc in this tree.
- Time of the count: when the request is set up, before it is queued or
  sent, so syncfs also waits for requests still on `fi->queued_writes`.
- `fc->sync_fs` clear: `fuse_writepage_add_to_bucket()` takes no count and
  `wpa->bucket` stays NULL.
- `fuse_sync_fs_writes()`: returns without swapping when the old count
  is 1; otherwise the new bucket holds one extra count until the old bucket
  drains, so a later syncfs also waits for the earlier buckets.
- Dirty folios before `fuse_sync_fs()`: `fuse_sb_defaults()` sets
  `SB_I_NO_DATA_INTEGRITY`, and with it `sync_inodes_sb()` only wakes the
  flusher and returns, so dirty data is not known to be written or waited
  for.
- Before FSYNC, after `fuse_sync_writes()`: `fuse_fsync()` calls
  `file_check_and_advance_wb_err()`, then `sync_inode_metadata(inode, 1)`;
  an error from either skips FSYNC.
- FSYNCDIR: sent by `fuse_dir_fsync()` in `fs/fuse/dir.c`, not by
  `fuse_fsync()`.
- Writeback error routes, all fed by `mapping_set_error()` in
  `fuse_writepage_end()`:

| Caller | Where the error is read |
|---|---|
| fsync | `file_check_and_advance_wb_err()` in `fuse_fsync()` |
| close | `filemap_check_errors()` in `fuse_flush()` |
| syncfs | `sb->s_wb_err`, checked in the `syncfs` syscall in `fs/sync.c` |
| munmap | none; `fuse_vma_close()` stores the `write_inode_now()` result with `mapping_set_error()` for a later caller |
