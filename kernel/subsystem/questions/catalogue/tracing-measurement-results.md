# What the tracing measurement found

Three models were asked the 40 questions in `tracing-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader C was the most current (it
assumed kernels from 6.12 up to 7.0), reader A a little behind it (6.12 to
6.17) and reader B older again (6.10 to 6.12). The hand-written guide was never
checked against current sources, so differences between it and the built guide
are expected and are noted near the end.

All three know what a tracepoint, a trace event, the ring buffer, an
`ftrace_ops` and a probe event are, and how the pieces fit. What they get wrong
is what moved in the last few releases, and in tracing a great deal has: how a
tracepoint protects its probes, the names bare tracepoints get, how filters and
triggers are freed, what fprobe is built on, three new kinds of ring buffer,
and files split out of `kernel/trace/trace.c`. Reader C had most of the
tracepoint changes; readers A and B had none of them.

## What all three readers got wrong

- **Unused tracepoints are detected at build time.** Readers A and B said the
  tree has no such check; reader C invented two Kconfig options for it. The
  check is `TRACEPOINT_CHECK()` in `include/linux/tracepoint.h` and
  `scripts/tracepoint-update.c`, run from `scripts/link-vmlinux.sh` and
  `scripts/Makefile.modfinal`, and it is turned on with `make UT=1`. It only
  warns, and a tracepoint that is only exported counts as used.
- **The snapshot buffer.** Every reader called it max_buffer under
  `CONFIG_TRACER_MAX_TRACE`. In `struct trace_array` it is `snapshot_buffer`
  under `CONFIG_TRACER_SNAPSHOT`, and the snapshot code is in
  `kernel/trace/trace_snapshot.c`.
- **trace_printk and the trace marker.** There is one section,
  `__trace_printk_fmt`; two readers named a second one after its bound
  symbols. A write to `trace_marker` is copied into a per-CPU buffer by
  `trace_user_fault_read()` with preemption enabled and migration disabled,
  then `write_marker_to_buffer()` reserves the event; nobody described that.
  `trace_printk()` output goes to `printk_trace`, which the `trace_printk_dest`
  option moves.
- **Resizing the ring buffer.** All three had `ring_buffer_resize()` disabling
  recording and waiting for a grace period. It takes `cpus_read_lock()` and
  `buffer->mutex`, raises `resizing`, and only page removal disables recording
  on that CPU. `ring_buffer_swap_cpu()` takes no lock and refuses on
  `record_disabled`, `current_context`, `resizing` or `rb_is_static()`.
  `ring_buffer_subbuf_order_set()` is refused through `resize_disabled`.
- **Fixed-page ring buffers.** Invented names (rb_meta_valid(), a mapped field
  in the per-CPU buffer, max_data_size); the counter is `user_mapped`, the
  checks are `rb_meta_init()` and `rb_cpu_meta_valid()`, the size limit is
  `rb_subbuf_max_data_size()`. Remote buffers (`__ring_buffer_alloc_remote()`,
  `kernel/trace/trace_remote.c`) were a guess for reader A, "only a posted
  series" for reader C and unknown to reader B. A mapped reader learns of lost
  events from `RB_MISSED_EVENTS` in the sub-buffer's commit word, not from the
  meta page's lost_events, which `ring_buffer_map_get_reader()` clears first.
- **Freeing filters and triggers.** An old filter goes through
  `call_rcu_tasks_trace()` and then `queue_rcu_work()`
  (`try_delay_free_filter()`), with `tracepoint_synchronize_unregister()` only
  as the fallback when an allocation fails. A removed trigger is handed to a
  kthread that synchronizes and frees (`trigger_data_free()`). Readers gave a
  synchronous wait or a plain call_rcu().
- **`dyn_event_release()` never calls `is_busy()`.** It calls the kind's
  `free()`, which returns `-EBUSY`; only `dyn_events_release_all()` calls
  `is_busy()`. User events are a dynamic event kind, which two readers left
  out.
- **fprobe.** An fprobe with no exit handler is not on the function graph
  infrastructure: `fprobe_is_ftrace()` puts it on the shared `fprobe_ftrace_ops`
  when the architecture passes arguments or registers. Lookup is the rhltable
  `fprobe_ip_table`. `unregister_fprobe()` waits with `synchronize_rcu()`;
  `unregister_fprobe_async()` does not, and no reader described both correctly.
- **ftrace trampolines and the sysctl.** `arch_ftrace_update_trampoline()` runs
  for every ops at registration; `FTRACE_FL_TRAMP` on a record is what depends
  on the ops being alone there. `ftrace_enable_sysctl()` refuses every write of
  0 with `-EOPNOTSUPP`, so `FTRACE_OPS_FL_PERMANENT` now only makes a
  registration fail while ftrace is off. `FTRACE_OPS_FL_DIRECT` is internal.
- **Kernel lockdown** is checked in `tracefs_create_file()` and
  `tracefs_create_dir()` as well as in `tracing_check_open_get_tr()`.
- **eventfs.** A callback return of zero or less hides the file, not only
  zero. Two readers invented names (EVENTFS_TOPLEVEL, create_dentry()).
- **What a core change must keep working.** Every reader listed paths that are
  gone: the rcuidle tracepoint variants, a 32-bit form of the ring buffer
  timestamp, a separate PREEMPT_RT path. None listed the Rust helpers
  (`rust_do_trace_` and the name) generated from the same headers.
- **Runtime verification.** No reader had hybrid automaton monitors
  (`include/rv/ha_monitor.h`) or per-object monitors (`RV_MON_PER_OBJ`).

## What only some readers got wrong

Readers A and B, the facts the hand-written guide is also wrong about:

- **A tracepoint does not disable preemption.** `__DECLARE_TRACE` takes
  `guard(srcu_fast_notrace)(&tracepoint_srcu)`. Both readers said
  guard(preempt_notrace) and an RCU-sched read side, and both then said the
  trace event probe leaves preemption alone. It is the other way round:
  `trace_event_raw_event_` and the name, the perf probe in
  `include/trace/perf.h` and the syscall probes each take
  `guard(preempt_notrace)()` themselves, and BPF disables only migration
  (reader C thought it disabled preemption).
- **`tracepoint_synchronize_unregister()`** calls
  `synchronize_rcu_tasks_trace()` and then `synchronize_srcu(&tracepoint_srcu)`.
  A `synchronize_rcu()` after an unregister no longer waits for probes.
  `release_probes()` uses `call_srcu()` or `call_rcu_tasks_trace()`.
- **The non-blocking form exists**: `call_tracepoint_unregister_atomic()` and
  `call_tracepoint_unregister_syscall()`; `bpf_link_free()` uses the first.
  Both readers said there was none.
- **Bare tracepoints get a `_tp` suffix.** `DECLARE_TRACE()` of foo gives
  trace_foo_tp(), register_trace_foo_tp() and
  EXPORT_TRACEPOINT_SYMBOL_GPL(foo_tp), and nothing calls `DEFINE_TRACE()` by
  hand: `define_trace.h` generates it under `CREATE_TRACE_POINTS`.
- **`trace_call__` and the name** fires a tracepoint without testing the static
  key again, for use after trace_foo_enabled() or `tracepoint_enabled()`.
  Reader A did not recognise it; reader B called it an rcuidle fast path.
- **A format that fails `test_event_printk()` still registers.** The check only
  warns. At read time `ignore_event()` prints "HAS UNSAFE POINTER FIELD" in
  place of the event.
- Which configurations define the page fault tracepoints, and what the RV
  monitor's Kconfig says about it.
- `tracing_open_file_tr()` takes the instance reference first, then under
  `event_mutex` tests `EVENT_FILE_FL_FREED` and takes the file reference.
- Where soft disable, the PID filter and triggers act in the record path, and
  that `trace_buffered_event` is a speed-up used for any filtered or
  soft-disabled file.

Reader B alone:

- **Lock order reversed.** It had `event_mutex` inside `trace_types_lock`; it
  is outside. It also had the dynamic event mutex inside `event_mutex` (it is
  outside), the hotplug lock outside `trace_types_lock` (inside), and
  `tracepoints_mutex` independent (it is taken under `event_mutex`).
- Names that are gone: include/trace/ftrace.h, __DO_TRACE, event_trigger_ops
  and its func callback (triggers call `cmd_ops->trigger()` on
  `struct event_command`), trace_event_raw_output_ for the output function,
  event_id_open(). A filter is a `prog_entry` program, not a predicate array.
- A NULL `__string()` source reserves one byte (it reserves the seven of
  "(null)"); `__string()` evaluates its source once (the measuring step
  expands it twice).
- ftrace recursion bits are per CPU (they are in `current->trace_recursion`);
  a trampoline disables preemption (only `trace_test_and_set_recursion()`
  does); the owner of a dynamic ops must wait for a grace period itself
  (`ftrace_shutdown()` does).
- `ring_buffer_read_start()` disables recording (it raises `resize_disabled`);
  `ring_buffer_read_page()` always swaps pages; a mapped reader advances
  without a system call.
- The function graph shadow stack is allocated on first trace (it is allocated
  for every task when the first user registers); `FGRAPH_ARRAY_SIZE` is 16.

Reader A alone: a tainted module's tracepoints are refused for three taints
(five are exempt, `TAINT_TEST` and `TAINT_LIVEPATCH` among them); module unload
resets every ring buffer (only instances whose `clear_trace` is set);
`TP_fast_assign()` must not take locks (btrfs events take a spinlock there; the
rule is that it must not sleep); `ftrace_release_mod()` frees records under
`ftrace_lock` (it unlinks under the lock and frees after `synchronize_rcu()`).

Reader C alone: `DECLARE_TRACE_SYSCALL()` listed as usable (nothing uses it and
`define_trace.h` has no case for it); `struct trace_entry` members given with
the common_ prefix that only the format file adds; every probe event kind
shares the nofault fetch helpers (uprobe events use `copy_from_user()`).

## What the readers already knew

Readers A and C needed little or nothing on the file map, the layout of a trace
event header, the ring buffer's pages and the lockless page swap, the order of
the global mutexes, the lifetime of an event file, the function graph
interface, and how the probe list is updated. All three knew the field macros
apart from the relative forms, that `__assign_str()` takes one argument, and
that a string is measured in one step and copied in another. These are dropped
from the build set or kept only as the table a reviewer looks things up in.

## Where the hand-written guide is stale

- It says non-faultable tracepoints run their probes under
  `preempt_disable_notrace()` through guard(preempt_notrace). They run under
  `guard(srcu_fast_notrace)(&tracepoint_srcu)` with preemption as the caller
  left it; the trace event, perf and syscall probes disable it themselves.
- It says `tracepoint_synchronize_unregister()` issues
  `synchronize_rcu_tasks_trace()` and synchronize_rcu(). The second call is
  `synchronize_srcu(&tracepoint_srcu)`, so code that frees probe data after a
  bare `synchronize_rcu()` is no longer covered.
- It names `DECLARE_TRACE_SYSCALL` beside `TRACE_EVENT_SYSCALL` as the way a
  faultable tracepoint is declared. Only the second is used, by `sys_enter` and
  `sys_exit`.
- Its quick check asks for exactly one file defining `CREATE_TRACE_POINTS` per
  header, and its own example, `include/trace/events/exceptions.h`, has two,
  one per architecture. The rule is one per built kernel.
- Its field table has four macros. It lacks `__string_len()`,
  `__dynamic_array()`, the bitmask, CPU mask and socket address fields and the
  relative forms, and does not say that `__assign_vstr()` takes a pointer to
  the `va_list`.
- "`TP_fast_assign()` must not contain side effects" is stated as an absolute.
  In-tree events take a spinlock or `rcu_read_lock()` there; what matters is
  that the block runs only when the event is enabled and must not sleep.
- It offers `TRACE_EVENT_CONDITION` as the way to avoid expensive argument
  work. The condition is tested after the static branch but the arguments are
  still evaluated at the call site; the form for that is trace_foo_enabled()
  around the preparation and trace_call__foo() inside it, which the guide
  does not have.
- It says nothing about bare tracepoints taking a `_tp` suffix, about pointers
  in `TP_printk()`, about the non-blocking unregister helpers, or about
  anything else in `kernel/trace/`.
- What it says about the static key, about `__assign_str()` taking only the
  field name, about `might_fault()` and RCU Tasks Trace on the syscall
  tracepoints, and about the page fault tracepoints and
  `kernel/trace/rv/monitors/pagefault/Kconfig` is correct.

## Left out of the build set

The hand-written guide is 585 words, which is under 600, so the build set is
sized to 600 words: 10 of the 40 questions with 550 words of budget, none under
45. The guide is loaded for any patch that calls a `trace_` function,
which is mostly code that defines or fires trace events, not code under
`kernel/trace/`. So the ten are the ones a user of tracepoints needs, which is
also what the old guide was about: the file map, bare tracepoints, the field
macros, the probe's context, strings, pointers in the format, freeing after an
unregister, work in the assignment block, the configurations that lack a
tracepoint, and a short list of what a core change must keep working.

The first cut gave the ten 500 words, 35 to 45 for most, and each of them asks
four or five things, so the answers came out as fragments that needed the
question beside them. Six budgets were raised to 50 or 60 (bare tracepoints,
strings, pointers in the format, freeing after an unregister, the assignment
block, the core change list). No question was added back: the ten with room to
say what each fact is about already fill the size, and everything left out
belongs to a different reader, as follows.

Left out although every reader got them wrong, because they matter only to
someone changing `kernel/trace/` itself: all five ring buffer questions, the
snapshot buffer and the rest of `struct trace_array`, trace_printk and the
marker, filters and triggers, dynamic events, probe events, eventfs, all six
ftrace questions including fprobe, and runtime verification. A guide for that
work would want `tracing.rb-resize`, `tracing.rb-persistent-mapped`,
`tracing.filters-triggers`, `tracing.dynamic-events`, `tracing.fprobe`,
`tracing.ftrace-patching` and `tracing.tracefs-open-usage` first; the ring
buffer and ftrace are each big enough for a guide of their own. Left out as
narrow: unused tracepoints (a warning under `make UT=1` only), tracepoints in
modules, enums in formats, the user-visible formats, documentation and tests.
Left out because readers A and C already knew them: the event header layout,
the code an event expands to, the record path, event file lifetime, the lock
order, how the probe list is updated. Reader B's reversed lock order is the one
loss there that would change a verdict.

Two questions changed after they were measured.
`tracing.tracepoint-availability`
asked for "an in-tree user whose Kconfig entry accounts for that", and one of
the two first builds answered with the architecture dependency alone and left
out `depends on MMU`, which is the half a reviewer misses: on RISC-V the file
that defines the page fault tracepoints is built only with `CONFIG_MMU`. The
question now asks under which options each defining file is built and for a
user whose Kconfig entry accounts for all of them.
`tracing.probe-unregister-usage` asked "what is provided for a caller that
cannot block", which presupposes that something is; on a tree without the two
helpers the right answer is that nothing is. It now asks whether anything is
provided. Both changes are in the measurement set too.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A: 103 corrections, 36% rewritten on average
reader B: 122 corrections, 74% rewritten on average
reader C: 89 corrections, 27% rewritten on average

question                            reader A      reader B      reader C
tracing.core-files                   9% ( 2)      28% ( 4)       1% ( 1)
tracing.docs-and-tests              48% ( 3)      50% ( 4)      45% ( 4)
tracing.probe-context               52% ( 3)      74% ( 4)      28% ( 2)
tracing.probe-unregister-usage      46% ( 3)      79% ( 3)      15% ( 1)
tracing.probe-list-update           29% ( 1)      81% ( 3)       7% ( 1)
tracing.declare-variants            49% ( 2)      80% ( 2)      36% ( 1)
tracing.event-header-layout          4% ( 2)      80% ( 1)      32% ( 1)
tracing.tracepoint-availability     59% ( 2)      82% ( 1)      15% ( 1)
tracing.unused-tracepoints          98% ( 1)      92% ( 1)      41% ( 1)
tracing.module-tracepoints          39% ( 3)      85% ( 3)      40% ( 1)
tracing.event-expansion             38% ( 3)      66% ( 4)      14% ( 2)
tracing.field-macros                21% ( 1)      44% ( 3)      29% ( 3)
tracing.string-fields               32% ( 1)      74% ( 3)      21% ( 1)
tracing.assign-usage                38% ( 6)      80% ( 5)      36% ( 3)
tracing.printk-usage                42% ( 3)      85% ( 3)      22% ( 3)
tracing.enum-symbols                22% ( 1)      82% ( 1)      28% ( 1)
tracing.event-record-path           49% ( 7)      89% ( 3)      13% ( 4)
tracing.event-file-lifetime          3% ( 1)      81% ( 3)       9% ( 3)
tracing.filters-triggers            40% ( 2)      74% ( 3)      31% ( 4)
tracing.dynamic-events              46% ( 5)      68% ( 4)      30% ( 4)
tracing.probe-events                33% ( 4)      64% ( 4)      47% ( 2)
tracing.user-visible-abi            26% ( 1)      70% ( 2)      30% ( 1)
tracing.rb-layout                   16% ( 1)      57% ( 1)       2% ( 1)
tracing.rb-write-usage              53% ( 1)      68% ( 1)      20% ( 3)
tracing.rb-readers                  15% ( 1)      72% ( 2)      45% ( 2)
tracing.rb-resize                   54% ( 1)      81% ( 1)      31% ( 4)
tracing.rb-persistent-mapped        41% ( 1)      84% ( 1)      52% ( 4)
tracing.trace-array                 27% ( 2)      76% ( 5)      41% ( 2)
tracing.tracefs-open-usage          43% ( 3)      89% ( 3)      29% ( 2)
tracing.lock-order                   4% ( 1)      67% ( 6)       4% ( 1)
tracing.trace-printk                46% ( 2)      85% ( 4)      39% ( 2)
tracing.eventfs                     45% ( 2)      90% ( 2)      50% ( 2)
tracing.ftrace-ops                  25% ( 3)      69% ( 4)      22% ( 3)
tracing.ftrace-callback-usage       38% ( 3)      75% ( 3)      33% ( 2)
tracing.ftrace-patching             50% ( 5)      68% ( 3)      58% ( 3)
tracing.ftrace-direct               32% ( 3)      78% ( 5)      29% ( 3)
tracing.fgraph                      26% ( 2)      63% ( 4)       5% ( 1)
tracing.fprobe                      39% ( 3)      73% ( 3)      36% ( 3)
tracing.rv-monitors                 47% ( 7)      81% ( 7)      29% ( 4)
tracing.change-checklist            55% ( 5)      86% ( 3)      19% ( 2)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `tracing.rb-write-usage`, `tracing.rb-resize`, `tracing.rb-persistent-mapped`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `tracing.event-header-layout`, `tracing.event-expansion`, `tracing.event-record-path`, `tracing.event-file-lifetime`, `tracing.dynamic-events`, `tracing.probe-events`, `tracing.user-visible-abi`, `tracing.rb-layout`, `tracing.rb-readers`, `tracing.trace-array`, `tracing.tracefs-open-usage`, `tracing.lock-order`, `tracing.ftrace-ops`, `tracing.ftrace-callback-usage`, `tracing.fgraph`.

## Questions reorganised

Every question now has a section. Subjects: tracepoints, defining a trace event, events at run
time, ring buffer, instances and tracefs files (now with `tracing.event-file-lifetime` and
`tracing.lock-order`), function tracing. Nothing merged or dropped: 30 before and after.
`tracing.change-checklist` lost the ring buffer and sits with the event macros, as the other
consumers of an event header. The questions that asked how a mechanism works inside
(`tracing.event-expansion`, `tracing.event-record-path`, `tracing.dynamic-events`,
`tracing.probe-events`, `tracing.rb-layout`, `tracing.trace-array`, `tracing.fgraph`) now ask the
two or three things a reviewer would get wrong, and `tracing.user-visible-abi` is a hazard.
