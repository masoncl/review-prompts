# VFS Subsystem

## Main structures

### Objects and how they relate

- `struct inode` holds no reference on its superblock, active or passive.
  `generic_shutdown_super()` evicts the inodes with a zero count with
  `evict_inodes()`; any inode still on `s_inodes` afterwards is reported as
  "Busy inodes" and has `i_sb` poisoned, or is a `BUG()` under
  `CONFIG_BUG_ON_DATA_CORRUPTION`.
- `struct mount`: defined in `fs/mount.h` and used across `fs/`, for example
  `fs/namei.c` and `fs/d_path.c`, not only `fs/namespace.c` and `fs/pnode.c`.
- `struct mountpoint`: in `fs/mount.h`, with no reference count. It holds a
  reference on its dentry and lives while `m_list` is non-empty; `m_list`
  links the mounts on that dentry and any `struct pinned_mountpoint`.
- `struct mnt_namespace`: not always what a task sees. One with `is_anon` set
  holds a detached tree. A mount's `mnt_ns` can also be NULL or
  `MNT_NS_INTERNAL`. Mounts of a namespace are in the rbtree `mounts`, keyed
  by `mnt_id_unique`.
- Namespace root: `init_mount_tree()` makes a `nullfs_fs_type` mount
  (`fs/nullfs.c`, empty and immutable) the root of the initial namespace and
  mounts the rootfs on top of it. The visible root of a namespace is
  `topmost_overmount()` of its `root`, not `root` itself; see
  `current_chrooted()`.
- `struct file` `f_inode`: always set from `f_path.dentry->d_inode`, in
  `do_dentry_open()` and `file_init_path()`; `file_dentry()` warns if the two
  differ.
- Stacking filesystems such as overlayfs: a second `struct file`, embedded in
  `struct backing_file` (`fs/file_table.c`, `FMODE_BACKING`), has both
  `f_path` and `f_inode` on the underlying filesystem. The path the user
  opened is kept beside it; read it with `file_user_path()`.
- `struct address_space` of a block device: `bdev_open()` in `block/bdev.c`
  redirects the file's `f_mapping`; the device node's `i_mapping` is left
  alone. `i_mapping` is repointed elsewhere, for example in
  `drivers/dax/device.c`.
- `struct dentry` parent chain: ends at an `IS_ROOT()` dentry, which need not
  be `s_root`. `d_obtain_alias()` makes disconnected roots, and
  `d_obtain_root()` makes secondary roots listed on `s_roots`.
- Directory aliases: a directory inode has at most one.
  `d_splice_alias_ops()` moves the existing alias, hashed or not, into place
  or fails with `-ELOOP` or `-ESTALE`; `d_obtain_alias()` returns the existing
  one.
- `struct super_dev` (`fs/super.c`): one registration of a superblock under a
  device number, holding `s_passive`. One device can map to several
  superblocks and one superblock to several devices
  (`fs_bdev_file_open_by_dev()`); `user_get_super()` and the block holder
  callbacks walk it.
- `struct fs_struct` per task: `struct task_struct` has two pointers. `real_fs`
  is the one the task owns and `fs/proc/base.c` reports; `fs` is the one
  `scoped_with_init_fs()` swaps to `userspace_init_fs` for a scope.
- `init_fs`: its root and cwd are a private nullfs mount, so a kthread
  sharing it resolves nothing unless it uses `scoped_with_init_fs()`. PID 1
  gets its own copy, which `init_userspace_fs()` moves to the rootfs.
- failfs (`fs/failfs.c`): one internal mount in no namespace whose root fails
  every walk with `-EOPNOTSUPP`. A task makes it its root or cwd by passing
  `FD_FAILFS_ROOT`; see `fs/open.c`.

## Where to look

**Core files**

| Job | File in this tree |
|---|---|
| `struct super_block`, `struct super_operations` | `include/linux/fs/super_types.h`, not `include/linux/fs.h` |
| Superblock inline helpers, for example `sb_rdonly()`, `sb_start_write()` | `include/linux/fs/super.h`; `include/linux/fs.h` includes it, and it includes `include/linux/fs/super_types.h` |
| `struct inode`, `struct file`, `struct file_operations`, `struct inode_operations` | still `include/linux/fs.h` |
| `struct dentry` | `include/linux/dcache.h` |
| Every other core job (lookup, caches, superblocks, mounts, open, file and descriptor tables, attributes, readdir, pseudo-filesystem library, mount context) | Models have these right; all under `fs/`, starting from `fs/namei.c` |

**Entry points**

| Job | Start reading from |
|---|---|
| Open a file | `do_file_open()` in `fs/namei.c`; there is no do_filp_open() here. `do_sys_openat2()` and `file_open_name()` in `fs/open.c` call it |
| Create by name, from a syscall | `filename_mknodat()`, `filename_mkdirat()`, `filename_symlinkat()`, `filename_linkat()` in `fs/namei.c`; there is no do_mknodat() or do_mkdirat() here |
| Create on open with `O_CREAT` | `lookup_open()` in `fs/namei.c`; it calls `atomic_open()` or `->create` directly and does not call `vfs_create()` |
| Unlink by name, from a syscall | `filename_unlinkat()`, `filename_rmdir()` in `fs/namei.c`; there is no do_unlinkat() here |
| Rename by name, from a syscall | `filename_renameat2()` in `fs/namei.c`; there is no do_renameat2() here |
| Create, remove, rename by name from kernel code, under a known parent | `start_creating()`, `start_removing()`, `start_renaming()` in `fs/namei.c`, paired with `end_creating()`, `end_removing()`, `end_renaming()` |
| Create or remove from kernel code, by path string | `start_creating_path()` with `end_creating_path()`; `start_removing_path()` with `end_removing_path()` |
| Look up one name under a directory from kernel code | `lookup_one()` (checks permission on the parent) or `lookup_noperm()` (does not); both take a `struct qstr`. There is no lookup_one_len() here |
| Drop the last reference to a dentry | `dput()`, then `fast_dput()`, `finish_dput()`, `dentry_kill()` in `fs/dcache.c`; there is no __dentry_kill() here |
| Drop the last reference to a file | `fput()`, then `__fput_deferred()`, `__fput()` in `fs/file_table.c`. `close(2)` uses `fput_close_sync()` and `filp_close()` uses `fput_close()` instead of `fput()` |
| Resolve a user path; find or create an inode; drop the last reference to an inode | Models have these right: `user_path_at()`, `iget_locked()` and `iget5_locked()`, `iput()` |

## Inodes

**Inode state word**

- `i_state` in `struct inode`: a `struct inode_state_flags` whose only member
  is `enum inode_state_flags_enum __state`; all access goes through the
  helpers in `include/linux/fs.h`.
- Locked writers: `inode_state_set()`, `inode_state_clear()`,
  `inode_state_assign()`, `inode_state_replace()`; each has a `_raw` twin that
  only drops the lockdep assertion.
- Unlocked read: `inode_state_read_once()` is the only one; there is no `_raw`
  read and no accessor with an _unlocked suffix.
- `I_FREEING` alone does not stop other writers: a writeback pass that holds
  `I_SYNC`, and `inode_unpin_lru_isolating()`, still change the word under
  `i_lock`.
- **Potentially unsafe usage**: changing the state with a `_raw` writer.
  - Unsafe: while another task can still change the state; the `_raw` writers
    store the whole word with a plain `WRITE_ONCE()`, so a change made under
    `i_lock` elsewhere is lost.
  - Safe: on a freshly allocated inode, as `inode_init_always_gfp()` does.
  - Safe: in `clear_inode()` called from the eviction method, because
    `evict()` has already waited for `I_LRU_ISOLATING` and `I_SYNC`.

**Lifecycle state flags**

- `I_CREATING` setters in `fs/inode.c`: `insert_inode_locked()` (with `I_NEW`,
  under `i_lock`) and `insert_inode_locked4()` (before it calls
  `inode_insert5()`); `inode_insert5()` itself sets only `I_NEW`. Filesystems
  set it too, on an inode not yet hashed, for example `ovl_create_object()`.
- `discard_new_inode()`: clears `I_NEW` only; `I_CREATING`, if set, stays, so
  `find_inode()` and `find_inode_fast()` keep returning `ERR_PTR(-ESTALE)` for
  that inode until `I_FREEING` or `I_WILL_FREE` is set on it.
- `I_NEW` without `I_CREATING` seen by a hash lookup: `find_inode()` and
  `find_inode_fast()` take a reference with `__iget()` first; the caller,
  except `ilookup5_nowait()`, then sleeps in `wait_on_new_inode()`; there is
  no wait_on_inode() in this tree.
- `I_FREEING` setters: `iput_final()`, `evict_inodes()`, `inode_lru_isolate()`;
  all under `i_lock` with `i_count` 0; there is no invalidate_inodes() here.
- Wakeups on `__I_NEW`: `inode_wake_up_bit()`, which is `wake_up_var()` on
  `inode_state_wait_address()`; `wake_up_bit()` on the word wakes nobody.
- Not every flag test is under `i_lock`: `igrab_from_hash()`,
  `find_inode_rcu()` and `find_inode_by_ino_rcu()` use
  `inode_state_read_once()`.
- `igrab_from_hash()` in `fs/inode.c`: tried first on each matching inode in
  `find_inode()` and `find_inode_fast()`; if none of `I_NEW`, `I_CREATING`,
  `I_FREEING`, `I_WILL_FREE` is seen and `i_count` is nonzero it takes the
  reference without `i_lock`.
- **Unsafe usage**: setting `I_NEW` or `I_CREATING` on an inode that is
  already inserted in the inode hash table; `igrab_from_hash()` may have
  tested the flags just before and hands the inode out as initialised.
  - Safe: set the flag before the insertion, as `insert_inode_locked4()` does,
    or together with it inside one `i_lock` hold, as `iget_locked()` and
    `insert_inode_locked()` do.

**Finding or creating an inode**

- Created inode on return: no lock is held; "locked" means `I_NEW` is set.
- Waiters: sleep in `wait_on_new_inode()` only when the lookup reported
  `isnew`; afterwards they test `inode_unhashed()` and, if true, `iput()` and
  retry, so they never return the inode that `iget_failed()` made bad.
- `iget_failed()`: `make_bad_inode()` (which calls `remove_inode_hash()`),
  `unlock_new_inode()`, `iput()`.
- `discard_new_inode()`: does not unhash; a waiter that already holds a
  reference returns that inode unless the filesystem unhashed it first.
- `ilookup5_nowait()`: reports `I_NEW` through its `bool *isnew` argument and
  does not wait.
- First hash probe: RCU-only in `iget_locked()`, `iget5_locked_rcu()` and
  `ilookup()`; `iget5_locked()` probes through `ilookup5()`, under
  `inode_hash_lock`.

**Inode references**

- `igrab()`: first tries `atomic_add_unless(&inode->i_count, 1, 0)` with no
  lock; it takes `i_lock` and tests `I_FREEING | I_WILL_FREE` only when the
  count is 0.
