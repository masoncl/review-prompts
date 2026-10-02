- The bound is `file_inode(of->file)->i_size`, not `battr->size`;
  `kernfs_init_inode()` sets it from the size given at creation, so a later
  change to `battr->size` does not move the bound. A size of 0 means no
  bound.
- `sysfs_kf_bin_write()` with a non-zero size and `pos >= size`: returns
  `-EFBIG`, including a write that starts exactly at the end; it does not
  return `-ENOSPC`.
- `sysfs_kf_bin_write()` order: bound test, then zero count returns 0, then
  NULL `write` returns `-EIO`.
- `sysfs_kf_bin_read()` order: zero count returns 0, then bound test, then
  NULL `read` returns `-EIO`.
- The `-EIO` for a missing callback is reachable only through
  `sysfs_bin_kfops_mmap`, which has both kernfs ops whatever the attribute
  sets; with the other tables open has already failed with `-EACCES`.
- One read(2) or write(2) makes one callback call of at most `PAGE_SIZE`
  bytes; kernfs does not loop, it returns the short count.
