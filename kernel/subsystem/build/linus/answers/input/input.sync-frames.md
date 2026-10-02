- Driver that never syncs: `input_event_dispose()` appends `input_value_sync`
  and then calls `input_pass_values()`, so handlers do get a sync at the cut.
- Flush threshold: `dev->num_vals >= dev->max_vals - 2`, tested after each
  queued value; there is no INPUT_MAX_VALS in this tree.
- `dev->max_vals`: 10 from `input_allocate_device()`;
  `input_device_tune_vals()` raises it, never lowers it, and runs only from
  `input_register_device()`.
- `input_set_events_per_packet()` after registration: does not resize
  `dev->vals`.
- Synthetic sync: value 1; `input_sync()` sends value 0.
- `input_value_sync`: used only for the overflow flush; other core syncs pass
  a literal 1, for example `input_repeat_key()`.
- Value 1 is a convention the core does not enforce: `drivers/tty/sysrq.c`
  injects syncs with value 1 and `uinput_inject_events()` forwards whatever
  value userspace wrote.
- `evdev_pass_values()`: copies the sync value to the client unchanged.
