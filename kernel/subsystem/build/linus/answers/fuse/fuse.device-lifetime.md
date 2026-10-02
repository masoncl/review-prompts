- `file->private_data` is never NULL on an open device file:
  `fuse_dev_open()` allocates the `struct fuse_dev`, with `ref` 1 and no
  `pq.processing` array.
- States of `fud->chan`:
  1. NULL after `fuse_dev_open()`
  2. the channel, set by `cmpxchg()` from NULL in
     `fuse_dev_install_with_pq()` under `fch->lock`
  3. `FUSE_DEV_CHAN_DISCONNECTED`, set by `xchg()` in `fuse_dev_release()`
- No other change: `fuse_dev_release()` goes to state 3 from state 1 as well
  as from state 2, and an install after release fails.
- Install callers: `fuse_dev_install()` (mount, under `fuse_mutex`; virtiofs;
  CUSE through `fuse_dev_alloc_install()`) and `fuse_dev_ioctl_clone()`.
- `fuse_dev_ioctl_clone()`: takes no `fuse_mutex`; returns `-EINVAL` when the
  `cmpxchg()` fails.
- Sync INIT: there is no FUSE_DEV_SYNC_INIT pointer value;
  `FUSE_DEV_IOC_SYNC_INIT` sets `fud->sync_init`, allowed only while
  `fud->chan` is NULL.
- `fuse_get_dev()`: never returns NULL; `ERR_PTR(-EPERM)` when not installed,
  but with `fud->sync_init` it sleeps interruptibly on `fuse_dev_waitq` until
  installed.
- `__fuse_get_dev()`: returns NULL when not installed and never sleeps; the
  write paths use it and return `-EPERM`.
- `fuse_dev_release()`: when the old value was a channel, ends the requests
  on `fpq->processing`, unlinks the device, aborts if `fch->devices` became
  empty, and drops the connection reference; `struct fuse_conn` and
  `struct fuse_chan` have no dev_count field.
- `struct fuse_dev` is freed by the last `fuse_dev_put()`, which need not be
  the one in `fuse_dev_release()`; `fuse_opt_fd()` takes a second `fud->ref`
  with `fuse_dev_grab()` and does not keep the file, and `fuse_free_fsc()`
  drops it.
- `fuse_dev_release()` takes `fch->lock` before `list_del()` so that a
  concurrent `fuse_dev_install_with_pq()` has finished its `list_add_tail()`.
- First read of `fud->chan`: through `fuse_dev_chan_get()`, which is
  `smp_load_acquire()`.
- **Potentially unsafe usage**: dereferencing the value of `fud->chan`.
  - Unsafe: when the caller holds only `fud->ref` and not the open file, as a
    mount context does; the value can be `FUSE_DEV_CHAN_DISCONNECTED`, or a
    channel whose connection reference `fuse_dev_release()` already dropped.
  - Safe: compare only, as `fuse_dev_is_installed()` and `fuse_dev_verify()`
    do.
  - Safe: in a file operation of the device file after `fuse_get_dev()` or
    `__fuse_get_dev()` succeeded, as `fuse_dev_do_read()` does with a plain
    `fud->chan`; release cannot run during the operation.
  - Safe: in the last `fuse_dev_put()`, which tests for NULL and
    `FUSE_DEV_CHAN_DISCONNECTED` first; a real pointer there means the device
    still holds its connection reference.
- **Unsafe usage**: testing the result of `fuse_get_dev()` with `!fud`.
  - Safe: `IS_ERR()` for `fuse_get_dev()`, as `fuse_dev_read()` does; a NULL
    test for `__fuse_get_dev()`, as `fuse_dev_write()` does.
