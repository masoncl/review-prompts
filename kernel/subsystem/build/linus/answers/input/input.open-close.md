- `input_start_device()` in `drivers/input/input.c` holds the user count and
  the `open()` call; `input_open_device()` calls it under `dev->mutex`.
- Handler with `passive_observer` set: `handle->open` is counted, but
  `input_start_device()` and the `--dev->users` branch are skipped, so such a
  handle never causes `open()` or `close()`.
- `passive_observer`: no handler in this tree sets it.
- `input_close_device()`: its first step is `__input_release_device()`.
- `synchronize_rcu()` in `input_close_device()`: runs when `--handle->open`
  reaches 0, not on list removal.
- `open()` error: `dev->users--` in `input_start_device()`, then
  `handle->open--` and `synchronize_rcu()` in `input_open_device()`;
  `handler->start()` is not called.
- Unregister: `input_disconnect_device()` zeroes every `handle->open` but
  leaves `dev->users`, so `close()` still runs from the handlers'
  `disconnect()` via `input_close_device()`, if the device is not inhibited.
