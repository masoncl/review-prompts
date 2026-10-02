- `perf_session__process_event()`: calls `perf_session__process_user_event()`
  directly for types at or above `PERF_RECORD_USER_TYPE_START`; only kernel
  records go through `perf_session__deliver_event()`.
- Order in `perf_session__process_event()`: size alignment, type range,
  `perf_event__too_small()`, swap, `events_stats__inc()`, dispatch. A record
  skipped by the range, size or swap check is not counted in `nr_events[]`.
- Type at or above `PERF_RECORD_HEADER_MAX`: reaches neither dispatcher;
  `perf_session__process_event()` prints a `ui__warning()` and returns 0.
- Unknown type in `machines__deliver_event()`: `nr_unknown_events++` and -1,
  which aborts the read.
- `perf_session__deliver_event()`: calls `evlist__event2evsel()` then
  `evsel__parse_sample()`; a NULL evsel is `-EFAULT` and aborts.
- Sample id that matches no evsel, in an evlist with more than one evsel:
  aborts with `-EFAULT`; it is not counted in `nr_unknown_id`.
- `nr_unknown_id` in `machines__deliver_event()`: reachable only when the
  caller passes a sample with no `evsel`, as through
  `perf_session__deliver_synth_event()`; `__evsel__parse_sample()` always
  sets `evsel`.
- Ordered mode: an error other than -1 from
  `evlist__parse_sample_timestamp()` aborts before the record is queued.
- Queued record: the checks and the handler in `perf_session__deliver_event()`
  run at flush time, so their error is returned by the `finished_round` call
  or the final flush.
- `perf_session__deliver_synth_event()`: applies the same split by type, with
  no alignment, range, size or swap step and no queue.
- Records inside `PERF_RECORD_COMPRESSED` and `PERF_RECORD_COMPRESSED2`:
  `__perf_session__process_decomp_events()` feeds each one to
  `perf_session__process_event()`, so they are checked and queued like any
  other.
