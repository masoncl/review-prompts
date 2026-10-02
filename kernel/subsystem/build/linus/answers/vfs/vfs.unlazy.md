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
