- Four files in `fuse-y` of `fs/fuse/Makefile` are built unconditionally and
  hold code that is not in `fs/fuse/dev.c`, `fs/fuse/file.c` or
  `fs/fuse/inode.c`:

  | File | Side | Holds |
  |---|---|---|
  | `fs/fuse/req.c` | filesystem | `__fuse_simple_request()`, `fuse_simple_background()`, `fuse_simple_notify_reply()`: fill credentials, test `fc->conn_error`, hand off to the channel |
  | `fs/fuse/notify.c` | filesystem | `fuse_notify()` and the `FUSE_NOTIFY_*` handlers |
  | `fs/fuse/poll.c` | filesystem | `fuse_file_poll()`, `fuse_notify_poll_wakeup()`, `fuse_end_polls()` |
  | `fs/fuse/req_timeout.c` | transport | `fuse_check_timeout()`, `fuse_init_server_timeout()`, `fuse_request_expired()` |

- Transport files are `fs/fuse/dev.c`, `fs/fuse/dev_uring.c` and
  `fs/fuse/req_timeout.c`: none of them includes `fs/fuse/fuse_i.h`, so none
  can dereference `struct fuse_conn`, `struct fuse_mount` or
  `struct fuse_inode`.
- `fs/fuse/virtio_fs.c` and `fs/fuse/cuse.c` include both sides' headers; each
  creates its own channel and connection.
- `fs/fuse/backing.c`: built with `fs/fuse/passthrough.c` under
  `CONFIG_FUSE_PASSTHROUGH`.
- `fuse_backing_files_init()` and `fuse_backing_files_free()` in
  `fs/fuse/backing.c` have no stub in `fs/fuse/fuse_i.h`; a call from
  unconditional code needs `IS_ENABLED(CONFIG_FUSE_PASSTHROUGH)` around it, as
  in `fuse_conn_init()`.
- `fs/fuse/dax.c`: `CONFIG_FUSE_DAX` depends on `CONFIG_VIRTIO_FS`, but
  `dax.o` links into `fuse.o`, not `virtiofs.o`.
- `fs/fuse/sysctl.c`: built only under `CONFIG_SYSCTL`; the variables it
  exposes are defined in files that are always built:
  `fuse_default_req_timeout` and `fuse_max_req_timeout` in
  `fs/fuse/req_timeout.c`, `fuse_max_pages_limit` in `fs/fuse/inode.c`.
- `fs/fuse/iomode.c` and `fs/fuse/trace.c`: built unconditionally.
