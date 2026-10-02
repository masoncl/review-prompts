# Tracing Subsystem

## Main structures

### Objects and how they relate

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

## Where to look

**Core files**

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

## Tracepoints

**Tracepoints without trace events**

- `DECLARE_TRACE()`: passes `name##_tp` to `__DECLARE_TRACE()`, so every
  generated name carries the suffix; a call site fires it as, for example,
  `trace_sched_set_need_resched_tp()` in `kernel/sched/core.c`.
- `DECLARE_TRACE_EVENT()` is what `TRACE_EVENT()` and `DEFINE_EVENT()` expand
  to; it passes the name unchanged.
- Definition: no `.c` file in this tree calls `DEFINE_TRACE()`; it takes name,
  proto and args. A bare tracepoint is defined by including its header under
  `CREATE_TRACE_POINTS`; `include/trace/define_trace.h` turns
  `DECLARE_TRACE()` into `DEFINE_TRACE()` on the suffixed name.
- `DECLARE_TRACE_SYSCALL()`: `include/trace/define_trace.h` has no mapping for
  it, and nothing in this tree uses it.
- Export: there is no EXPORT_TRACEPOINT_GPL() or EXPORT_TRACEPOINT() here; use
  `EXPORT_TRACEPOINT_SYMBOL_GPL()` or `EXPORT_TRACEPOINT_SYMBOL()` with the
  suffixed name, as `kernel/sched/core.c` does for `sched_set_state_tp`.
- `trace_call__` plus the name: defined beside the normal trace function by
  `__DECLARE_TRACE()` and `__DECLARE_TRACE_SYSCALL()`; it runs the probes
  without testing the static key.
- `trace_call__` form, what it keeps: in `__DECLARE_TRACE()` the `cond` test
  (`cpu_online(raw_smp_processor_id())` and any `TP_CONDITION()`), the
  read-side guard, and `might_fault()` in the syscall variant.
- `trace_call__` form, what it drops: the `CONFIG_LOCKDEP` "RCU not watching"
  warning that the normal trace function makes.
- `trace_call__` form, intended place: code reached only after
  `tracepoint_enabled()` or the generated enabled function tested true, for
  example `__trace_set_current_state()` in `kernel/sched/core.c` and
  `queued_spin_release_traced()` in `kernel/locking/qspinlock.c`.
- `trace_call__` form with no probe registered: enters the read section (in
  `__DECLARE_TRACE()` only when `cond` passes), finds `funcs` NULL and calls
  nothing; the cost is the lost static branch, not a crash.

**Enabled test in headers**

- Header side: `DECLARE_TRACEPOINT()` plus `tracepoint_enabled()`, then a call
  to a wrapper function defined in a `.c` file that includes the trace header;
  see `include/linux/mmap_lock.h` and `mm/mmap_lock.c`.
- `DECLARE_TRACEPOINT()`: defined unconditionally as the `extern`
  declaration; only `tracepoint_enabled()` becomes `false` without
  `CONFIG_TRACEPOINTS`.
- Bare tracepoint: pass the name with its `_tp` suffix, as
  `tracepoint_enabled(sched_set_state_tp)` in `include/linux/sched.h`.
- Tracepoint or wrapper built only under another option:
  `tracepoint_enabled()` still references `__tracepoint_` plus the name
  whenever `CONFIG_TRACEPOINTS` is set, so the header needs its own gate; see
  `page_ref_tracepoint_active()` in `include/linux/page_ref.h` (tracepoint
  defined only under `CONFIG_DEBUG_PAGE_REF`) and the `IS_ENABLED()` test in
  `queued_spin_unlock()` in `include/asm-generic/qspinlock.h` (wrapper defined
  only under `CONFIG_QUEUED_SPINLOCKS_TRACE_CONTENDED_RELEASE`).
- Inline usable from modules: export both the wrapper and the tracepoint;
  `net/9p/client.c` uses `EXPORT_TRACEPOINT_SYMBOL(9p_fid_ref)` for the test
  and `EXPORT_SYMBOL(do_trace_9p_fid_get)` for the wrapper.
- Wrapper body: either the normal trace function, which tests the key again
  (`do_trace_write_msr()` in `arch/x86/lib/msr.c`), or the `trace_call__`
  form, which does not (`__trace_set_current_state()`).
- Wrapper that uses the `trace_call__` form: the wrapper no longer tests the
  key, so a caller that skips the enabled test enters the read section on
  every call that passes `cond`.

**Probe calling context**

- `__DECLARE_TRACE`: probes run under
  `guard(srcu_fast_notrace)(&tracepoint_srcu)`; the tracepoint does not
  disable preemption or migration.
- `__DECLARE_TRACE` probe that uses per-CPU data or `smp_processor_id()`: has
  to disable preemption or migration itself unless the call site already did;
  the generated event probe disables preemption, with
  `guard(preempt_notrace)()` in `trace_event_raw_event_` plus the class name
  in `include/trace/trace_events.h`.
- `__DECLARE_TRACE` and sleeping: the probe inherits the context of the call
  site and nothing marks that site as sleepable; `bpf_raw_tp_link_attach()` in
  `kernel/bpf/syscall.c` returns `-EINVAL` for a sleepable program unless
  `tracepoint_is_faultable()`.
- `__DECLARE_TRACE_SYSCALL`: `rcu_read_lock_trace()` does not disable
  migration; `__bpf_trace_run()` in `kernel/trace/bpf_trace.c` runs a
  sleepable program under `rcu_read_lock_tasks_trace()` and calls
  `migrate_disable()` itself.
- `might_fault()` in the syscall variant: runs before the static-key test, so
  it checks the call site even while the tracepoint is disabled.
- Old probe array: `release_probes()` in `kernel/tracepoint.c` frees it with
  one callback, `call_srcu()` on `tracepoint_srcu` or
  `call_rcu_tasks_trace()`, chosen by `tracepoint_is_faultable()`.
- Probe `data`: the pointer is stored in the same `struct tracepoint_func`
  entry as the function, and the entry is covered by the same grace period;
  the tracepoint never frees what it points to.
- Static-call path: `__DO_TRACE_CALL()` reads `data` from the first array
  entry and the function from the static call separately;
  `tp_rcu_cond_sync()` in `kernel/tracepoint.c` keeps a new function from
  seeing old `data`.
- Comments in `kernel/tracepoint.c` that mention `rcu_dereference_sched()` or
  `preempt_disable()` around the call site do not describe what
  `__DECLARE_TRACE` does in this tree.

**Configurations that lack a tracepoint**

- Two failure modes, depending on where the option is tested.
- Header declares unconditionally, defining file not built: the register
  function compiles and the link fails on the undefined
  `__tracepoint_` symbol.
- Header hides the event behind `#ifdef`: the register function is not
  declared at all, so the compile fails; `include/trace/events/preemptirq.h`
  leaves only the empty `trace_preempt_enable()` and `trace_preempt_disable()`
  macros without `CONFIG_TRACE_PREEMPT_TOGGLE`, and
  `include/trace/events/syscalls.h` declares nothing without
  `CONFIG_HAVE_SYSCALL_TRACEPOINTS`.
- Architecture-defined tracepoint: `page_fault_user` and `page_fault_kernel`,
  declared in `include/trace/events/exceptions.h`, defined only by
  `arch/x86/mm/fault.c` and `arch/riscv/mm/fault.c`.
- `arch/riscv/mm/Makefile`: builds `fault.o` only under `CONFIG_MMU`.
- User that accounts for it: `RV_MON_PAGEFAULT` in
  `kernel/trace/rv/monitors/pagefault/Kconfig`, with `depends on X86 || RISCV`
  and `depends on MMU`.
- Other RV entries of the same kind, for example: `RV_MON_SNEP` depends on
  `TRACE_PREEMPT_TOGGLE`, `RV_MON_STS` on `TRACE_IRQFLAGS`, `RV_MON_SLEEP` on
  `HAVE_SYSCALL_TRACEPOINTS`.