- `i_count` transitions 0 to 1 and 1 to 0: made only under `i_lock`; every
  other change may be made without it.
- `__iget()` in `include/linux/fs.h`: `lockdep_assert_held()` on `i_lock` and
  an `atomic_inc()`; it does not touch the LRU, `inode_lru_isolate()` removes
  referenced inodes lazily.
- `icount_read()`: asserts `i_lock`; `icount_read_once()` is the lockless
  hint.
- `iput()`: asserts `i_lock` is not held, and under `CONFIG_DEBUG_VFS` that
  neither `I_FREEING` nor `I_CLEAR` is set and the count is at least 1.
- `iput_if_not_last()` in `include/linux/fs.h`: does not sleep; returns
  `false` without dropping when the reference is the last, and the caller
  must then call `iput()` from a context that may sleep.
- **Unsafe usage**: setting `I_FREEING` or `I_WILL_FREE` while `i_count` is
  nonzero or without `i_lock`; `igrab()` and `igrab_from_hash()` take the
  reference on a nonzero count alone, and their `VFS_BUG_ON_INODE()` catches
  it only under `CONFIG_DEBUG_VFS`.
  - Safe: test `icount_read()` under `i_lock`, then set the flag in the same
    hold, as `evict_inodes()` does.

**Last reference**

- `iput()` fast path: `atomic_add_unless(&inode->i_count, -1, 1)`; only a
  count of 1 goes on to `i_lock` and `atomic_dec_and_test()`; it does not call
  `atomic_dec_and_lock()`.
- Lazytime before the last drop: `iput()` calls `sync_lazytime()` when
  `i_nlink` is nonzero and retries if it returned true; `sync_lazytime()`
  returns false when `I_DIRTY_TIME` is clear, otherwise it calls
  `->sync_lazytime` of `struct inode_operations` if set, else
  `mark_inode_dirty_sync()`.
- `inode_generic_drop()`: what `iput_final()` calls when `->drop_inode` is
  NULL; static inline in `include/linux/fs.h`, true for `!i_nlink` or
  `inode_unhashed()` only; `I_DONTCACHE` is tested by `iput_final()`.
- Old helper names generic_drop_inode and generic_delete_inode: not in this
  tree.
- Inode kept: drop returned 0, `I_DONTCACHE` clear and `SB_ACTIVE` set;
  `iput_final()` then calls `__inode_lru_list_add(inode, true)`; there is no
  inode_add_lru() here, the non-static form is `inode_lru_list_add()`.
- `I_REFERENCED`: set by `__inode_lru_list_add()` only when called with
  `rotate` true, which only `iput_final()` does, and the inode was already on
  the LRU.
- Writeback before eviction: only when drop returned 0 (so `I_DONTCACHE` is
  set or `SB_ACTIVE` is clear); `write_inode_now(inode, 1)` runs under
  `I_WILL_FREE`, then `inode_state_replace()` swaps it for `I_FREEING`.
- `i_count` recheck after `->drop_inode`: `iput_final()` makes it only on the
  evict path and only with `CONFIG_DEBUG_VFS`; on the cache path
  `__inode_lru_list_add()` just declines a nonzero count.

**Inode eviction**

- Order in `evict()`: `inode_io_list_del()`, `inode_sb_list_del()`, then under
  `i_lock` `inode_wait_for_lru_isolating()` and `inode_wait_for_writeback()`,
  the method, `cd_forget()` for a character device, `remove_inode_hash()`,
  `inode_wake_up_bit()` on `__I_NEW`, `destroy_inode()`.
- Waited for before the method: `I_LRU_ISOLATING` and `I_SYNC`; after it:
  nothing.
- Final `inode_wake_up_bit()`: called without `i_lock`; it changes no flag,
  and it wakes only `__wait_on_freeing_inode()` sleepers, which abort their
  sleep if they find the inode unhashed.
- `clear_inode()`: has `BUG_ON()` for `nrpages`, missing `I_FREEING`, `I_CLEAR`
  already set, and a non-empty `i_wb_list`.
- Metadata buffers: there is no i_private_list and no
  invalidate_inode_buffers() here; the buffer-list helpers, for example
  `mmb_invalidate()` and `mmb_sync()`, are in `fs/buffer.c`. A filesystem that
  keeps a `struct mapping_metadata_bhs` empties it with `mmb_invalidate()` in
  its own eviction method, as `ext2_evict_inode()` does; `clear_inode()` does
  not check it.

**Freeing an inode**

- `->destroy_inode` set and `->free_inode` NULL: `destroy_inode()` returns
  after the method and queues nothing; the filesystem frees the memory and
  must supply the RCU delay.
- Neither set: `i_callback()` calls `free_inode_nonrcu()` after the grace
  period.
- `i_fop`: shares a union with `free_inode`; `destroy_inode()` overwrites it
  before the grace period, so it must not be read through an RCU-only pointer.
- `i_dentry`: shares a union with `i_rcu`, which `call_rcu()` uses in
  `destroy_inode()`.
- Lockless hash probes are a second RCU reader: `find_inode()` and
  `find_inode_fast()`, when called with `hash_locked` false, walk the chain
  under `rcu_read_lock()` only, read `i_sb`, `i_ino`, the state and `i_count`,
  call the `test` callback and take `i_lock`; the memory of a hashed inode
  must outlive the grace period.
- `i_link` freed in `->free_inode`: see `shmem_free_in_core_inode()` in
  `mm/shmem.c`.

**Walking a superblock's inodes**

- `evict_inodes()` on `need_resched()`: drops the lock, runs
  `dispose_list()`, retakes the lock and resumes from the current inode; it
  does not restart from the list head.
- `inode_sb_list_del()`: called only from `evict()`, so an inode leaves
  `s_inodes` only in the hands of whoever set `I_FREEING` on it.
- **Potentially unsafe usage**: dropping `s_inode_list_lock` inside the loop
  and continuing from the current inode.
  - Unsafe: when nothing keeps the current inode on `s_inodes`; `evict()`
    unlinks and frees it and the next-pointer read is a use after free.
  - Safe: holding a reference taken with `__iget()` under `i_lock`, after
    skipping `I_NEW | I_FREEING | I_WILL_FREE`, and deferring `iput()` of the
    previous inode to the unlocked window, as `drop_pagecache_sb()`,
    `add_dquot_ref()` and `sync_bdevs()` do.
  - Safe: the walker itself set `I_FREEING` on the current inode and has not
    yet put it on the list it passes to `dispose_list()`, as `evict_inodes()`
    does.
- Loop that never drops the lock: needs no reference; `remove_dquot_ref()` in
  `fs/quota/dquot.c` scans `I_NEW` inodes too and touches only pointers
  guarded by `dq_data_lock`.
- `wait_sb_inodes()`: not an example; it walks `s_inodes_wb` under
  `s_inode_wblist_lock` and `rcu_read_lock()`.
- `fsnotify_unmount_inodes()`: not an example; through
  `fsnotify_get_living_inode()` it walks `inode_conn_list` of
  `struct fsnotify_sb_info` under `list_lock`, in `fs/notify/mark.c`.

## Dentries

**Dentry links and their locks**

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

**Dentry states**

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

**Attaching an inode**

| Helper | Dentry: what the code checks | Inode: what the code checks |
|---|---|---|
| `d_instantiate()` | `BUG_ON()` if positive; `WARN_ON()` if in-lookup; hashed or unhashed both pass | NULL: returns, nothing done |
| `d_instantiate_new()` | same as `d_instantiate()` | `BUG_ON(!inode)`; missing `I_NEW` is only a `WARN_ON()` |
| `d_add()` | nothing; ends in-lookup | NULL allowed |
| `d_splice_alias()` | `BUG_ON(!d_unhashed(dentry))`; ends in-lookup, except when it returns `-ELOOP` or `-ESTALE` | `IS_ERR()` returned first; NULL allowed |

- `d_add()` on a hashed dentry: not caught; `__d_add()` calls `__d_rehash()`
  unconditionally.
- `d_instantiate_new()`: does not call `unlock_new_inode()`; it clears
  `I_NEW | I_CREATING` and wakes waiters itself, under `i_lock`.
- `d_splice_alias()` with a hashed dentry: `BUG_ON()` fires, also for a NULL
  inode; only an `IS_ERR()` inode returns before the test.
- `d_splice_alias()` errors of its own: `-ELOOP` (alias is an ancestor of the
  dentry) and `-ESTALE` (from `__d_unalias()`: a trylock or
  `->d_unalias_trylock()` failed). It does not return `-EIO`.
- `d_splice_alias()` after moving an alias: the passed dentry is left
  negative and unhashed.
- `d_splice_alias_ops()`: in `fs/dcache.c`, not exported; also sets `d_op`
  through `d_set_d_op()`. Used by procfs.
- `d_make_persistent()`: a fifth helper. `WARN_ON()` for a positive dentry and
  for a NULL inode; consumes the inode reference, hashes the dentry if
  unhashed, sets `DCACHE_PERSISTENT` and takes one extra dentry reference that
  the caller does not own. For example `simple_link()` in `fs/libfs.c`.

**Result of a directory lookup**

- Non-NULL, non-error return: taken as a different dentry that carries its own
  reference. `__lookup_slow()`, `lookup_one_qstr_excl()` and `lookup_open()`
  `dput()` the passed dentry without comparing the two.
- **Unsafe usage**: `->lookup` returning the dentry it was passed, with no
  reference of its own; the caller's `dput()` drops the only reference to the
  dentry it then uses.
  - Safe: return NULL when the passed dentry was used, as `d_splice_alias()`
    does; `__lookup_slow()` then keeps the passed dentry and its reference.
- NULL return: the passed dentry may be positive, hashed negative, or left
  unhashed; `simple_lookup()` returns NULL without hashing for a casefolded
  directory under `CONFIG_UNICODE`.
- `lookup_one_qstr_excl()`: allocates with `d_alloc()`, not
  `d_alloc_parallel()`, so `->lookup` gets a dentry that is not in-lookup, and
  no `d_lookup_done()` follows. Callers such as `__start_dirop()` hold the
  directory's `i_rwsem` exclusive.
- `->lookup` therefore sees both kinds of dentry; `d_add_ci()` tests
  `d_in_lookup()` to pick `d_alloc_parallel()` or `d_alloc()`.

**Moving a dentry**

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

**Dentry references**

- Kill path: `dput()` calls `fast_dput()`, then `finish_dput()`, which loops
  over `dentry_kill()`. `dentry_kill()` calls `lock_for_kill()` itself; there
  is no __dentry_kill().
- `dentry_kill()` return: the parent, with its `d_lock` held, when the
  parent's count reached zero; `finish_dput()` then runs
  `retain_dentry()` on it and kills it if not retained.
