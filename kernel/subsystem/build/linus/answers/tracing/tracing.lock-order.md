- CPU hotplug lock: taken inside `trace_types_lock` and inside
  `tracepoints_mutex`, never outside them in the paths below.
  - `tracing_resize_ring_buffer()` holds `trace_types_lock` and calls
    `ring_buffer_resize()`, which takes the hotplug lock.
  - `tracepoint_add_func()` runs under `tracepoints_mutex` and calls
    `static_branch_enable()`.
- `ring_buffer_resize()`: takes the hotplug lock first, then `buffer->mutex`.
- `osnoise_hotplug_workfn()`: `trace_types_lock`, then the hotplug lock, then
  `interface_lock`. `hwlat_hotplug_workfn()`: `trace_types_lock`,
  `hwlat_data.lock`, then the hotplug lock.
- **Unsafe usage**: taking `trace_types_lock` in a CPU hotplug callback.
  - Safe: schedule work from the callback and take the locks in the work
    function, as `osnoise_cpu_init()` and `hwlat_cpu_init()` do;
    `tracing_resize_ring_buffer()` defines the order.
- `kernel/tracepoint.c` has two mutexes under `CONFIG_MODULES`.
  `tracepoint_module_list_mutex` protects `tracepoint_module_list` and is held
  across the `tracepoint_notify_list` notifier chain. `tracepoints_mutex`
  protects the probe arrays and nests inside it.
- `__tracepoint_probe_module_cb()` in `kernel/trace/trace_fprobe.c`: shows that
  order; it runs from the notifier chain, takes `tracepoint_user_mutex`, and
  registers a probe.
- `dyn_event_ops_mutex`: protects `dyn_event_ops_list` and `trace_probe_log`.
  `trace_probe_log_init()`, `trace_probe_log_set_index()`,
  `trace_probe_log_clear()` and `__trace_probe_log_err()` in
  `kernel/trace/trace_probe.c` assert it.
- `dyn_event_create()` and `create_dyn_event()`: hold `dyn_event_ops_mutex`
  across the `create` callback, which takes `event_mutex`, for example in
  `register_trace_kprobe()`.
- `dyn_event_release()` and `dyn_events_release_all()`: take `event_mutex` and
  not `dyn_event_ops_mutex`; inside it `tracing_reset_all_online_cpus()` takes
  `trace_types_lock`.
- `trace_event_dyn_try_get_ref()`: takes `trace_event_sem` for read and no
  mutex.
- `text_mutex`: no file under `kernel/trace` names it. It is taken by the x86
  and riscv overrides of `ftrace_arch_code_modify_prepare()` and released by
  `ftrace_arch_code_modify_post_process()`; the weak defaults in
  `kernel/trace/ftrace.c` are empty.
- `ftrace_lock` outside `text_mutex`: `ftrace_module_enable()` calls
  `ftrace_arch_code_modify_prepare()` with `ftrace_lock` held, only when
  `ftrace_start_up` is non-zero.
- `trace_types_lock` outside `ftrace_lock`: `__remove_instance()` calls
  `ftrace_clear_pids()`. `ftrace_module_enable()` drops `ftrace_lock` before
  `process_cached_mods()`, which takes `trace_types_lock`.
