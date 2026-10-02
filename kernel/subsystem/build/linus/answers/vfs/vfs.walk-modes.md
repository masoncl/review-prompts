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