- Killed at count zero, per `retain_dentry()`: unhashed;
  `DCACHE_DISCONNECTED`; `DCACHE_OP_DELETE` and `->d_delete()` non-zero;
  `DCACHE_DONTCACHE`. It tests neither `SB_ACTIVE` nor `I_DONTCACHE`, and a
  clear `DCACHE_REFERENCED` never causes a kill.
- `DCACHE_REFERENCED`: not set when the dentry is first put on the LRU; set by
  a later last `dput()` that finds it already there.
- `DCACHE_DONTCACHE` source: also inherited from `sb->s_d_flags` in
  `__d_alloc()`; ramfs, shmem, debugfs and others set it for every dentry.
- `DCACHE_PERSISTENT`: marks one counted reference taken by
  `d_make_persistent()`, which keeps such a dentry alive; in an in-memory
  filesystem the dentry is the only record of the name, not a cache entry. It
  is dropped by `d_make_discardable()`, and at umount by
  `select_collect_umount()`.
- `d_lookup()`: `__d_lookup()` checks each candidate under its `d_lock`, not
  `d_seq`, and increments the count there.
- `dget_parent()`: the fast path rechecks the child's `d_seq` after
  `lockref_get_not_zero()`; the slow path has `BUG_ON()` on a zero parent
  count.
- Alive test under `d_lock`: hashed, positive or count not dead each prove it,
  because `dentry_kill()` marks dead, unhashes and detaches the inode within
  one hold of `d_lock`.
- **Unsafe usage**: `dget()` with that dentry's `d_lock` held; `lockref_get()`
  in `lib/lockref.c` falls back to taking the same lock.
  - Safe: `dget_dlock()` under `d_lock`, as `d_alloc()` does for the parent.
- **Potentially unsafe usage**: `dget()` or `lockref_get()` on a dentry the
  caller holds no reference to.
  - Unsafe: when nothing the caller holds blocks `dentry_kill()`;
    `lockref_get()` increments a zero or dead count without a test.
  - Unsafe: on a `DCACHE_NORCU` dentry whose count is zero, even under
    `i_lock`; `lock_for_kill()` relies on that count never rising again.
  - Safe: on an alias without `DCACHE_NORCU`, taken from `inode->i_dentry`
    with `inode->i_lock` held, as `__d_find_dir_alias()` does for a
    directory; `lock_for_kill()` must take that `i_lock` before
    `dentry_kill()` marks the dentry dead.
  - Safe: `dget_alias_ilocked()` with `inode->i_lock` held, for any alias; it
    handles `DCACHE_NORCU`, as `__d_find_any_alias()` and
    `find_acceptable_alias()` show.
  - Safe: on `d_parent` of a dentry the caller holds, while `d_parent` cannot
    change: `d_splice_alias_ops()` does it under write-held `rename_lock`.
    The child's reference on the parent is taken in `d_alloc()`.

## Path walking

**Walk modes**

- `path_init()`: samples `nd->m_seq` from `mount_lock.seqcount` and `nd->r_seq`
  from `rename_lock.seqcount` in both modes; `nd->seq` is the `d_seq` of
  `nd->path.dentry`, and is zero in ref mode.
- `nd->r_seq`: compared only in `handle_dots()`, only under
  `LOOKUP_IS_SCOPED`, in both modes, together with `nd->m_seq`; a mismatch
  returns `-EAGAIN`, which `fs/namei.c` does not retry.
- `follow_dotdot_rcu()`: does not compare `nd->r_seq`; it checks `mount_lock`
  against `nd->m_seq` (only when it crosses a mount or stays where it is), the
  old dentry's `d_seq` against `nd->seq`, and `path_connected()`, each failing
  with `-ECHILD`.
- `lookup_fast()` in RCU mode: rechecks the parent's `d_seq` against `nd->seq`
  right after `__d_lookup_rcu()`, before `d_revalidate()`; `step_into()` checks
  the child's `d_seq` against `nd->next_seq`, not the parent's.
- `lookup_fast()` on a dcache miss in RCU mode: calls `try_to_unlazy()` itself
  and returns NULL, so the same component continues in ref mode, in
  `walk_component()` through `lookup_slow()`; `-ECHILD` only if the unlazy
  fails.
- Empty pathname: `path_init()` clears `LOOKUP_RCU`, so the first attempt is
  already a ref-walk.
- `do_file_open()` and `do_file_open_root()` in `fs/namei.c` run the
  `-ECHILD` / `-ESTALE` ladder for opens.
- `-EOPENSTALE`: `path_openat()` turns it into `-ECHILD` when the attempt was
  started with `LOOKUP_RCU`, into `-ESTALE` otherwise.

**Leaving RCU mode**

- `LOOKUP_CACHED`: `try_to_unlazy()` and `try_to_unlazy_next()` test it
  themselves and return false before legitimizing anything;
  `legitimize_links()` only has a `VFS_BUG_ON()` for it.
- `LOOKUP_CACHED` walk that had to unlazy: `-ECHILD`, then the rerun without
  `LOOKUP_RCU` gets `-EAGAIN` from `path_init()`.
- `complete_walk()`: clears `LOOKUP_CACHED` before `try_to_unlazy()`, so the
  final unlazy of a cached walk is allowed.
- `complete_walk()`: sets `nd->root.mnt` to NULL first, unless `ND_ROOT_PRESET`
  or `LOOKUP_IS_SCOPED`, so the root is not legitimized at the end of a walk.
- There is no LOOKUP_ROOT_GRABBED here; the bits are `ND_ROOT_GRABBED` and
  `ND_ROOT_PRESET` in `nd->state`.
- `legitimize_root()`: does nothing when `nd->root.mnt` is NULL or
  `ND_ROOT_PRESET` is set; otherwise sets `ND_ROOT_GRABBED` before the attempt;
  it has no `LOOKUP_IS_SCOPED` test.
- `__legitimize_path()`: calls `__legitimize_mnt()` first, then
  `lockref_get_not_dead()`, then checks `d_seq`; `legitimize_mnt()` is static
  in `fs/namespace.c` and `fs/namei.c` does not use it.
- `try_to_unlazy_next()`: does not call `__legitimize_path()` on `nd->path`;
  it takes the mount and parent references without rechecking the parent's
  `d_seq`, and checks the child's `d_seq` against `nd->next_seq`.
- `try_to_unlazy_next()` precondition: `dentry` is what `nd->next_seq` was
  sampled from; `handle_mounts()` restores `nd->next_seq` before the call
  because `__follow_mount_rcu()` may have overwritten it.
- `try_to_unlazy_next()` callers: `lookup_fast()`, on any `d_revalidate()`
  result <= 0, and `handle_mounts()`.
- `may_lookup()`: unlazies on any permission error in RCU mode, not only
  `-ECHILD`; `link_path_walk()` unlazies before it returns `-ENOTDIR`.
- **Potentially unsafe usage**: using, after `try_to_unlazy()`, a dentry or
  path found under RCU that is not `nd->path`, `nd->root` or an entry of
  `nd->stack`.
  - Unsafe: when nothing took a reference on it before `leave_rcu()` ran
    `rcu_read_unlock()`; `try_to_unlazy()` legitimizes only `nd->path`,
    `nd->root` and `nd->stack`, so the dentry may already be freed.
  - Safe: pass the child to `try_to_unlazy_next()`, as `lookup_fast()` does;
    it takes the reference with `lockref_get_not_dead()` before `leave_rcu()`.
  - Safe: call `legitimize_path()` on it with `nd->next_seq` before
    `try_to_unlazy()`, and still call `try_to_unlazy()` if that failed, as
    `reserve_stack()` does.
  - Safe: the link is already stored in `nd->stack` with its `seq`, so
    `legitimize_links()` covers it, as in `pick_link()` before
    `touch_atime()`.

**Filesystem methods in RCU mode**

- What the walk does with a return value in RCU mode:

  | Method | Asks to leave RCU mode | Other error |
  |---|---|---|
  | `->d_revalidate()` | `-ECHILD`; called again after `try_to_unlazy_next()` | walk unlazies first; `-ECHILD` if that fails |
  | `->permission()` | `-ECHILD`; called again after `try_to_unlazy()` | walk unlazies first; `-ECHILD` if that fails |
  | `->get_link()` | `ERR_PTR(-ECHILD)`; called again with the dentry | returned at once, still in RCU mode |
  | `->d_manage()` | any nonzero value except `-EISDIR` | same: called again with `false` |
  | `->get_inode_acl()` | any `ERR_PTR()` | same: `check_acl()` returns `-ECHILD` |

- `->d_revalidate()` returning 0 in RCU mode: not asked again; after a
  successful unlazy `lookup_fast()` calls `d_invalidate()` and returns NULL.
- `->d_manage()` returning `-EISDIR` in RCU mode: accepted there;
  `__follow_mount_rcu()` stops crossing mounts and the walk stays in RCU mode.
- `->get_inode_acl()` in RCU mode: called only by `get_cached_acl_rcu()`, and
  only for an inode whose ACL slot is `ACL_DONT_CACHE`.
- `security_inode_follow_link()` error in RCU mode: `pick_link()` returns it
  with no unlazy and no second call; `-ECHILD` restarts the whole walk.
- `->permission()` during a walk: `may_lookup()` calls
  `lookup_inode_permission_may_exec()`, which skips the method when
  `IOP_FASTPERM` or `IOP_FASTPERM_MAY_EXEC` is set, all of mode 0111 is set
  and `no_acl_inode()` is true.
- `->permission()` mask from `may_lookup()`: `MAY_EXEC`, plus `MAY_NOT_BLOCK`
  in RCU mode, and nothing else.
- `->get_link()` in RCU mode: may take a reference if it registers the release
  with `set_delayed_call()`, as `page_get_link()` does with a folio.
- `delayed_call` set in RCU mode: may run under `rcu_read_lock()`, since
  `terminate_walk()` calls `drop_links()` before `leave_rcu()`; it must not
  sleep.
- Data reached through `sb->s_fs_info` by a method that runs in RCU mode: must
  be freed after a grace period, for example `fat_put_super()` with
  `call_rcu()`; `struct super_block` itself is freed after a grace period,
  through `destroy_super_rcu()`.

## The inode lock and rename

**Inode lock by method**

- `->tmpfile`: called with no `i_rwsem` held; `vfs_tmpfile()` in `fs/namei.c`
  locks nothing on the directory.
- `->lookup`: the parent is held shared from `lookup_slow()`, exclusive from
  `lookup_one_qstr_excl()` and from `lookup_open()` when `O_CREAT` is set.
- `lookup_one()` and `lookup_noperm()`: call `->lookup` under whichever mode
  the caller holds; they only `WARN_ON_ONCE()` when the lock is not held.
- `->atomic_open`: the `open_flag` argument does not tell the lock mode.
  `lookup_open()` picks the mode from `op->open_flag`, then clears `O_CREAT`
  from the value it passes on when `create_error` is set, so the method can
  see no `O_CREAT` with the parent held exclusive.
