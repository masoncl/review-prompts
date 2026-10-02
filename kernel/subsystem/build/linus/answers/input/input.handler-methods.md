- `input_handle_setup_event_handler()`: static in `drivers/input/input.c`;
  `handle->handle_events`, which it sets, is the only pointer
  `input_pass_values()` calls.
- A handler may set at most one of `filter()`, `event()` and `events()`:
  `input_handler_check_methods()` makes `input_register_handler()` return
  `-EINVAL` otherwise.
- A handler that sets none of the three is accepted, for example
  `kgdboc_reset_handler` in `drivers/tty/serial/kgdboc.c`; a handle of such a
  handler gets `input_handle_events_null()`.
- `events()` returning 0: ends the walk of `dev->h_list`, so no later handle
  sees the packet; `evdev_events()` returns `count` unchanged.
- `filter()` returning `true`: `input_handle_events_filter()` removes that one
  value and passes the rest of the packet on; the walk stops only when no
  value is left.
- With `dev->grab` set: `input_pass_values()` calls only the grabbing handle,
  so filters on the device do not see the events, and `handle->open` of the
  grabber is not tested.