- RV monitors are `bool`, so a missing dependency breaks the vmlinux build, not
  a module.

**Freeing after unregistering a probe**

- `tracepoint_synchronize_unregister()`: `synchronize_rcu_tasks_trace()`, then
  `synchronize_srcu(&tracepoint_srcu)`; it contains no direct
  `synchronize_rcu()` call.
- What it waits for: probes already running on faultable tracepoints (Tasks
  Trace RCU, the guard in `__DECLARE_TRACE_SYSCALL`) and on tracepoints
  declared with `__DECLARE_TRACE` (`tracepoint_srcu`); it takes no tracepoint
  argument.
- **Potentially unsafe usage**: freeing probe `data`, or returning from the
  exit function of the module that holds the probe, after
  `tracepoint_probe_unregister()` with no grace period.
  - Unsafe: when the probe dereferences `data` that is freed, or its text is
    unloaded, before a grace period of the reader's domain ends; a task that
    loaded the old array entry still calls the probe. `synchronize_rcu()` or
    `call_rcu()` is not that grace period: the reader in `__DECLARE_TRACE`
    holds only `tracepoint_srcu`.
  - Safe: `tracepoint_synchronize_unregister()` between the unregister and the
    free, as `perf_trace_event_unreg()` in `kernel/trace/trace_event_perf.c`
    does before `free_percpu()`; the readers it waits for are the guards in
    `__DECLARE_TRACE` and `__DECLARE_TRACE_SYSCALL`.
  - Safe: deferring the free with `call_tracepoint_unregister_atomic()`, which
    does not block, for a tracepoint that is not faultable, as
    `bpf_link_free()` in `kernel/bpf/syscall.c` does; it is `call_srcu()` on
    `tracepoint_srcu`, the domain the reader holds.
  - Safe: for a faultable tracepoint, `call_tracepoint_unregister_syscall()`,
    which is `call_rcu_tasks_trace()`; `bpf_link_free()` calls
    `call_rcu_tasks_trace()` directly for those links.
  - Safe: a built-in probe registered with NULL `data`, where nothing is freed,
    as `tracing_sched_unregister()` in `kernel/trace/trace_sched_switch.c`.
- `call_tracepoint_unregister_syscall()`: has no caller in this tree.
- Choosing between the two helpers: test `tracepoint_is_faultable()`, as
  `release_probes()` in `kernel/tracepoint.c` does.
- Without `CONFIG_TRACEPOINTS`: both helpers are empty stubs that never invoke
  the callback, so a free deferred through them never happens.
- `bpf_probe_unregister()` in `kernel/trace/bpf_trace.c`: only unregisters; the
  deferred free is in `bpf_link_free()`.

## Defining a trace event

**Trace event headers**

- `TRACE_SYSTEM`: becomes `.system` of `struct trace_event_class` through
  `TRACE_SYSTEM_STRING` (`include/trace/stages/init.h`); `struct
  trace_event_call` has no system member.
- `TRACE_SYSTEM`: `include/trace/define_trace.h` never undefines it; a header
  does `#undef TRACE_SYSTEM` itself before its `#define`, outside the guard in
  `include/trace/events/sched.h`, inside it in for example
  `arch/x86/kvm/trace.h`.
- `TRACE_INCLUDE_PATH` set: the re-include is a quoted include built by
  `__stringify(TRACE_INCLUDE_PATH/system.h)`, so it is looked up first relative
  to `include/trace/` (where the including files live) and then on the `-I`
  path; `.` works only through `-I$(src)`.
- `TRACE_INCLUDE_PATH` and `TRACE_INCLUDE_FILE`: macro-expanded before being
  stringified, so a path component that is also a macro name is replaced.
- `TRACE_INCLUDE_PATH` / `TRACE_INCLUDE_FILE` defined by a header: stay defined
  after `define_trace.h` (it undefines only its own defaults, see
  `UNDEF_TRACE_INCLUDE_PATH`); a later trace header in the same `.c` inherits
  them unless it does `#undef` first.
- Guard without `|| defined(TRACE_HEADER_MULTI_READ)`: every re-read is empty,
  including the first one in `define_trace.h` that expands `DEFINE_TRACE()`,
  so neither the tracepoint nor the event is defined.
- `CREATE_TRACE_POINTS` in two files linked together: the clash is on the
  non-static objects from `__DEFINE_TRACE_EXT()` in
  `include/linux/tracepoint.h` (`__tracepoint_<name>`, `__traceiter_<name>`,
  `__probestub_<name>`, the static call); the event structures and strings are
  `static` and do not clash.

**Code generated for an event**

- `trace_event_raw_event_<class>()`: disables preemption itself with
  `guard(preempt_notrace)()` and then calls
  `do_trace_event_raw_event_<class>()`, which holds the reserve, assign and
  commit steps; see `include/trace/trace_events.h`.
- There is no __DO_TRACE() here; `__do_trace_<name>()` and
  `__DO_TRACE_CALL()` do that job.
- `DECLARE_EVENT_SYSCALL_CLASS()`: the probe differs from the normal one only
  by `might_fault()` before the same `guard(preempt_notrace)()`.
- `perf_trace_<class>()` in `include/trace/perf.h`: same wrapper pattern
  around `do_perf_trace_<class>()`.
- `tracing_gen_ctx_dec()` in `trace_event_buffer_reserve()`: under
  `CONFIG_PREEMPTION` it subtracts the probe's own increment so the record
  shows the call site's preempt count; without it nothing is subtracted.
- Commit: `trace_event_buffer_commit()`; there is no separate filter-aware
  commit call in the probe.
- `DEFINE_EVENT()`: generates no output function and no format; `event_<name>`
  points at `trace_event_type_funcs_<class>` and `print_fmt_<class>`. Only
  `DEFINE_EVENT_PRINT()` generates its own pair.
- Shared per class beyond the ftrace objects: `perf_trace_<class>()` under
  `CONFIG_PERF_EVENTS`, `__bpf_trace_<class>()` under `CONFIG_BPF_EVENTS`, and
  under `CONFIG_BPF_EVENTS` with `CONFIG_DEBUG_INFO_BTF` the id list from
  `_TRACE_BTF_IDS_DECLARE()`.

**Field and assignment macros**

- `__dynamic_array(type, item, len)`: has no assign macro; the block writes
  through `__get_dynamic_array(item)`.
- `__dynamic_array()` `len`: a count of elements; `__get_dynamic_array_len()`
  returns bytes.
- `__string_len(item, src, len)`: filled with `__assign_str(item)`, read with
  `__get_str(item)`.
- `__sockaddr(field, len)`: filled with `__assign_sockaddr(dest, src, len)`,
  read with `__get_sockaddr(field)`.
- `__rel_string()`, `__rel_string_len()`, `__rel_bitmask()`, `__rel_cpumask()`
  and `__rel_sockaddr()`: filled and read with their own macros in
  `include/trace/stages/stage6_event_callback.h` and
  `include/trace/stages/stage3_trace_output.h`, for example
  `__assign_rel_str()` and `__get_rel_str()`;
  `__rel_dynamic_array()` has no assign macro and is written through
  `__get_rel_dynamic_array()`. Mixing with the plain forms names a
  `__data_loc_<item>` or `__rel_loc_<item>` member that the record does not
  have and fails to build.
- `__get_bitmask()` and `__get_cpumask()`: inside `TP_fast_assign()` they are
  the raw destination pointer (`include/trace/stages/stage6_event_callback.h`);
  inside `TP_printk()` they return a formatted string from
  `trace_print_bitmask_seq()` (`include/trace/stages/stage3_trace_output.h`).
- `__assign_bitmask(dst, src, nr_bits)`: copies `__bitmask_size_in_bytes()`,
  which is `nr_bits` rounded up to whole longs; `src` must be readable to that
  size.

