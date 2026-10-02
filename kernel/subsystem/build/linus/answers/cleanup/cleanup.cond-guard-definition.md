- `DEFINE_GUARD_COND_4()` and `DEFINE_LOCK_GUARD_1_COND_4()`: built on
  `EXTEND_CLASS_COND()`, not directly on `EXTEND_CLASS()`.
- Conditional class destructor: its own function,
  `class_##_name##ext##_destructor`; it returns when `__GUARD_IS_ERR()` is
  true and otherwise calls the base destructor.
- Conditional constructor: does not call the base constructor; it builds the
  instance and evaluates `_lock` into `int _RET` itself.
- Failure value: `ERR_PTR(_RET)`; NULL only when `_RET` is 0, as for a failed
  trylock.
- `_cond`: a separate fourth macro argument over `_RET`; `_lock` is the bare
  call and does not assign `_RET`.
- Conditional class made without these macros: gets no `__GUARD_IS_ERR()`
  test; the pointer is tested in the unlock expression of `irqdesc_lock` in
  `kernel/irq/internals.h`, and in `unlock_timer()`, which the unlock
  expression of `lock_timer` in `kernel/time/posix-timers.c` calls.
- **Unsafe usage**: a 4-argument definition whose `_cond` can be false while
  `_RET` is positive.
  - Unsafe: `ERR_PTR()` of a positive value fails `__GUARD_IS_ERR()`, so the
    instance counts as held and the destructor unlocks.
  - Safe: `_RET` on failure is 0 or a negative errno, as in
    `pm_runtime_active_try`, where `pm_runtime_get_active()` turns every
    non-negative result of `__pm_runtime_resume()` into 0.
