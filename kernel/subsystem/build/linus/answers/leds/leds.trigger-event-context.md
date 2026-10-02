- Walk: `list_for_each_entry_rcu()` over `trig->led_cdevs` inside
  `rcu_read_lock()`; no lock is taken.
- `led_trigger_blink()`: calls `led_blink_set_nosleep()` for each LED, not
  `led_blink_set()`.
- Delays: `led_trigger_blink()` and `led_trigger_blink_oneshot()` take them by
  value.
- Driver `blink_set` without `brightness_set_blocking`: must not sleep,
  because it runs inline in the walk.
- `led_blink_set_oneshot()`: never calls the driver's `blink_set`; a oneshot
  blink always goes through `led_set_software_blink()`.
- `led_trigger_event()` and `led_trigger_blink_oneshot()`: reach no
  `timer_delete_sync()` in the core; `led_set_brightness()` defers stopping a
  software blink to the work item.
- **Potentially unsafe usage**: calling `led_trigger_blink()` from atomic
  context.
  - Unsafe: in hard interrupt context; `led_blink_set()` calls
    `timer_delete_sync()` on `blink_timer`, and `__timer_delete_sync()` in
    `kernel/time/timer.c` warns there, since the timer is not
    `TIMER_IRQSAFE`.
  - Safe: from a timer callback, as `tpt_trig_timer()` in
    `net/mac80211/led.c` does; `in_hardirq()` is false there, so the
    `WARN_ON()` in `__timer_delete_sync()` does not fire.
  - Safe: from process context, as `power_supply_update_status_leds()` does.
