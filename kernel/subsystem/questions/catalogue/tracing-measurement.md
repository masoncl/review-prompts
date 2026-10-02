# Questions: Tracing (measurement set)

- guide: tracing.md
- title: Tracing Subsystem

A wide set of questions about the tracing core under `kernel/trace/`: the
tracepoint mechanism in `kernel/tracepoint.c` and `include/linux/tracepoint.h`,
the trace event macros under `include/trace/`, the ring buffer, trace
instances and their tracefs files, ftrace and the function graph tracer,
fprobe, the probe events and the dynamic event framework. It is used to
measure what a model already knows before deciding what the built guide should
spend its words on. The hand-written guide it will replace is 585 words and is
about three things only (string fields in trace events, the context a
tracepoint probe runs in, and the configuration a tracepoint depends on), so
most of what is asked here cannot be in the built guide; the point is to find
which few things must be. The latency tracers, blktrace, the BPF side in
`kernel/trace/bpf_trace.c` and the individual runtime verification monitors are not
covered. The trimmed set a guide is built from is `../tracing.md`. Format:
`../../../docs/subsystem-questions.md`.

# Where to look

## tracing.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 120

Which files hold the tracepoint core, the macros that turn a trace event
header into code, the ring buffer, trace instances and the main tracefs files,
the trace event core with its filters, triggers and histograms, ftrace, the
function graph infrastructure, fprobe, the probe events and what they share,
the dynamic event framework, user events, tracefs itself and runtime
verification? A table. Start from `kernel/trace/`, `include/trace/` and
`fs/tracefs/`.

## tracing.docs-and-tests: Documentation and tests

- section: Finding your way
- relevance: 3 - a change has to be run against the right tests
- words: 90

Which files under `Documentation/trace/` are the authority on tracepoints, on
trace events, on the ring buffer design and on using ftrace from kernel code,
and which tests exercise this code: the selftest directories under
`tools/testing/selftests/`, the tests that run at boot and the configuration
options that build them, and the sample modules under `samples/`?

# Tracepoints

## tracing.probe-context: Probe calling context

- section: Tracepoints
- relevance: 5 - decides what a probe may do and what an unregister must wait for
- words: 100

In what context does a tracepoint probe run? What protects the array of probes
and each probe's data while the probes are being called, is preemption
disabled by the tracepoint itself, and may a probe sleep or take a page fault?
How does the answer differ for the system call tracepoints? Start from
`__DECLARE_TRACE` and `__DECLARE_TRACE_SYSCALL` in
`include/linux/tracepoint.h`.

## tracing.probe-unregister-usage: Freeing after unregistering a probe

- section: Tracepoints
- relevance: 5 - a use after free that no diff shows
- words: 100

After a probe is unregistered from a tracepoint, what usage of the probe's
data, or of a module that holds the probe function, is unsafe, and what that
looks similar is correct? What exactly does
`tracepoint_synchronize_unregister()` wait for, and is anything provided for a
caller that cannot block? Name in-tree code that shows the correct form.

## tracing.probe-list-update: Updating the probe list

- section: Tracepoints
- relevance: 3 - the core's own invariant, touched rarely and subtle
- words: 100

How is a tracepoint's list of probes changed while the tracepoint may be
firing on other CPUs: which lock serialises updates, how is the old array
freed, when is the call made directly to a single probe and when through an
iterator, and what keeps the function that is called consistent with the data
pointer it is given across those transitions? Start from
`tracepoint_add_func()` and `tracepoint_remove_func()` in
`kernel/tracepoint.c`.

## tracing.declare-variants: Tracepoints without trace events

- section: Tracepoints
- relevance: 4 - the call site's name and the export rules are easy to get wrong
- words: 100

Which macros declare and define a bare tracepoint that has no trace event
behind it, and what name does a call site use to fire one? How does code in
another file or in a module get to fire it or attach a probe to it, how is a
tracepoint tested for being enabled from a header file, and what is
`trace_call__` followed by the name for? Start from `DECLARE_TRACE` in
`include/linux/tracepoint.h` and `include/linux/tracepoint-defs.h`.

## tracing.event-header-layout: Trace event headers

- section: Tracepoints
- relevance: 4 - a wrong header builds and then fails to link or defines twice
- words: 100

