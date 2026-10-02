- `tr->snapshot_buffer`: the second `struct array_buffer`, compiled under
  `CONFIG_TRACER_SNAPSHOT`. There is no field named max_buffer in this tree.
- `CONFIG_TRACER_MAX_TRACE`: selects `CONFIG_TRACER_SNAPSHOT`; inside
  `struct trace_array` it guards only `max_latency` and its notify fields.
- Instance with `tr->range_addr_start` set (boot-mapped persistent memory, or
  a backup copy of it): `trace_allocate_snapshot()` returns 0 without
  allocating, so `tr->snapshot_buffer.buffer` stays NULL.
- `__trace_array_get()`: returns -ENODEV and takes no reference when
  `tr->free_on_close` is set and `autoremove_wq` exists, although the instance
  is still on `ftrace_trace_arrays`.
- `trace_array_get_by_name()` on such an instance: returns NULL; it does not
  create a second one. `trace_array_find_get()` returns NULL too.
- `tr->free_on_close`: set by `update_last_data()` on a
  `TRACE_ARRAY_FL_VMALLOC` instance, which is a backup instance.
  `__trace_array_put()` then queues `trace_array_autoremove()` when `tr->ref`
  falls to 1, which calls `trace_array_destroy()`.
- `__remove_instance()`: one -EBUSY test,
  `tr->ref > 1 || (tr->current_trace && tr->trace_ref)`. It makes no test of
  the tracer's own state.
- `tr->trace_ref`: incremented only by `tracing_open_pipe()` and
  `tracing_buffers_open()`. `tracing_open()`, the open of the `trace` file,
  holds `tr->ref` only.
- `enable_instances()`: takes an extra `tr->ref` that is never dropped when it
  sets `TRACE_ARRAY_FL_MEMMAP`, so removing that instance always returns
  -EBUSY.
- `trace_array_destroy()`: -EINVAL for a NULL pointer, -ENODEV when the pointer
  is not on the list. `instance_rmdir()`: -ENODEV when no instance has the
  name.
