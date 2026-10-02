- `struct lease`: shared and reference counted (`refcount`, `lease_get()`,
  `lease_put()` in `fs/smb/server/oplock.c`); `lease_put()` does `kfree()` at
  the last reference.
- `smb_grant_oplock()`: allocates a lease with `alloc_lease()`, then, when
  `same_client_has_lease()` returns an opinfo, puts the new lease and takes a
  reference on that opinfo's `o_lease` instead.
- An open keeps the lease from `alloc_lease()` when `same_client_has_lease()`
  finds no match, and also when the open jumps to `set_lev` before
  `same_client_has_lease()` runs, for example the first oplock on the inode
  or a stat open.
- Lease references: one per opinfo, dropped in `__free_opinfo()`; one for the
  table, taken in `lease_add_table()` and dropped in `lease_del_table()`.
- There is no copy_lease(); `lease->state` is the shared state, and
  `lease_update_oplock_levels()` writes the mapped level into every opinfo on
  `lease->open_list`.
- `lb->lease_list`: links `struct lease` through `lease->l_entry`, not opinfos.
- `lease->open_list`: links the opinfos through `opinfo->lease_entry`, under
  the spinlock `lease->lock`.
- `lease_list_lock`: an rwlock; it protects `lease_table_list`, each
  `lb->lease_list` and `lease->l_lb`.
- Writers of `lb->lease_list`: `add_lease_global_list()`, `lease_del_open()`
  and `destroy_lease_table()`, each under `write_lock(&lease_list_lock)`.
- Readers of `lb->lease_list`: `find_same_lease_key()` and
  `lookup_lease_in_table()` use plain `list_for_each_entry()` under
  `read_lock(&lease_list_lock)`; neither takes `rcu_read_lock()` or `lb_lock`.
- `lb->lb_lock`: taken only inside `lease_add_table()` and
  `lease_del_table()`, nested in the write lock.
- `struct lease_table`: holds a counted `conn`, the connection of the open that
  created the table; `free_lease_table()` puts it.
- `add_lease_global_list()`: receives a table preallocated by
  `alloc_lease_table()` and frees it when the client already has one, so
  nothing after `opinfo_add()` can fail.
- `destroy_lease_table()`: calls `lease_del_table()` on every lease of each
  matching table, which sets `l_lb` to NULL and drops the table's reference;
  opinfos stay on `lease->open_list`.
- There is no lb_add(), lease_add_list() or lease_del_list() in this tree.