**Recording a string**

- Source pointer: saved by the measure step in member `<item>_ptr_` of
  `struct trace_event_data_offsets_<class>`; `__assign_str()` reads it from
  there. There is no __str_src helper; `__string_src()` only substitutes
  `EVENT_NULL_STR` for the `strlen()`.
- `__assign_str()`: `memcpy()` of the measured length minus one, then writes
  the NUL itself; it does not use `strcpy()`, so the copy cannot exceed the
  reserved bytes and the field always ends in NUL.
- Source that shrank between the steps: `__assign_str()` still reads the full
  measured length from the source.
- `__string()` source expression: expanded twice in the measure step (once for
  `strlen()`, once for the saved pointer).
- **Potentially unsafe usage**: `__string_len()` with a source that can be
  NULL.
  - Unsafe: with a non-zero `len`; nothing measures the source, and
    `__assign_str()` copies `len` bytes starting at `EVENT_NULL_STR`.
  - Safe: `len` is 0 whenever the source is NULL, as `nfsd_handle_dir_event`
    in `fs/nfsd/trace.h`; the record then holds an empty string, not
    `"(null)"`.
  - Safe: `__string()`, which measures `EVENT_NULL_STR` itself.

**Formatted string fields**

- `__trace_event_vstr_len()` in `include/linux/trace_events.h`: reserves the
  formatted length plus one, capped at `TRACE_EVENT_STR_MAX` (512).
- `__assign_vstr()`: passes `TRACE_EVENT_STR_MAX` as the `vsnprintf()` size,
  not the reserved length.
- Field overrun: prevented only by the second formatting producing no more
  than the first.
- **Potentially unsafe usage**: a `va_list` argument that `vsnprintf()`
  dereferences, such as a `%s` string.
  - Unsafe: when its content can grow between `trace_event_get_offsets_<class>()`
    and the assign block; `__assign_vstr()` then writes past the field, up to
    `TRACE_EVENT_STR_MAX` bytes.
  - Safe: arguments by value or strings nothing else writes during the call,
    as `do_simple_thread_func()` in
    `samples/trace_events/trace-events-sample.c`; `__assign_vstr()` then
    formats the same length that `__trace_event_vstr_len()` reserved.

**Other consumers of event headers**

- Boot self-test: `event_trace_self_tests()` in `kernel/trace/trace_events.c`
  is under `CONFIG_EVENT_TRACE_STARTUP_TEST`; its per-event pass tests only
  events whose class has a `probe`, and skips system `syscalls` without
  `CONFIG_EVENT_TRACE_TEST_SYSCALLS`.
- BPF probe: named `__bpf_trace_<class>()`; there is no bpf_trace_<call>.
- Per-class BTF ids: `_TRACE_BTF_IDS_DECLARE()` in
  `include/trace/trace_events.h` lists `__bpf_trace_<class>` and
  `struct trace_event_raw_<class>` for `resolve_btfids` to resolve at link
  time, under `CONFIG_BPF_EVENTS` with `CONFIG_DEBUG_INFO_BTF`; an unresolved
  name is a warning, and an error under `CONFIG_WERROR`.
- Custom events: `TRACE_CUSTOM_EVENT()` in
  `include/trace/trace_custom_events.h` attaches a second record format to an
  existing tracepoint by name and type-checks it with
  `check_trace_callback_type_<name>()`; a prototype change breaks its build.
  In-tree user and build test: `samples/trace_events/trace_custom_sched.h`
  (`CONFIG_SAMPLE_TRACE_CUSTOM_EVENTS`).
- Tracepoint probe events: `tracepoint_user_register()` in
  `kernel/trace/trace_fprobe.c` registers `__probestub_<name>` as the probe;
  tests are for example `add_remove_tprobe.tc` and
  `add_remove_tprobe_module.tc` under
  `tools/testing/selftests/ftrace/test.d/dynevent/`.
- Sample module as test fixture: several tests in that directory load
  `trace-events-sample`, for example `btf_probe_event.tc`, which enables
  `foo_timer_fn`.
- Rust: `samples/rust/rust_print_events.c` defines `CREATE_RUST_TRACE_POINTS`,
  which makes `define_trace.h` emit `rust_do_trace_<name>()`.
- Runtime verification monitors: tests are in
  `tools/testing/selftests/verification`; there is no selftests/rv directory.
- Unused-tracepoint check: `TRACEPOINT_CHECK()` records each tracepoint that
  has a call site or export; `make UT=1` runs `scripts/tracepoint-update.c`,
  which warns about a defined tracepoint with neither.
- perf tests that read tracepoint fields: for example
  `tools/perf/tests/evsel-tp-sched.c` and
  `tools/perf/tests/openat-syscall-tp-fields.c`.

**Call-site arguments and assignment block**

- Call-site arguments: evaluated on every call, event enabled or not;
  `trace_<name>()` is a static inline that tests the key inside its body.
- With `CONFIG_TRACEPOINTS=n`: `trace_<name>()` is an empty inline and
  arguments with side effects are still evaluated.
- `TP_STRUCT__entry()` source and length expressions: run in
  `trace_event_get_offsets_<class>()`, before the reserve and before
  `TP_fast_assign()`, also when the reserve then fails.
- `do_perf_trace_<class>()`: runs those expressions before it tests whether
  any perf event is attached on this CPU.
- **Potentially unsafe usage**: a function call or side effect in a call-site
  argument.
  - Unsafe: when the work is only for the event and is costly or takes a lock;
    it runs with the event disabled.
  - Safe: pass the object and compute in the block, as `sched_switch` does
    with `__trace_sched_switch_state()` in `include/trace/events/sched.h`.
  - Safe: prepare inside `if (trace_<name>_enabled())`, as
    `__smp_call_single_queue()` in `kernel/smp.c`.
- **Potentially unsafe usage**: dereferencing a pointer argument in
  `TP_fast_assign()` or in a `TP_STRUCT__entry()` expression.
  - Unsafe: when a call site can pass NULL; the probe dereferences it in the
    caller's context.
  - Safe: test it in the expression, as `nfsd_handle_dir_event` in
    `fs/nfsd/trace.h` does for `dir` and `name`.
  - Safe: a NULL source to `__string()`; `__string_src()` and
    `__assign_str()` substitute `EVENT_NULL_STR`.
- **Unsafe usage**: sleeping or faulting in `TP_fast_assign()`, syscall events
  included; `trace_event_raw_event_<class>()` and `perf_trace_<class>()` hold
  `guard(preempt_notrace)()` around it.
  - Safe: per-CPU access without further protection, as `foo_timer_fn` in
    `samples/trace_events/trace-events-sample.h`.

**Skipping argument preparation**

- `TP_CONDITION()` under `CONFIG_LOCKDEP`: `trace_<name>()` evaluates it on
  every call, enabled or not, for the `rcu_is_watching()` warning; when
  enabled it is evaluated twice.
- `TP_CONDITION()` must therefore be free of side effects and safe to evaluate
  with the event disabled.
- Every tracepoint's condition, except the syscall variants
  (`__DECLARE_TRACE_SYSCALL()` takes none), also includes
  `cpu_online(raw_smp_processor_id())`; see `DECLARE_TRACE_EVENT()` in
  `include/linux/tracepoint.h`. A call on an offline CPU runs no probe.
- Condition examples: `smbus_write` in `include/trace/events/smbus.h` and
  `foo_bar_with_cond` in `samples/trace_events/trace-events-sample.h`;
  `include/trace/events/sched.h` has no `TRACE_EVENT_CONDITION()`, only the
  bare tracepoint `sched_set_state` from `DECLARE_TRACE_CONDITION()`, which
  like `DECLARE_TRACE()` adds `_tp` to every generated name
  (`trace_<name>_tp()`, `trace_<name>_tp_enabled()`).
