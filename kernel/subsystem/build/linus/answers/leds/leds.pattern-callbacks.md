- One-callback check: made only by `pattern_trig_activate()`; the NULLs it
  writes stay in `struct led_classdev` after the trigger is deactivated.
- `led_cdev->pattern_clear()` in `pattern_trig_store_patterns()` and
  `repeat_store()`: called with no NULL test; this relies on the activate
  check and on `hw_pattern` being hidden without `pattern_set`.
- Call sites and conditions:

| Callback | Called from | Condition |
|---|---|---|
| `pattern_set` | `pattern_trig_start_pattern()` | `data->type` is `PATTERN_TYPE_HW` and `npatterns != 0` |
| `pattern_clear` | `pattern_trig_store_patterns()` | the type before this write was `PATTERN_TYPE_HW` |
| `pattern_clear` | `repeat_store()` | `data->type` is `PATTERN_TYPE_HW` |
| `pattern_clear` | `pattern_trig_deactivate()` | pointer is non-NULL, whatever the type |

- `pattern_set` is reached from a `hw_pattern` write, and from a `repeat`
  write while the type is `PATTERN_TYPE_HW`; never from `pattern`,
  `hr_pattern` or activate.
- `data->type` after a failed `hw_pattern` write: stays `PATTERN_TYPE_HW`
  with `npatterns` 0, so the next store calls `pattern_clear` although
  `pattern_set` never succeeded.
- Context: sysfs store calls run under the mutex `data->lock` and may sleep;
  the `pattern_trig_deactivate()` call runs without `data->lock`, and before
  the software timers are stopped.
- `pattern_clear` return value: ignored at all three call sites.
- `repeat` argument: `data->repeat`, not `data->last_repeat`.
- `data->repeat` before any `repeat` write: 0, because
  `pattern_trig_activate()` sets only `last_repeat` to -1 and
  `is_indefinite`; the `repeat` file reads -1 while `pattern_set` gets 0.
- `data->repeat` after a finite software pattern:
  `pattern_trig_update_patterns()` has decremented it, and a later
  `hw_pattern` write passes what is left.
- `pattern_set` that returns `-EINVAL` for `repeat == 0`: every
  `hw_pattern` write fails until `repeat` has been written.
- Tuple meaning in software patterns: brightness goes linearly from this
  tuple's `brightness` to the next tuple's `brightness` over this tuple's
  `delta_t`; the last tuple ramps to the first
  (`pattern_trig_compute_brightness()`); a `delta_t` below
  `UPDATE_INTERVAL` gives no ramp.
- Values the trigger guarantees to `pattern_set`: `len` from 1 to
  `MAX_PATTERNS`, `brightness` from 0 to `max_brightness`; `delta_t` is any
  `u32`, 0 included; the 2-tuple minimum is not applied.
- `pattern` array: writable; `hw_pattern` reads back `data->patterns`, so a
  driver may store the values it programmed, as `sc27xx_led_pattern_set()`
  does with the rounded `delta_t`.
- **Unsafe usage**: a `pattern_clear` that needs a hardware pattern to be
  running.
  - Safe: reset the hardware unconditionally, as
    `sc27xx_led_pattern_clear()` does; `pattern_trig_deactivate()` calls it
    for software patterns too.
  - Safe: free only what was allocated, as `lpg_pattern_clear()` does;
    `lpg_lut_free()` returns early when both indexes are 0.
- **Unsafe usage**: a `pattern_set` that keeps the `pattern` pointer after
  it returns.
  - Safe: program the hardware before returning, as
    `sc27xx_led_pattern_set()` does; the array is `patterns` inside
    `struct pattern_trig_data`, rewritten by `pattern_trig_store_patterns()`
    and freed by `pattern_trig_deactivate()`.
  - Safe: copy into the driver's own allocation, as `lpg_pattern_set()`
    does.
- **Potentially unsafe usage**: `pattern_set` reading `pattern[i]` with no
  test of `len`.
  - Unsafe: for `i >= 1`; with a shorter `len` the entry holds zeros or a
    tuple from an earlier write, because a store resets `npatterns` and not
    the array.
  - Safe: `pattern[0]` alone, as `ncp5623_pattern_set()` reads;
    `pattern_trig_start_pattern()` returns before the callback when
    `npatterns` is 0.
  - Safe: after a test of `len`, as `cht_wc_leds_pattern_set()` does with
    `len != 2`.
