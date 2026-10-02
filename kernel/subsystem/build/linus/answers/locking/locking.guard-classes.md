- Naming: no rule is enforced; the class name is the first argument of the
  defining macro. Many classes keep `_lock` in the name, for example
  `read_lock`, `write_lock`, `local_lock`, `task_lock`, `mmap_read_lock`,
  `cpus_read_lock`, `console_lock`.
- `mutex`: defined with `DEFINE_LOCK_GUARD_1()` in `include/linux/mutex.h`,
  not with `DEFINE_GUARD()`; its class type is a struct with a `lock` member.
- Generated typedefs: `class_##_name##_t` and `lock_##_name##_t` (the lock
  type); there is no lock_guard_ struct.
- Killable suffix: `_kill`, defined for `mutex_kill` and `rwsem_write_kill`
  only.
- rwsem conditional classes: read has `_try` and `_intr`; write has `_try`
  and `_kill`.
- rwlock classes (`read_lock`, `write_lock` and their irq forms): no
  conditional forms.
- Suffix is free-form: for example `_try_enabled` in
  `include/linux/pm_runtime.h`, `_try_direct` in `include/linux/iio/iio.h`.
- `DEFINE_GUARD_COND()` and `DEFINE_LOCK_GUARD_1_COND()`: optional fourth
  argument is the success test on `_RET`; with three arguments success is
  `_RET` non-zero (trylock style); errno-style lock functions pass
  `_RET == 0`.
- `_init` classes (`mutex_init`, `spinlock_init`, `raw_spinlock_init`,
  `rwlock_init`, `rwsem_init`, `seqlock_init`, `local_lock_init`,
  `local_trylock_init`): the constructor initialises the lock, the destructor
  is empty; they take no lock and exist so context analysis treats guarded
  members as accessible during initialisation.
- Context analysis companion: a `DEFINE_LOCK_GUARD_1()` class is visible to
  the analysis only if it also has `DECLARE_LOCK_GUARD_1_ATTRS()` and a
  `#define` of its constructor to `WITH_LOCK_GUARD_1_ATTRS()`; a
  `DEFINE_LOCK_GUARD_0()` class needs only `DECLARE_LOCK_GUARD_0_ATTRS()`, as
  `rcu` has; each conditional class needs its own pair under its full name,
  as for `mutex_try` in `include/linux/mutex.h`.
- `cpus_read_lock`: defined in `include/linux/cpuhplock.h`.
- `migrate`: defined in `include/linux/sched.h`.
- Definition sites outside `include/linux/`: `.c` files and private headers
  define classes too, for example `core_lock` in `kernel/sched/core.c`;
  search for the `DEFINE_` macro names.
- `DEFINE_LOCK_GUARD_2()`: exists only in `kernel/sched/sched.h`.