- `dentry_create()`: also calls `->atomic_open`, under a parent lock that its
  caller took.
- `->fileattr_get`: `vfs_fileattr_get()` takes no lock; `vfs_fileattr_set()`
  calls it with the inode held exclusive.
- `->rename`: both parents are exclusive; the children that `vfs_rename()`
  locks are:

| Child | Locked by `vfs_rename()` |
|---|---|
| non-directory source | always |
| directory source | only when the parents differ |
| non-directory target that exists | always |
| directory target | unless the parents are equal and `RENAME_EXCHANGE` is set |

**Lock subclasses**

- `I_MUTEX_PARENT2`: spelled so; used only by `lock_two_directories()` in
  `fs/namei.c`, for the second directory, after `I_MUTEX_PARENT`.
- `I_MUTEX_CHILD`: not used for a parent in `lock_rename()`.
- `I_MUTEX_XATTR`: used by ext4 on EA inodes, in `fs/ext4/xattr.c`.
- lock_two_inodes(): not in this tree; `lock_two_nondirectories()` in
  `fs/inode.c` is the helper for two non-directories.
- `lookup_slow()` and `lookup_open()`: lock the parent with subclass 0
  (`inode_lock_shared()`, `inode_lock()`), not `I_MUTEX_PARENT`.
- Subclasses of the children in `vfs_rename()`:

| Source | Target | Source lock | Target lock |
|---|---|---|---|
| directory | any | `I_MUTEX_CHILD`, first | `inode_lock()`, second |
| non-directory | directory | `inode_lock()`, second | `I_MUTEX_CHILD`, first |
| non-directory | non-directory or none | `lock_two_nondirectories()` | same call |

- `__simple_recursive_removal()` in `fs/libfs.c`: locks each inode with
  `I_MUTEX_CHILD`, so a caller of `locked_recursive_removal()` holds the
  parent with `I_MUTEX_PARENT`, as `psinfo_lock_root()` does.
- Enum values are not a lock order: lockdep never compares two of them. See
  `look_up_lock_class()` in `kernel/locking/lockdep.c`; each key and subclass
  pair is one class, and the order is learned from use.
- Order the VFS uses: `I_MUTEX_PARENT`, `I_MUTEX_PARENT2`, `I_MUTEX_CHILD`,
  `I_MUTEX_NORMAL`, `I_MUTEX_NONDIR2`; that is 1, 5, 2, 0, 4.
- Subclass limit: below `MAX_LOCKDEP_SUBCLASSES`, which is 8; at or above it
  `__lock_acquire()` warns and turns lockdep off.
- Same key and same subclass held twice: `check_deadlock()` reports recursion
  whatever the real order; address order does not silence it, which is why
  `lock_two_nondirectories()` uses `I_MUTEX_NONDIR2` for the second inode.
- Lock keys: `inode_init_always_gfp()` gives every inode `i_mutex_key`. A
  directory moves to `i_mutex_dir_key` in
  `lockdep_annotate_inode_mutex_key()`, which is an empty stub without
  `CONFIG_DEBUG_LOCK_ALLOC`, or where the filesystem sets the class itself,
  as `xfs_setup_inode()` does.
- `lockdep_annotate_inode_mutex_key()`: called from `unlock_new_inode()`,
  `discard_new_inode()` and `d_instantiate_new()`, among others. A directory
  that never passes through it, in a filesystem that sets no class itself,
  shares a key with non-directories, so there only the subclass tells parent
  from child.
- **Potentially unsafe usage**: taking a second `i_rwsem` with the subclass
  already held.
  - Unsafe: when both inodes have the same lock key; `check_deadlock()`
    reports "possible recursive locking".
  - Safe: when the keys differ, as in `ecryptfs_do_unlink()` under
    `->unlink`: the eCryptfs directory and the lower directory are both held
    with `I_MUTEX_PARENT`, and `ecryptfs_get_tree()` refuses a lower
    filesystem of type eCryptfs, so the keys belong to two
    `struct file_system_type`.
  - Safe: when the second uses another subclass, as in `filename_rmdir()`:
    parent `I_MUTEX_PARENT` in `__start_dirop()`, child `inode_lock()` in
    `vfs_rmdir()`.

**Rename locking**

- `lock_rename()`, `lock_rename_child()`, `unlock_rename()` and
  `lock_two_directories()`: all `static` in `fs/namei.c`, declared in no
  header, not exported.
- `vfs_rename()`: exported; it expects the parents locked already.
- `lock_rename()`: when `p1 != p2`, takes `s_vfs_rename_mutex` of `p1->d_sb`
  with no test that the two directories share a superblock.
- `-EXDEV` from `lock_two_directories()`: returned when the `d_parent` walks
  find no common ancestor; that branch drops `s_vfs_rename_mutex` itself.
- Directory locked second by `lock_two_directories()`: always
  `I_MUTEX_PARENT2`; it is `p1` when `p2` is an ancestor of `p1`.
- `lock_rename_child()`: no retry loop. It tries once without the mutex,
  then decides under `s_vfs_rename_mutex`.
- `lock_rename_child()` returning NULL: can mean one directory locked and
  the mutex not held; `unlock_rename()` handles that because it is then
  called with `p1 == p2`.

**Rename start helpers**

- Helpers, all exported from `fs/namei.c` and declared in
  `include/linux/namei.h`:

| Function | Caller has | Permission check |
|---|---|---|
| `start_renaming()` | two parents, two names | `MAY_EXEC` on both parents |
| `start_renaming_dentry()` | source dentry, target name | `MAY_EXEC` on `new_parent` |
| `start_renaming_two_dentries()` | both dentries | none |
| `end_renaming()` | a successful start | - |

- Superblock: the helpers do not compare superblocks. `nfsd_rename()` and
  `ksmbd_vfs_rename()` compare the mounts before the call.
- Dentry variants after locking: `-EINVAL` if `old_dentry` is unhashed, or
  if `rd->old_parent` is non-NULL and is not `old_dentry->d_parent`.
- `start_renaming_two_dentries()`: also `-EINVAL` if `new_dentry` is
  unhashed or `rd->new_parent != new_dentry->d_parent`, and `-EEXIST` if
  `new_dentry` is positive with `RENAME_NOREPLACE`.
- `struct renamedata`, filled by the caller: `mnt_idmap`, `new_parent`,
  `flags`, `delegated_inode`, and `old_parent`.
- `old_parent`: required by `start_renaming()`; may be NULL for the two
  dentry variants, which then set it.
- `old_dentry` and `new_dentry`: filled by the helpers, with references.
- `mnt_idmap`: one field; there are no per-side idmap fields.
- `delegated_inode`: a `struct delegated_inode *`, read only by
  `vfs_rename()`; may be NULL.
- `struct renamedata` on the stack without an initialiser: the helpers read
  `old_parent` and `flags`, so set every caller field, as
  `ksmbd_vfs_rename()` does.
- `end_renaming()`: calls `dput()` on `rd->old_parent`; that is the extra
  reference the start helper took, not the caller's.
- **Unsafe usage**: calling `end_renaming()` after a start helper returned an
  error; nothing is locked and `rd->old_dentry` was not set.
  - Safe: skip it on error, as `nfsd_rename()` does.

**Locking a parent by hand**

- `filename_create()`: static; it locks through `start_dirop()`.
- `start_creating()` family: declared in `include/linux/namei.h`; each locks
  the parent with `I_MUTEX_PARENT`. All but `start_creating_dentry()` and
  `start_removing_dentry()` do so in `__start_dirop()` and look the name up.
- nfsd, cachefiles, overlayfs, ecryptfs, ksmbd and devtmpfs: use that family;
  none locks a parent itself to create, remove or rename an entry.
- By-hand examples: `fuse_reverse_inval_entry()` in `fs/fuse/dir.c` and
  `bm_remove_entry()` in `fs/binfmt_misc.c`.
- **Potentially unsafe usage**: plain `inode_lock()` on a parent directory.
  - Unsafe: when `vfs_rmdir()`, `vfs_unlink()` or `vfs_link()` follows; each
    calls `inode_lock()` on the victim or the link source, and
    `check_deadlock()` reports recursion if the two share a lock key.
  - Safe: when no second `i_rwsem` of that key is taken under it, as in
    `lookup_open()`.
  - Safe: `inode_lock_nested(dir, I_MUTEX_PARENT)` then `inode_lock()` on the
    child, as `fuse_reverse_inval_entry()` does.
- **Potentially unsafe usage**: holding `i_rwsem` on two directories.
  - Unsafe: when both are on one filesystem, neither is the parent of the
    other and `s_vfs_rename_mutex` is not held; `lock_two_directories()`
    orders by ancestry and can take them in the opposite order.
  - Safe: parent then its child, as `cachefiles_get_directory()` does after
    `start_creating()`.
  - Safe: through `start_renaming()` and its variants.
  - Safe: a directory of a stacking filesystem, then one of the filesystem
    below it, as `ecryptfs_do_unlink()` does under `->unlink`;
    `lock_two_directories()` returns `-EXDEV` without locking when the two
    share no ancestor.

## Looking up and changing directory entries

**Looking up one name**

- `lookup_one()` and `lookup_noperm()`: the caller holds
  `base->d_inode->i_rwsem`; both open with
  `WARN_ON_ONCE(!inode_is_locked(base->d_inode))`.
- `inode_is_locked()`: is `rwsem_is_locked()`, so a shared hold satisfies it,
  and so does a hold by any other task.
- Shared hold: enough for `lookup_one()` and `lookup_noperm()`; they fall back
  to `__lookup_slow()`, the same function `lookup_slow()` runs under
  `inode_lock_shared()`.
- `lookup_one_positive_killable()`: checks permission, is called unlocked,
  on a dcache miss takes the lock shared with a killable wait, returns
  `ERR_PTR(-EINTR)` if killed and `ERR_PTR(-ENOENT)` for a negative dentry.
- `try_lookup_noperm()`: after `lookup_noperm_common()` it calls `d_lookup()`
  only; it does not revalidate and never calls `->lookup`. The other forms
  revalidate through `lookup_dcache()`.
- `lookup_one_qstr_excl()`: `static` in `fs/namei.c`; no name validation, no
  hashing, no permission check, no lock assertion; the caller holds the lock
  exclusive and passes a hashed name.
- `start_dirop()`: the lock-and-lookup wrapper around
  `lookup_one_qstr_excl()`; declared in `fs/internal.h` and not exported.
  Other code uses the helpers in "Create and remove start helpers".
- lookup_one_len() and its variants: not defined in this tree; every form
  takes a `struct qstr *`.

**Lookup without permission check**

- `lookup_one_common()` in `fs/namei.c`: is `lookup_noperm_common()` followed
  by `inode_permission(idmap, base->d_inode, MAY_EXEC)`; that call is the
  whole difference between the two families.
- `ecryptfs_lookup()` and `ksmbd_vfs_path_lookup()`: call
  `lookup_noperm_unlocked()`, not a `lookup_one()` form.