How is a trace event header laid out and turned into code: what do
`TRACE_SYSTEM`, the include guard with `TRACE_HEADER_MULTI_READ`,
`TRACE_INCLUDE_PATH` and `TRACE_INCLUDE_FILE` each do, where is
`CREATE_TRACE_POINTS` defined and in how many files for one header, and what
goes wrong when it is defined in none or in two? Start from
`include/trace/define_trace.h`.

## tracing.tracepoint-availability: Configurations that lack a tracepoint

- section: Tracepoints
- relevance: 4 - a dependency that is missing only shows on a rare configuration
- words: 100

A tracepoint is declared in a header that any file can include. What decides
whether it is actually defined in a given kernel configuration, what happens at
build or link time to code that registers a probe on one that is not, and how
does a reviewer find the configuration options it depends on? Give an in-tree
tracepoint whose definition lives in architecture code, say under which options
each file that defines it is built, and name an in-tree user whose Kconfig
entry accounts for all of them. Start from `kernel/trace/rv/monitors/`.

## tracing.unused-tracepoints: Tracepoints that are never called

- section: Tracepoints
- relevance: 2 - a build warning a new tracepoint can trip
- words: 60

Does the build detect a tracepoint that is defined but never called from
anywhere, and one that is only exported? How is it done and how is it turned
on? Start from `TRACEPOINT_CHECK` and `scripts/tracepoint-update.c`. If this
tree has neither, say so and stop.

## tracing.module-tracepoints: Tracepoints and events in modules

- section: Tracepoints
- relevance: 3 - load and unload order is where probes and events dangle
- words: 90

How do the tracepoints and the trace events that a module defines become
visible when it loads and go away when it unloads, which modules are refused,
and what happens to events already recorded in the ring buffers when a module
that defined events is removed? Start from `tracepoint_module_coming()` and
`trace_module_notify()`.

# Trace events

## tracing.event-expansion: Code generated for an event

- section: Defining a trace event
- relevance: 4 - explains what each macro argument is compiled into
- words: 110

What does one `TRACE_EVENT()` generate when its header is read with
`CREATE_TRACE_POINTS` defined: which structures and functions, in which of the
stages under `include/trace/stages/`, and which of them are shared when
several events are made from one `DECLARE_EVENT_CLASS()` with `DEFINE_EVENT()`?
Which function is the probe that writes the record, and does it change the
preemption state? Start from `include/trace/trace_events.h`.

## tracing.field-macros: Field and assignment macros

- section: Defining a trace event
- relevance: 5 - the argument lists have changed and old forms no longer build
- words: 130

Give a table of the macros used inside `TP_STRUCT__entry()` to declare fields
(fixed size, arrays, dynamic arrays, strings of each kind, bitmasks, CPU masks,
socket addresses, and the forms whose offset is relative), and for each the
macro used in `TP_fast_assign()` to fill it and the one used in `TP_printk()`
to read it, with the arguments each takes in this tree. Start from
`include/trace/stages/stage6_event_callback.h` and
`include/trace/stages/stage3_trace_output.h`.

## tracing.string-fields: Recording a string

- section: Defining a trace event
- relevance: 5 - truncated or overrun strings come from misunderstanding this
- words: 100

How is a dynamic-length string recorded by a trace event: at what point is its
length measured and at what point is it copied, how does the copy step find
the source, what is recorded when the source is NULL, what happens if the
source changes between the two steps, and what bounds a string that is
formatted from a `va_list`? Start from
`include/trace/stages/stage5_get_offsets.h` and
`include/trace/stages/stage6_event_callback.h`.

## tracing.assign-usage: Work done in the assignment block

- section: Defining a trace event
- relevance: 4 - behaviour that differs when tracing is on is very hard to debug
- words: 90

What usage of `TP_fast_assign()`, or of the arguments passed to a tracepoint
at its call site, is unsafe or wasteful, and what that looks similar is
correct? When are the arguments at the call site evaluated, when does the
assignment block run, and which forms let a caller skip expensive argument
preparation or skip the event on a condition? Name in-tree code that shows the
correct forms.

## tracing.printk-usage: Pointers in the print format

- section: Defining a trace event
- relevance: 5 - the record is printed long after the object may be gone
- words: 110

