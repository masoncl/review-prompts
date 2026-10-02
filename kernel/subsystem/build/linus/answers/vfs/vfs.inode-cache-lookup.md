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