- cachefiles: calls `lookup_one_positive_unlocked()` and `start_creating()`
  with `&nop_mnt_idmap`, not a noperm form.
- overlayfs: `ovl_lookup_positive_unlocked()` and
  `ovl_lookup_upper_unlocked()` (in `fs/overlayfs/overlayfs.h`) call
  `lookup_one_unlocked()` with the layer's idmap, and `ovl_lookup_index()`
  calls `lookup_one_positive_unlocked()`; there is no ovl_lookup_upper().
- overlayfs NFS export code: uses noperm forms, in `ovl_get_index_fh()` and
  `ovl_lookup_real_one()`.
- **Potentially unsafe usage**: a `lookup_noperm()` form on a directory, with
  a name that comes from a user or a network client.
  - Unsafe: when nothing before the call checked `MAY_EXEC` on that directory
    for the acting credentials; `lookup_noperm_common()` makes no permission
    check, so an unsearchable directory is searched.
  - Safe: when the directory was reached by a path walk, which calls
    `may_lookup()` on it in `link_path_walk()` before parsing the last
    component, as `kern_path_parent()` and `ksmbd_vfs_path_lookup()` do after
    `filename_parentat()` and `vfs_path_parent_lookup()`.
  - Safe: when a filesystem looks up, in its own tree, a name chosen by kernel
    code, as `debugfs_lookup()` does.

**Kernel path helpers**

- kern_path_locked(), kern_path_create(), done_path_create(),
  user_path_locked_at() and start_removing_user_path_at(): none is defined in
  this tree, not even as a wrapper.

| Helper | Returns | Holds on success | Released by |
|---|---|---|---|
| `start_creating_path()` | negative dentry, or `-EEXIST` | parent lock, write access, parent path | `end_creating_path()` |
| `start_creating_user_path()` | same, from a user string | same | `end_creating_path()` |
| `start_removing_path()` | positive dentry, or `-ENOENT` | parent lock, write access, parent path | `end_removing_path()` |

- `end_removing_path()`: is `end_creating_path()`; it unlocks, drops the
  dentry, calls `mnt_drop_write()` and `path_put()`. `end_removing()` plus
  `path_put()` leaks the write access.
- `end_creating_path()` with an `ERR_PTR` dentry: skips unlock and `dput()`
  but still drops write access and the path, so it is right after a failed
  `vfs_mkdir()` and wrong after a failed `start_creating_path()`.
- User-string removal: no helper; `filename_rmdir()` and
  `filename_unlinkat()` call `filename_parentat()`, `mnt_want_write()` and
  `start_dirop()` themselves.
- `kern_path_parent()`: returns the parent in `*path` and the child dentry
  with nothing locked and no write access; the child can be negative; the
  caller releases with `dput()` and `path_put()`.

**Create and remove start helpers**

- `start_creating()`, `start_creating_killable()`, `start_creating_noperm()`
  on an existing name: return the positive dentry, not `-EEXIST`; they pass
  `LOOKUP_CREATE` without `LOOKUP_EXCL`.
- Positive dentry from `start_creating()`: the bracket is open and must be
  ended; `may_create_dentry()` in the `vfs_` helpers returns `-EEXIST` for
  it. `cachefiles_get_directory()` tests `d_is_negative()` and reuses a
  positive one.
- Exclusive creation: `simple_start_creating()` in `fs/libfs.c` and
  `start_creating_path()` pass `LOOKUP_CREATE | LOOKUP_EXCL` and return
  `ERR_PTR(-EEXIST)` for an existing name.
- `start_creating_dentry()` and `start_removing_dentry()`: do no lookup and no
  permission check; the checks they do make under the lock, and what they
  return, are in "Rechecking a dentry after locking".
- Write access: none of the forms that take a parent dentry calls
  `mnt_want_write()`; the caller does, as `ksmbd_vfs_kern_path_create()` does
  before `start_creating_noperm()`.
- `end_creating_keep()`: takes the one dentry, unlocks the parent, returns
  the same pointer with a reference the caller now owns; an `ERR_PTR` passes
  through untouched.
- `end_dirop()`: unlocks `de->d_parent->d_inode`, so the dentry passed to any
  end function must be the one whose parent was locked, or its replacement
  from `vfs_mkdir()`.
- `start_dirop()`: no name validation, no hashing, no permission check;
  declared in `fs/internal.h`; `end_dirop()` is exported and declared in
  `include/linux/fs.h`.

**Result of mkdir**

- `vfs_mkdir()` on failure: calls `end_creating(dentry)` on every error path,
  so the parent is unlocked and the passed dentry is released before the
  `ERR_PTR` returns.
- `vfs_mkdir()` return value: the dentry to use or an `ERR_PTR`, never NULL;
  only the `->mkdir` method returns NULL.
- Unlock target: `dentry->d_parent->d_inode`, not the `dir` argument, so it
  happens however the caller took the lock.
- Other `vfs_` helpers in `fs/namei.c`: none calls `end_creating()`; after a
  failed `vfs_create()` or `vfs_link()` the parent is still locked and the
  caller ends the bracket with the original dentry.
- Parent after failure: a caller that reached the parent only through the
  passed dentry has no dentry left that names it; `ecryptfs_mkdir()` takes
  `dget(lower_dentry->d_parent)` before the call.
- Successful return: `vfs_mkdir()` does not test that the dentry is positive
  or hashed; `nfsd_create_locked()` tests `d_is_negative()`,
  `ecryptfs_mkdir()` tests `d_unhashed()`, `cachefiles_get_directory()` tests
  both and retries.
- **Unsafe usage**: unlocking the parent, or passing the original dentry to
  `end_creating()`, after `vfs_mkdir()` returned an `ERR_PTR`.
  - Safe: assign the return value over the dentry variable and pass that to
    `end_creating()`, which does nothing for an `ERR_PTR`, as
    `nfsd4_create_clid_dir()` and `cachefiles_get_directory()` do.
  - Safe: pass the return value to `end_creating_path()`, which still drops
    write access and the path, as `dev_mkdir()` in `drivers/base/devtmpfs.c`
    does.
- **Potentially unsafe usage**: `dput()` of the original dentry after
  `vfs_mkdir()` returned an `ERR_PTR`.
  - Unsafe: when the caller's only reference was the one it passed in;
    `end_dirop()` already dropped it.
  - Safe: when the caller took a second reference with `dget()` before the
    call, as `nfsd_create_locked()` does with `dget(resfhp->fh_dentry)`;
    `nfsd_create()` then calls `dput()` on the original.

**Calling the vfs_ helpers**

- may_delete(): not defined; the VFS checks are `may_create_dentry()` and
  `may_delete_dentry()` in `fs/namei.c`, both exported. `may_create()` in
  this tree is an unrelated static in `security/selinux/hooks.c`.
- `may_delete_dentry()` with a wrong parent: `BUG_ON(victim->d_parent->d_inode
  != dir)`, not an error return; a negative victim gives `-ENOENT` first.
- Trap checks: made inside the `start_renaming()` family (`-EINVAL` for a
  source that is an ancestor, `-ENOTEMPTY` or `-EINVAL` for a target that
  is); the caller never sees the trap dentry.
- `RENAME_NOREPLACE`: the `start_renaming()` family returns `-EEXIST` for a
  positive target itself.
- `vfs_rename()`: does not compare mounts and does not validate `flags`;
  `filename_renameat2()` does both before the call.
- Delegations: `vfs_create()`, `vfs_mknod()`, `vfs_mkdir()`, `vfs_symlink()`,
  `vfs_rmdir()`, `vfs_unlink()`, `vfs_link()` and `vfs_rename()` each take a
  `struct delegated_inode *` (`vfs_rename()` in `rd->delegated_inode`), and
  each calls `try_break_deleg()` on the parent directory; `vfs_unlink()`,
  `vfs_link()` and `vfs_rename()` also call it on a non-directory victim or
  source.
- `delegated_inode` NULL: allowed; `try_break_deleg()` can then still return
  `-EWOULDBLOCK`, without recording an inode to wait on.
- `vfs_create()`: takes idmap, dentry, mode and `struct delegated_inode *`;
  no directory inode, it uses `dentry->d_parent`; returns `-EACCES`, not
  `-EPERM`, when the filesystem has no `->create`.

**Rechecking a dentry after locking**

- Checks under the lock, as `start_removing_dentry()` and
  `start_creating_dentry()` in `fs/namei.c` make them:
  `!IS_DEADDIR(parent->d_inode)`, `child->d_parent == parent`,
  `!d_unhashed(child)`, then positive for removal or negative for creation.
- Error codes: `-EINVAL` when one of the first three fails; then `-ENOENT`
  from `start_removing_dentry()` for a negative child, `-EEXIST` from
  `start_creating_dentry()` for a positive one; the parent is unlocked on
  each.
- Reference: the helper returns `dget(child)`; the end function drops that
  one, the caller's own reference stays.
- Rename helpers: test `d_unhashed()` and the parent of a passed dentry, not
  that the source is positive or that its parent is dead;
  `may_delete_dentry()` in `vfs_rename()` tests those.
- lock_parent(), fh_lock() and ovl_parent_lock(): not defined in this tree.
- **Unsafe usage**: locking a directory taken from a held dentry, then
  passing the dentry to a `vfs_` helper or an end function with no recheck.
  - Unsafe: when another task can rename or remove the entry before the lock
    is taken; `may_delete_dentry()` hits its `BUG_ON()`, `vfs_create()` works
    on `dentry->d_parent`, and `end_dirop()` unlocks
    `de->d_parent->d_inode`, each of which may be an unlocked directory.
  - Safe: `start_removing_dentry()`, as in `cachefiles_delete_object()`,
    `ovl_cleanup()` and `ksmbd_vfs_unlink()`; the last takes the parent with
    `dget_parent()` first.
  - Safe: `start_creating_dentry()`, as in `ecryptfs_start_creating_dentry()`.
  - Safe: `start_renaming_dentry()`, as in `ksmbd_vfs_rename()` and
    `cachefiles_bury_object()`.
  - Safe: looking the name up under the lock instead, with
    `start_removing()` or `start_removing_path()`, as `handle_remove()` in
    `drivers/base/devtmpfs.c` does.

## Files and descriptors

**File references**

- `f_ref` in `struct file`: a `file_ref_t` from `include/linux/file_ref.h`, not
  an `atomic_long_t`; `struct file` has no `f_count` field.
- `get_file()`: calls `file_ref_inc()`, which increments unconditionally and
  only `WARN_ONCE()`s if the count was already released.
- `get_file_rcu()`: takes the address of the slot (`struct file __rcu **`),
  not a file pointer; the caller holds `rcu_read_lock()`.
- `get_file_rcu()` recheck: done inside, in `__get_file_rcu()` in `fs/file.c`;
  the caller does not re-read the slot.