What usage of a pointer in `TP_printk()` is unsafe, and what that looks
similar is correct? Which format specifiers and which kinds of string argument
are accepted, what checks an event's format when the event is registered and
what checks a string again when the trace is read, and what is the result of
failing each check? Start from `test_event_printk()` in
`kernel/trace/trace_events.c` and `ignore_event()` in `kernel/trace/trace.c`.

## tracing.enum-symbols: Enums and symbolic names in formats

- section: Defining a trace event
- relevance: 3 - user space tools cannot parse a format that names an enum
- words: 70

Why does an enum or a `sizeof` used inside `TP_printk()` need to be declared
to the tracing core, with which macros, and what does the core do with the
declaration? Start from `TRACE_DEFINE_ENUM` and `trace_event_update_all()`.

## tracing.event-record-path: Recording an event

- section: Events at run time
- relevance: 4 - filters, triggers and soft disable all act inside this path
- words: 110

Trace the path of one trace event from its probe being called to the record
being visible to a reader: where are soft disable, PID filtering, triggers and
the event filter each applied, when is a record written to a temporary per-CPU
buffer instead of the ring buffer and why, and how is a record that the filter
rejects thrown away? Start from `trace_event_buffer_reserve()` and
`trace_event_buffer_commit()`.

## tracing.event-file-lifetime: Lifetime of event files

- section: Events at run time
- relevance: 4 - a tracefs file can be open when its event or instance is removed
- words: 100

What keeps a `struct trace_event_file` alive while one of its tracefs files is
open, what marks it as gone when its event or its instance is removed, and
what must a file operation check before using it? What usage of the pointer
stored in the inode is unsafe, and what is correct? Start from
`event_file_get()`, `event_file_put()` and `remove_event_file_dir()`.

## tracing.filters-triggers: Filters and triggers

- section: Events at run time
- relevance: 3 - each is replaced and freed while events are firing
- words: 100

Where are event filters and event triggers implemented, how is each attached to
an event file, what runs when an event fires, and how is an old filter or a
removed trigger freed safely while the event may be firing on another CPU?
Which trigger commands exist? Start from `filter_match_preds()`,
`event_triggers_call()` and `struct event_command`.

## tracing.dynamic-events: Dynamic events

- section: Events at run time
- relevance: 4 - every probe event and synthetic event is created and removed through it
- words: 110

What is the dynamic event framework: which kinds of event register with it,
which tracefs files create and remove them, which callbacks does a kind
supply, which lock protects the list, and what stops an event that is in use
from being removed? Start from `struct dyn_event_operations` and
`dyn_event_release()` in `kernel/trace/trace_dynevent.c`.

## tracing.probe-events: Probe events

- section: Events at run time
- relevance: 4 - argument fetching reads arbitrary memory in any context
- words: 120

What do the kprobe, uprobe, fprobe, tracepoint-probe and event-probe trace
events share: which structure describes a probe and its arguments, how is an
argument specification compiled and then executed when the probe fires, how are
memory and strings read without faulting, and where do parse errors go so that
a user can read them? Start from `struct trace_probe`,
`traceprobe_parse_probe_arg()` and `process_fetch_insn()`.

## tracing.user-visible-abi: User-visible formats

- section: Events at run time
- relevance: 4 - tools parse these files and buffers directly
- words: 90

Which parts of tracing are read by user space tools in binary or parsed form,
so that a change to them breaks those tools: the per-event `format` files, the
files describing the ring buffer page and event headers, the raw per-CPU
buffer files, the common fields at the start of every record? Which in-tree
and out-of-tree tools read them?

# The ring buffer

## tracing.rb-layout: Ring buffer structure

- section: Ring buffer
- relevance: 4 - nothing else about the buffer makes sense without it
- words: 120

What is a ring buffer made of: the per-CPU buffers, the list of sub-buffers,
the head, tail, commit and reader pages and what each means, how flags stored
in list pointers let a writer and a reader move pages without a lock, and
which fields of `struct ring_buffer_per_cpu` a writer touches as against a
reader? Start from `struct buffer_page` and `rb_get_reader_page()` in
`kernel/trace/ring_buffer.c` and `Documentation/trace/ring-buffer-design.rst`.

