- Defined in this tree, each as `DEFINE_LOCK_GUARD_1()` with an empty unlock
  expression; search for `DEFINE_LOCK_GUARD_1\(\w+_init`. For example
  `mutex_init` in `include/linux/mutex.h` and `spinlock_init` in
  `include/linux/spinlock.h`.
- Names that do not match the init function: for example `rwsem_init` calls
  `init_rwsem()`. `local_trylock_init` is a separate class from
  `local_lock_init`.
- `guard(mutex_init)(&m)`: the constructor calls `mutex_init()` on the lock, so
  the guard replaces the init call rather than accompanying it.
- Plain `mutex_init()`: carries no context-analysis annotation. The documented
  alternatives to the guard are `context_unsafe()` and `__context_unsafe()`.
- `scoped_guard(spinlock_init, &lock) { }`: limits the region in which the
  analysis treats the lock as held to the block; see `drivers/scsi/hosts.c`.
- Lockdep key under `CONFIG_DEBUG_LOCK_ALLOC`: `mutex_init()` expands its
  `static struct lock_class_key __key` inside the guard constructor. Every
  mutex initialised with `guard(mutex_init)` in one translation unit therefore
  shares one key, and the lockdep name is `_T->lock`.
- A direct `mutex_init()` call: gets one key per call site and the caller's
  expression as the name.