- `get_file_rcu()` return: a file with a reference held that the slot still
  pointed to after the reference was taken; NULL only when the slot read NULL.
- `get_file_rcu()` on a dead count or a changed slot: retries, never returns
  NULL for it.
- `get_file_active()`: takes `rcu_read_lock()` itself and makes one attempt;
  NULL also means the count was dead or the slot changed.
- Cache: `filp_cache` (and `bfilp_cache` for backing files) in
  `fs/file_table.c`, both `SLAB_TYPESAFE_BY_RCU`; `files_cachep` is the
  `struct files_struct` cache.
- Stray references: `__get_file_rcu()` and `__fget_files_rcu()` take the
  reference before they validate, so a recycled file can briefly carry a
  reference from a lookup of another file.
- `file_count()`: can be transiently high for that reason.
- Final `fput()`: can be the one that drops such a stray reference, so
  `__fput()` may be queued by a task that never used the file.

**Descriptor lookup**

- Models have the layout, the accessors and the borrow rule right; see
  `__fget_light()` in `fs/file.c`.
- `fdget_pos()`: takes `f_pos_lock` only when `file_needs_f_pos_lock()` agrees:
  `FMODE_ATOMIC_POS` is set and either the count is not exactly one or the
  file has `iterate_shared`.

**Installing a descriptor**

- `fd_install()` on a `FMODE_BACKING` file: `WARN_ON_ONCE()` and return;
  nothing is installed and the reference is not consumed.
- Combined helpers, all in `include/linux/file.h`:

| Helper | Use |
|---|---|
| `FD_ADD(flags, file_expr)` | reserve, create, install; returns the fd or an error |
| `FD_PREPARE(fdf, flags, file_expr)` | reserve and create; test `fdf.err`; setup may follow |
| `fd_publish(fdf)` | install; returns the fd; cannot fail |
| `CLASS(get_unused_fd, fd)(flags)` with `take_fd()` | reservation only |

- `FD_PREPARE()` scope exit without `fd_publish()`: `put_unused_fd()` and
  `fput()` run from `class_fd_prepare_destructor()`.
- `fd_prepare_fd()` and `fd_prepare_file()`: the only accessors; after
  `fd_publish()` they give `-EBADF` and NULL.
- File expression: evaluated only if the descriptor was reserved; see
  `__FD_PREPARE_INIT()`.
- Existing file passed as the expression: when the reservation fails the file
  is not put and the caller still owns its reference; `receive_fd()` in
  `fs/file.c` calls `get_file()` only after `fdf.err` was checked.
- There is no anon_inode_getfd_secure() here; `anon_inode_create_getfd()` in
  `fs/anon_inodes.c` does that.
- `anon_inode_getfile()`: creates the file only; `anon_inode_getfd()` is the
  combined form, built on `FD_ADD()`.
- There is no `DEFINE_FREE()` wrapper for `put_unused_fd()`; `DEFINE_FREE(fput,
  ...)` gives `__free(fput)` for the file.

**Open-time checks**

- Just-created file (`FMODE_CREATED`): `may_open()` still runs;
  `inode_permission()` is called with `MAY_OPEN` alone, and the type switch,
  `IS_APPEND()` and `O_NOATIME` tests still apply.
- `mnt_want_write()` in `do_open()`: taken before `may_open()`, and only for a
  regular file with `O_TRUNC` that was not just created; that same test
  decides whether `handle_truncate()` runs.
- After `vfs_open()`: `do_open()` calls `security_file_post_open()`, then
  `handle_truncate()`; it does not call `ima_file_check()`, which is a static
  LSM hook in `security/integrity/ima/ima_main.c`, reached through
  `security_file_post_open()`.
- `->atomic_open()` that opened the file (`FMODE_OPENED`): `may_open()` runs
  after the filesystem's open method.
- `vfs_tmpfile()`: calls `may_open()` with `acc_mode` 0 after `->tmpfile()` has
  created and opened the file.
- No `may_open()` at all, for example: `O_PATH` (`do_o_path()`),
  `dentry_open()`, `kernel_file_open()` and `vfs_lookup_open()` reach
  `vfs_open()` without it.
- `__O_REGULAR` on a non-regular file: `-EFTYPE` from `do_open()`, before
  `may_open()`.
- `O_CREAT` on an existing directory: `-EISDIR` from `do_open()`, not from
  `may_open()`.

| Type | `may_open()` check |
|---|---|
| `S_IFLNK` | `-ELOOP` |
| `S_IFDIR` | `MAY_WRITE` gives `-EISDIR`; `MAY_EXEC` gives `-EACCES` |
| `S_IFBLK`, `S_IFCHR` | `may_open_dev()` false gives `-EACCES`: `MNT_NODEV` or `SB_I_NODEV` |
| devices, `S_IFIFO`, `S_IFSOCK` | `MAY_EXEC` gives `-EACCES` |
| `S_IFREG` | `MAY_EXEC` with `path_noexec()` gives `-EACCES`; nothing else |
| other | `VFS_BUG_ON_INODE(!IS_ANON_FILE(inode), inode)`, only with `CONFIG_DEBUG_VFS` |

- Devices, FIFOs and sockets: `O_TRUNC` is dropped from the local `flag` only;
  `acc_mode` is kept and `inode_permission()` still runs.
- Immutable inode: not tested in `may_open()`; `inode_permission()` returns
  `-EPERM` for `MAY_WRITE`.

**File operations pointer**

- NULL `i_fop` or failed `try_module_get()`: both hit `WARN_ON(!f->f_op)` in
  `do_dentry_open()` and return `-ENODEV`.
- Failed open: `cleanup_all` calls `fops_put(f->f_op)` and leaves `f_op`
  pointing at the table; it is not reset to NULL.
- `replace_fops()`: a statement macro; it returns nothing and calls no
  `->open`.
- New `->open` failing after `replace_fops()`: `do_dentry_open()` drops the
  new table's reference under `cleanup_all`; the open method must not drop it
  too, see `chrdev_open()` in `fs/char_dev.c`.
- Pseudo files: `file_init_path()` in `fs/file_table.c` stores the caller's
  table without `fops_get()`, yet `__fput()` always calls `fops_put()`.
- `__anon_inode_getfile()`: takes that module reference itself with
  `try_module_get()` before `alloc_file_pseudo()`.
- **Potentially unsafe usage**: assigning `file->f_op` directly.
  - Unsafe: when the old or the new table sets `owner`, the two differ, and
    the code does not itself pin the new owner and drop the old one;
    `do_dentry_open()` pinned the old owner and `fops_put()` in `__fput()`
    drops the new one.
  - Safe: `fops_get()` on the new table, then `replace_fops()`, inside
    `->open()`, as `chrdev_open()` does.
  - Safe: `fops_get()` on the new table by hand, with the old table saved
    and passed to `fops_put()` later, as `snd_card_disconnect()` and
    `snd_card_file_remove()` in `sound/core/init.c` do.
  - Safe: when neither table sets `owner`, as `memory_open()` in
    `drivers/char/mem.c`; `module_put()` ignores NULL.

**Private data**

- Failure after `->open()` returned 0: `FMODE_OPENED` is already set, so the
  caller's `fput()` runs `->release()`; the open method's allocation must not
  be freed a second time.
- Such failures, for example: the `O_DIRECT` test at the end of
  `do_dentry_open()`; in `do_open()`, `security_file_post_open()` and
  `handle_truncate()`; `may_open()` after `->atomic_open()` opened the file.
- Files from `alloc_file_pseudo()` or `alloc_file_clone()`: `file_init_path()`
  sets `FMODE_OPENED` although `->open()` never ran.
- `fput()` on an error path after such a file was created: runs `->release()`
  with whatever `private_data` holds then.
- `__anon_inode_getfile()`: sets `private_data` to its `priv` argument before
  it returns the file.

**Final fput**

- File without `FMODE_OPENED` and without `FMODE_BACKING`: `__fput_deferred()`
  calls `file_free()` at once, in any context; nothing is queued.
- `__fput_sync()`: the body has no check of the caller; it runs `__fput()`
  inline, which calls `might_sleep()`, `->release()`, `dput()` and `mntput()`.
- `__fput_sync()` caller: must be able to sleep and hold nothing those calls
  may need; a kernel thread is not required.
- `close(2)`: uses `fput_close_sync()`, not `__fput_sync()`.
- `filp_close()`: uses `fput_close()`, which defers like `fput()`.
- `fput_close_sync()` and `fput_close()`: declared in `fs/internal.h`, not
  exported; same requirements as `__fput_sync()` and `fput()`.
- `fput_close()` with other references outstanding: correct, only slower;
  `file_ref_put_close()` falls back to `file_ref_put()`. `path_openat()` uses
  it for a file that was never installed.
- No variant waits for `->release()` when another reference exists; all of
  them return at once unless the caller dropped the last one.
- `flush_delayed_fput()`: runs `delayed_fput_list` in the caller's context,
  then flushes `delayed_fput_work`; it does not reach files queued as task
  work.
- `task_work_run()`: not exported; `init_flush_fput()` in `init/do_mounts.h`
  calls `flush_delayed_fput()` and then `task_work_run()`.
- Flush and synchronous release together: see `nfsd_filp_close()` in
  `fs/nfsd/vfs.c`; it takes a reference, calls `filp_close()`, then
  `__fput_sync()`.

## Superblocks and write access

**Superblock references**

- `s_passive`: the passive count, a `refcount_t` in `struct super_block`
  (`include/linux/fs/super_types.h`); `struct super_block` has no `s_count`
  member and there is no __put_super() in this tree.
- What each keeps alive: `s_active` the filesystem, `s_passive` the
  structure.
- `s_passive` needs no `sb_lock`: `put_super()` and `user_get_super()` change
  it without `sb_lock`.
- `put_super()` (`fs/super.c`, declared in `fs/internal.h`): takes `sb_lock`
  itself on the final drop, so call it with `sb_lock` not held.
- Final `put_super()`: unlinks `s_list` and `s_instances`, queues
  `destroy_super_rcu()`, then calls `put_filesystem()`.
- `s_passive` therefore also pins the filesystem module, taken by
  `get_filesystem()` in `sget_fc()`; `deactivate_locked_super()` has no
  `put_filesystem()` call of its own, only the one in its `put_super()`.
- A dead superblock stays on `super_blocks` and `fs_supers` until the last
  passive reference goes; `kill_super_notify()` does not unhash it.
- `kill_super_notify()`: drops the `struct super_dev` claim of `sget_fc()`,
  then sets `SB_DEAD` under `sb_lock`; `sget_fc()` skips entries with
  `SB_DEAD`.
- A listed superblock can have `s_passive` already at zero: walkers pin with
  `refcount_inc_not_zero()` under `sb_lock`, before they call `super_lock()`,
  and skip on failure, as `__iterate_supers()` and `iterate_supers_type()`
  do.