## tracing.rb-write-usage: Writing to the ring buffer

- section: Ring buffer
- relevance: 5 - every producer has to follow these rules
- words: 110

What are the rules for a writer: what state is the CPU left in between
`ring_buffer_lock_reserve()` and `ring_buffer_unlock_commit()`, what may be
done between them, how are writes from an interrupt or NMI that lands on a
writer handled, how many levels may nest, what is the largest event, and when
does a reserve return NULL? What usage is unsafe, and what that looks similar
is correct?

## tracing.rb-readers: Reading the ring buffer

- section: Ring buffer
- relevance: 4 - four kinds of reader with different locking
- words: 110

Which ways are there to read a ring buffer (consuming, the non-consuming
iterator, whole sub-buffers for splice, memory mapping), which function starts
each, what does each hold or disable while it reads, and how does a reader
learn that events were lost? Start from `ring_buffer_consume()`,
`ring_buffer_read_start()`, `ring_buffer_read_page()` and `ring_buffer_map()`.

## tracing.rb-resize: Resizing, swapping and resetting

- section: Ring buffer
- relevance: 4 - these change pages under writers and readers
- words: 110

How are resizing a buffer, changing its sub-buffer order, swapping a per-CPU
buffer with another buffer's and resetting a buffer each made safe against
writers and readers that are running: which locks and counters, what waits for
what, and in which states is each refused? Start from `ring_buffer_resize()`,
`ring_buffer_subbuf_order_set()`, `ring_buffer_swap_cpu()` and
`ring_buffer_reset_cpu()`.

## tracing.rb-persistent-mapped: Persistent, mapped and remote buffers

- section: Ring buffer
- relevance: 4 - new kinds of buffer whose pages the kernel does not own in the usual way
- words: 120

Which kinds of ring buffer have a fixed set of pages: one placed in reserved
memory so that it survives a reboot, one mapped into user space, one written
by something other than this kernel? For each, which function creates it, what
metadata describes it, how is its content checked before it is trusted, and
which operations are refused while it is in that state? Start from
`__ring_buffer_alloc_range()`, `ring_buffer_map()` and
`__ring_buffer_alloc_remote()`.

# Instances and tracefs

## tracing.trace-array: Trace instances

- section: Instances and tracefs
- relevance: 4 - almost every tracefs file acts on one of these
- words: 120

What is a `struct trace_array`: which buffers does it own and what are they
called, what is per instance and what is global, how are instances created (by
user space, from the kernel command line, by kernel code) and destroyed, what
counts references to one, and when does removing one fail? Start from
`struct trace_array` in `kernel/trace/trace.h` and `trace_array_get_by_name()`.

## tracing.tracefs-open-usage: Opening a tracefs file

- section: Instances and tracefs
- relevance: 5 - a missing reference or lockdown check is a recurring bug
- words: 100

What must the open and release methods of a tracefs file that acts on an
instance do, and which helpers do it? What usage of the instance pointer
stored in the inode is unsafe, and what that looks similar is correct? Where
is kernel lockdown checked? Start from `tracing_check_open_get_tr()`,
`tracing_open_generic_tr()` and `tracing_open_file_tr()`.

## tracing.lock-order: Locks and their order

- section: Instances and tracefs
- relevance: 5 - several global mutexes nest and a new path can invert them
- words: 110

Which global locks does tracing use and what does each protect:
`trace_types_lock`, `event_mutex`, `ftrace_lock`, the mutex in
`kernel/tracepoint.c`, the dynamic event mutex, the CPU hotplug lock,
`text_mutex`? In which order do they nest where two are held together? Name
the functions that show each ordering.

## tracing.trace-printk: trace_printk and the trace marker

- section: Instances and tracefs
- relevance: 3 - debugging aids that must not be left in a patch
- words: 90

What does using `trace_printk()` anywhere in the kernel or in a module cause at
boot or at module load, which buffers does it allocate, which instance does
its output go to, and how do writes to the `trace_marker` file get from user
memory into the ring buffer? Start from `trace_printk_init_buffers()` and
`tracing_mark_write()`.

## tracing.eventfs: eventfs

- section: Instances and tracefs
- relevance: 3 - the events directory is not made of ordinary dentries
- words: 100

