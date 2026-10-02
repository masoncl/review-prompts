Instances and buffers

- Snapshot swap: `update_max_tr()` swaps only the `buffer` pointers of
  `array_buffer` and `snapshot_buffer`; each `struct array_buffer` keeps its
  own per-CPU `data`. `update_max_tr_single()` swaps one CPU with
  `ring_buffer_swap_cpu()`.
- Kinds of instance: the flags enum that starts with `TRACE_ARRAY_FL_GLOBAL`
  in `kernel/trace/trace.h`. The surprising one is `TRACE_ARRAY_FL_RDONLY`, a
  boot-time backup copy of a persistent instance; write opens through
  `tracing_open_generic_tr()` fail and `event_create_dir()` creates only its
  read-only event files.
- `struct trace_array` has two counters, both plain `int` under
  `trace_types_lock`: `ref` (base value 1) pins the instance; `trace_ref`
  counts open `trace_pipe` and `trace_pipe_raw` readers and makes
  `tracing_set_tracer()` return `-EBUSY`. `__remove_instance()` tests both.
- `struct trace_remote` in `kernel/trace/trace_remote.c`: a buffer written by
  something outside the kernel (for example the pKVM hypervisor, through
  `kernel/trace/simple_ring_buffer.c`) and only read here. It is not a
  `struct trace_array`: own `remotes/` tracefs directory, own
  `struct trace_remote_iterator`, events are `struct remote_event`, and each
  record starts with `struct remote_event_hdr`, not `struct trace_entry`.

Tracers

- `struct tracers` in `kernel/trace/trace.c`: one per instance for each tracer
  that `trace_ok_for_array()` accepts, on `tr->tracers`. `trace_types` is
  still the global registration list, but `tracing_set_tracer()` looks a name
  up in `tr->tracers`.
- `tr->current_trace_flags`: the option flags of the current tracer for this
  instance. A tracer that sets `default_flags` instead of `flags` gets a
  private copy per instance in `add_tracer()`; for example the function and
  function_graph tracers.

Events

- `struct trace_event_file`: not one per (instance, call) pair in every
  instance. An instance created with a `systems` list
  (`trace_array_get_by_name()`) gets files only for calls that
  `event_in_systems()` accepts.
- Tracepoint callback: `trace_event_reg()` registers `class->probe` once per
  enabled `struct trace_event_file`, with the file as data, so each call
  writes to one instance. Perf registers `class->perf_probe` with the
  `struct trace_event_call` as data.
- `ref` of `struct trace_event_file`: held by the creator, by the eventfs
  `enable` entry (`event_create_dir()`, dropped in `event_release()`), and by
  each open through `tracing_open_file_tr()`. Triggers do not take it.
- `struct event_filter`: `struct trace_event_call` holds none. The holders
  declared in headers are `struct trace_event_file`, `struct event_subsystem`,
  `struct event_trigger_data` and `struct perf_event`.
- `struct event_command`: holds the trigger callbacks (`trigger`,
  `count_func`, `init`, `free`, `print`) as well as `parse` and `reg`; a
  `struct event_trigger_data` reaches them through `cmd_ops`. There is no
  separate event_trigger_ops type.
- `struct trace_seq`: `TRACE_SEQ_SIZE` is 8192 bytes, not one page.

Dynamic events

- Embedding, not wrapping: `struct trace_kprobe`, `struct trace_uprobe`,
  `struct trace_fprobe` and `struct trace_eprobe` each embed a
  `struct dyn_event` and a `struct trace_probe`.
- `struct trace_probe_event`: embeds the `struct trace_event_call` and the
  `struct trace_event_class`; a `struct trace_probe` only points at it.
- `struct synth_event` and `struct user_event`: embed `struct dyn_event`, call
  and class directly and have no `struct trace_probe`.
- `struct tracepoint` is not always a static site: `struct user_event` embeds
  one and `struct synth_event` points at one made at run time.

Function tracing

- `struct fprobe`: holds no `struct ftrace_ops` and no `struct fgraph_ops`.
  `kernel/trace/fprobe.c` has one shared `fprobe_graph_ops` for fprobes with
  an `exit_handler`, and one shared `fprobe_ftrace_ops` for entry-only
  fprobes; see `fprobe_is_ftrace()`.
- `fprobe_ftrace_ops` exists only with `CONFIG_DYNAMIC_FTRACE_WITH_ARGS` or
  `CONFIG_DYNAMIC_FTRACE_WITH_REGS`; otherwise every fprobe goes through
  `fprobe_graph_ops`.
- `struct fgraph_ops`: its embedded `ops` is not registered on its own.
  `register_ftrace_graph()` attaches it to the single `graph_ops` in
  `kernel/trace/fgraph.c` with `ftrace_startup_subops()`.
- Instance `tr->gops`: under `CONFIG_DYNAMIC_FTRACE`, `fgraph_init_ops()`
  points its `ops.func_hash` at `tr->ops->local_hash`, so the function and
  function_graph tracers of one instance share one filter.
