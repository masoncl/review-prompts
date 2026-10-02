- Walk: `led_trigger_unregister()` walks `leds_list` under `leds_list_lock`
  and compares `led_cdev->trigger`; it does not walk `trig->led_cdevs`.
- Context: process context only; it takes rwsems, and `led_trigger_set()`
  calls `synchronize_rcu()`.
- `synchronize_rcu()`: only inside `led_trigger_set()`, once per detached
  LED; with no LED attached, `led_trigger_unregister()` does not wait for RCU
  readers.
- Repeat call: returns at once through `list_empty_careful()`;
  `heartbeat_reboot_notifier()` followed by `heartbeat_trig_exit()` relies on
  it.
- `trigger_data`: per LED and owned by the trigger's `deactivate`; the core
  sets it to NULL after `deactivate` returns, and the caller of
  `led_trigger_unregister()` has none to free.
- After return: `trig->led_cdevs` is an empty list, so `led_trigger_event()`
  on a trigger that is still allocated reaches no LED.
- **Unsafe usage**: `led_trigger_unregister()` on a zeroed trigger that was
  never registered, or whose `led_trigger_register()` returned `-EEXIST`;
  `next_trig` is not an empty list, so `list_del_init()` runs on NULL links.
  - Safe: unregister only what registered, as `ieee80211_led_exit()` does by
    testing the `name` that `ieee80211_led_init()` clears on failure.
  - Safe: `devm_led_trigger_register()`, which adds its release action only
    on success.
  - Safe: `led_trigger_unregister_simple()` on NULL.
- **Potentially unsafe usage**: an event source that can still call
  `led_trigger_event()` when `led_trigger_unregister()` returns.
  - Unsafe: when the trigger is then freed; the event functions dereference
    `trig`, and `led_trigger_unregister()` does not stop the source.
  - Safe: when the trigger stays allocated until the source is stopped, as in
    `rfkill_global_led_trigger_unregister()`, which calls
    `cancel_work_sync()` after unregistering its static triggers.
