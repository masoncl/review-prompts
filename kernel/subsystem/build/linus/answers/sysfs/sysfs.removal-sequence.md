- `__kernfs_remove()` early return: tests `kernfs_parent(kn) &&
  RB_EMPTY_NODE(&kn->rb)`, that is, already unlinked; it does not test
  `KERNFS_REMOVING`.
- Deactivation: there is no kernfs_deactivate() here; `__kernfs_remove()` adds
  `KN_DEACTIVATED_BIAS` inline, in a post-order walk with
  `kernfs_next_descendant_post()`.
- `kernfs_drain()`: deactivates nothing; it does `WARN_ON_ONCE()` if the node
  is still active.
- `kernfs_drain()` early return: when the count is already at
  `KN_DEACTIVATED_BIAS` and `kernfs_should_drain_open_files()` is false, it
  returns without dropping any lock.
- Second remover of a node that is still linked: passes the early test,
  drains as well and returns only after the drain; only the cleanup is
  skipped for the caller that loses `kernfs_unlink_sibling()`.
- Unlink winner: also calls `kernfs_clear_inode_nlink()`, which walks
  `root->supers` and does `clear_nlink()` on each cached inode of the node;
  this is why `kernfs_supers_rwsem` is held.
- Root node (no parent): the cleanup branch runs without
  `kernfs_unlink_sibling()`.
