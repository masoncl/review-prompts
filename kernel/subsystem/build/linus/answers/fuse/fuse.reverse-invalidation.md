- `fuse_reverse_inval_inode()`: returns only `-ENOENT` or 0; the result of
  `invalidate_inode_pages2_range()` is ignored.
- `fuse_reverse_inval_inode()`: also raises `fi->attr_version` and calls
  `forget_all_cached_acls()`.
- `fuse_invalidate_entry_cache()`: sets the dentry time to 0 through
  `fuse_dentry_settime()`; it does not unhash. The unhash is the
  `d_invalidate()` call in `fuse_reverse_inval_entry()`, skipped with
  `FUSE_EXPIRE_ONLY`.
- Expire-only flag: named `FUSE_EXPIRE_ONLY`; there is no
  FUSE_NOTIFY_EXPIRE_ENTRY in this tree.
- Unknown bits in `flags` of the entry notification: ignored, not rejected.
- `FUSE_NOTIFY_DELETE`: always passes flags 0, so it always calls
  `d_invalidate()`.
- `fuse_reverse_inval_entry()` errors before touching the dentry: `-ENOENT`
  (parent inode not cached, parent has no alias, or name not in the dcache)
  and `-ENOTDIR` (parent is not a directory).
- Entry and delete handlers: also return `-ENOMEM` from the name buffer
  allocation; `-ENAMETOOLONG` is tested after the minimum size test and
  before the exact size test.
- Delete errors `-ENOENT` (child nodeid mismatch), `-EBUSY` (mountpoint) and
  `-ENOTEMPTY`: returned after `fuse_dir_changed()`, `d_invalidate()` and the
  expiry have already been applied.
- Delete with child nodeid 0 or a negative dentry: behaves as invalidate entry
  and returns 0.
- `fuse_notify_prune()`: returns `-ENOMEM`, `-EINVAL` (size below the header,
  or size against count) or the error from `fuse_copy_one()`; the allocation
  comes first, before the size tests.
