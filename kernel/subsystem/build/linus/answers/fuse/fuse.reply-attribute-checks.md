- `fuse_invalid_attr()`: tests only the file type (`fuse_valid_type()`) and
  `attr->size <= LLONG_MAX` (`fuse_valid_size()`, static in `fs/fuse/dir.c`).
  `nlink`, `blksize`, `uid`, `gid` and `rdev` are not checked.
- `fuse_lookup_name()`: does not call `invalid_nodeid()`. Zero means a
  negative entry; `FUSE_ROOT_ID` is accepted because the export paths look up
  `.` and `..`.
- `fuse_lookup()`: rejects a result with `FUSE_ROOT_ID` with `-EIO` only after
  `fuse_iget()` has run, then calls `iput()`.
- `create_new_entry()`: also requires the type in the reply to equal the
  requested type. For `FUSE_LINK` the requested type is `i_mode` of the
  existing inode.
- `fuse_create_open()`: requires `S_ISREG()` on the reply mode.
- `fuse_do_setattr()`: same checks as `fuse_do_getattr()`,
  `fuse_invalid_attr()` and `inode_wrong_type()`, then `fuse_make_bad()` and
  `-EIO`.
- `fuse_do_statx()`: does not call `fuse_invalid_attr()`. It checks size only
  if `STATX_SIZE` is in `sx->mask` and type only if `STATX_TYPE` is.
- `fuse_change_attributes_common()`: keeps `inode->i_mode & S_IFMT` and takes
  only the low 07777 bits from the reply, so an update cannot change the type
  of a live inode.
- **Unsafe usage**: passing `attr` from a reply to `fuse_iget()` before
  `fuse_invalid_attr()` has passed.
  - Unsafe: for a new inode `fuse_init_inode()` reaches `BUG()` when
    `attr->mode` is none of the seven types; `inode->i_size` is set from
    an unchecked `attr->size`.
  - Safe: `fuse_invalid_attr()` first, as `fuse_lookup_name()`,
    `create_new_entry()`, `fuse_create_open()` and `fuse_direntplus_link()`
    do.
  - Safe: `attr` not taken from a reply, as in `fuse_fill_super_submount()`,
    which builds it from a live inode with `fuse_fill_attr_from_inode()`.
- **Unsafe usage**: passing `attr` from a reply to `fuse_change_attributes()`
  before the size and the type against the inode were checked.
  - Unsafe: `fuse_change_attributes_i()` does `i_size_write()` with
    `attr->size`, which is negative as `loff_t` above `LLONG_MAX`.
  - Safe: `fuse_invalid_attr()` plus `inode_wrong_type()`, as
    `fuse_do_getattr()` does, or plus `fuse_stale_inode()`, as
    `fuse_dentry_revalidate()` and `fuse_direntplus_link()` do.
  - Safe: `fuse_valid_size()`, `fuse_valid_type()` and `inode_wrong_type()`
    under the `sx->mask` tests, as `fuse_do_statx()` does; it updates only
    when `sx->mask` has all of `STATX_BASIC_STATS`, which includes
    `STATX_SIZE` and `STATX_TYPE`.
