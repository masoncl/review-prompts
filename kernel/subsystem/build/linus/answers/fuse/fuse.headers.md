- `struct fuse_chan` is the transport object; it is defined in
  `fs/fuse/fuse_dev_i.h`, reached as `fc->chan`, and points back with
  `fch->conn`.

| Header | Defines | Included by |
|---|---|---|
| `fs/fuse/fuse_i.h` | `struct fuse_conn`, `struct fuse_mount`, `struct fuse_inode`, `struct fuse_file` | filesystem files; not `fs/fuse/dev.c`, `fs/fuse/dev_uring.c`, `fs/fuse/req_timeout.c` |
| `fs/fuse/args.h` | `struct fuse_args`, `struct fuse_args_pages` | `fs/fuse/fuse_i.h`, and directly `fs/fuse/dev.c`, `fs/fuse/dev_uring.c` |
| `fs/fuse/dev.h` | `struct fuse_chan_param`; every other struct it names is only forward-declared | both sides |
| `fs/fuse/fuse_dev_i.h` | `struct fuse_chan`, `struct fuse_dev`, `struct fuse_req`, `struct fuse_iqueue`, `struct fuse_iqueue_ops`, `struct fuse_pqueue`, `struct fuse_copy_state`, `struct fuse_forget_link`, `enum fuse_req_flag` | transport files, plus `fs/fuse/cuse.c`, `fs/fuse/virtio_fs.c`, `fs/fuse/trace.c` |

- `fs/fuse/dev.c` and `fs/fuse/dev_uring.c` get `fs/fuse/fuse_dev_i.h`
  through `fs/fuse/dev_uring_i.h`.
- Filesystem files such as `fs/fuse/inode.c`, `fs/fuse/dir.c`,
  `fs/fuse/file.c` and `fs/fuse/control.c` include `fs/fuse/dev.h` and not
  `fs/fuse/fuse_dev_i.h`: to them `struct fuse_chan`, `struct fuse_dev` and
  `struct fuse_req` are opaque.
- Filesystem code reads and sets channel state through functions in
  `fs/fuse/dev.h`, for example `fuse_chan_num_waiting()`,
  `fuse_chan_max_background_set()`, `fuse_dev_is_installed()`; a patch that
  writes `fc->chan->` in such a file does not compile.
- `fs/fuse/dev.h` also declares what the transport calls back on the
  filesystem side with an opaque `struct fuse_conn *`: `fuse_conn_get()`,
  `fuse_conn_put()`, `fuse_conn_get_id()`, `fuse_end_polls()`,
  `fuse_notify()`, `fuse_backing_open()`, `fuse_backing_close()`.
- `no_interrupt`, `io_uring` and `timeout` are fields of `struct fuse_chan`,
  not of `struct fuse_conn`.
- `struct fuse_dev` has `chan` and `struct fuse_req` has `chan`; neither has a
  pointer to `struct fuse_conn` or `struct fuse_mount`.
- Copy helpers are split: `fuse_copy_one()`, `fuse_copy_folio()` and
  `fuse_copy_finish()` are declared in `fs/fuse/dev.h` so that
  `fs/fuse/notify.c` can call them; `fuse_copy_init()`, `fuse_copy_args()` and
  `fuse_copy_out_args()` are declared in `fs/fuse/fuse_dev_i.h`.
