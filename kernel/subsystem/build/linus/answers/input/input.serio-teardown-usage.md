- `serio_pause_rx()`: `spin_lock_irq()`, not irqsave;
  `serio_continue_rx()` enables interrupts unconditionally, so the pair is
  for callers with interrupts on.
- **Potentially unsafe usage**: `input_unregister_device()` before
  `serio_close()`.
  - Unsafe: unmanaged device, `interrupt()` reports unconditionally and the
    driver holds no extra reference; a byte arriving before `serio_close()`
    reaches `input_event()` on a freed device.
  - Safe: a flag cleared under `serio_pause_rx()` first, tested before any
    `input_event()`, as `atkbd_disable()` and `atkbd_receive_byte()` do for
    `atkbd_disconnect()`.
  - Safe: `input_get_device()` before unregistering and `input_put_device()`
    after `serio_close()`, as `elo_disconnect()` in
    `drivers/input/touchscreen/elo.c` does.
  - Safe: `serio_close()` first, as `nkbd_disconnect()` does.
- **Potentially unsafe usage**: cancelling work that `event()` queues before
  `input_unregister_device()`.
  - Unsafe: when an LED is on; unregistration calls `event()` and the work is
    queued again, then runs after `kfree()`.
  - Safe: `cancel_delayed_work_sync()` after unregistering and before
    `serio_close()`, as `atkbd_disconnect()` does; `atkbd_event_work()` only
    reschedules itself while `enabled` is clear.
- `atkbd_disconnect()` unregisters before `serio_close()`; it is not an
  example of close-first. `psmouse_disconnect()` is.
