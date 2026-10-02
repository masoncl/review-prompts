- `process_init_limits()`: the clamp to `max_user_bgreq` and
  `max_user_congthresh` is lifted by `capable(CAP_SYS_ADMIN)`, not
  `CAP_SYS_RESOURCE`.
- `request_wait_answer()`, request without `args->abort_on_kill`: a fatal
  signal ends the wait only while the request is still `FR_PENDING`. Once
  `FR_PENDING` is clear, for example after the server has read the request,
  the task waits in an uninterruptible `wait_event()`.
- After that point the wait ends when the request is ended, for example by
  a reply, by `fuse_chan_abort()` (which the request timeout calls) or by
  `fuse_dev_release()` of the device that read it; a signal does not end it.
- `args->force` in `fuse_chan_send()`: sets `FR_FORCE` unless
  `args->abort_on_kill` is set, so the killable wait is skipped.
  `fuse_flush()` sets `args.force`, so it is not killable.
- Request timeout: `fuse_check_timeout()` in `fs/fuse/req_timeout.c`, state
  in `fch->timeout`. `struct fuse_conn` has no `timeout` field, and there is
  no FUSE_DEFAULT_REQ_TIMEOUT.
- `fuse_release()`: calls `write_inode_now(inode, 1)` first when
  `fc->writeback_cache` is set, so the closing task waits for writeback.
  Only the `FUSE_RELEASE` request is asynchronous.
- Writeback: there is no tmp_page copy and no NR_WRITEBACK_TEMP. The
  page-cache folio itself is under writeback
  (`fuse_iomap_writeback_range()`), so `folio_wait_writeback()` on a FUSE
  folio waits for the server.
- `mapping_writeback_may_deadlock_on_reclaim()`: called only in
  `mm/vmscan.c`. `mm/migrate.c` does not test it and calls
  `folio_wait_writeback()` in `MIGRATE_SYNC` mode.
- `fuse_sync_fs()`: returns 0 unless `fc->sync_fs`, which is set for fuseblk
  in `fuse_fill_super_common()` and in `fs/fuse/virtio_fs.c`.
- `SB_I_UNTRUSTED_MOUNTER`: set in `fuse_sb_defaults()`, only when
  `sb->s_user_ns` is not `init_user_ns`.
- `SB_I_NODEV`: set by `alloc_super()` in `fs/super.c` when `s_user_ns` is
  not `init_user_ns`. `fs/fuse` forces neither nosuid nor nodev.
- **Potentially unsafe usage**: a synchronous `fuse_simple_request()` from
  the final `fput()` of a file.
  - Unsafe: when the server is a local process; release requests set
    `args->force`, so the task waits in `request_wait_answer()` with no
    signal escape.
  - Safe: `fuse_simple_background()` with `args->end` set, as
    `fuse_file_put()` does when `sync` is false.
  - Safe: when `fc->auto_submounts` is set, which only
    `virtio_fs_get_tree()` does; `fuse_file_release()` passes it as `sync`.
  - Safe: `fuse_sync_release()` on the error path of an open or create, as
    in `fuse_open()`; the caller is the opener and the function warns if
    `ff->count` is above 1.
