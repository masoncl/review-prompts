- Flush before SETATTR: done only for `ATTR_MODE`, `ATTR_UID`, `ATTR_GID`,
  `ATTR_MTIME_SET` or `ATTR_TIMES_SET` on a writeback-cache regular file,
  with `write_inode_now(inode, true)` then a set/release nowrite pair; a
  plain size change flushes nothing.
- `FUSE_I_SIZE_UNSTABLE`: set with `set_bit()` outside `fi->lock`; it is one
  bit with no count, and its setters, for example `fuse_perform_write()` and
  `fuse_file_fallocate()`, hold the inode lock.
- Test of the flag: in `fuse_change_attributes_i()` in `fs/fuse/inode.c`; a
  reply that meets it is dropped whole, not only its size.
  `fuse_read_update_size()` tests it too.
- `trust_local_cmtime`: a local in `fuse_do_setattr()`, true for a
  writeback-cache regular file; it is not a field of `struct fuse_conn`.
- New size: `i_size_write()` takes `outarg.attr.size` from the reply, not
  `attr->ia_size`.
- Page cache after success: one branch, taken only when the size changed
  and the call is a truncate or the writeback cache is off; it calls
  `truncate_pagecache_range()` when the file grew, then
  `truncate_pagecache()`, then `invalidate_inode_pages2()`.
- `-EINTR` from SETATTR: `fuse_invalidate_attr()` runs before the error
  path.
- Bad reply (`fuse_invalid_attr()` or `inode_wrong_type()`):
  `fuse_make_bad()`, `-EIO`, then the same error path.
