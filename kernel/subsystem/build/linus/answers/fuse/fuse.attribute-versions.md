- Staleness test: in `fuse_change_attributes_i()` (static, `fs/fuse/inode.c`),
  under `fi->lock`, not `fc->lock`.
- `fuse_get_attr_version()` and `fuse_get_evict_ctr()`: plain `atomic64_read()`,
  no lock.
- `fuse_change_attributes()`: has no `evict_ctr` parameter and passes 0; a
  non-zero `evict_ctr` reaches `fuse_change_attributes_common()` only through
  `fuse_iget()`.
- `evict_ctr` never drops a reply: attributes and `fi->i_time` are still
  applied.
- `evict_ctr` effect, in `fuse_change_attributes_common()`: `STATX_BASIC_STATS`
  stays set in `fi->inval_mask` when `evict_ctr` is non-zero,
  `fi->attr_version` is 0 and the counter has moved.
- `fuse_evict_inode()`: increments `fc->evict_ctr` only when the superblock has
  `SB_ACTIVE` and `inode->i_nlink > 0`.
- `fuse_dentry_revalidate()`: reads `attr_version` only, not `evict_ctr`.
- `create_new_entry()` and `fuse_create_open()`: pass 0, 0 to `fuse_iget()`, so
  the reply is applied with no version test.
- `FUSE_LINK` goes through `create_new_entry()` on an inode that already
  exists; `fuse_link()` itself changes neither nlink nor `fi->attr_version`.
- `fuse_do_setattr()`: samples `attr_version` before sending; if
  `fi->attr_version` is newer on reply it still applies the attributes, with a
  zero timeout.
- `fuse_do_setattr()` calls `fuse_change_attributes_common()` directly and does
  not test `FUSE_I_SIZE_UNSTABLE`.
- `fuse_update_ctime()` and `fuse_link_write_file()`: do not bump
  `fi->attr_version`; there is no fuse_write_update_size() in this tree.
- `fuse_write_update_attr()`: bumps on every call, also when nothing was
  written or the size did not grow.
- Bump sites: search `fs/fuse` for `atomic64_inc_return(&fc->attr_version)`;
  easy to miss are `fuse_aio_complete()`, `fuse_read_update_size()` and
  `fuse_truncate_update_attr()`.
- `FUSE_I_SIZE_UNSTABLE`: not set by `fuse_open()` with `O_TRUNC`, nor by
  `fuse_direct_io()`; `fuse_perform_write()` sets it only for an extending
  write.
