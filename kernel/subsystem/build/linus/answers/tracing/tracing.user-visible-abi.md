- `trace_pipe_raw`: exists only in each `per_cpu` CPU directory; there is no
  top-level one. See `tracing_init_tracefs_percpu()` in
  `kernel/trace/trace.c`.
- `id` file: created only under `CONFIG_PERF_EVENTS` and only when the event
  class has `reg`; the `ID:` line of `format` is always present.
- `btf_ids` file: per event under `CONFIG_BPF_EVENTS` when the class has
  `btf_ids`; it prints `btf_obj_id`, `raw_btf_id` and `tp_btf_id`. See
  `event_btf_ids_read()` in `kernel/trace/trace_events.c`.
- `header_page`: is per instance; the size of its `data` field comes from
  `rb_subbuf_capacity()` of that instance's buffer, so it changes with
  `buffer_subbuf_size_kb`.
- `header_event`: fixed text, the same in every instance.
- `common_flags` bits: `__event_in_hardirq()`, `__event_in_softirq()` and
  `__event_in_irq()` in `include/trace/stages/stage7_class_define.h` put the
  literals 0x8, 0x10 and 0x18 into print formats, so `TRACE_FLAG_HARDIRQ` and
  `TRACE_FLAG_SOFTIRQ` cannot change value.
- `buffer_meta`: per CPU, created only when the instance has
  `range_addr_start` set.
