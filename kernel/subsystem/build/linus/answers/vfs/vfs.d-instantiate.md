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
