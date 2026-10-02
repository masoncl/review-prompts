- Hash key: the node id alone, as both hash value and compare argument of
  `iget5_locked()` in `fuse_iget()`. `inode->i_ino` is not the key; it is
  `fuse_squash_ino(attr->ino)`, set in `fuse_change_attributes_common()`.
- Submount points (`fc->auto_submounts`, `FUSE_ATTR_SUBMOUNT`, `S_ISDIR()`):
  `fuse_iget()` makes them with `new_inode()` and never hashes them, so each
  call returns a new inode.
- `fuse_stale_inode()` in `fs/fuse/fuse_i.h`: a pure test, changes nothing.
- `fuse_make_bad()`: only sets `FUSE_I_BAD`. It does not call
  `remove_inode_hash()`; `fuse_iget()` does that itself, for a stale inode
  that is not the root.
- `FUSE_I_BAD` is never cleared.
- Inode marked bad outside `fuse_iget()` (`fuse_do_getattr()`,
  `fuse_do_setattr()`, `fuse_do_statx()`, `fuse_direntplus_link()`): stays
  hashed.
- `fuse_iget()` and `fuse_inode_eq()` do not test `fuse_is_bad()`: a hashed bad
  inode whose generation and type match the reply is returned again, with
  `nlookup` raised and attributes updated.
- Stale root: marked bad, kept in the hash, and `fuse_iget()` goes on to raise
  `nlookup` and update it.
- `fuse_lookup_name()` sets a nonzero generation to 0 for `FUSE_ROOT_ID`
  before `fuse_iget()`; a wrong type in the reply still marks the root bad.
- `fuse_dentry_revalidate()` does not call `fuse_make_bad()`; a stale or
  invalid reply only makes it return 0.
- Error for a bad inode: `-EIO` at every `fuse_is_bad()` test that returns an
  error. Within `fs/fuse`, `-ESTALE` is set only in the export paths
  `fuse_get_dentry()` and `fuse_get_parent()`, which do not test
  `fuse_is_bad()`.