- Each `struct super_dev` in `super_dev_table` holds one passive reference:
  taken in `super_dev_insert()`, dropped in `super_dev_put()` when `sd_ref`
  reaches zero.
- `deactivate_super()`: `atomic_add_unless(&s->s_active, -1, 1)`; only when
  that fails does it take `s_umount` exclusive and call
  `deactivate_locked_super()`.
- `generic_shutdown_super()`: sets `SB_DYING` after the teardown, just before
  it releases `s_umount`; the teardown before it runs only if `s_root` is set.

**The superblock lock**

- `super_lock()`: waits first, with `wait_var_event()` on `s_flags`, for
  `SB_BORN` or `SB_DYING`; it does not sleep on the rwsem while the superblock
  is being set up.
- `super_lock()` with `SB_DYING` set after the wait: returns false and never
  takes `s_umount`; otherwise it locks, rechecks `SB_DYING`, and unlocks and
  returns false if set.
- `super_lock()`, `super_lock_shared()`, `super_lock_excl()`: static in
  `fs/super.c`. Code elsewhere uses `iterate_supers()`,
  `iterate_supers_type()`, `user_get_super()` or `super_trylock_shared()`.
- `__iterate_supers()`: makes no `s_root` test; the callback gets every
  superblock for which `super_lock()` returned true.
- `SUPER_ITER_UNLOCKED`: the callback runs with no `s_umount`; each in-tree
  callback calls `get_active_super()` before it acts, for example
  `filesystems_freeze_callback()`.
- `SUPER_ITER_EXCL`: the callback runs with `s_umount` exclusive; used by
  `do_emergency_remount()`.
- Lookup by device: there is no bdev_super_lock() here. `user_get_super()`
  and the four `fs_holder_ops` callbacks, for example `fs_bdev_mark_dead()`,
  walk `super_dev_table` with `super_dev_first()` and `super_dev_next()`,
  without `sb_lock`.
- The pinned `struct super_dev` supplies the passive reference for
  `super_lock()` in those walks.
- `->get_tree()`: entered with no superblock lock; returns with `s_umount`
  exclusive on `fc->root->d_sb`, for a reused superblock too (`grab_super()`).
- quotactl: `s_umount` exclusive when `quotactl_cmd_onoff()` is true, shared
  otherwise; see `quotactl_block()` in `fs/quota/quota.c`.
- `->evict_inode()`: no `s_umount` from `iput()`; exclusive when reached from
  `evict_inodes()` in `generic_shutdown_super()`; shared from
  `fs_bdev_mark_dead()`.
- `->remove_bdev()`: `s_umount` shared, from `fs_bdev_mark_dead()`.
- `->nr_cached_objects()`: called from `super_cache_count()` with no
  `s_umount`, after an `SB_BORN` test only; `super_cache_scan()` calls it
  under `super_trylock_shared()`.
- **Potentially unsafe usage**: taking `s_umount` with `down_read()` or
  `down_write()` instead of `super_lock()`.
  - Unsafe: on a superblock reached only through `super_blocks`, `fs_supers`
    or `super_dev_table`, with no active reference; it may lack `SB_BORN` or
    have `SB_DYING`, which `super_lock()` and `super_trylock_shared()` test.
  - Safe: while holding an active reference through a mount or an open file,
    as `do_remount()` and the `syncfs` syscall in `fs/sync.c` do;
    `deactivate_locked_super()` calls `->kill_sb()` only when `s_active`
    reaches zero.
- **Unsafe usage**: calling `put_super()` with `sb_lock` held; the final drop
  takes `sb_lock` again.
  - Safe: drop `sb_lock`, call `put_super()`, retake `sb_lock`, as
    `iterate_supers_type()` does.

**Mount context API**

- `struct file_system_type` (`include/linux/fs.h`): has no `mount` member;
  `init_fs_context` is the only entry point.
- There is no legacy_init_fs_context() wrapper in `fs/fs_context.c`.
- `init_fs_context` must be non-NULL: `alloc_fs_context()` and
  `finish_clean_context()` call it unconditionally, and
  `register_filesystem()` does not test it.
- `struct super_operations` has no remount_fs member; `fc->ops->reconfigure()`
  is the only remount hook.
- `init_fs_context()` also runs for a remount: `alloc_fs_context()` calls it
  with `fc->purpose == FS_CONTEXT_FOR_RECONFIGURE` and `fc->root` already set.
- `reconfigure_super()`: is entered with `s_umount` held exclusive; each
  caller takes it first, for example `do_remount()` and
  `vfs_cmd_reconfigure()`.
- `reconfigure_super()` on a remount read-only with `s_pins` not empty: drops
  and retakes `s_umount` around `group_pin_kill()`, and returns 0 if `s_root`
  is then NULL.
- `vfs_get_super()`: static in `fs/super.c`; a filesystem calls
  `get_tree_nodev()`, `get_tree_single()`, `get_tree_keyed()`,
  `get_tree_bdev()`, `get_tree_bdev_flags()`, `get_tree_mtd()`
  (`drivers/mtd/mtdsuper.c`), or `sget_fc()` and `sget_dev()` directly.
- `alloc_super()`: static in `fs/super.c`; `sget_fc()` is its only caller.
- `set` callback of `sget_fc()`: when it returns 0 it must have set `s_dev`
  and registered it in the device table; callbacks outside `fs/super.c` do
  this through `set_anon_super()` or `set_anon_super_fc()`.
- `sget_fc()` warns with `VFS_WARN_ON_ONCE()` if `s_super_dev->sd_dev` is
  still zero after `set()` succeeds.
- `set` callback of `sget_fc()`: runs under `sb_lock`, so it must not sleep.
- There is no kill_litter_super() here; in-memory filesystems use
  `kill_anon_super()`, for example debugfs in `fs/debugfs/inode.c`.

**Write access and freezing**

- `mnt_want_write()` (`fs/namespace.c`): `sb_start_write()`, then
  `mnt_get_write_access()`; on failure it has already called `sb_end_write()`,
  so the caller calls `mnt_drop_write()` only after success.
- `guard(super_write)(sb)` and `scoped_guard(super_write, sb)`: an
  `sb_start_write()` and `sb_end_write()` pair, from `DEFINE_GUARD()` in
  `include/linux/fs/super.h`; `do_ftruncate()` in `fs/open.c` uses it.
- `mnt_want_write_file()`: skips the writer count only if the file has
  `FMODE_WRITER`, and then still fails with `-EROFS` if `__mnt_is_readonly()`.
- `FMODE_WRITER`: `do_dentry_open()` sets it for a file opened for write
  unless `special_file()` is true; a special file opened for write holds no
  mount write access.
- Freeze levels: `freeze_super()` blocks `SB_FREEZE_WRITE` first, then
  `SB_FREEZE_PAGEFAULT`, then `SB_FREEZE_FS`.
- A task inside `sb_start_pagefault()` or `sb_start_intwrite()` must not then
  call `sb_start_write()`; it would block on the first level while
  `freeze_super()` waits for it on a later one.
- There is no do_unlinkat() here; `filename_unlinkat()` in `fs/namei.c` shows
  `mnt_want_write()` taken before the directory lock.

## Permission and attributes

**Permission check chain**

- `devcgroup_inode_permission()`: runs after `do_inode_permission()` and before
  `security_inode_permission()`; returns 0 at once unless the inode is a block
  or char device with a non-zero `i_rdev`; a stub that returns 0 when neither
  `CONFIG_CGROUP_DEVICE` nor `CONFIG_CGROUP_BPF` is set.
- Mount read-only state: not tested anywhere in `inode_permission()`;
  `sb_permission()` looks only at `sb_rdonly()`, so the caller still needs
  `mnt_want_write()`, as `vfs_truncate()` does after its `inode_permission()`.
- New test in `sb_permission()` or `inode_permission()` that applies without
  `MAY_WRITE`: `lookup_inode_permission_may_exec()` bypasses it on its fast
  path and has to be changed too.
- `IOP_FASTPERM_MAY_EXEC`: set by a filesystem on directories that have a
  `->permission` method, to let path lookup skip that method; the method must
  then add nothing for `MAY_EXEC` on a directory. Set only in
  `fs/btrfs/inode.c`.
- **Potentially unsafe usage**: calling only `security_inode_permission()`.
  - Unsafe: when the mask can hold `MAY_WRITE`, the inode can be a device
    node, or the mode bits, ACL or `->permission` method could deny; the
    `-EROFS`, `-EPERM`, `-EACCES` and device cgroup results are never produced.
  - Safe: mask is `MAY_EXEC` with at most `MAY_NOT_BLOCK`, the inode is a
    directory with `IOP_FASTPERM` or `IOP_FASTPERM_MAY_EXEC`, all of mode
    `0111` is set and `no_acl_inode()` is true, as in
    `lookup_inode_permission_may_exec()`; `acl_permission_check()` returns 0
    for the same condition.
- **Potentially unsafe usage**: calling `generic_permission()` directly.
  - Unsafe: as the whole access decision; everything in `inode_permission()`
    outside `do_inode_permission()` is skipped, including the LSM hook.
  - Safe: inside a `->permission` method, which `do_inode_permission()` calls
    from within the chain, as `btrfs_permission()` does.

**Idmapped mounts**

- `struct mnt_idmap`: holds `uid_map`, `gid_map` and `count`, no user
  namespace pointer; `alloc_mnt_idmap()` in `fs/mnt_idmapping.c` copies the
  maps out of the namespace.
- `&invalid_mnt_idmap`: no mount carries it; only `fs/fuse/` passes it, for
  requests that have no idmap; `make_vfsuid()` returns `INVALID_VFSUID` and
  `from_vfsuid()` returns `INVALID_UID` for it.
- `&nop_mnt_idmap`: `make_vfsuid()` returns the kuid unchanged and never looks
  at `s_user_ns`, so the vfsuid is invalid only when `i_uid` is `INVALID_UID`.
- Mount idmap changes: `can_idmap_mount()` allows one only while the mount is
  in an anonymous mount namespace (`is_anon_ns()`); replacing or clearing an
  existing idmap needs `MOUNT_KATTR_IDMAP_REPLACE`, which only
  `open_tree_attr()` with `OPEN_TREE_CLONE` sets.
- `SB_I_NOIDMAP`: `can_idmap_mount()` returns `-EINVAL` for it even with
  `FS_ALLOW_IDMAP`; fuse sets it and clears it only for `FUSE_ALLOW_IDMAP`
  with `default_permissions`.
- nfsd and ecryptfs: pass `&nop_mnt_idmap` for the exported or lower object,
  and refuse an idmapped mount up front with `is_idmapped_mnt()` in
  `check_export()` and `ecryptfs_get_tree()`.
- overlayfs: passes the idmap of the layer's mount, for example
  `mnt_idmap(realpath.mnt)` in `ovl_permission()`.
- New inode owner: `inode_init_owner()` in `fs/inode.c`, built on
  `mapped_fsuid()` and `mapped_fsgid()`.
