- `fc->no_lock` and `fc->no_flock`: written only in `process_init_reply()`
  in `fs/fuse/inode.c`; an `-ENOSYS` reply to a lock request does not set
  them.
- `fc->no_flock` for protocol minor < 17: follows `FUSE_POSIX_LOCKS`, not
  `FUSE_FLOCK_LOCKS`; for minor < 6 both kinds stay in the kernel.
- There is no flock field in `struct fuse_conn`; `fc->no_flock` is the gate
  and `ff->flock` is per open file.
- Local POSIX path: `posix_lock_file(file, fl, NULL)` and
  `posix_test_lock()`, not `locks_lock_file_wait()`.
- `fuse_setlk()`: only sends the request; it records nothing in the kernel
  lock lists.
- `fuse_setlk()`: has no test of `FL_CLOSE` or `FL_CLOSE_POSIX`.
- Pid sent to the server: the result of `pid_nr_ns()`, 0 when the task is
  not visible in `fc->pid_ns` or the type is `F_UNLCK`; `fuse_setlk()` has
  no `-EOVERFLOW` test for a pid of 0.
- `fuse_lock_owner_id()`: 32 XTEA rounds over the pointer, keyed by
  `fc->scramble_key`.
- Owner pointer: `fuse_lk_fill()` sends `fl->c.flc_owner` whatever the lock
  kind; for OFD locks `fcntl_setlk()` in `fs/locks.c` sets it to the
  `struct file`, and `struct fuse_lk_in` has no OFD marker.
- `fuse_flush()`: the request it builds is `FUSE_FLUSH` carrying
  `lock_owner`; it does not call `fuse_setlk()`.
- `fuse_flush()` returns before sending when the file has `FOPEN_NOFLUSH`
  and `fc->writeback_cache` is clear, and skips the request when
  `fc->no_flush` is set.
- `FUSE_RELEASE_FLOCK_UNLOCK`: set by `fuse_file_release()`, only when
  `ff->args` is non-NULL and `ff->flock` is set.
- `ff->flock`: set by `fuse_file_flock()` only after `fuse_setlk()` returns
  0.
- flock kept in the kernel (`fc->no_flock`): released at close by
  `locks_remove_flock()` in `fs/locks.c`, which calls `fuse_file_flock()`
  and so `locks_lock_file_wait()`.
