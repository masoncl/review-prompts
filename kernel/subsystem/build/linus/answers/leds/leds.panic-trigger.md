- Takeover and lighting are separate steps: `led_trigger_panic_notifier()`
  relinks LEDs and zeroes their blink delays; nothing changes brightness until
  `led_panic_blink()` runs through `panic_blink`.
- `led_trigger_set_panic()`: does not call `led_trigger_set()`, `activate` or
  `deactivate`, and does not search `trigger_list`; it uses the file-static
  `trigger`.
- `led_trigger_set_panic()` list handling: plain `list_del()` and
  `list_add_tail()` on `trig_list`, without `leddev_list_lock`.
- `vpanic()` in `kernel/panic.c` holds the body; `panic()` is a wrapper.
- Notifier chain in `vpanic()`: runs after `panic_other_cpus_shutdown()`, with
  local interrupts disabled.
- `panic_blink` in `vpanic()`: called from the reboot countdown loop with
  local interrupts disabled (only when `panic_timeout` is positive), and from
  the final loop after `local_irq_enable()`.
- `brightness_set` of a panic indicator therefore has to work with local
  interrupts disabled and without scheduling.
- `panic-indicator`: the LED core does not parse it; each driver sets
  `LED_PANIC_INDICATOR` itself. Search for the flag to list them.
- No code rejects `LED_PANIC_INDICATOR` on an LED that lacks `brightness_set`;
  the only test of the flag is in `led_trigger_panic_notifier()`.
- `brightness_set_blocking` on its own: `led_set_brightness_nopm()` never
  calls it directly, it only queues `set_brightness_work`; making the blocking
  callback atomic-safe does not help.
