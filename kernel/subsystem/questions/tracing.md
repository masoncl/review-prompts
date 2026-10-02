# Questions: Tracing Subsystem

- guide: tracing.md
- title: Tracing Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/tracing-measurement.md` is the
wider set the readers were measured on and `catalogue/tracing-measurement-results.md` says what
they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## tracing.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## tracing.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup

A table and nothing else, job to file: the tracepoint core; the macros that turn a trace event
header into code; the ring buffer; trace instances and the main tracefs files; snapshots; the
trace event core, and its filters, triggers and histograms; ftrace; the function graph
infrastructure; fprobe; the probe events and what they share; the dynamic event framework; user
events; tracefs itself; runtime verification. Start from `kernel/trace/`, `include/trace/` and
`fs/tracefs/`.

# Tracepoints

## tracing.declare-variants: Tracepoints without trace events

- section: Tracepoints
- relevance: 4 - the call site's name and the export rules are easy to get wrong

What does `DECLARE_TRACE()` name the function that a call site uses to fire a bare tracepoint, one
with no trace event behind it? What must the file that defines the tracepoint export so that a
module can fire it or attach a probe to it? What is `trace_call__` followed by the name for? Start
from `DECLARE_TRACE` in `include/linux/tracepoint.h` and `include/linux/tracepoint-defs.h`.

## tracing.header-enabled-test: Enabled test in headers

- section: Tracepoints
- relevance: 4 - a header file cannot include the header that declares the tracepoint

How does code in a header file test whether a tracepoint is enabled, and what are the requirements
for firing the tracepoint after that test? Start from `include/linux/tracepoint-defs.h`.

## tracing.probe-context: Probe calling context

- section: Tracepoints
- relevance: 5 - decides what a probe may do and what an unregister must wait for

What protects the array of probes and each probe's data while a tracepoint calls its probes, and
what does the tracepoint guarantee a probe about preemption? May a probe sleep or take a page
fault, for a tracepoint declared with `__DECLARE_TRACE` and for one declared with
`__DECLARE_TRACE_SYSCALL`? Start from `__DECLARE_TRACE` and `__DECLARE_TRACE_SYSCALL` in
`include/linux/tracepoint.h`.

## tracing.tracepoint-availability: Configurations that lack a tracepoint

- section: Tracepoints
- relevance: 4 - a dependency that is missing only shows on a rare configuration

A tracepoint is declared in a header that any file can include. What decides whether it is defined
in a given kernel configuration, and what happens at build or link time to code that registers a
probe on one that is not? Name an in-tree tracepoint whose definition lives in architecture code,
and an in-tree user whose Kconfig entry accounts for the options that definition depends on. Start
from `kernel/trace/rv/monitors/`.

## tracing.probe-unregister-usage: Freeing after unregistering a probe

- section: Tracepoints
- relevance: 5 - a use after free that no diff shows

After `tracepoint_probe_unregister()` returns, what are the requirements for freeing the probe's
data, or for unloading a module that holds the probe function, in order to assure safe usage? What
exactly does `tracepoint_synchronize_unregister()` wait for, and is anything provided for a caller
that cannot block? Name in-tree code that shows it.

# Defining a trace event

## tracing.event-header-layout: Trace event headers

- section: Defining a trace event
- relevance: 4 - a wrong header builds and then fails to link or defines twice

In a trace event header, what do `TRACE_SYSTEM`, the include guard with
`TRACE_HEADER_MULTI_READ`, `TRACE_INCLUDE_PATH` and `TRACE_INCLUDE_FILE` each do? Where is
`CREATE_TRACE_POINTS` defined and in how many files for one header, and what goes wrong when it
is defined in none or in two? Start from `include/trace/define_trace.h`.

## tracing.event-expansion: Code generated for an event

- section: Defining a trace event
- relevance: 4 - the probe is a generated function, and a class shares most of the code

Which generated function is the probe that writes an event's record, and does it change the
preemption state? What do several events made from one `DECLARE_EVENT_CLASS()` with
`DEFINE_EVENT()` share, as against a `TRACE_EVENT()` each? Start from
`include/trace/trace_events.h` and the stages under `include/trace/stages/`.

## tracing.field-macros: Field and assignment macros

- section: Defining a trace event
- relevance: 5 - the argument lists have changed and old forms no longer build

What do the macros that declare a dynamically sized field in `TP_STRUCT__entry()` require of the
macro that fills the field in `TP_fast_assign()` and of the macro that reads it in `TP_printk()`?
Which arguments does each take in this tree? Start from
`include/trace/stages/stage6_event_callback.h` and `include/trace/stages/stage3_trace_output.h`.

## tracing.string-fields: Recording a string

- section: Defining a trace event
- relevance: 5 - truncated or overrun strings come from misunderstanding this

At what point does a trace event measure the length of a dynamic-length string and at what point
does it copy the string, and how does the copy step find the source? What does the event guarantee
about the record when the source is NULL, or changes between the two steps? Start from
`include/trace/stages/stage5_get_offsets.h` and `include/trace/stages/stage6_event_callback.h`.

## tracing.vstring-bound: Formatted string fields

- section: Defining a trace event
- relevance: 5 - a formatted string is measured in one step and written in another

What bounds the length of a string that a trace event formats from a `va_list` with `__vstring()`
and `__assign_vstr()`? Start from `include/trace/stages/stage5_get_offsets.h` and
`include/trace/stages/stage6_event_callback.h`.

## tracing.change-checklist: Other consumers of event headers

- section: Defining a trace event
- relevance: 4 - the macros have more consumers than the trace file

Besides ftrace's own trace file, which consumers are generated from the same event headers and
tracepoint call sites, so that a change to the macros or to an event's arguments has to build and
work for each? Which in-tree tests exercise each consumer?

## tracing.assign-usage: Call-site arguments and assignment block

- section: Defining a trace event
- relevance: 4 - behaviour that differs when tracing is on is very hard to debug

When are the arguments at a tracepoint's call site evaluated, and when does the `TP_fast_assign()`
block run? What are the requirements for the call-site arguments and for the code in
`TP_fast_assign()` in order to assure safe usage? Name in-tree code that shows it.

## tracing.skip-forms: Skipping argument preparation

- section: Defining a trace event
- relevance: 4 - argument preparation that runs while the tracepoint is off costs every caller

What does `TRACE_EVENT_CONDITION()` let an event skip, and what does the enabled test that every
tracepoint declares let a call site skip? What does each require of the call site? Name in-tree
code that shows it. Start from `include/linux/tracepoint.h`.

## tracing.printk-usage: Pointers in the print format

- section: Defining a trace event
- relevance: 5 - the record is printed long after the object may be gone

What are the requirements for a pointer argument of `TP_printk()`, a string argument included, in
order to assure safe usage? What does `test_event_printk()` check when an event is registered and
what does `ignore_event()` check when the trace is read, and what is the result of failing each?
Start from `test_event_printk()` in `kernel/trace/trace_events.c` and `ignore_event()` in
`kernel/trace/trace.c`.

# Events at run time

## tracing.event-record-path: Soft disable, triggers and filters

- section: Events at run time
- relevance: 4 - filters, triggers and soft disable all act inside this path

Between a trace event's probe being called and its record being visible to a reader, where are
soft disable, PID filtering, triggers and the event filter each applied, so that a change to one
knows what has already run? When is a record written to a temporary per-CPU buffer in place of
the ring buffer and why, and how is a record that the filter rejects thrown away? Start from
`trace_event_buffer_reserve()` and `trace_event_buffer_commit()`.

## tracing.dynamic-events: Dynamic events

- section: Events at run time
- relevance: 4 - every probe event and synthetic event is created and removed through it

What must a kind of event supply in `struct dyn_event_operations` to register with the dynamic
event framework? Which lock protects the list of dynamic events, and how does the framework find
out that an event is in use when it is asked to remove the event? Start from `struct
dyn_event_operations` and `dyn_event_release()` in `kernel/trace/trace_dynevent.c`.

## tracing.probe-events: Probe events

- section: Events at run time
- relevance: 4 - argument fetching reads arbitrary memory in any context

When a kprobe, uprobe, fprobe, tracepoint-probe or event-probe trace event fires, how are memory
and strings read for its arguments without faulting, and does any kind read them another way?
Where do parse errors in an argument specification go so that a user can read them? Start from
`struct trace_probe`, `traceprobe_parse_probe_arg()` and `process_fetch_insn()`.

## tracing.user-visible-abi: User-visible formats

- section: Events at run time
- relevance: 4 - tools parse these files and buffers directly

What does the tree promise user space tools about the layout of an event's record, its common
fields and its print format included, and about the ring buffer's page and event headers? Which
tracefs files describe each of them to a tool?

# Ring buffer

## tracing.rb-layout: Ring buffer structure

- section: Ring buffer
- relevance: 4 - nothing else about the buffer makes sense without it

What do the head, tail, commit and reader pages of a per-CPU buffer each mean, how do flags
stored in list pointers let a writer and a reader move pages without a lock, and what may a
writer touch as against a reader? Start from `struct buffer_page` and `rb_get_reader_page()` in
`kernel/trace/ring_buffer.c` and `Documentation/trace/ring-buffer-design.rst`.

## tracing.rb-readers: Reading the ring buffer

- section: Ring buffer
- relevance: 4 - four kinds of reader with different locking

A table of the ways to read a ring buffer to choose among (consuming, the non-consuming iterator,
whole sub-buffers for splice, memory mapping): what each holds or disables while it reads, and
how each learns that events were lost. Start from `ring_buffer_consume()`,
`ring_buffer_read_start()`, `ring_buffer_read_page()` and `ring_buffer_map()`.

## tracing.rb-resize: Resizing, swapping and resetting

- section: Ring buffer
- relevance: 4 - these change pages under writers and readers

What do `ring_buffer_resize()`, `ring_buffer_subbuf_order_set()`, `ring_buffer_swap_cpu()` and
`ring_buffer_reset_cpu()` each do to be safe against writers and readers that are running, and
what does each require of its caller? When does each refuse? Start from `ring_buffer_resize()`,
`ring_buffer_subbuf_order_set()`, `ring_buffer_swap_cpu()` and `ring_buffer_reset_cpu()`.

## tracing.rb-persistent-mapped: Persistent, mapped and remote buffers

- section: Ring buffer
- relevance: 4 - new kinds of buffer whose pages the kernel does not own in the usual way

For a ring buffer with a fixed set of pages (one placed in reserved memory so that it survives a
reboot, one mapped into user space, one written by something other than this kernel), how is its
content checked before it is trusted, and which operations are refused while it is in that state?
Start from `__ring_buffer_alloc_range()`, `ring_buffer_map()` and `__ring_buffer_alloc_remote()`.

## tracing.rb-write-usage: Writing to the ring buffer

- section: Ring buffer
- relevance: 5 - every producer has to follow these rules

What state is the CPU left in between `ring_buffer_lock_reserve()` and
`ring_buffer_unlock_commit()`, and what are the requirements for the code that runs between them
in order to assure safe usage? When does `ring_buffer_lock_reserve()` return NULL?

# Instances and tracefs files

## tracing.trace-array: Trace instances

- section: Instances and tracefs files
- relevance: 4 - almost every tracefs file acts on one of these

Which buffers does a `struct trace_array` own and what are they called in this tree? What counts
references to an instance, however it was created, and when does removing one fail? Start from
`struct trace_array` in `kernel/trace/trace.h` and `trace_array_get_by_name()`.

## tracing.lock-order: Locks and their order

- section: Instances and tracefs files
- relevance: 5 - several global mutexes nest and a new path can invert them

What does each of the global locks tracing uses protect (`trace_types_lock`, `event_mutex`,
`ftrace_lock`, the mutex in `kernel/tracepoint.c`, the dynamic event mutex, the CPU hotplug lock,
`text_mutex`), and in which order do they nest where two are held together? Name the functions
that show each ordering.

## tracing.tracefs-open-usage: Opening a tracefs file

- section: Instances and tracefs files
- relevance: 5 - a missing reference or lockdown check is a recurring bug

What do `tracing_open_generic_tr()` and `tracing_open_file_tr()` do on behalf of the open method
of a tracefs file that acts on an instance, and what must the release method then do? What are the
requirements for using the instance pointer stored in the inode in order to assure safe usage?
Start from `tracing_check_open_get_tr()`, `tracing_open_generic_tr()` and
`tracing_open_file_tr()`.

## tracing.lockdown-check: Lockdown check on open

- section: Instances and tracefs files
- relevance: 5 - an open method that lacks the check lets a locked-down kernel be traced

Where is kernel lockdown checked when a tracefs file is opened, and what must an open method that
calls neither `tracing_open_generic_tr()` nor `tracing_open_file_tr()` do to make that check?
Start from `tracing_check_open_get_tr()`.

## tracing.event-file-lifetime: Lifetime of event files

- section: Instances and tracefs files
- relevance: 4 - a tracefs file can be open when its event or instance is removed

What keeps a `struct trace_event_file` alive while one of its tracefs files is open, and what
marks it as gone when its event or its instance is removed? What are the requirements for a file
operation that uses the pointer stored in the inode in order to assure safe usage? Start from
`event_file_get()`, `event_file_put()` and `remove_event_file_dir()`.

# Function tracing

## tracing.ftrace-ops: ftrace_ops flags and guarantees

- section: Function tracing
- relevance: 4 - the interface every function hook uses

How does an ftrace callback get at registers or function arguments through the arguments it is
passed in this tree? Which flags of `struct ftrace_ops` does the owner set to get a guarantee, and
which are not the owner's to set? What are the requirements for freeing a dynamically allocated
`struct ftrace_ops` in order to assure safe usage? Start from `struct ftrace_ops` in
`include/linux/ftrace.h`.

## tracing.fgraph: Function graph infrastructure

- section: Function tracing
- relevance: 4 - several users now share one return hook and one shadow stack

What does the entry callback of a `struct fgraph_ops` decide by its return value, and how is
per-call data passed from entry to return? What must a stack unwinder call to find the real return
address? Start from `struct fgraph_ops`, `function_graph_enter_regs()` and
`ftrace_graph_ret_addr()`.

## tracing.fgraph-users: Registered users and shadow stack

- section: Function tracing
- relevance: 4 - registration fails when every slot is taken

How many `struct fgraph_ops` can be registered at one time, and what does
`register_ftrace_graph()` return when there is no room? When is the shadow stack of a task
allocated? Start from `register_ftrace_graph()`.

## tracing.ftrace-callback-usage: Inside an ftrace callback

- section: Function tracing
- relevance: 5 - a callback runs anywhere, including where RCU is not watching

In what contexts can an ftrace callback be called, and what does the core guarantee it about
preemption and about recursing into itself? What are the requirements for the code inside an
ftrace callback, and for the functions it calls, in order to assure safe usage? Start from
`ftrace_test_recursion_trylock()` and `ftrace_ops_assist_func()`.

# Model gaps

## tracing.model-gaps: Other mistakes models make

- drafts: all
- relevance: 5 - a model that is told how it is wrong can correct for it

Going by what each reader said from memory for every question in this guide, which is given
below, what do models believe about this code that is wrong in this tree? One bullet per mistake:
the belief, put plainly as a model would hold it, then what is true here and where to see it.
Cover names that are gone and what does the job now, numbers and limits that have changed,
behaviour that has changed, rules the readers state more broadly than the code supports, and what
is new that none of them knew. Most consequential first: a belief that would make a reviewer
approve a bug or reject correct code comes before a file that moved. Leave out what the readers
had right, and a slip only one of them made that the others show is not a belief. One or two lines to
a bullet: the belief and the truth. Every section of this guide already corrects what models
get wrong about its subject, and what a section covers is taken out of this list afterwards, so what
matters most here is what no question above asks about.