- `trace_call__<name>()` inside an enabled test: fires without testing the
  key again, as `trace_call__csd_queue_cpu()` after
  `trace_csd_queue_cpu_enabled()` in `__smp_call_single_queue()`
  (`kernel/smp.c`).
- `trace_<name>()` inside an enabled test: also correct, it tests the key a
  second time.
- `trace_<name>_enabled()` under `CONFIG_LOCKDEP`: warns once if RCU is not
  watching; `__trace_<name>_enabled()` is the same test without the warning.

**Pointers in the print format**

- `test_event_printk()` failing: warns only (`WARN_ON_ONCE()` plus `pr_warn()`
  with the argument number and the format); it returns `void` and
  `trace_event_raw_init()` returns 0, so the event is registered and usable.
- `test_double_dereference()`: any argument containing `REC->a->b` warns,
  whatever the conversion is.
- `%s` check, `process_string()`: accepts without further inspection any
  argument that contains a function-style call, a string literal, or an index
  using `REC->`. A helper that returns a pointer into freed memory passes.
- `%s` on a bare pointer field: accepted only if the argument text starts with
  `REC->` and names a field (`find_event_field()`); the field gets `needs_test`
  and the event `TRACE_EVENT_FL_TEST_STR`.
- Dereferencing `%p` forms, `process_pointer()`: accepts `&` before `REC->`, an
  array field, `__get_dynamic_array()`, `__get_dynamic_array_len()`,
  `__get_sockaddr()`, `__get_rel_dynamic_array()`,
  `__get_rel_dynamic_array_len()` and `__get_rel_sockaddr()`. `__get_str()`,
  `__get_bitmask()` and `__get_cpumask()` are not accepted there.
- Which `%p` suffixes count as dereferencing: the `case` list under
  `do_pointer:` in `test_event_printk()`.
- `ignore_event()`: for each `needs_test` field, reads the pointer from the
  record and passes it to `trace_safe_str()`. It has nothing to do with
  instances or the persistent buffer; there is no trace_check_vprintf() here.
- `trace_safe_str()` accepts: inside the record, inside `iter->tmp_seq`, kernel
  rodata, a `tracepoint_string()`, or the core area of the event's module.
- `ignore_event()` failing: `WARN_ONCE()`, and for every such record the line
  `EVENT <name>: HAS UNSAFE POINTER FIELD '<field>'` replaces the event text.
- `ignore_event()` is called only from `trace_event_printf()`. The output
  function generated by `DEFINE_EVENT_PRINT()` prints through
  `trace_output_call()`, which does not call it.
- `tp_printk`: `output_printk()` in `kernel/trace/trace.c` calls the same
  output function, so the check still runs; there is no trace_no_verify key.
- **Potentially unsafe usage**: `%s` on a `__field()` that holds a pointer.
  - Unsafe: when the memory can be freed or belongs to another module;
    `trace_safe_str()` rejects it when the trace is read.
  - Safe: `__string()`, `__assign_str()` and `__get_str()`, as `foo_bar` in
    `samples/trace_events/trace-events-sample.h`.
  - Safe: a pointer that `trace_safe_str()` accepts, such as a string literal
    in core kernel rodata or a `tracepoint_string()`, as `rcu_utilization` in
    `include/trace/events/rcu.h`, whose callers pass `TPS()` strings.

## Events at run time

**Soft disable, triggers and filters**

- `EVENT_FILE_FL_TRIGGER_COND` decides the whole order, per file.
  `update_cond_flag()` in `kernel/trace/trace_events_trigger.c` sets it when
  any trigger on the file has a filter, `EVENT_CMD_FL_POST_TRIGGER` or
  `EVENT_CMD_FL_NEEDS_REC`.

| `EVENT_FILE_FL_TRIGGER_COND` | `trace_trigger_soft_disabled()` | `trace_event_buffer_reserve()` | `__event_trigger_test_discard()` |
|---|---|---|---|
| clear | every unpaused trigger, NULL record; then soft disable; then PID filter | PID filter again | soft disable, event filter, PID filter; no triggers |
| set | returns false, nothing runs | PID filter | triggers with the record, each after its own filter, post triggers only marked; then soft disable, event filter, PID filter |

- Soft-disabled file with `EVENT_FILE_FL_TRIGGER_COND` set: the record is
  still reserved and filled, triggers see it, then it is discarded.
- PID-filtered task: triggers still fire when `EVENT_FILE_FL_TRIGGER_COND` is
  clear, and never fire when it is set, because reserve returns NULL first.
- Triggers run before the event filter and see records it will reject.
- Post triggers: `struct event_command` has no `post_trigger` member; the
  flag is `EVENT_CMD_FL_POST_TRIGGER` in `flags` of `struct event_command`,
  set only by `trigger_traceoff_cmd` and `trigger_stacktrace_cmd`.
- `event_triggers_post_call()`: runs after the commit or the discard; picks
  triggers by `trigger_type` bit, so one deferred `ETT_TRACE_ONOFF` selects
  every trigger of that type; it passes NULL for buffer, record and event.
- Per-CPU page `trace_buffered_event`: chosen in
  `trace_event_buffer_lock_reserve()` when the file has
  `EVENT_FILE_FL_SOFT_DISABLED` or `EVENT_FILE_FL_FILTERED`,
  `tr->no_filter_buffering_ref` is zero, the page is allocated,
  `trace_buffered_event_cnt` becomes 1 and `len` fits.
- `EVENT_FILE_FL_TRIGGER_COND` and `EVENT_FILE_FL_PID_FILTER` alone do not
  select the per-CPU page.
- `tr->no_filter_buffering_ref`: raised by hist triggers that use timestamps
  (`tracing_set_filter_buffering()` in `kernel/trace/trace_events_hist.c`).
- `tracing_event_time_stamp()`: for a record in the per-CPU page it returns
  the current buffer time, not a reserve time.
- `temp_buffer` in `kernel/trace/trace.c`: a second fallback, a private ring
  buffer used when the real reserve fails and `EVENT_FILE_FL_TRIGGER_COND` is
  set; `fbuffer->buffer` then points at it and the commit lands there.
- There is no event_trigger_unlock_commit_regs() here;
  `trace_event_buffer_commit()` calls `__event_trigger_test_discard()` in
  `kernel/trace/trace.h` itself.
- There is no call_filter_check_discard() here; records a tracer writes
  itself, for example `trace_function()`, are committed with
  `__buffer_unlock_commit()` and no filter test.
- **Unsafe usage**: returning after a successful
  `trace_event_buffer_reserve()` without commit or discard.
  - Safe: end with `trace_event_buffer_commit()`, or with
    `__trace_event_discard_commit()` as `user_event_ftrace()` does; both
    release the preempt count and `trace_buffered_event_cnt` that reserve
    took.

**Dynamic events**

- `dyn_event_release()`: does not call `is_busy`; it calls `match`, then
  `free`, and learns that an event is in use only from the error `free`
  returns.
- `dyn_event_release()` and `dyn_events_release_all()`: take `event_mutex`
  themselves; a caller that holds it deadlocks.
- `is_busy` and `free` test different things: for example
  `trace_kprobe_is_busy()` tests only `trace_probe_is_enabled()`, while
  `unregister_trace_kprobe()` also tests `trace_event_dyn_busy()`.
- Third busy test inside `free`: `trace_remove_event_call()` returns -EBUSY
  for a non-zero `perf_refcount` (under `CONFIG_PERF_EVENTS`) or a file with
  `EVENT_FILE_FL_ENABLED`; see `probe_remove_event_call()` in
  `kernel/trace/trace_events.c`.
- `dyn_events_release_all()`: the `is_busy` pass frees nothing on -EBUSY, but
  the `free` pass stops at the first error of any kind, with earlier events
  already freed.
