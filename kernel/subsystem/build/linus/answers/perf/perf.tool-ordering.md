- `PERF_RECORD_FINISHED_INIT`: does not flush; it calls `tool->finished_init`,
  whose default is `process_event_op2_stub()`.
- Switch-off in `__perf_session__new()`: needs `ordering_requires_timestamps`,
  `ordered_events`, input that is not a pipe, and `evlist__sample_id_all()`
  false. `PERF_SAMPLE_TIME` is not tested.
- Switch-off message: `dump_printf()` only; nothing is printed in a normal
  run.
- Switch-off effect: writes `false` into the caller's `tool->ordered_events`
  and leaves `tool->finished_round` as it was.
- Pipe input: never switched off; `__perf_session__process_pipe_events()`
  calls `ordered_events__set_copy_on_queue()` because its read buffer is
  reused.
- `OE_FLUSH__HALF`: `ordered_events__init()` sets `max_alloc_size` to
  `(u64)-1`, so it happens only after `ordered_events__set_alloc_size()`, as
  in `cmd_report()`, or when an allocation fails.
- First `OE_FLUSH__ROUND`: delivers nothing; `do_flush()` returns while
  `next_flush` is 0, and each round delivers up to the previous round's
  `max_timestamp`.
