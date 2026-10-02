- tracefs makes no lockdown check at open or permission time.
  `tracefs_create_file()` and `tracefs_create_dir()` in `fs/tracefs/inode.c`
  check only when the file is created.
- Open method with no instance to pin: may call
  `security_locked_down(LOCKDOWN_TRACEFS)` directly instead of
  `tracing_check_open_get_tr(NULL)`, as `ftrace_avail_open()` does, and
  `ftrace_event_avail_open()` through the helper `ftrace_event_open()`.
- `show_traces_open()`: passes `tr`, not NULL, and releases with
  `tracing_seq_release()`.
- Option files: `trace_array_options_get()` and
  `trace_array_tracer_options_get()` carry their own copy of the lockdown and
  `tracing_disabled` tests, because they cannot pass a `struct trace_array`
  pointer.
- Error code: not every caller returns the lockdown error unchanged.
  `ftrace_regex_open()` and `trace_options_open()` return -ENODEV whatever
  the check returned.
- `ftrace_filter_open()`: makes the check through `ftrace_regex_open()`.
- Event files with no lockdown check on open: `trace_format_open()` makes
  none, and `ftrace_event_id_fops` and `ftrace_event_btf_ids_fops` have no
  open method.
