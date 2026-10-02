- There is no fuse_abort_conn() here; `fuse_chan_abort(fc->chan, false)` in
  `fs/fuse/dev.c` does that, in `cuse_process_init_reply()` and in
  `cuse_class_abort_store()`.
- `cuse_channel_open()`: gets the channel from `fuse_dev_chan_new()` and
  passes it as the fourth argument of `fuse_conn_init()`; `fuse_dev_fiq_ops`
  is static in `fs/fuse/dev.c`.
- `fuse_dev_alloc_install()`: takes the `struct fuse_chan *`, not the
  connection.
- `cuse_channel_open()`: stores the `struct fuse_dev` in
  `file->private_data`, and only after `cuse_send_init()` succeeded.
- `cuse_channel_open()`: sets `cc->fc.chan->initialized` with
  `smp_store_release()` before `CUSE_INIT` is sent; it does not call
  `fuse_chan_set_initialized()`.
- `fch->minor`, `fch->max_write`, `fch->max_pages`, `fch->io_uring`: 0 on a
  CUSE channel for its whole life; they are set only through
  `fuse_chan_set_initialized()` with a `struct fuse_chan_param`, which only
  `process_init_reply()` in `fs/fuse/inode.c` passes.
- `cuse_process_init_reply()`: of `struct fuse_conn` it sets only
  `fc->minor`, `fc->max_read` and `fc->max_write`; `fc->max_pages` stays
  `FUSE_DEFAULT_MAX_PAGES_PER_REQ` from `fuse_conn_init()`.
- `cuse_process_init_reply()`: reads its own flag word in
  `struct cuse_init_out`; `CUSE_UNRESTRICTED_IOCTL` is the only flag, and no
  FUSE_INIT flag is parsed.
- `cuse_process_init_reply()`: builds the device with `device_initialize()`
  and `device_add()`, not `device_create()`; the devt comes from
  `arg->dev_major` and `arg->dev_minor`, and a zero major is allocated by
  `alloc_chrdev_region()`.
- `cuse_process_init_reply()`: returns `void`; a duplicate `DEVNAME` and
  every other failure end in `fuse_chan_abort()`, no error code is reported.
- `cuse_open()`: takes `cuse_lock` with `mutex_lock()`; it does not call
  `nonseekable_open()` and does not force `FOPEN_DIRECT_IO`.
- `ff->open_flags` on a CUSE file: whatever the server replied; with
  `FOPEN_DIRECT_IO` set, `fuse_direct_io()` runs
  `filemap_write_and_wait_range()` and, for a write,
  `invalidate_inode_pages2_range()` on the chrdev inode's mapping, outside
  the `FUSE_DIO_CUSE` test.
- `fc->no_open` and `fc->no_poll`: set on a CUSE connection by an `-ENOSYS`
  reply, in `fuse_file_open()` and `fuse_file_poll()`; with `fc->no_open`
  set, `cuse_open()` succeeds without `FUSE_OPEN` and `fuse_file_put()`
  sends no `FUSE_RELEASE`.
- `cc->fm`: is on `fc->mounts` with `fm->sb == NULL`; `fuse_ilookup()` is
  the only walker of that list and skips it.
- Core functions `fs/fuse/cuse.c` calls with the chrdev file or its
  `struct fuse_file`: `fuse_do_open()`, `fuse_sync_release()`,
  `fuse_direct_io()`, `fuse_do_ioctl()`, `fuse_file_poll()`.
- `fs/fuse/cuse.c` does not call `fuse_release_common()`,
  `fuse_direct_read_iter()`, `fuse_direct_write_iter()` or
  `fuse_file_ioctl()`; those are the FUSE-only wrappers and they use the
  FUSE inode.
- `fuse_do_ioctl()`: has no CUSE flag and touches no inode; the inode checks
  are in `fuse_ioctl_common()` in `fs/fuse/ioctl.c`.
- `fuse_fill_creds()` in `fs/fuse/req.c`: runs for every CUSE request and
  treats `!fm->sb` as no idmapping.
- `cuse_class_waiting_show()`: reads `cc->fc.chan->num_waiting`; CUSE never
  calls `fuse_conn_destroy()` or `fuse_chan_wait_aborted()`.
- `cuse_channel_release()`: only unhashes and removes the device; the abort
  is in `fuse_dev_release()`, when the last `struct fuse_dev` leaves
  `fch->devices`.
- `struct cuse_conn`: freed by the last `fuse_conn_put()`, through
  `call_rcu()` and `fc->release`; an open frontend file holds a reference,
  so the last put can be in `cuse_release()`, after the channel is aborted.
- `cuse_init()`: copies `fuse_dev_operations`, replaces `.open` and
  `.release`, and sets `.unlocked_ioctl` to NULL; no command of
  `fuse_dev_ioctl()` is reachable on `/dev/cuse`, and `compat_ptr_ioctl()`
  returns `-ENOIOCTLCMD`.
