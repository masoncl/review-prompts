- `__trace_event_vstr_len()` in `include/linux/trace_events.h`: reserves the
  formatted length plus one, capped at `TRACE_EVENT_STR_MAX` (512).
- `__assign_vstr()`: passes `TRACE_EVENT_STR_MAX` as the `vsnprintf()` size,
  not the reserved length.
- Field overrun: prevented only by the second formatting producing no more
  than the first.
- **Potentially unsafe usage**: a `va_list` argument that `vsnprintf()`
  dereferences, such as a `%s` string.
  - Unsafe: when its content can grow between `trace_event_get_offsets_<class>()`
    and the assign block; `__assign_vstr()` then writes past the field, up to
    `TRACE_EVENT_STR_MAX` bytes.
  - Safe: arguments by value or strings nothing else writes during the call,
    as `do_simple_thread_func()` in
    `samples/trace_events/trace-events-sample.c`; `__assign_vstr()` then
    formats the same length that `__trace_event_vstr_len()` reserved.
