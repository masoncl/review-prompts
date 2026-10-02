- Only files that are easy to miss are listed; most other jobs are in the
  file their name suggests under `kernel/trace/`, `include/trace/` and
  `fs/tracefs/`, for example `kernel/trace/trace_events_hist.c`; the
  tracepoint core is outside them, in `kernel/tracepoint.c`.

| Job | File in this tree | Easy to miss |
|---|---|---|
| Snapshots | `kernel/trace/trace_snapshot.c` | Built only under `CONFIG_TRACER_SNAPSHOT`; `tracing_snapshot()` and `tracing_alloc_snapshot()` are still defined in `kernel/trace/trace.c` |
| Max-latency buffer swap | `kernel/trace/trace_snapshot.c` | `update_max_tr()`, `update_max_tr_single()` and the `tracing_max_latency` file are here, not in `kernel/trace/trace.c`; of these only the `tracing_max_latency` file is under `CONFIG_TRACER_MAX_TRACE` |
| `trace_printk()` backend | `kernel/trace/trace_printk.c`, `include/linux/trace_printk.h` | `trace_vbprintk()`, `trace_array_printk()` and `__trace_puts()` are not in `kernel/trace/trace.c` |
| PID filtering helpers | `kernel/trace/trace_pid.c` | `trace_pid_write()` and `trace_ignore_this_task()` are not in `kernel/trace/trace.c`; `kernel/trace/ftrace.c` and `kernel/trace/trace_events.c` call them |
| Ring buffer page and event layout | `include/linux/ring_buffer_types.h` | `struct buffer_data_page`, `RB_EVNT_HDR_SIZE` and `RB_ALIGNMENT` are here, not in `kernel/trace/ring_buffer.c` |
| Ring buffer written by a remote | `kernel/trace/simple_ring_buffer.c`, `include/linux/simple_ring_buffer.h` | A second writer implementation, also built into `arch/arm64/kvm/hyp/nvhe/`; the kernel reads it through a `struct trace_buffer` from `__ring_buffer_alloc_remote()` in `kernel/trace/ring_buffer.c` |
| Trace remotes (tracefs `remotes/` directory) | `kernel/trace/trace_remote.c`, `include/linux/trace_remote.h` | `CONFIG_TRACE_REMOTE`; separate from `struct trace_array` instances |
| Remote event macros | `include/trace/define_remote_events.h` | `REMOTE_EVENT()`; not part of the `TRACE_EVENT()` stage headers |
| Trace event stage headers | `include/trace/stages/` | `include/trace/trace_events.h` includes `include/trace/stages/init.h` before stage 1 |
| fprobe header | `include/linux/fprobe.h` | There is no fprobes.h |
| Shared probe code, kernel-only part | `kernel/trace/trace_probe_kernel.h` | Not included by `kernel/trace/trace_uprobe.c`; also included by `kernel/trace/trace_events_synth.c` |
| BTF argument lookup for probes | `kernel/trace/trace_btf.c` | Built only under `CONFIG_PROBE_EVENTS_BTF_ARGS` |
| RV reactor framework | `kernel/trace/rv/rv_reactors.c` | `kernel/trace/rv/reactor_printk.c` and `kernel/trace/rv/reactor_panic.c` are the reactors themselves |
| RV monitor templates | `include/rv/da_monitor.h`, `include/rv/ha_monitor.h`, `include/rv/ltl_monitor.h` | `include/rv/ha_monitor.h` (hybrid automata) is layered on the DA hooks |
| RV monitor KUnit tests | `kernel/trace/rv/rv_monitors_test.c`, `include/rv/kunit.h` | A monitor's test file, for example `kernel/trace/rv/monitors/sco/sco_kunit.c`, sits beside the monitor; not every monitor has one |
