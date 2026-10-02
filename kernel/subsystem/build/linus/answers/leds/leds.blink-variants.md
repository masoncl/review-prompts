- `led_blink_set_nosleep()`: takes the delays by value; `led_blink_set()` and
  `led_blink_set_oneshot()` take pointers.
- `led_blink_set_nosleep()` defers to `set_brightness_work` only when the
  driver sets both `blink_set` and `brightness_set_blocking`.
- `led_blink_set_nosleep()` in every other case: calls `led_blink_set()` in
  the caller's context, and with it `timer_delete_sync()` and the driver's
  `blink_set` if there is one.
- Hard IRQ context: `led_blink_set()` and the direct path of
  `led_blink_set_nosleep()` trip the `WARN_ON(in_hardirq() ...)` in
  `__timer_delete_sync()` in `kernel/time/timer.c`; `led_init_core()` sets up
  `blink_timer` without `TIMER_IRQSAFE`.
- `CONFIG_PREEMPT_RT`: the same `__timer_delete_sync()` calls
  `lockdep_assert_preemption_enabled()`, which tests only with
  `CONFIG_PROVE_LOCKING`.
- `led_blink_set_oneshot()`: 500/500 is substituted only when both delays are
  zero, in `led_blink_setup()`, the same as for the other two.
- A single zero delay on the software path, one-shot included: no blink
  starts; `led_set_software_blink()` sets the LED off (`delay_on` zero) or to
  `blink_brightness` (`delay_off` zero) and arms no timer.
