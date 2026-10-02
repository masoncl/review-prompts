- Inode states by sign of `fi->iocachectr`: caching (> 0), neutral (0),
  uncached (< 0); there is no direct-I/O mode, and a `FOPEN_DIRECT_IO` open
  without `FOPEN_PASSTHROUGH` takes no count.
- Negative count: passthrough opens plus one per direct write that holds
  the shared inode lock, taken by `fuse_dio_lock()` with
  `fuse_inode_uncached_io_start(fi, NULL)` and dropped by
  `fuse_dio_unlock()`.
- Conflicting open: `fuse_file_io_open()` returns `-EIO` for every failure;
  the inner `-ETXTBSY`, `-EBUSY`, `-EINVAL` and `-ENOENT` reach only
  `pr_debug()`.
- Caching open against parallel direct writes that hold the count: does not
  fail; `fuse_file_cached_io_open()` sleeps in `wait_event()` until the
  count is no longer negative.
- Parallel direct write against caching mode: does not fail;
  `fuse_dio_lock()` retakes the inode lock exclusive.
- `fuse_file_mmap()`: returns the error of `fuse_file_cached_io_open()`
  unchanged, not `-EIO`.
- `fc->writeback_cache`: not tested in `fs/fuse/iomode.c`;
  `process_init_reply()` leaves `fc->passthrough` clear when the server set
  `FUSE_WRITEBACK_CACHE`, so a `FOPEN_PASSTHROUGH` open on such a mount gets
  `-EIO`.
- Server with `fc->no_open`: does not bypass io modes; `ff->args` is set for
  every regular file, so the `!ff->args` tests in `fs/fuse/iomode.c` do not
  fire and the open enters caching mode.