How is the `events` directory of an instance implemented: what is a
`struct eventfs_inode`, when are dentries and inodes for an event's files
created, what do the callbacks passed in a `struct eventfs_entry` do, how are
ownership and mode changes remembered, and how is a directory removed while
files under it are open? Start from `fs/tracefs/event_inode.c`.

# ftrace

## tracing.ftrace-ops: ftrace_ops

- section: Function tracing
- relevance: 4 - the interface every function hook uses
- words: 120

What is the signature of an ftrace callback in this tree and what is the last
argument, how does a callback get at registers or function arguments, and what
do the flags an `ftrace_ops` owner may set mean (saving registers, recursion
protection, RCU, IP modification, permanent, direct)? How are the functions an
ops applies to chosen, and what must happen before a dynamically allocated ops
is freed? Start from `struct ftrace_ops` in `include/linux/ftrace.h`.

## tracing.ftrace-callback-usage: Inside an ftrace callback

- section: Function tracing
- relevance: 5 - a callback runs anywhere, including where RCU is not watching
- words: 100

In what contexts can an ftrace callback be called, is preemption disabled for
it, and what protects it from recursing into itself? What usage inside a
callback is unsafe, and what that looks similar is correct? Which functions
must be marked so that they are never traced? Start from
`ftrace_test_recursion_trylock()` and `ftrace_ops_assist_func()`.

## tracing.ftrace-patching: Patching call sites

- section: Function tracing
- relevance: 3 - module load, init memory and live updates all go through it
- words: 110

How are the call sites at function entry recorded, enabled and disabled: what
is a `struct dyn_ftrace` and its flags, which locks are held while code is
modified, how does an ops get its own trampoline, and how are the records for
a module's text and for init memory added and then removed? Start from
`ftrace_startup()`, `ftrace_module_init()`, `ftrace_release_mod()` and
`ftrace_free_init_mem()`.

## tracing.ftrace-direct: Direct calls and IP modification

- section: Function tracing
- relevance: 3 - live patching and BPF trampolines share call sites
- words: 100

What is a direct call, which functions register, modify and remove one, how
many users that modify the instruction pointer can share one function, and how
do a direct-call user and an IP-modifying user on the same function negotiate?
Start from `register_ftrace_direct()`, `FTRACE_OPS_FL_IPMODIFY` and the
`ops_func` callback of `struct ftrace_ops`.

## tracing.fgraph: Function graph infrastructure

- section: Function tracing
- relevance: 4 - several users now share one return hook and one shadow stack
- words: 120

How does the function graph infrastructure let several users hook function
entry and return: what does a user register and with what callback signatures,
what does the entry callback's return value decide, how is per-call data passed
from entry to return, how many users can there be, where is the shadow stack
kept and when is it allocated for a task, and how must a stack unwinder find
the real return address? Start from `struct fgraph_ops`,
`function_graph_enter_regs()` and `ftrace_graph_ret_addr()`.

## tracing.fprobe: fprobe

- section: Function tracing
- relevance: 3 - the mechanism behind function entry and exit probe events
- words: 100

What is an fprobe built on in this tree, what are the signatures of its entry
and exit handlers, how does an entry handler pass data to the exit handler or
cancel it, how are probes found when a function is hit, and what may be freed
after each of the unregister functions returns? Start from `struct fprobe` and
`kernel/trace/fprobe.c`.

# Runtime verification and changes

## tracing.rv-monitors: Runtime verification monitors

- section: Beyond the core
- relevance: 2 - a separate directory whose monitors are tracepoint users
- words: 80

What is a runtime verification monitor, how does one attach to the tracepoints
it needs and detach from them, what kinds of monitor are there, and what does
a monitor's Kconfig entry have to say about the tracepoints it uses? Start
from `rv_register_monitor()`, `rv_attach_trace_probe()` and
`kernel/trace/rv/Kconfig`.

## tracing.change-checklist: Changing the core

- section: Beyond the core
- relevance: 4 - the macros and the buffer have more consumers than the trace file
- words: 100

What must a change to the trace event macros, to the tracepoint call site or to
the ring buffer keep working besides ftrace's own trace file: which other
consumers are generated from the same event headers, which architectures and
configurations take a different path, and which tests would show a
regression?
