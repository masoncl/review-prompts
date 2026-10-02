- `FS_RENAME_DOES_D_MOVE`: when set in `fs_flags`, `vfs_rename()` calls
  neither `d_move()` nor `d_exchange()`; the filesystem does it. Search for
  the flag to list the filesystems.
- Outside `->rename`: filesystems also call `d_move()` and `d_exchange()`
  directly, for example `vfat_lookup()` (from `->lookup`),
  `nfs_sillyrename()` and `security/selinux/selinuxfs.c`.
- `__d_move()` lock order: the two parents' `d_lock`s are taken in an order
  that depends on ancestry (`d_ancestor()` on the old parent and the target);
  then the dentry's, then the target's.
- `take_dentry_name_snapshot()`: takes no lock. It runs under RCU, retries on
  `d_seq`, and pins an external name with `atomic_inc_not_zero()`.
- `d_splice_alias()` moves: do not have both parents' `i_rwsem` exclusive; see
  "Dentry links and their locks".