- What is refused when an id has no mapping, beyond `inode_permission()` and
  `notify_change()`:

| Where | Unmapped | Result |
|---|---|---|
| `may_create_dentry()`, `may_o_create()`, `vfs_tmpfile()` | caller's fsuid or fsgid | `-EOVERFLOW` |
| `may_delete_dentry()` | victim's owner | `-EOVERFLOW`, before `inode_permission()` on the directory |
| `may_linkat()` | source's owner | `-EOVERFLOW` |
| `vfs_link()` | source's owner | `-EPERM` |
| `may_write_xattr()` | inode's owner | `-EPERM` |
| `atime_needs_update()` | inode's owner | returns false, no error |

- `setattr_prepare()`: has no `-EOVERFLOW` test for an unmapped id;
  `-EOVERFLOW` for attribute changes comes from `notify_change()`.
- `chown_ok()` and `chgrp_ok()` with an invalid current owner: return true
  when the caller has `CAP_CHOWN` in `inode->i_sb->s_user_ns`, so an unmapped
  owner can be made valid.
- **Potentially unsafe usage**: comparing `inode->i_uid` or `inode->i_gid`
  with the caller's ids, or comparing or storing `ia_uid` or `ia_gid`, as raw
  kuid/kgid values.
  - Unsafe: in a filesystem with `FS_ALLOW_IDMAP`, or in code that can be
    reached with any mount's idmap; on an idmapped mount the wrong user
    matches, or an unmapped id is stored.
  - Safe: in a filesystem without `FS_ALLOW_IDMAP`, as `jfs_setattr()` does;
    `can_idmap_mount()` returns `-EINVAL` for it, so the idmap is always
    `&nop_mnt_idmap` and `ia_uid` equals `ia_vfsuid`.
  - Safe: through `i_uid_into_vfsuid()` with `vfsuid_eq_kuid()`, and
    `i_uid_update()` for the store, as `inode_owner_or_capable()` and
    `setattr_copy()` do.

**Attribute changes**

- should_remove_suid() does not exist here; callers compute the kill flags
  with `setattr_should_drop_suidgid()` (through `dentry_needs_remove_privs()`
  in `do_truncate()`) or `setattr_should_drop_sgid()` (in `chown_common()`).
- `notify_change()` and the kill flags: it does not call
  `setattr_should_drop_suidgid()`; it tests `S_ISUID` and `S_ISGID` in
  `inode->i_mode` and builds `ATTR_MODE` with `ia_mode` from them.
- `ATTR_MODE` together with `ATTR_KILL_SUID` or `ATTR_KILL_SGID`: `BUG()`.
- `ATTR_MODE` on a symlink: `-EOPNOTSUPP`, tested right after
  `may_setattr()`.
- `S_IALLUGO` masking: done by `chmod_common()` in `fs/open.c`;
  `notify_change()` passes `ia_mode` on as given.
- Time fields: `notify_change()` sets no `ATTR_*` time flag; it overwrites
  `ia_atime`, `ia_mtime` and `ia_ctime` with `current_time()`, except a field
  whose `ATTR_ATIME_SET`, `ATTR_MTIME_SET` or `ATTR_CTIME_SET` is set, which
  it passes through `timestamp_truncate()`.
- `ATTR_DELEG`: with it `notify_change()` skips `try_break_deleg()`; nfsd sets
  it for updates from a delegation holder.
- `may_setattr()`: its owner test is for `ATTR_TOUCH` only, with
  `inode_permission()` and `MAY_WRITE` as the fallback; the
  `inode_owner_or_capable()` test for explicit times is in
  `setattr_prepare()`.
- Unmapped-owner tests (`-EOVERFLOW`): run after the early `return 0` for an
  `ia_valid` holding only kill flags, and before `security_inode_setattr()`.
- Mount write access: `notify_change()` does not test it; `chmod_common()`
  takes `mnt_want_write()` itself, `chown_common()` relies on its caller, for
  example `do_fchownat()`.
- `delegated_inode`: a `struct delegated_inode *`, tested afterwards with
  `is_delegated()`; `NULL` is accepted, as `do_truncate()` passes, and then
  `-EWOULDBLOCK` comes back with nothing to wait on.
- Quota step in `->setattr`: `is_quota_modification()` gates
  `dquot_initialize()`; `dquot_transfer()` is gated by `i_uid_needs_update()`
  or `i_gid_needs_update()`; see `ext2_setattr()`.
- `setattr_copy()` on an `is_mgtime()` inode: ignores `ia_ctime` unless
  `ATTR_CTIME_SET`; with `ATTR_CTIME` it takes the ctime from
  `inode_set_ctime_current()`; see `setattr_copy_mgtime()` in `fs/attr.c`.

## Changing the VFS

**Changing a method or helper**

- Written request: only in the preamble of
  `Documentation/filesystems/locking.rst` and in the comment under
  `struct dentry_operations` in `include/linux/dcache.h`; the latter names
  both `locking.rst` and `vfs.rst`.
- `locking.rst` preamble: also asks the patch to convert the instances in the
  tree itself, to list dubious cases at the end of the file, and not to turn
  the file into a log.
- `Documentation/filesystems/porting.rst`: no text in the tree asks for an
  entry; it is a list with the newest entry last, entries separated by
  `---`.
- `porting.rst` tags: `**mandatory**`, `**recommended**` and
  `**informational**`, plus one entry tagged `**highly recommended**` and one
  tagged `**strongly recommended**`; `**informational**` is used for a
  change that needs no conversion, such as a lock that callers now hold.
- `locking.rst` and `vfs.rst`: each holds its own copy of the prototypes, so a
  prototype change edits both.
- Document copies are not all in step with the headers (for example
  `setlease` in `locking.rst` against `include/linux/fs.h`); check a patch
  against the header, not the document.
- `locking.rst` sections beyond the five method tables:
  `struct xattr_handler`, `struct file_system_type`,
  `struct file_lock_operations`, `struct lock_manager_operations`,
  `struct block_device_operations`, `struct dquot_operations`,
  `struct vm_operations_struct`.
- `Documentation/filesystems/api-summary.rst`: holds only `kernel-doc::`
  directives, so updating the kernel-doc comment in the source is enough.
- `Documentation/filesystems/mount_api.rst`: holds a copy of
  `struct fs_context_operations`.
- `Documentation/filesystems/mmap_prepare.rst`: covers the `mmap_prepare`
  hook.
- Path-creation helpers used outside `fs/`: `start_creating_path()` and
  `end_creating_path()`, for example in `net/unix/af_unix.c` and
  `drivers/base/devtmpfs.c`; `porting.rst` records the renames.
- drivers/misc/ibmasm is not in this tree.
- `fs/internal.h` helpers: have callers outside `fs/`; files under
  `io_uring/` and `block/bdev.c` include `../fs/internal.h`, search for that
  include. For example `filename_renameat2()` is called from
  `io_uring/fs.c`.
- Direct `f_op->` callers outside `fs/`: not found by a search for callers of
  the `vfs_` helpers; search for `f_op->` instead. For example
  `drivers/block/loop.c`, `drivers/block/zloop.c`,
  `drivers/target/target_core_file.c`, `io_uring/rw.c`, `ipc/shm.c`,
  `kernel/acct.c`, `drivers/gpu/drm/i915/gem/i915_gem_shmem.c`.
- Char-device multiplexers: call `f_op->open()` themselves after
  `replace_fops()`; search for `replace_fops(`. For example
  `drivers/char/misc.c`, `sound/core/sound.c`, `drivers/gpu/drm/drm_drv.c`.
- Rust: code that fills a `bindings::file_operations` with `extern "C"`
  functions, for example `rust/kernel/miscdevice.rs` and
  `rust/kernel/debugfs/file_ops.rs`; a changed method prototype has to be
  changed there too.
- `tools/testing/vma/include/dup.h`: holds its own copy of
  `struct file_operations` with `mmap` and `mmap_prepare`.
- Method tables implemented outside `fs/` in files that define no
  `struct file_system_type`: for example `block/fops.c`,
  `drivers/dax/device.c`, `drivers/video/fbdev/core/fb_defio.c`,
  `mm/swap_state.c`.
- To list implementers outside `fs/`: search for `struct inode_operations`,
  `struct super_operations`, `struct address_space_operations`,
  `struct dentry_operations` and `struct file_system_type` definitions with
  `fs/` excluded.

## Model gaps

### Other mistakes models make

- Models take `VFS_BUG_ON()`, `VFS_BUG_ON_INODE()` and `VFS_WARN_ON_ONCE()` to
  be checks that always run. Without `CONFIG_DEBUG_VFS` they compile to nothing
  (`include/linux/vfsdebug.h`), for example the occupied-slot check in
  `fd_install()`.
- Models take the syscall helpers that replaced do_unlinkat(), do_mkdirat()
  and do_renameat2() to consume the name. `filename_unlinkat()`,
  `filename_mkdirat()` and `filename_renameat2()` do not put the
  `struct filename`, the caller does (see the `CLASS(filename, ...)` users in
  `fs/namei.c`).
- Models take the delegated inode to be passed as a pointer to an inode pointer,
  and only to unlink, link and rename. It is `struct delegated_inode *`
  (`include/linux/filelock.h`), also taken by, for example, `vfs_create()`,
  `vfs_mkdir()`, `vfs_rmdir()` and `vfs_mknod()`, which call
  `try_break_deleg()` on the parent directory; `try_break_deleg()` takes a
  flags argument.
- Models take `->create` to take an excl flag. `->create` has four arguments.
  See `struct inode_operations` in `include/linux/fs.h`.
- Models take a NULL `->setlease` to mean the generic lease code is used.
  `kernel_setlease()` in `fs/locks.c` returns `-EINVAL` when the method is NULL.
- Models take `->update_time` and `->fileattr_set` at their older prototypes,
  and know only `->mmap`. `->update_time` takes `enum fs_update_time` and
  flags, `->fileattr_set` takes `struct file_kattr *`, and `->sync_lazytime`
  and `->mmap_prepare` exist; compare against `include/linux/fs.h`.
- Models take a filesystem to set sb->s_d_op directly and to call
  `d_set_d_op()`. The field is `__s_d_op`, set by `set_default_d_op()`;
  `d_set_d_op()` is static in `fs/dcache.c`.
- Models take `i_ino` and the inode-hash keys to be `unsigned long`. `i_ino` is
  `u64`, and `iget_locked()`, `ilookup()` and `iget5_locked()` take `u64`.
- Models write `f_path` freely. `f_path` is const and core code writes
  `__f_path`; `f_owner` is a pointer set up by `file_f_owner_allocate()`.
- Models take inode-state waiters to wait in wait_on_inode(). Waiters use
  `inode_bit_waitqueue()`, as `wait_on_new_inode()` does.
- Models miss that `setattr_prepare()` returns `-EPERM` for `ATTR_SIZE` on an
  `IS_VERITY()` inode.
