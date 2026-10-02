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