- `fuse_uring_cmd()` on `/dev/cuse`: inherited under
  `CONFIG_FUSE_IO_URING`; no command is dispatched because `fch->io_uring`
  is 0, and a command with `IO_URING_F_SQE128` on a connected channel gets
  `-EOPNOTSUPP`.
- `fuse_notify()` on `/dev/cuse`: `fuse_dev_do_write()` passes every
  notification to it once `fch->initialized` is set and while
  `fch->connected`, so before the `CUSE_INIT` reply too.
- Exports: `CONFIG_CUSE` is tristate, so each core function
  `fs/fuse/cuse.c` calls needs `EXPORT_SYMBOL_GPL()`;
  `__fuse_simple_request()` and `fuse_chan_set_initialized()` are not
  exported.
- **Potentially unsafe usage**: using the file's inode as a FUSE inode in
  `fuse_do_open()`, `fuse_direct_io()`, `fuse_sync_release()`,
  `fuse_do_ioctl()`, `fuse_file_poll()` or a function they call.
  - Unsafe: on a path that runs for a CUSE file; the inode is the chrdev
    inode, `get_fuse_inode()` is a `container_of()` and returns a bad
    pointer, not NULL, and `get_fuse_conn()` reads another filesystem's
    `s_fs_info`.
  - Safe: behind `!(flags & FUSE_DIO_CUSE)`, as the `fuse_sync_writes()`
    call in `fuse_direct_io()`; the flag is defined in `fs/fuse/fuse_i.h`.
  - Safe: behind the `fi` NULL test and `sync`, as in
    `fuse_prepare_release()`; `cuse_release()` passes `fi == NULL`.
  - Safe: behind `fuse_file_passthrough(ff)`, as the
    `fuse_inode_backing(fi)` call in `fuse_prepare_release()`;
    `ff->passthrough` is set only by `fuse_passthrough_open()`, reached from
    `fuse_finish_open()`, which CUSE does not call.
  - Safe: on the `io->async` path only, as `fuse_aio_complete()`;
    `FUSE_IO_PRIV_SYNC()` sets `async` to 0 and CUSE uses nothing else.
  - Safe: in the FUSE-only wrapper, outside the shared call, as
    `fuse_ioctl_common()` and `fuse_direct_write_iter()` do.
  - Safe: taking the connection from `ff->fm`, as `fuse_file_poll()` does.
- **Potentially unsafe usage**: branching on `fch->minor`,
  `fch->max_write` or `fch->max_pages` in `fs/fuse/dev.c`.
  - Unsafe: when the branch changes what is sent for an opcode CUSE sends
    (`CUSE_INIT`, `FUSE_OPEN`, `FUSE_RELEASE`, `FUSE_READ`, `FUSE_WRITE`,
    `FUSE_IOCTL`, `FUSE_POLL`, `FUSE_INTERRUPT`); the value is 0, so the
    oldest-protocol branch is taken.
  - Safe: `fuse_adjust_compat()`, which changes only opcodes CUSE does not
    send.
  - Safe: `fuse_read_forget()`, which only picks the forget format; no
    function `fs/fuse/cuse.c` calls reaches `fuse_chan_queue_forget()`.
  - Safe: `fuse_dev_do_read()`, where `fch->max_write` only raises the
    minimum read buffer; with 0 the `nbytes < reqsize` test still ends a
    request that does not fit with `-EIO`.
  - Safe: reading `fc->minor` or `fc->max_write` instead, as
    `fuse_write_args_fill()` and `fuse_direct_io()` do;
    `cuse_process_init_reply()` sets those.
- **Unsafe usage**: a `fuse_notify()` handler that reaches a superblock or
  inode without `fuse_ilookup()`.
  - Safe: look the inode up with `fuse_ilookup()` and use the
    `struct fuse_mount` it returns, as `fuse_epoch_work()` and
    `fuse_notify_retrieve()` do; on CUSE the lookup returns NULL.
- **Potentially unsafe usage**: reading `fm->sb` without a NULL test.
  - Unsafe: when `fm` can be CUSE's `cc->fm`, as in `fs/fuse/req.c` and in
    the functions `fs/fuse/cuse.c` calls; `fm->sb` is NULL there.
  - Safe: test `!fm->sb` first, as `fuse_fill_creds()` does.
  - Safe: when `fm` is the out pointer of `fuse_ilookup()`, which skips a
    mount whose `sb` is NULL, as in `fuse_epoch_work()`.
  - Safe: when `fm` came from `get_fuse_mount()` on a FUSE inode, as in
    `fuse_access()`; `fuse_fill_super_common()` and
    `fuse_fill_super_submount()` set `fm->sb` before they create the root
    inode.
