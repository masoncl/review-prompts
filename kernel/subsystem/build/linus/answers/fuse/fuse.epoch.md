- `fuse_notify_inc_epoch()` is in `fs/fuse/notify.c`; besides `atomic_inc()`
  it calls `schedule_work(&fc->epoch_work)` when `inval_wq` is non-zero.
- `fuse_epoch_work()`: calls `shrink_dcache_sb()` on the superblock found by
  looking up `FUSE_ROOT_ID`; that kills every unused dentry on the LRU, not
  only those with an old epoch.
- With `inval_wq` at 0: an epoch bump removes nothing; dentries fail at their
  next revalidation.
- Two things compare with `fc->epoch`: dentries (`fd->epoch <`, in
  `fuse_dentry_revalidate()`) and the readdir cache (`fi->rdc.epoch !=`, in
  `fuse_readdir_cached()`); inodes and attributes do not.
- Initial values: `fc->epoch` starts at 1, `fuse_dentry_init()` sets the
  dentry epoch to 0, so a dentry whose epoch is not set again after
  `fuse_dentry_init()` fails every revalidation.
- `fuse_dentry_set_epoch()`: a call separate from setting the timeout;
  `fuse_lookup()`, `fuse_create_open()` and `create_new_entry()` pass a value
  read from `fc->epoch` before the request is sent.
- Background removal of expired dentries: happens only while module parameter
  `inval_wq` (seconds, in `fs/fuse/dir.c`) is non-zero; the default is 0.
- `inval_wq` accepted values: 0, or `FUSE_DENTRY_INVAL_FREQ_MIN` (5) up to
  `USHRT_MAX`.
- `fuse_dentry_tree_add_node()`: returns at once when `inval_wq` is 0, so a
  dentry whose time was set while the parameter was 0 is not in the tree
  until its time is set again.
- `fuse_dentry_tree_work()`: does not call `d_invalidate()` or `d_drop()`; it
  sets `DCACHE_OP_DELETE`, calls `__move_to_shrink_list()` under `d_lock`,
  then `shrink_dentry_list()`. There is no d_dispose_if_unused() in this tree.
- Expired dentry that is still referenced: stays hashed and is only taken out
  of the tree; the `DCACHE_OP_DELETE` flag makes its final `dput()` drop it
  through `fuse_dentry_delete()`.
- Bucket lock in `fuse_dentry_tree_work()`: held across the whole bucket walk,
  including the `d_lock` section; released only at `need_resched()`.
- The tree: one static array `dentry_hash` shared by all connections, hashed
  by dentry pointer.
