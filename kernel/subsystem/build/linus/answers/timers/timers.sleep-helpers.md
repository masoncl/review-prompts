- `Documentation/timers/delay_sleep_functions.rst`: gives no "10 us – 20 ms"
  or "20 ms and up" ranges. Its order for non-atomic code is `fsleep()` when
  unsure, `msleep()` and its variants whenever possible, `usleep_range()` and
  its variants only when `msleep()` accuracy is not sufficient, `udelay()` and
  its variants for very short delays.
- `schedule_timeout()`: not mentioned in the rst; its rules are in the
  kerneldoc in `kernel/time/sleep_timeout.c`.
- `fsleep()` middle branch: `usleep_range(usecs, usecs + (usecs >> 2))`, taken
  for `10 < usecs < USLEEP_RANGE_UPPER_BOUND`.
- `USLEEP_RANGE_UPPER_BOUND` in `include/linux/delay.h`: 4 ticks in
  microseconds, so it depends on `HZ`: 4000 at `HZ=1000`, 16000 at `HZ=250`,
  40000 at `HZ=100`. `fsleep(20000)` is `msleep(20)` at `HZ=1000` and
  `usleep_range(20000, 25000)` at `HZ=100`.
- `fsleep()` on the `msleep()` branch: the request is rounded up to a whole
  millisecond, then to a whole jiffy by `msecs_to_jiffies()`, and at wheel
  level 0 the wheel adds up to one jiffy. Just above the bound the total can
  exceed 25%; for example `fsleep(4001)` at `HZ=1000` can take up to 6 ms.
- `msleep()`: passes `msecs_to_jiffies(msecs)` to
  `schedule_timeout_uninterruptible()` with no extra jiffy. Its timer still
  cannot fire early, because `calc_index()` in `kernel/time/timer.c` rounds
  every timer up to the next bucket of its wheel level.
- `msleep()` and `schedule_timeout()` lateness: up to one jiffy while the
  timeout is below `LVL_START(1)` (63 jiffies, wheel level 0). Above that it is
  up to one granule of the level, `LVL_GRAN()`, which the rst and the
  `msleep()` kerneldoc give as 12.5%.
- `usleep_range()`: `min` is the hrtimer's soft expiry and `max` its hard
  expiry; in high-resolution mode the clock event is programmed for the hard
  expiry. The task then wakes before `max` only when another hrtimer interrupt
  runs in the window, and interrupt and scheduling latency come on top of
  `max`.
- `schedule_timeout()` in `TASK_UNINTERRUPTIBLE`: any `wake_up_process()` on
  the task ends it early and it returns the jiffies left.
  `schedule_timeout_uninterruptible()` alone is therefore not a guaranteed
  minimum delay; `msleep()` and `usleep_range_state()` repeat their timeout
  call until it returns 0.
- `schedule_timeout()` with a timeout of `WHEEL_TIMEOUT_CUTOFF` jiffies or
  more: `calc_wheel_index()` expires the timer at `WHEEL_TIMEOUT_MAX` (about
  12 days at `HZ=1000`), so the call returns early with a non-zero remainder.
- `udelay()`: the generic definition in `include/asm-generic/delay.h` does not
  cap a non-constant argument; a constant argument of `DELAY_CONST_MAX`
  (20000) or more fails to link through `__bad_udelay()`.
- `MAX_UDELAY_MS` in `include/linux/delay.h`: decides whether the `mdelay()`
  defined there, with a constant argument, is one `udelay()` call or a loop of
  `udelay(1000)`.
