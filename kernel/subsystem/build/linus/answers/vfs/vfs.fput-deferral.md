- File without `FMODE_OPENED` and without `FMODE_BACKING`: `__fput_deferred()`
  calls `file_free()` at once, in any context; nothing is queued.
- `__fput_sync()`: the body has no check of the caller; it runs `__fput()`
  inline, which calls `might_sleep()`, `->release()`, `dput()` and `mntput()`.
- `__fput_sync()` caller: must be able to sleep and hold nothing those calls
  may need; a kernel thread is not required.
- `close(2)`: uses `fput_close_sync()`, not `__fput_sync()`.
- `filp_close()`: uses `fput_close()`, which defers like `fput()`.
- `fput_close_sync()` and `fput_close()`: declared in `fs/internal.h`, not
  exported; same requirements as `__fput_sync()` and `fput()`.
- `fput_close()` with other references outstanding: correct, only slower;
  `file_ref_put_close()` falls back to `file_ref_put()`. `path_openat()` uses
  it for a file that was never installed.
- No variant waits for `->release()` when another reference exists; all of
  them return at once unless the caller dropped the last one.
- `flush_delayed_fput()`: runs `delayed_fput_list` in the caller's context,
  then flushes `delayed_fput_work`; it does not reach files queued as task
  work.
- `task_work_run()`: not exported; `init_flush_fput()` in `init/do_mounts.h`
  calls `flush_delayed_fput()` and then `task_work_run()`.
- Flush and synchronous release together: see `nfsd_filp_close()` in
  `fs/nfsd/vfs.c`; it takes a reference, calls `filp_close()`, then
  `__fput_sync()`.
