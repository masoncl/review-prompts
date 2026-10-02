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
