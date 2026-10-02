- `perf_event__synthesize_for_pipe()` in
  `tools/perf/util/synthetic-events.c`: emits attrs, then features with the
  end marker, then, under `HAVE_LIBTRACEEVENT`, tracing data if the evlist has
  tracepoints.
- It emits no `PERF_RECORD_HEADER_BUILD_ID`, no
  `PERF_RECORD_HEADER_EVENT_TYPE` and no `PERF_RECORD_FINISHED_INIT`.
- `PERF_RECORD_FINISHED_INIT`: written by `write_finished_init()` in
  `tools/perf/builtin-record.c`.
- Event names, units and scales: arrive later as `PERF_RECORD_EVENT_UPDATE`
  from `perf_event__synthesize_extra_attr()`; the name only when `is_pipe`.
- Features are sent in the same call as the attrs. `record__synthesize()`
  makes that call before recording, or after it when `opts.tail_synthesize`
  is set.
- `perf_event__synthesize_for_pipe()` output: all attrs precede the first
  feature event. `process_header_feature()` in `tools/perf/builtin-evlist.c`
  relies on it to stop reading.
- `perf_tool__init()` defaults: `attr` is `process_event_synth_attr_stub()`,
  `feature` is `process_event_op2_stub()`. Both return 0, so the events are
  dropped without an error.
- `attr`: must be `perf_event__process_attr()` or a wrapper that calls it
  first, for any command that reads samples from a pipe.
- `feature`: not needed to read samples. For example
  `tools/perf/builtin-kwork.c` and `tools/perf/builtin-mem.c` set `attr` and
  leave `feature` at the stub.
- `perf_event__process_tracing_data()`: declared only under
  `HAVE_LIBTRACEEVENT`. `cmd_report()` wraps the assignment in that `#ifdef`.
- **Potentially unsafe usage**: dereferencing `evlist__first()` or
  `evlist__last()` of `session->evlist`, directly or through a helper, after
  `perf_session__new()`.
  - Unsafe: on pipe input before the first attr was processed, when the list
    is empty. `perf_evlist__first()` is a bare `list_entry()` on the list
    head, so `evlist__sample_id_all()` reads memory that is not an evsel.
  - Safe: on file input with at least one attr, guarded by `!data->is_pipe`,
    as `__perf_session__new()` does for `evlist__sample_id_all()`;
    `perf_session__read_header()` has added the file's attrs with
    `evlist__add()`.
  - Safe: inside an `attr` wrapper after `perf_event__process_attr()`
    returned 0, as `process_attr()` in `tools/perf/builtin-script.c` does with
    `evlist__last()`; `perf_event__process_attr()` has then called
    `evlist__add()`.
  - Safe: `evlist__combined_sample_type()`, which iterates and returns 0 on an
    empty list. `report__setup_sample_type()` guards its tests of that value
    with `!is_pipe`.
