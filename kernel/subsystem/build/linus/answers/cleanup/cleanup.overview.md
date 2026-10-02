- `__free()` and classes: two separate mechanisms on top of `__cleanup()`.
  `DEFINE_FREE()` generates only `__free_##_name()`; it does not use
  `DEFINE_CLASS()` and creates no type, constructor or destructor.
- A class is a naming convention: `CLASS()` pastes `class_##_name##_t`,
  `class_##_name##_constructor` and `class_##_name##_destructor`, whoever
  defined them.
- `DEFINE_GUARD()`: the only guard definer that calls `DEFINE_CLASS()`.
  `DEFINE_LOCK_GUARD_0()` and `DEFINE_LOCK_GUARD_1()` generate the same
  names: type and destructor through `__DEFINE_UNLOCK_GUARD()`, constructor
  through `__DEFINE_LOCK_GUARD_0()` or `__DEFINE_LOCK_GUARD_1()`.
- There is no DEFINE_LOCK_GUARD_N here. `DEFINE_LOCK_GUARD_2()` exists, but
  only in `kernel/sched/sched.h`.
- Conditional guard instance from `DEFINE_GUARD_COND()` or
  `DEFINE_LOCK_GUARD_1_COND()`: has the base class's type and no extra
  "acquired" field. Failure is stored in the lock pointer as `ERR_PTR(_RET)`:
  NULL for a failed trylock, an error pointer for the forms that return an
  errno.
- `ACQUIRE()`: exactly `CLASS()`, so a named instance.
- Macros that add `class_##_name##_lock_ptr()` and
  `class_##_name##_is_conditional` to an existing class:

  | Macro | Use when |
  |---|---|
  | `DEFINE_CLASS_IS_GUARD()` | instance is a pointer, class is not conditional |
  | `DEFINE_CLASS_IS_COND_GUARD()` | instance is a pointer, NULL or error pointer means not acquired; for example `lock_timer` in `kernel/time/posix-timers.c` |
  | `DEFINE_CLASS_IS_UNCONDITIONAL()` | instance is not a lock pointer; for example `sched_change` in `kernel/sched/sched.h` |

- Context-analysis alias: for lock classes that follow
  `DECLARE_LOCK_GUARD_1_ATTRS()` with a `#define` of the constructor name to
  `WITH_LOCK_GUARD_1_ATTRS()`, for example
  `#define class_mutex_constructor(_T) WITH_LOCK_GUARD_1_ATTRS(mutex, _T)` in
  `include/linux/mutex.h`, the constructor is a macro.
  - One `guard()`, `CLASS()` or `scoped_guard()` then declares two
    `__cleanup()` variables: the instance, and a pointer alias whose cleanup
    `__class_##_name##_cleanup_ctx()` has an empty body.
- `scoped_seqlock_read()` in `include/linux/seqlock.h`: not a class; it puts
  `__cleanup()` directly on a `struct ss_tmp`. Its `for` loop is a retry
  loop, so the body can run a second time, unlike `scoped_guard()`.
- There is no `DEFINE_FREE()` and no class named fdput; `fdput()` is the
  destructor expression of the classes `fd` and `fd_raw` in
  `include/linux/file.h`.