- Sibling probes: when `trace_probe_has_sibling()` is true the probe kinds
  skip every busy test and remove that one probe, even if the event is
  enabled.
- `refcnt` in `struct trace_event_call`: opening a tracefs file does not
  raise it; the takers are the callers of `trace_event_try_get_ref()`, for
  example `perf_trace_init()` and `trace_get_event_file()`.
- `dyn_event_add()`: sets `TRACE_EVENT_FL_DYNAMIC` on the call, which is what
  makes `trace_event_try_get_ref()` use `refcnt` and not `module`.
- `create`: the framework calls it under `dyn_event_ops_mutex`, not
  `event_mutex`. A probe kind's own control file gets that lock through
  `dyn_event_create()`, as `create_or_delete_trace_kprobe()` and
  `create_or_delete_trace_uprobe()` do, because the probe log asserts it.
- `create_or_delete_synth_event()`: calls `__create_synth_event()` directly,
  without `dyn_event_ops_mutex`; synthetic events do not use the probe log.

**Probe events**

- `CONFIG_ARCH_HAS_NON_OVERLAPPING_ADDRESS_SPACE`: when it is set,
  `fetch_store_strlen()`, `fetch_store_string()` and `probe_mem_read()` in
  `kernel/trace/trace_probe_kernel.h` read an address below `TASK_SIZE` as
  a user address; when it is not set they read every address as kernel.
- Uprobe: uses only faulting copies, `copy_from_user()`,
  `strncpy_from_user()` and `strnlen_user()`; none of its helpers in
  `kernel/trace/trace_uprobe.c` is a nofault call.
- Uprobe `$comm`: `FETCH_OP_COMM` yields the sentinel `FETCH_TOKEN_COMM`, and
  the string helpers copy `current->comm` directly when they see it.
- When the fetch runs: kprobe, fprobe and eprobe call `store_trace_args()`
  after reserve, into the record, with preemption off; uprobe fetches first
  into `struct uprobe_cpu_buffer` under its mutex, then copies after reserve.
- `struct trace_probe`: has no probe_flags member; the `TP_FLAG_TRACE` and
  `TP_FLAG_PROFILE` bits are in `flags` of `struct trace_probe_event`.
- Tracepoint probes: live in `kernel/trace/trace_fprobe.c` and share its
  `process_fetch_insn()`.
- `error_log` instance: `__trace_probe_log_err()` passes a NULL trace array to
  `tracing_log_err()`, so the entry always goes to the top-level file.
- Unlogged errors: `__trace_probe_log_err()` returns without logging when
  `trace_probe_log_init()` has not run or its own `kzalloc()` fails.

**User-visible formats**

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

## Ring buffer

**Ring buffer structure**

- `rb_get_reader_page()`: only dispatches. `__rb_get_reader_page()` does the
  cmpxchg swap; `__rb_get_reader_page_from_remote()` asks the remote to swap
  and relinks with plain stores, no cmpxchg.
- `cpu_buffer->head_page`: a hint; the write path never writes it.
  `rb_handle_head_page()` moves the `RB_PAGE_HEAD` flag and never this field;
  `rb_set_head_page()` finds the real head from the flag.
- Writer on the reader page: after a swap the writer may still be writing the
  page the reader took (`commit_page == reader_page`).
  `__rb_get_reader_page()` waits up to `USECS_WAIT` for `write` to fall back
  inside the page.
- Write path: takes neither `cpu_buffer->lock` nor `cpu_buffer->reader_lock`,
  including `rb_move_tail()` and `rb_handle_head_page()`.
- `cpu_buffer->pages`: points at one page of the ring; the ring has no list
  head. `list_for_each_entry()` from it skips that page, which is why
  `rb_reset_cpu()` calls `rb_clear_buffer_page()` on `head_page` separately.
- Persistent buffer (`cpu_buffer->ring_meta` set): the writer also updates
  `head_buffer` in `rb_update_meta_head()` and `commit_buffer` in
  `rb_set_commit_to_write()`; the reader updates `buffers[]` in
  `rb_update_meta_reader()`.

**Reading the ring buffer**

- `ring_buffer_read_start()`: raises only `cpu_buffer->resize_disabled`;
  writers keep running. It takes a `gfp_t`, and takes `buffer->mutex` around
  the increment when the flags allow blocking.
- `kernel/trace/trace.c` stops the tracer for an iterator only when
  `TRACE_ITER(PAUSE_ON_TRACE)` is set.
- `ring_buffer_read_page()`: holds `reader_lock` with interrupts off from
  before `rb_get_reader_page()` until it returns, the event-by-event copy
  included.
- `ring_buffer_read_page()` on a mapped, persistent or remote buffer
  (`rb_is_static()`), or with a page of another order: copies, never swaps,
  never refuses for that reason.
- `ring_buffer_map_get_reader()`: reports loss in the new reader sub-buffer
  (`RB_MISSED_EVENTS`, plus `RB_MISSED_STORED` and the count when there is
  room), unless that sub-buffer is also the commit page. It zeroes
  `cpu_buffer->lost_events` before `rb_update_meta_page()` copies that field
  to `reader.lost_events`.
- Unknown loss count: a page whose `commit` carries `RB_MISSED_EVENTS` gives
  `lost_events` of -1. `ring_buffer_read_page()` then stores no count and
  does not add `RB_MISSED_STORED`.
- `ring_buffer_iter_dropped()`: boolean only, no count;
  `ring_buffer_iter_advance()` clears it.
- `ring_buffer_peek()`: leaves `cpu_buffer->lost_events` set, so the same
  loss is reported again; `ring_buffer_consume()` and
  `ring_buffer_read_page()` clear it.
- Iterator after a consuming read or a page removal: `rb_iter_peek()` resets
  it silently; `rb_iter_reset()` zeroes `missed_events`.
- `rb_reader_lock()` in NMI: only tries `reader_lock`; on failure reads
  unlocked and raises `cpu_buffer->record_disabled` for good. Only
  `ring_buffer_consume()`, `ring_buffer_peek()`, `ring_buffer_empty()` and
  `ring_buffer_empty_cpu()` use it.

**Resizing, swapping and resetting**

- `ring_buffer_resize()` returns 0 without resizing: for a NULL buffer, a CPU
  not in `buffer->cpumask`, or one CPU already at the size (tested before
  `resize_disabled`).
- `ring_buffer_resize()` with `RING_BUFFER_ALL_CPUS`: one CPU with
  `resize_disabled` set refuses the whole call with -EBUSY.
- Persistent and remote buffers: `rb_allocate_cpu_buffer()` raises
  `resize_disabled` and never drops it, so resize and order change return
  -EBUSY for the life of the buffer.
- `ring_buffer_subbuf_order_set()`: raises `buffer->record_disabled` once,
  then `synchronize_rcu()`; it does not raise `resize_disabled` or the
  per-CPU `record_disabled`.
- `ring_buffer_subbuf_order_set()` -EINVAL: a NULL buffer, `order < 0`,
  `psize <= BUF_PAGE_HDR_SIZE` or `psize > RB_WRITE_MASK + 1`. An unchanged
  order returns 0 before the busy test.
- Splice reader holding a page of the old order: `ring_buffer_read_page()`
  copies on an order mismatch; `ring_buffer_alloc_read_page()` reallocates.
- `buffer_subbuf_size_write()` in `kernel/trace/trace.c`: calls
  `tracing_stop_tr()` and `trace_access_lock()` around the order change.
- `ring_buffer_swap_cpu()`: there is no RB_FL_SNAPSHOT flag here; it does not
  test `resize_disabled` and calls no `synchronize_rcu()`.
- `ring_buffer_swap_cpu()` -EBUSY: `current_context` non-zero on either CPU
  buffer (not `committing`), or `buffer->resizing` set on either buffer.
- `ring_buffer_swap_cpu()` on a `rb_is_static()` buffer: `WARN_ON_ONCE()` and
  -EBUSY; keeping static buffers away is the caller's job.
