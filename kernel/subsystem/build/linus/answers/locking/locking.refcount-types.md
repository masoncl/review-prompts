- `rcuref_t`, get after the last put: fails only once the count is
  `RCUREF_DEAD`. The last put leaves `RCUREF_NOREF` and
  `rcuref_put_slowpath()` in `lib/rcuref.c` then tries to mark it dead; a
  `rcuref_get()` in that window succeeds, and the put returns false if the
  count is no longer `RCUREF_NOREF`.
- `rcuref_t`, overflow: `rcuref_get_slowpath()` sets `RCUREF_SATURATED`, warns
  once and returns true; the object is leaked.
- `rcuref_t`, memory: a failed `rcuref_get()` still writes the counter, so an
  object that a `rcuref_get()` can still reach has to be freed through RCU
  after `rcuref_put()` returns true.
- `rcuref_put()`: does `preempt_disable()` itself. `rcuref_put_rcusafe()`
  does not; under `CONFIG_PROVE_RCU` `__rcuref_put()` warns unless the caller
  is in `rcu_read_lock()` or not preemptible. `rcuref_get()` asserts nothing.
- `percpu_ref_tryget()`: fails only when the ref is in atomic mode and the
  count is zero. After `percpu_ref_kill()` it still succeeds while other
  references remain.
- `percpu_ref_tryget_live()`: certain to fail only after the callback given to
  `percpu_ref_kill_and_confirm()` has run; return of `percpu_ref_kill()` is
  not enough.
- `struct percpu_ref`, overflow: `atomic_long_t` plus `unsigned long` per-CPU
  counters, 32 bits wide on a 32-bit kernel; no get tests for overflow or
  saturates.
- `struct percpu_ref`, lookup: every get and put needs the ref to be between
  `percpu_ref_init()` and `percpu_ref_exit()`, and `percpu_ref_kill()` implies
  no grace period before the release callback. A lookup under RCU needs the
  containing object freed through RCU by its user, as `fs/aio.c` does.
- `struct lockref`: `lockref_get_not_zero()` fails at count `<= 0`;
  `lockref_get_not_dead()` fails only at count `< 0`, so it takes a
  reference on a live object whose count is 0.
