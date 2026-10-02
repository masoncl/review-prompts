- `return` expression at function level: evaluated before the unlock, so
  `return p->field;` reads under the lock; `snd_seq_timer_get_cur_tick()` in
  `sound/core/seq/seq_timer.c` relies on this.
- `guard()` under a `case` label: in-tree code braces the case body
  (`case X: {` then `guard()`), as `iio_dummy_read_raw()` in
  `drivers/iio/dummy/iio_simple_dummy.c` does; the lock is then held to the
  closing brace of that case.
- Conditional class under `guard()`: the variable is named by
  `__UNIQUE_ID(guard)`, so `ACQUIRE_ERR()` cannot test it, and the rest of the
  scope runs whether or not the lock was taken.
- Conditional class, form to use: `ACQUIRE()` followed by `ACQUIRE_ERR()`, or
  `scoped_cond_guard()`.
