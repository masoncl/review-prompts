- `__scoped_guard()` loop condition:
  `__guard_ptr(_name)(&scope) || !__is_cond_ptr(_name)`; on failure the body
  is never entered.
- `scoped_cond_guard()` on an unconditional class: the only check is
  `BUILD_BUG_ON(!__is_cond_ptr(_name))`, which sits inside the failure branch
  of `__scoped_cond_guard()`, `if (!__guard_ptr(_name)(&scope))`, which is a
  call to `class_##_name##_lock_ptr()`; `__compiletime_assert()` in
  `include/linux/compiler_types.h` reports it through a call to an error
  function, so it fires only where the compiler keeps that branch.
  `class_##_name##_lock_ptr()` from `DEFINE_CLASS_IS_UNCONDITIONAL()` always
  returns `(void *)1`.
- `scoped_irqdesc_get_and_lock()` and `scoped_irqdesc_get_and_buslock()` in
  `kernel/irq/internals.h`: are `scoped_guard()` on the conditional class
  `irqdesc_lock`, so their body is skipped when the descriptor lookup fails.
- **Potentially unsafe usage**: code after `scoped_guard()` on a conditional
  class.
  - Unsafe: when it reads a result that only the body sets, or touches the
    protected data.
  - Safe: every path through the body returns and the statement after
    returns the error, as `min_show()` in
    `drivers/input/mouse/elan_i2c_core.c` does with `return -EINTR`.
  - Safe: the result is preset to the failure value before the statement, as
    `ret = -EINVAL` in `__irq_apply_affinity_hint()` in
    `kernel/irq/manage.c`.
  - Safe: skipping is the intended outcome and nothing after depends on the
    body, as in `tsc200x_esd_work()` in
    `drivers/input/touchscreen/tsc200x-core.c`, which only re-arms the work.
