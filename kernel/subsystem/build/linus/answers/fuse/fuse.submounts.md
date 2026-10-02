- `fuse_iget()` sets `S_AUTOMOUNT`; there is no fuse_get_attr here.
- `fuse_iget()` conditions: `fc->auto_submounts`, `FUSE_ATTR_SUBMOUNT` in
  `attr->flags`, and `S_ISDIR(attr->mode)`.
- Mountpoint inode: made with `new_inode()`, never hashed, `fi->nlookup` not
  incremented; the lookup is held by `fi->submount_lookup` with count 1.
- `fuse_dentry_automount()`: only creates the context with
  `fs_context_for_submount()`, stores the mountpoint `struct fuse_inode` in
  `fsc->fs_private` and calls `fc_mount()`.
- `fuse_get_tree_submount()` allocates the `struct fuse_mount`, takes the
  connection reference and links the mount under
  `down_write(&fc->killsb)`.
- Route to `fuse_get_tree_submount()`: `virtio_fs_init_fs_context()` calls
  `fuse_init_fs_context_submount()` for `FS_CONTEXT_FOR_SUBMOUNT`;
  `fuse_init_fs_context()` has no such branch.
- Submount root: built by `fuse_iget()` from `fuse_fill_attr_from_inode()`,
  which sets no `flags`, so the root is hashed in the new superblock and
  `fuse_fill_super_submount()` undoes the `nlookup` increment.
- `refcount_inc(&sl->count)` is the last step of
  `fuse_fill_super_submount()`, after every failure return.
- There is no fuse_queue_forget() here; `fuse_cleanup_submount_lookup()`
  calls `fuse_chan_queue_forget()` with nlookup 1 on the last put.
- `fuse_dentry_revalidate()` increments `fi->nlookup` of the mountpoint inode
  on a successful re-LOOKUP; `fuse_evict_inode()` then sends that count as a
  second FORGET, separate from the shared one.
- `fuse_evict_inode()` drops the shared count only while `SB_ACTIVE` is set.
- Unmount still drops it: `.drop_inode` is `inode_just_drop()` and
  `generic_shutdown_super()` runs `shrink_dcache_for_umount()` before it
  clears `SB_ACTIVE`, so the root is evicted while the flag is set.
- `fuse_free_inode()` does not free `fi->submount_lookup`.
