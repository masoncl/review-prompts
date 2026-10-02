- Kinds: three, in `enum pattern_type`, chosen by the sysfs file written.

| `data->type` | File | Driven by |
|---|---|---|
| `PATTERN_TYPE_SW` | `pattern` | `struct timer_list timer` |
| `PATTERN_TYPE_HR` | `hr_pattern` | `struct hrtimer hrtimer` |
| `PATTERN_TYPE_HW` | `hw_pattern` | no timer; the driver's `pattern_set` |

- No fallback between kinds: `pattern_trig_store_patterns()` takes the type
  from the file written and never tries another one.
- `hw_pattern` without `pattern_set`: the file does not exist
  (`pattern_trig_attrs_mode()`); it does not return an error.
- Firmware `led-pattern` default: `pattern_init()` stores it as
  `PATTERN_TYPE_SW`; `pattern_trig_activate()` never calls `pattern_set`.
- Minimum for `PATTERN_TYPE_SW` and `PATTERN_TYPE_HR`: 2 tuples, which is
  4 numbers; `npatterns` counts tuples.
- Exactly 1 tuple in `pattern` or `hr_pattern`:
  `pattern_trig_start_pattern()` returns `-EINVAL`.
- 0 tuples (a write of only a newline): `pattern_trig_start_pattern()`
  returns 0 before the minimum test; the write succeeds and the running
  pattern stays stopped.
- More than `MAX_PATTERNS` tuples: `pattern_trig_store_patterns_string()`
  stops parsing and returns 0; the first `MAX_PATTERNS` tuples run, with no
  error.
- Timer handlers: `pattern_trig_timer_common_function()` does not take
  `data->lock`.
- `data->lock`: held only by the show and store functions, and by
  `pattern_init()` through `pattern_trig_store_patterns()`; a store cancels
  the timer synchronously before it changes `patterns`, `curr`, `next` or
  `repeat`.
- `pattern_trig_timer_cancel()`: stops one timer, selected by `data->type`;
  it is correct only because the store assigns the new `data->type` after
  the cancel.
- `pattern_trig_deactivate()`: the one place that stops both timers.
- Handler context for `PATTERN_TYPE_HR`: the hrtimer is set up with
  `HRTIMER_MODE_REL`, without `HRTIMER_MODE_SOFT`; the handler writes the LED
  only through `led_set_brightness()`.
- `led_set_brightness()` from the handlers: calls `brightness_set` directly,
  through `led_set_brightness_nopm()`, if the driver has one, and otherwise
  queues `set_brightness_work`.