- `ring_buffer_swap_cpu()` check order: masks (-EINVAL), static (-EBUSY),
  `nr_pages` and `subbuf_order` (-EINVAL), `record_disabled` (-EAGAIN), then
  the -EBUSY tests.
- `ring_buffer_swap_cpu()` caller: recording must be enabled (else -EAGAIN);
  its one caller, `update_max_tr_single()` in
  `kernel/trace/trace_snapshot.c`, asserts that interrupts are off.
- Without `CONFIG_RING_BUFFER_ALLOW_SWAP`: `ring_buffer_swap_cpu()` is a stub
  in `include/linux/ring_buffer.h` that returns -ENODEV.
- `ring_buffer_reset_cpu()` on a mapped buffer: resets and refreshes the meta
  page through `rb_update_meta_page()`.
- `reset_disabled_cpu_buffer()`: if `committing` is still non-zero it skips
  the reset, and `RB_WARN_ON()` leaves `buffer->record_disabled` raised.
- `rb_reset_cpu()` on a remote buffer: calls `remote->reset`; does nothing
  when that callback is NULL.

**Persistent, mapped and remote buffers**

- `rb_is_static()`: true for a mapped, persistent
  (`struct ring_buffer_cpu_meta`) or remote (`struct ring_buffer_remote`) CPU
  buffer.
- Persistent header check: `rb_meta_init()` tests `magic`, `struct_sizes`,
  `total_size` and `buffers_offset`. There is no rb_meta_valid() or
  rb_cpu_meta_init function.
- `rb_cpu_meta_valid()`: tests `subbuf_size == PAGE_SIZE`, `nr_subbufs`,
  `head_buffer` and `commit_buffer` in range, `buffers[]` in range and
  unique. The `commit` bound is in `__rb_validate_buffer()`.
- `struct ring_buffer_cpu_meta`: `head_buffer` and `commit_buffer` are
  addresses, rebased in `rb_range_meta_init()`; the reader page is
  `buffers[0]`.
- Bad sub-buffer: `__rb_validate_buffer()` empties that page alone and sets
  `commit` to `RB_MISSED_EVENTS`; the rest of the CPU buffer is kept.
- Whole CPU buffer wiped: when `rb_meta_init()` or `rb_cpu_meta_valid()`
  fails, or when `rb_meta_validate_events()` never reaches the commit page.
- Head rewind: `rb_meta_validate_events()` walks back from the head, so pages
  already read in the last boot are readable again; see
  `rb_meta_inject_reader_page()`.
- Persistent in `kernel/trace/trace.c`: `allocate_trace_buffer()` does
  `tr->mapped++`, so snapshots are refused; `trace_ok_for_array()` rejects
  tracers that use a snapshot.
- `tracing_buffers_mmap()`: -ENODEV for `TRACE_ARRAY_FL_MEMMAP` and
  `TRACE_ARRAY_FL_VMALLOC`; other persistent buffers can be mapped.
- `ring_buffer_map()` on an already mapped CPU buffer: maps again and counts
  `user_mapped`; -EBUSY only at `UINT_MAX`. Nothing is read back from user
  space.
- `ring_buffer_map()` errors: -EINVAL for a remote buffer, -E2BIG above
  `rb_static_max_pages()`; `__rb_map_vma()` gives -EPERM for `VM_WRITE`,
  `VM_EXEC` or no `VM_MAYSHARE`.
- Snapshot against mapping: `get_snapshot_map()` in
  `kernel/trace/trace_snapshot.c` returns -EBUSY when `tr->snapshot` is set.
- Remote allocation: `alloc_buffer()` needs 2 to `rb_static_max_pages()`
  pages; `__rb_allocate_pages()` fails unless `nr_page_va` is `nr_pages + 1`.
- Remote page ids: `ring_buffer_desc_page()` bounds them by `nr_page_va`;
  `__rb_get_reader_page_from_remote()` rejects `reader.id > nr_pages` after
  the swap.
- Remote event content: not validated at allocation.
  `rb_meta_validate_events()` returns at once without `ring_meta`;
  `rb_read_remote_meta_page()` copies the counters.
- Remote refusals: `record_disabled` is raised at allocation on the buffer
  and each CPU buffer, so `ring_buffer_lock_reserve()` returns NULL and
  `ring_buffer_write()` -EBUSY; resize and order change -EBUSY.
- Remote data arrival: `ring_buffer_poll_remote()` re-reads the counters from
  the meta page and wakes waiters; `kernel/trace/trace_remote.c` calls it
  from delayed work.

**Writing to the ring buffer**

- `cpu_buffer->nest`: not changed by a reserve; only
  `ring_buffer_nest_start()` and `ring_buffer_nest_end()` change it.
- Length limit: `rb_subbuf_max_data_size()`. `struct trace_buffer` has no
  `max_data_size` field and there is no BUF_MAX_DATA_SIZE; the only disable
  tests in `ring_buffer_lock_reserve()` are the two `record_disabled`
  counters.
- Second reserve in the same context without `ring_buffer_nest_start()`:
  `trace_recursive_lock()` lets the first one through on
  `RB_CTX_TRANSITION`; NULL comes only when that bit is already set.
- Nested reserve inside an open reserve of the same context: bracket it with
  `ring_buffer_nest_start()` and `ring_buffer_nest_end()`, as
  `__synth_event_trace_start()` and `__synth_event_trace_end()` in
  `kernel/trace/trace_events_synth.c` do.
- `ring_buffer_lock_reserve()` also returns NULL:
  - in NMI without `CONFIG_ARCH_HAVE_NMI_SAFE_CMPXCHG` or with
    `CONFIG_GENERIC_ATOMIC64`;
  - with absolute timestamps, when the event length (header included) plus
    `RB_LEN_TIME_EXTEND` exceeds `rb_subbuf_max_data_size()`;
  - on a remote buffer, every time.
- Swapped-buffer test in `rb_reserve_next_event()`: compiled only under
  `CONFIG_RING_BUFFER_ALLOW_SWAP`.
- Retry limit in `rb_reserve_next_event()`: 1000 loops, then `RB_WARN_ON()`
  leaves `buffer->record_disabled` raised.
- `ring_buffer_event_time_stamp()`: valid only between reserve and commit, in
  the context that reserved; it indexes `event_stamp[]` by the nesting level
  in `committing`.
- **Unsafe usage**: enabling preemption or sleeping between
  `ring_buffer_lock_reserve()` and `ring_buffer_unlock_commit()`, a page
  fault that sleeps included.
  - Unsafe: when the code between them can schedule;
    `ring_buffer_unlock_commit()` finds the CPU buffer with
    `raw_smp_processor_id()`; `reset_disabled_cpu_buffer()` and
    `ring_buffer_subbuf_order_set()` rely on `synchronize_rcu()` to have
    waited for every open commit.
  - Safe: copy user data before the reserve, as `tracing_mark_write()` does
    with `trace_user_fault_read()`; `write_marker_to_buffer()` then copies
    from that kernel buffer between reserve and commit.
  - Safe: a user copy that cannot sleep, under `pagefault_disable()`, as
    `copy_nofault()` in `user_event_ftrace()` in
    `kernel/trace/trace_events_user.c`; a failed copy discards the event.

## Instances and tracefs files

**Trace instances**

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

**Locks and their order**

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

**Opening a tracefs file**

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

**Lockdown check on open**

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

**Lifetime of event files**

- `ref` in `struct trace_event_file`: a `refcount_t`.
- `event_file_put()`: frees the structure only when the count reaches zero and
  `EVENT_FILE_FL_FREED` is set. At zero without the flag it warns and does not
  free. It does not free the filter.
- `remove_event_file_dir()`: frees the filter with `free_event_filter()` and
  does not free triggers. On instance removal `event_trace_del_tracer()` calls
  `clear_event_triggers()` first.
