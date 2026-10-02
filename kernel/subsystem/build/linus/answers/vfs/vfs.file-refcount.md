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
