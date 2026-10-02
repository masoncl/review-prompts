- `d_alias`: member of an anonymous union in `struct dentry`; there is no
  d_u.d_alias. It shares storage with `d_in_lookup_hash`, `d_rcu` and
  `waiters`, and is valid only while the dentry is positive.
- `d_alias` on a negative dentry: holds no list state; `__d_alloc()`
  initialises `waiters`, not `d_alias`, and `dentry_unlink_inode()` writes
  `waiters` over it. `d_instantiate()` tests `d_really_is_positive()` instead.
- `d_sib`: the names are `d_sib` and `d_children`. `d_sib` has a second use: an
  `IS_ROOT()` dentry from `d_obtain_root()` is linked through it on
  `sb->s_roots`, under `s_roots_lock` taken inside the dentry's `d_lock`; see
  `unlink_secondary_root()` in `fs/dcache.c`.
- `d_lru`: a plain member, not in a union; `struct dentry` has no d_wait field.
- `d_name` writers: besides `__d_move()`, `d_mark_tmpfile()` and
  `d_mark_tmpfile_name()` rewrite the name of an unlinked negative dentry
  under the parent's and the dentry's `d_lock`, with no `rename_lock` and no
  `d_seq` write. `d_lock` is the only protection that covers every writer.
- `d_name` and `d_parent` under the parent's `i_rwsem`: stable against
  `vfs_rename()`, whose callers hold it exclusive through `lock_rename()` or
  `lock_rename_child()`.
- `i_rwsem` held shared: does not stop a child from moving. `__d_unalias()`
  takes only `inode_trylock_shared()` on the alias's old parent, and no lock
  when alias and dentry share a parent; `vfat_lookup()` calls `d_move()` from
  `->lookup`.
- `d_flags` type bits: `__d_entry_type()` is a plain read without
  `READ_ONCE()`.