- Holders of `ref`: the creation reference, dropped in
  `remove_event_file_dir()`; one taken in `event_create_dir()` for eventfs;
  one for each open through `tracing_open_file_tr()`.
- eventfs reference: dropped by `event_release()`, the `release` callback of
  the `enable` entry, called from `release_ei()` in
  `fs/tracefs/event_inode.c` when the last reference to the
  `struct eventfs_inode` of the event directory goes: after
  `eventfs_remove_dir()` and after every dentry of the directory and its
  files is released. Every open file in the directory holds such a dentry.
- Open method that takes no reference of its own, such as
  `event_trigger_regex_open()` and `trace_format_open()`: the structure stays
  allocated through the eventfs reference.
- Open through `tracing_open_file_tr()`: also holds `tr->ref`, so
  `__remove_instance()` returns -EBUSY and only removal of the event can set
  `EVENT_FILE_FL_FREED` while the file is open.
- Open without it: instance removal can set the flag and free `file->tr` while
  the file is open.
- `event_file_data()`: asserts `event_mutex` with `lockdep_assert_held()` and
  warns when the pointer is NULL or `EVENT_FILE_FL_FREED` is set. It is for a
  second fetch while the mutex is still held after `event_file_file()`
  succeeded, as `f_next()` does after `f_start()`.
- `event_file_file()` and `event_file_data()`: read `i_private` with a plain
  load.
- `id` file: `i_private` holds the event type number, not a pointer;
  `event_id_read()` reads it directly.
- **Potentially unsafe usage**: using the `struct trace_event_file` from the
  inode without `event_mutex` and a non-NULL `event_file_file()`.
  - Unsafe: when the code follows `file->event_call`, `file->filter`,
    `file->system` or `file->triggers`, or follows `file->tr` in a file whose
    open did not take `tr->ref`; these may be freed once
    `remove_event_file_dir()` has run.
  - Safe: when it reads only a member stored in the structure while a
    reference is held, as `event_enable_read()` reads `file->sm_ref` after it
    drops the mutex; `event_file_put()` frees only at zero.
  - Safe: when it passes the value of `file->tr` to `trace_array_get()`, which
    dereferences it only after it matched a listed instance, as
    `tracing_open_file_tr()` does.
  - Safe: when it follows `file->tr` in a file opened through
    `tracing_open_file_tr()`, as `tracing_release_file_tr()` does; the open
    holds `tr->ref`, and `__remove_instance()` returns -EBUSY while
    `tr->ref > 1`.

## Function tracing

**ftrace_ops flags and guarantees**

- `fregs` may be NULL: `arch_ftrace_ops_list_func()` in
  `kernel/trace/ftrace.c` passes NULL when `ARCH_SUPPORTS_FTRACE_OPS` is 0.
  `ftrace_get_regs()` tests for it; `ftrace_regs_get_argument()` and the other
  accessors do not.
- `ftrace_get_regs()` result depends on the arch, not only on the flag:
  - arm64 and riscv define `arch_ftrace_get_regs()` as NULL under
    `CONFIG_DYNAMIC_FTRACE_WITH_ARGS`, so it is always NULL there.
  - without `CONFIG_HAVE_DYNAMIC_FTRACE_WITH_ARGS` the generic
    `arch_ftrace_get_regs()` returns `&arch_ftrace_regs(fregs)->regs` whenever
    `fregs` is non-NULL.
  - the x86, s390 and powerpc definitions return NULL unless a marker field
    shows a full save.
- `FTRACE_OPS_FL_SAVE_ARGS` in `include/linux/ftrace.h`: the flag an owner sets
  to be sure the argument accessors work. It is 0 with
  `CONFIG_DYNAMIC_FTRACE_WITH_ARGS`, else `FTRACE_OPS_FL_SAVE_REGS`.
- **Potentially unsafe usage**: calling `ftrace_regs_get_argument()` or
  another `fregs` accessor in a callback.
  - Unsafe: without `CONFIG_DYNAMIC_FTRACE_WITH_ARGS`, on an ops that did not
    ask for registers; `fregs` can be NULL and the accessor dereferences it.
  - Safe: the ops sets `FTRACE_OPS_FL_SAVE_ARGS`, as `fprobe_ftrace_ops` in
    `kernel/trace/fprobe.c` does; `__register_ftrace_function()` returns
    -EINVAL when that is `FTRACE_OPS_FL_SAVE_REGS` and
    `CONFIG_DYNAMIC_FTRACE_WITH_REGS` is off.
- `ftrace_partial_regs()`: use the return value, not the buffer passed in. The
  generic version ignores the buffer and returns a pointer into `fregs`; arm64
  and riscv copy into the buffer. It is not defined for an arch with
  `CONFIG_HAVE_DYNAMIC_FTRACE_WITH_ARGS` and without
  `CONFIG_HAVE_FTRACE_REGS_HAVING_PT_REGS` unless the arch supplies one.
- `ftrace_partial_regs_update()`: call it after changing the returned
  `struct pt_regs`; see `kernel/trace/bpf_trace.c`.
- `ftrace_regs_set_instruction_pointer()`: an empty macro without
  `CONFIG_HAVE_DYNAMIC_FTRACE_WITH_ARGS`; the ip is not changed.
- `FTRACE_OPS_FL_SAVE_REGS_IF_SUPPORTED`: read only in
  `__register_ftrace_function()`, under
  `#ifndef CONFIG_DYNAMIC_FTRACE_WITH_REGS`. With
  `CONFIG_DYNAMIC_FTRACE_WITH_REGS` it does nothing on its own; an ops that
  wants registers where available sets both flags, as `test_regs_probe` in
  `kernel/trace/trace_selftest.c` has on its second registration.
- Flags that are not the owner's to set, for example:

| Flag | Set by |
|---|---|
| `FTRACE_OPS_FL_DIRECT` | `register_ftrace_direct()` and `update_ftrace_direct_add()`, through `MULTI_FLAGS` |
| `FTRACE_OPS_FL_STUB` | core placeholder ops; `__ftrace_ops_list_func()` skips them |
| `FTRACE_OPS_FL_SUBOP` | `ftrace_startup_subops()` |
| `FTRACE_OPS_FL_GRAPH` | `register_ftrace_graph()` |
| `FTRACE_OPS_FL_ALLOC_TRAMP` | arch code, see `arch/x86/kernel/ftrace.c` |

- `FTRACE_OPS_FL_TRACE_ARRAY`: defined, never set or tested in this tree.
- `FTRACE_OPS_FL_DYNAMIC`: `__register_ftrace_function()` sets it when
  `is_kernel_core_data()` is false for the ops, whatever the owner set. A
  static ops in a module is therefore dynamic. There is no core_kernel_data()
  here.
- **Potentially unsafe usage**: setting `FTRACE_OPS_FL_PID` on an ops.
  - Unsafe: `ops->private` is non-NULL and is not a `struct trace_array *`;
    `ftrace_pids_enabled()` and `ftrace_pid_func()` dereference it as one.
  - Safe: `ops->private` is the trace array, as `ftrace_allocate_ftrace_ops()`
    in `kernel/trace/trace_functions.c` sets it.
- `ftrace_shutdown()` does the wait for the owner: `synchronize_rcu_tasks_rude()`
  then `synchronize_rcu_tasks()`, both unconditional inside
  `if (ops->flags & FTRACE_OPS_FL_DYNAMIC)`. `FTRACE_OPS_FL_RCU` plays no part.
