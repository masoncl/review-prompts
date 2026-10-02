- Killed: tested with `lockref_is_dead()` (`include/linux/lockref.h`), reliable
  only under `d_lock`; there is no __lockref_is_dead(). The count is
  `__LOCKREF_DEAD_VAL`, set by `lockref_mark_dead()` in `dentry_kill()`; this
  tree has no function __dentry_kill().
- `DCACHE_DENTRY_KILLED`: set later than the dead count, in `dentry_unlist()`,
  after `->d_release()` has run and `d_lock` was dropped and retaken.
- Between the two: the dentry is dead, negative and unhashed but still linked
  through `d_sib`, on the parent's `d_children` or on `s_roots`.
  `shrink_dcache_tree()` and `shrink_dcache_for_umount()` wait for it with
  `d_add_waiter()` on `waiters`.
- In-lookup: there is no d_wait field. A waiter sets `DCACHE_LOOKUP_WAITERS`
  and sleeps in `wait_var_event_spinlock()` on `d_flags`; see
  `d_wait_lookup()`. `d_alloc_parallel()` takes two arguments.
- In-lookup dentry: also `d_unhashed()`; it is on the in-lookup hash through
  `d_in_lookup_hash`, not on `d_hash`.
- Type bits and `d_inode`: written together, only by
  `__d_set_inode_and_type()` and `__d_clear_type_and_inode()`; under `d_lock`
  the two helper families give the same answer.
- `DCACHE_WHITEOUT_TYPE`: nothing in this tree sets it, and `d_is_whiteout()`
  has no caller. `d_backing_inode()` returns `d_inode`.
- Lockless difference: set stores `d_inode` first, then the type with
  `smp_store_release()`; clear stores the type first, then `d_inode`.
- Lockless positive test: `d_flags_negative(smp_load_acquire(&d->d_flags))`,
  as `traverse_mounts()` in `fs/namei.c` does; `d_is_negative()` has no
  acquire.
