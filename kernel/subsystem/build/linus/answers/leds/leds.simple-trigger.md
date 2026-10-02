- Name: `led_trigger_register_simple()` stores the caller's pointer and does
  not copy the string; the string must outlive the trigger.
- Allocation: `kzalloc_obj()` of one `struct led_trigger`.
- `led_trigger_unregister_simple()`: frees only the structure, with `kfree()`,
  and never the name.
- Caller's pointer after `led_trigger_unregister_simple()`: not cleared, and
  it points at freed memory; the event-source rule under Trigger
  unregistration applies.
- Without `CONFIG_LEDS_TRIGGERS`: `led_trigger_unregister_simple()`,
  `led_trigger_blink()` and `led_trigger_blink_oneshot()` are empty inlines in
  `include/linux/leds.h` too, like `led_trigger_event()`.
- Caller that tests the pointer, as `ledtrig_panic_init()` does: with
  `CONFIG_LEDS_TRIGGERS` the pointer is always written, NULL on failure; code
  that also builds without it must start the storage as NULL, for example
  with `DEFINE_LED_TRIGGER()`.
