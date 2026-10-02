- `mutex`, `rwsem_read` and `rwsem_write` guards: defined with
  `DEFINE_LOCK_GUARD_1()` and no extra member, in `include/linux/mutex.h` and
  `include/linux/rwsem.h`; their expressions use `_T->lock`, and the class type
  is a struct, not the lock pointer.
- A guard that is to carry `DECLARE_LOCK_GUARD_1_ATTRS()`:
  `DEFINE_LOCK_GUARD_1()` even with no extra state.
  `DECLARE_LOCK_GUARD_1_ATTRS()` declares the constructor with a
  `lock_##_name##_t *` parameter, which conflicts with the by-value `_type _T`
  constructor of `DEFINE_GUARD()`.
- `DEFINE_GUARD()`: `_T` is the value passed to `guard()`, which may be an
  object that holds the lock; the `cooling_dev` guard in
  `include/linux/thermal.h` locks `&_T->lock`.
- `DEFINE_GUARD()`, `DEFINE_LOCK_GUARD_1()` and `DEFINE_LOCK_GUARD_0()`
  destructors: run `_unlock` unconditionally, with no NULL or error-pointer
  test.
- `__GUARD_IS_ERR()`: true for NULL and for error pointers; tested only in the
  destructor that `DEFINE_GUARD_COND()` and `DEFINE_LOCK_GUARD_1_COND()`
  generate, which returns before the base destructor.
- A lock pointer that may be NULL: neither `DEFINE_GUARD()` nor
  `DEFINE_LOCK_GUARD_1()`; both constructors are `__nonnull_args(1)`.
  `DEFINE_CLASS()` plus `DEFINE_CLASS_IS_GUARD()`, with the NULL test written
  into both expressions, does it; see `nvdimm_bus` in `drivers/nvdimm/nd.h`.
- `DEFINE_LOCK_GUARD_0()`: `_T->lock` is a `void *` set to `(void*)1`, not NULL,
  so `class_##_name##_lock_ptr` returns non-NULL.
- `DEFINE_LOCK_GUARD_0()`: has no conditional form; the macros that add a
  conditional variant to a guard are `DEFINE_GUARD_COND()` and
  `DEFINE_LOCK_GUARD_1_COND()` only.
- Several extra members: one macro argument with the members separated by `;`,
  not `,`; see the `task_rq_lock` guard in `kernel/sched/sched.h`.
