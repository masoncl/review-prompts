- `mmap`, `mmap2`, `comm`, `fork`, `exit`, `namespaces`, `cgroup`: default to
  `process_event_stub()`. A command that leaves them unset gets no threads
  and no maps from these records.
- `attr`, `event_update`, `tracing_data`, `build_id`, `id_index`, `feature`:
  default to stubs. Nothing populates the evlist from pipe input unless the
  command installs `perf_event__process_attr()` or a wrapper that calls it.

| Default that is not a stub | Effect |
|---|---|
| `perf_event__process_switch()` for `context_switch` | changes `machine->parallelism` |
| `perf_event__process_ksymbol()`, `perf_event__process_bpf()`, `perf_event__process_text_poke()` | change kernel maps or their DSOs; `perf_event__process_bpf()` only with `HAVE_LIBBPF_SUPPORT` |
| `perf_event__process_finished_round()` (init boolean true) | flushes the queue |
| `perf_session__process_compressed_event()` (`HAVE_ZSTD_SUPPORT`) | adds a decompressed buffer to the session |
| `perf_event__process_lost()`, `perf_event__process_lost_samples()`, `perf_event__process_aux()`, `perf_event__process_itrace_start()`, `perf_event__process_aux_output_hw_id()` | print under dump only |

- Session work that does not depend on the callback, for example: the copy
  into `session->time_conv` for `PERF_RECORD_TIME_CONV`,
  `perf_session__auxtrace_error_inc()`, and after `tool->attr` returns 0
  `perf_session__set_id_hdr_size()` and `perf_session__set_comm_exec()`.
- Pointer comparisons: the session compares only `tool->lost`,
  `tool->lost_samples` and `tool->aux` with their defaults, and
  `tool->compressed` with its stub through `perf_tool__compressed_is_stub()`.
  It does not compare `sample`, `attr` or `finished_round`.
- `machines__deliver_event()`: adds to `total_lost`, `total_lost_samples`,
  `total_aux_lost`, `total_aux_partial` and `total_aux_collision` only while
  the default is installed.
- `PERF_RECORD_MISC_LOST_SAMPLES_BPF`: counted in `total_dropped_samples`
  whatever `tool->lost_samples` is.
- `perf_session__warn_about_errors()`: makes the same three comparisons, so
  replacing `lost`, `lost_samples` or `aux` also silences the matching
  end-of-run warnings.
- `delegate_tool__init()`: a wrapped tool fails all three comparisons and
  `perf_tool__compressed_is_stub()`, even when the delegate holds the
  defaults.
