- Models have the three setup functions and the absence of the hrtimer_init
  names right; see `include/linux/hrtimer.h`.
- `__hrtimer_setup()` and `__hrtimer_setup_sleeper()`: `static` in
  `kernel/time/hrtimer.c`; code outside that file cannot call them.
- Sleeper not on the stack: no setup function exists;
  `hrtimer_setup_sleeper_on_stack()` is the only sleeper setup.
- NULL callback at setup: `WARN_ON_ONCE()` and `hrtimer_dummy_timeout()` is
  installed; it is a static inline in `include/linux/hrtimer.h` and may be
  passed deliberately as a placeholder.
