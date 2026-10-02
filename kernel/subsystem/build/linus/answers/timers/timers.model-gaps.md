- Models take hrtimers to be queued on `struct timerqueue_head` through
  `struct timerqueue_node`. `timerqueue_add()` and `timerqueue_getnext()` take
  those types; the hrtimer queue is `struct timerqueue_linked_head` and is
  walked with `timerqueue_linked_first()` and `timerqueue_linked_next()`.
- Models take the two on-stack release functions to share one word order. They
  do not: `timer_destroy_on_stack()` in `include/linux/timer.h` is for
  `struct timer_list`, and `destroy_hrtimer_on_stack()` in
  `include/linux/hrtimer.h` is for `struct hrtimer`.
- Models take the timekeeper to be updated in place. Writers change
  `tk_core.shadow_timekeeper` under `tk_core.lock`, and
  `timekeeping_update_from_shadow()` copies it over `tk_core.timekeeper` inside
  the `tk_core.seq` write section. Exception: `tk_update_leap_state_all()`
  writes `next_leap_ktime` into both copies without the full copy.
- Models leave the auxiliary clocks out of the `ktime_get` family. When
  `ktime_get_aux()` or `ktime_get_aux_ts64()` returns `false`, no time was
  stored through the pointer.
- Models write `clock_was_set()` with no argument. It takes a mask of clock
  bases, `CLOCK_SET_WALL` or `CLOCK_SET_BOOT` from
  `kernel/time/tick-internal.h`, and sends an IPI only to CPUs for which
  `update_needs_ipi()` returns true, unless the cpumask allocation fails.
