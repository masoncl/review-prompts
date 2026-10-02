- `guard()`: is `CLASS(_name, __UNIQUE_ID(guard))` and nothing else; it has no
  `BUILD_BUG_ON()` and does not read `__is_cond_ptr()`, so `guard(mutex_try)`
  compiles.
- `BUILD_BUG_ON()` on `__is_cond_ptr()`: only in `__scoped_cond_guard()`, and
  it tests for the opposite case, an unconditional class.
- Header text in `include/linux/cleanup.h`: `guard()` is "not recommended for
  conditional locks"; it names `ACQUIRE()` with `ACQUIRE_ERR()` as the form
  for conditional locks and states no prohibition.
- Context analysis annotation: `DECLARE_LOCK_GUARD_1_ATTRS()` gives the
  constructors of `mutex_try`, `mutex_intr`, `mutex_kill` and
  `spinlock_try` the same unconditional `__acquires(_T)` as the base class,
  not `__cond_acquires()`.
- In-tree use: no `guard()` on a `_try`, `_intr` or `_kill` class exists in
  this tree to cite as correct.
