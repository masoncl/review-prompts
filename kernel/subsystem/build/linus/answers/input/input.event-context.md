- `dev->event_lock`: a `spinlock_t`, not a `raw_spinlock_t`; `input_event()`
  takes it with `guard(spinlock_irqsave)`.
- Lock scope: one `input_event()` call, not one frame; concurrent callers are
  safe, but their values interleave in `dev->vals`.
- `input_repeat_key()`: takes the lock for its key and sync together, so an
  autorepeat frame can land inside a driver's open frame.
- Callbacks that the core calls under `dev->event_lock`: `dev->event()`,
  handler `event()`, `events()` and `filter()`, `ff->playback()`,
  `ff->set_gain()`, `ff->set_autocenter()`, `dev->getkeycode()`,
  `dev->setkeycode()`, and `play_effect()` of `drivers/input/ff-memless.c`.
- **Potentially unsafe usage**: a callback from the list above takes a driver
  spinlock.
  - Unsafe: when the driver also holds that lock across `input_event()`;
    `input_event_dispose()` calls `dev->event()` with `dev->event_lock`
    held, so the two orders deadlock.
  - Safe: when the lock is never held across a report, as `usb_kbd_event()`
    does with `leds_lock`; `usb_kbd_irq()` reports without it.
  - Safe: when the callback only records the request and schedules work, as
    `atkbd_event()` does.
- **Potentially unsafe usage**: calling `input_event()` from a handler
  callback or from `dev->event()`.
  - Unsafe: on the same device; `dev->event_lock` is already held and
    `input_event()` takes it again.
  - Safe: on another device, as `mac_hid_emumouse_filter()` in
    `drivers/macintosh/mac_hid.c` does; `mac_hid_emumouse_connect()` refuses
    to bind to that device, and `mac_hid_create_emumouse()` gives its lock
    its own class with `lockdep_set_class()`.
