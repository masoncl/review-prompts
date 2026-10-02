| Job | Start at | File |
|---|---|---|
| Mounting | `fuse_get_tree()`, then `fuse_fill_super()`, `fuse_fill_super_common()`, `fuse_send_init()` | `fs/fuse/inode.c` |
| Send and wait | `fuse_simple_request()` (inline, `fs/fuse/fuse_i.h`), `__fuse_simple_request()` | `fs/fuse/req.c` |
| Send and wait, transport half | `fuse_chan_send()`, then `__fuse_request_send()`, `request_wait_answer()` | `fs/fuse/dev.c` |
| Send, no wait | `fuse_simple_background()` in `fs/fuse/req.c`, then `fuse_chan_send_bg()` | `fs/fuse/dev.c` |
| Read a request | `fuse_dev_read()`, `fuse_dev_splice_read()`, then `fuse_dev_do_read()` | `fs/fuse/dev.c` |
| Write a reply | `fuse_dev_write()`, `fuse_dev_splice_write()`, then `fuse_dev_do_write()` | `fs/fuse/dev.c` |
| Notification from the server | `fuse_notify()`, called from `fuse_dev_do_write()` | `fs/fuse/notify.c` |
| io_uring fetch and commit | `fuse_uring_cmd()` | `fs/fuse/dev_uring.c` |
| Abort | `fuse_chan_abort()` | `fs/fuse/dev.c` |

- `fuse_dev_is_installed()`: the test for "this device is mounted"; `fud->chan`
  is NULL before mount and `FUSE_DEV_CHAN_DISCONNECTED` after release.
- `fuse_send_init()`: returns `int`; with `fc->sync_init` it sends INIT with
  `fuse_simple_request()` and calls `process_init_reply()` itself, otherwise
  `process_init_reply()` is the `end` callback of a background request.
- Reply helpers in `fuse_dev_do_write()` are `fuse_request_find()`,
  `fuse_copy_out_args()` and `fuse_request_end()`; there are no unprefixed
  forms.
- `fuse_chan_abort()` clears `fch->connected`, `fiq->connected` and the
  `fpq->connected` of each device on `fch->devices`; `struct fuse_conn` has no
  `connected` field.