- **Potentially unsafe usage**: freeing the ops, or memory its callback reads,
  right after `unregister_ftrace_function()`.
  - Unsafe: it returned non-zero. `ftrace_shutdown()` returns `-ENODEV` when
    `ftrace_disabled` is set, or the error of `__unregister_ftrace_function()`,
    before the wait.
  - Unsafe: the ops is in core kernel `.data` or `.bss` and
    `FTRACE_OPS_FL_DYNAMIC` is not set on it, so no wait is done.
  - Unsafe: without `CONFIG_DYNAMIC_FTRACE`; `ftrace_shutdown()` is then a macro
    in `kernel/trace/ftrace_internal.h` with no wait of its own, and
    `update_ftrace_function()` waits only when the trace function changes.
  - Safe: it returned 0 for an ops outside core kernel data, with
    `CONFIG_DYNAMIC_FTRACE`; `ftrace_shutdown()` in `kernel/trace/ftrace.c` has
    then done both waits, also when `ftrace_enabled` is 0.

**Function graph infrastructure**

- Non-zero from `entryfunc` does not guarantee a `retfunc` call:
  `__ftrace_return_to_handler()` takes `ftrace_test_recursion_trylock()` and
  skips every `retfunc` when it fails.
- **Unsafe usage**: a `retfunc` that dereferences `fgraph_retrieve_data()`
  without a NULL test. The return side calls `retfunc` for each bit in the
  saved bitmap, and `function_graph_enter_regs()` always sets bit 0, so the
  user in slot 0 can be called for a call its `entryfunc` rejected.
  - Safe: test for NULL and return, as `trace_graph_return()` in
    `kernel/trace/trace_functions_graph.c` does.
- `fgraph_reserve_data()` called twice in one `entryfunc`: the second call is
  not refused, and `fgraph_retrieve_data()` returns only the later
  reservation.
- `FGRAPH_MAX_DATA_SIZE`: `sizeof(long) * 32`; a larger request returns NULL.
- `fregs` in `retfunc`: NULL without `CONFIG_HAVE_FUNCTION_GRAPH_FREGS`. The
  return value is in `retval` of `struct ftrace_graph_ret`, which exists only
  with `CONFIG_FUNCTION_GRAPH_RETVAL`.
- `fregs` in `entryfunc`: NULL when the arch hook uses
  `function_graph_enter()`.
- `ftrace_graph_ret_addr()` matches a frame on `retp`, which must equal the
  `retp` the arch hook gave `function_graph_enter_regs()`. That is the stack
  slot on x86 and the frame pointer value on arm64.
- `idx` only sets where the search starts; `*idx` is a shadow stack offset,
  0 meaning the top. A fresh `idx` of 0 for a single lookup is valid, as
  `function_get_true_parent_ip()` in `kernel/trace/trace_functions.c` does.
- `ftrace_graph_ret_addr()` with a NULL `idx`, or with a `retp` that matches
  no frame: returns `ret` unchanged, also when it is `return_to_handler`.
- There is no HAVE_FUNCTION_GRAPH_RET_ADDR_PTR in this tree.
- x86 unwinders call it through `unwind_recover_ret_addr()` in
  `arch/x86/include/asm/unwind.h`.

**Registered users and shadow stack**

- Limit: `FGRAPH_ARRAY_SIZE` is `FGRAPH_INDEX_BITS`, which is 16.
- No free slot: `register_ftrace_graph()` returns `-ENOSPC`.
- Existing tasks get a shadow stack only when `ftrace_graph_active` becomes 1;
  later registrations only call `init_task_vars()`.
- `SHADOW_STACK_SIZE`: 4096 bytes whatever the page size, from the cache
  `fgraph_stack_cachep`, which `register_ftrace_graph()` creates on its first
  call.
- Shadow stack allocation failure fails registration only in
  `start_graph_tracing()`. `ftrace_graph_init_idle_task()` and
  `ftrace_graph_init_task()` return silently and leave `ret_stack` NULL; that
  task is then not traced.
- `ftrace_graph_exit_task()` is called from `free_task()` in `kernel/fork.c`,
  when the `struct task_struct` is freed.

**Inside an ftrace callback**

- Preemption is disabled only by `trace_test_and_set_recursion()` in
  `include/linux/trace_recursion.h`, which `ftrace_ops_assist_func()`,
  `__ftrace_ops_list_func()` and `ftrace_test_recursion_trylock()` call. A
  trampoline that calls `ops->func` directly leaves preemption as it was.
- `ftrace_ops_assist_func()` and `__ftrace_ops_list_func()` use
  `TRACE_LIST_START`; `ftrace_test_recursion_trylock()` uses
  `TRACE_FTRACE_START`. The bits are separate, so a callback under the core's
  protection can still take its own trylock.
- One nested entry in the same context succeeds, through the transition bit.
  A callback that calls a traced function is re-entered once before the
  trylock returns -1; `trace_selftest_function_recursion()` in
  `kernel/trace/trace_selftest.c` accepts a count of 1 or 2.
- `CONFIG_FTRACE_VALIDATE_RCU_IS_WATCHING`: the trylock, and the core's own
  test, return -1 with a `WARN_ONCE()` when `rcu_is_watching()` is false.
- `FTRACE_OPS_FL_RCU` exists; in this tree only `samples/ftrace/ftrace-ops.c`
  sets it. `perf_ftrace_function_call()` in
  `kernel/trace/trace_event_perf.c` tests `rcu_is_watching()` itself.
- **Potentially unsafe usage**: calling a traceable function from a callback.
  - Unsafe: before recursion protection is held, on an ops without
    `FTRACE_OPS_FL_RECURSION`; this includes the callback itself when it is not
    `notrace` and its own filter covers it.
  - Safe: after `ftrace_test_recursion_trylock()` returned 0 or more, as
    `fprobe_ftrace_entry()` in `kernel/trace/fprobe.c` does.
  - Safe: the ops sets `FTRACE_OPS_FL_RECURSION`, as `test_rec_probe` in
    `kernel/trace/trace_selftest.c` does; `ftrace_ops_get_func()` then
    returns `ftrace_ops_assist_func()`.
- `kernel/trace/Makefile` removes `CC_FLAGS_FTRACE` for the directory, and adds
  it back for the files listed under `CONFIG_FUNCTION_SELF_TRACING`; code in
  those files is traceable.

## Model gaps

### Other mistakes models make

- Models take comments near this code as proof that a tracepoint disables
  preemption. The comment in `trace_event_buffer_reserve()` says the tracepoint
  itself disables preemption, and the one above `event_triggers_call()` says
  `rcu_read_lock_sched()` is held; `__DECLARE_TRACE()` in
  `include/linux/tracepoint.h` does neither.
- Models take `tracing_mark_write()` to copy user memory between reserve and
  commit with a nofault copy. `trace_user_fault_read()`, which does its copy,
  must be entered with preemption disabled, enables preemption while it
  copies, and its buffer is valid only while preemption stays off.
  `ftrace_syscall_enter()` in `kernel/trace/trace_syscalls.c` also reaches it,
  through `syscall_get_data()`, before its reserve.
- Models take `event_mutex` to be the only lock on `ftrace_events`.
  `__register_event()` and the removal paths also hold `trace_event_sem`
  (`kernel/trace/trace_output.c`) for write; it nests inside `event_mutex` and
  `trace_types_lock`, see `trace_remove_event_call()`.
- Models take an fprobe handler to get a `struct pt_regs *`. Both
  `entry_handler` and `exit_handler` of `struct fprobe` get a
  `struct ftrace_regs *`; see `include/linux/fprobe.h`.
- Models take trigger data to be freed in place after a grace period.
  `trigger_data_free()` in `kernel/trace/trace_events_trigger.c` queues it on
  `trigger_data_free_list`; a kthread, or the caller through
  `trigger_data_free_queued_locked()` when no kthread could be created, calls
  `tracepoint_synchronize_unregister()` before the free.
- Models take trace option masks to be named constants. `trace_flags` is a
  `u64` tested with `TRACE_ITER()` (`kernel/trace/trace.h`); apart from
  `TRACE_ITER_SYM_MASK` only the bit numbers have names.
