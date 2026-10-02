- `struct fuse_dentry` in `fs/fuse/dir.c`: holds both `time` and `epoch`
  (`u64`); the epoch is not in `dentry->d_time`, which nothing under
  `fs/fuse/` uses.
- Stale epoch (`fd->epoch < fc->epoch`) or bad inode: `fuse_dentry_revalidate()`
  returns 0 with no LOOKUP sent, in RCU walk too.
- Negative dentry that is expired or hit by a forcing flag: returns 0, never
  sends a LOOKUP; a negative dentry still inside its timeout returns 1.
- Forcing flags: `LOOKUP_EXCL`, `LOOKUP_REVAL` and `LOOKUP_RENAME_TARGET`
  each force the LOOKUP path on an unexpired dentry.
- The LOOKUP in revalidation: built with `fuse_lookup_init()` and sent with
  `fuse_simple_request()`; `fuse_lookup_name()` is not used here.
- Parent: taken from the `dir` and `name` arguments; revalidation does not
  call `dget_parent()`.
- Unexpired positive dentry in RCU walk: returns `-ECHILD` when
  `FUSE_I_INIT_RDPLUS` is set on the inode, 1 otherwise.
- Request errors: `-ENOMEM` (also from `fuse_alloc_forget()`) and `-EINTR`
  are returned as errors; any other error returns 0.
- Successful revalidation: resets `time`; `epoch` is not refreshed.
- `fuse_dentry_delete()`: reached at final `dput()` only while
  `DCACHE_OP_DELETE` is set; `fuse_dentry_settime()` clears the flag unless
  the time is 0 and `fc->delete_stale` is set.
- `fc->delete_stale`: set only in `fs/fuse/virtio_fs.c`; elsewhere an expired
  unused dentry stays cached after `dput()` unless `fuse_dentry_tree_work()`
  flagged it.
