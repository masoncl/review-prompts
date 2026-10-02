- `fuse_backing_open()`, `fuse_backing_close()` and `fuse_backing_lookup()`:
  in `fs/fuse/backing.c`, built with `fs/fuse/passthrough.c` only under
  `CONFIG_FUSE_PASSTHROUGH`.
- `fuse_dev_ioctl_backing_open()` in `fs/fuse/dev.c`: returns `-EOPNOTSUPP`
  without `CONFIG_FUSE_PASSTHROUGH`; `fuse_backing_open()` itself never
  returns that error.
- Checks in `fuse_backing_open()`, in order:

| Test that fails | Error |
|---|---|
| `fc->passthrough` clear, or no `capable(CAP_SYS_ADMIN)` | `-EPERM` |
| `map->flags` or `map->padding` non-zero | `-EINVAL` |
| `fget_raw(map->fd)` returns NULL | `-EBADF` |
| `d_is_reg()` false | `-EISDIR` for a directory, else `-EINVAL` |
| `s_stack_depth >= fc->max_stack_depth` | `-ELOOP` |

- `fuse_backing_open()`: does not test `->read_iter` or `->write_iter`, and
  has no test for a FUSE superblock; the depth test is the only limit on the
  backing filesystem.
- `fget_raw()`: unlike `fget()`, it does not mask `FMODE_PATH`, so an `O_PATH`
  fd is accepted.
- `fc->passthrough`: `process_init_reply()` in `fs/fuse/inode.c` sets it only
  when the reply has `FUSE_PASSTHROUGH`, `max_stack_depth` is between 1 and
  `FILESYSTEM_MAX_STACK_DEPTH`, and `FUSE_WRITEBACK_CACHE` is not set.
- `struct fuse_backing`: the refcount field is `count`; `cred` comes from
  `get_current_cred()`.
- `fuse_backing_free()`: calls `fput()` and `put_cred()` at once; only the
  `kfree_rcu()` is deferred.
- **Unsafe usage**: using `fb->file` or `fb->cred` of an entry from
  `idr_find()` on `fc->backing_files_map` under `rcu_read_lock()` alone.
  - Safe: take the reference with `fuse_backing_get()` first, as
    `fuse_backing_lookup()` does; RCU keeps only the memory of the
    `struct fuse_backing` valid.
- `struct fuse_file`: holds no `struct fuse_backing` reference.
  `ff->passthrough` is a separate `struct file` from `backing_file_open()`
  and `ff->cred` is its own cred reference; `fuse_passthrough_release()`
  drops both.
- `fi->fb`: holds one reference per inode, however many files are open.
- `fuse_inode_uncached_io_start()` on success: consumes the reference from
  `fuse_backing_lookup()`, storing it in `fi->fb` or putting it when `fi->fb`
  is already that backing file.
- `fuse_inode_uncached_io_start()` on failure: the caller keeps the
  reference; `fuse_file_passthrough_open()` puts it.
- `fi->fb` is put by `fuse_inode_uncached_io_end()` when `fi->iocachectr`
  returns to 0, and by `fuse_free_inode()` if still set.
- `fuse_backing_files_free()`, called from `fuse_conn_put()`: calls
  `fuse_backing_free()` on each IDR entry directly, without a put; it only
  warns when `count` is not 1.
