- `tracing_open_generic_tr()`: after it takes the reference, a write open of
  an instance for which `trace_array_is_readonly()` is true drops the
  reference and returns -EACCES.
- Open method that calls `tracing_check_open_get_tr()` itself: gets no
  read-only test from the helper; it refuses a write open of a
  `TRACE_ARRAY_FL_RDONLY` instance only if it also tests
  `trace_array_is_readonly()`, as `tracing_clock_open()` does.
- `tracing_open_file_tr()`: does not set `filp->private_data`. Later methods
  reach the event file through the inode, with `event_file_file()`.
- `tracing_release_generic_tr()` and `tracing_release_file_tr()`: read
  `inode->i_private`, so an open method may overwrite `filp->private_data`,
  as `event_hist_open()` does with `single_open()`.
- `tracing_open_file_tr()`: reads `file->tr` before it holds a reference of its
  own. The eventfs reference keeps the `struct trace_event_file` allocated,
  and `trace_array_get()` dereferences the pointer only after it matched a
  listed instance.
- `trace_array_put()`: takes `trace_types_lock` itself. A release method that
  already holds it uses `__trace_array_put()`, static in
  `kernel/trace/trace.c`, as `tracing_release()` and
  `tracing_buffers_release()` do.
- File whose `i_private` points at memory that an instance owns, not at the
  `struct trace_array`: the open method finds the instance by matching the
  address against each listed instance under `trace_types_lock`, before any
  dereference. See `trace_array_options_get()`,
  `trace_array_tracer_options_get()` and `subsystem_open()`.
- **Potentially unsafe usage**: `tracing_open_generic()` as the open method of
  a file whose `i_private` is a `struct trace_array`.
  - Unsafe: when the file is created for every instance, as the files in
    `init_tracer_tracefs()` are. No reference is held, and
    `__remove_instance()` frees `tr` while the file is open.
  - Safe: when the file is created only with `&global_trace`, as
    `tracing_thresh_fops` is. `global_trace` is static and has no name, so
    `trace_array_find()` in `instance_rmdir()` cannot select it.
