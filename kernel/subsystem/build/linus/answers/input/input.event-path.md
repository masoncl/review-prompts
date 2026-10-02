- `handle->handle_events` precedence: `handler->filter` gives
  `input_handle_events_filter()`, else `handler->event` gives
  `input_handle_events_default()`, else `handler->events` is installed
  directly, else `input_handle_events_null()`.
- `input_handle_event()`: not static, declared in
  `drivers/input/input-core-private.h`; core paths and
  `drivers/input/input-mt.c` call it with `dev->event_lock` already held,
  without going through `input_event()`; it asserts `dev->event_lock` and
  makes no test of the event type against `dev->evbit` itself.
- `input_set_keycode()`: calls `input_event_dispose()` directly, so the
  key-up it sends for a removed keycode skips `input_get_disposition()`.
