- Order in `fuse_get_tree()` and below:
  1. `fuse_dev_chan_new()`: channel, with `pq_prealloc` and
     `fuse_dev_fiq_ops`.
  2. `fc`, then `fm`, then `fuse_conn_init()`, which links `fc->chan` and
     `fch->conn`.
  3. superblock, through `get_tree_bdev()`, `sget_fc()` or
     `get_tree_nodev()`.
  4. in `fuse_fill_super_common()`: `fuse_dax_conn_alloc()`,
     `fuse_bdi_init()`, options, root inode and `d_make_root()`.
  5. under `fuse_mutex`: `fuse_dev_is_installed()` test,
     `fuse_ctl_add_conn()`, `fuse_conn_list`, `sb->s_root`, then
     `fuse_dev_install()`.
  6. `fuse_send_init()`, whose result `fuse_fill_super()` returns.
- `struct fuse_dev`: allocated at open of the device by `fuse_dev_open()`;
  `fuse_fill_super_common()` allocates none.
- `fuse_opt_fd()`: checks `f_op` and `fsc->user_ns` at option parse and
  keeps a `struct fuse_dev` reference in `ctx->fud` (`fuse_dev_grab()`).
- The mount holds no reference on the device file; `fuse_free_fsc()` drops
  `ctx->fud` with `fuse_dev_put()`.
- "Attached" means `fud->chan` is set; `fuse_dev_install()` also moves
  `pq_prealloc` to the device and takes a `fuse_conn_get()` reference.
- `fuse_dev_install()` returns void: if `fud->chan` is already set or is
  `FUSE_DEV_CHAN_DISCONNECTED` (file closed meanwhile), it calls
  `fuse_chan_abort()`, and the mount then fails in `fuse_send_init()`.
- Failure inside `fuse_fill_super_common()`: only `dput()` of the root and
  `fuse_dax_conn_free()`; there is no fuse_dev_free() and no device step to
  undo, because the attach is last.
- Failure of `fuse_send_init()`: `sb->s_root` is already set, so
  `fuse_sb_destroy()` runs `fuse_conn_destroy()`; an installed device stays
  attached to the aborted channel until its file is closed.
- Channel ownership: `__free(fuse_chan_free)` in `fuse_get_tree()` until
  `no_free_ptr()`; after that `delayed_release()` frees it with
  `fuse_chan_free()`.
