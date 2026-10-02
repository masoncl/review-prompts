- Backward readers exist: `list_bidir_prev_rcu()` in
  `include/linux/rculist.h` names `prev` for `rcu_dereference()`, as
  `__ns_tree_adjoined_rcu()` in `kernel/nstree.c` uses it.
- A list read with `list_bidir_prev_rcu()`: every removal must be
  `list_bidir_del_rcu()`, which leaves both `next` and `prev`. `list_del_rcu()`
  on such a list hands the backward reader `LIST_POISON2`.
- `next` of a removed entry: safe to follow only for a reader that was inside
  its read-side section when the entry was removed. Nothing updates the removed
  entry's `next` again, so after a later grace period it can point at a freed
  successor.
- `list_for_each_entry_continue_rcu()` and `list_for_each_entry_from_rcu()`
  from an entry kept alive by a reference count: the entry must still be on
  the list when the read-side section begins.
- `hlist_unhashed()` after `hlist_del_init_rcu()`: a plain load, for callers
  that hold the update lock. Without the lock use `hlist_unhashed_lockless()`,
  which pairs with the `WRITE_ONCE()` of `pprev`.
- **Potentially unsafe usage**: adding the removed entry to a list again
  before a grace period.
  - Unsafe: when readers cannot tell that they changed list. The add overwrites
    `next`, a reader standing on the entry continues in the new list, and
    `list_for_each_entry_rcu()` never meets its own `head`.
  - Safe: when readers detect the move and retry. `mnt_change_mountpoint()` in
    `fs/namespace.c` calls `hlist_del_init_rcu()` and then, through
    `attach_mnt()`, `hlist_add_head_rcu()`; its callers hold
    `write_seqlock(&mount_lock)` through `lock_mount_hash()` or
    `guard(mount_writer)`. `lookup_mnt()` rechecks with `read_seqretry()` in
    `__legitimize_mnt()`.
