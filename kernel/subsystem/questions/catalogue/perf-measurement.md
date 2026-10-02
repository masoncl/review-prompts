# Questions: Perf Tools (measurement set)

- guide: perf.md
- title: Perf Tools Subsystem

A wide set of questions about the perf tool under `tools/perf` and the
libraries it is built with, used to measure what a model already knows before
deciding what the built guide should spend its words on. The subject is the
user-space tool, not the perf events core under `kernel/events`. The
hand-written guide it will replace is 1,083 words and was never checked against
current sources. Format: `../../../docs/subsystem-questions.md`.

# The tool

## perf.source-layout: Source layout

- section: Finding your way
- relevance: 4 - several directories are newer than most readers
- words: 120

What is kept in each directory under `tools/perf` (the top level, `util`,
`arch`, `tests`, `ui`, `pmu-events`, `scripts`, `python`, `trace`,
`Documentation`), and which directories under `tools/lib` and `tools/build`
is perf built with? A table.

## perf.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 110

For each job, which function do you start reading from: dispatching a
subcommand, opening a perf.data file, reading its header, delivering one event
to a tool, parsing an event string, opening an event, resolving a sample's
address to a symbol, synthesizing events for existing threads? A table.

## perf.docs: Authoritative documentation

- section: Finding your way
- relevance: 3 - the file format is specified only there
- words: 60

Which files under `tools/perf/Documentation` and nearby are the authority on
the perf.data file format, on the build, on the build framework, on the JSON
event files and on the copies of kernel headers under `tools/include`?

## perf.core-objects: Core objects

- section: Finding your way
- relevance: 4 - every command is phrased in these
- words: 100

How do session, machines, machine, thread, maps, map, dso and symbol relate:
which holds which, and which are shared between several owners? Do the same
for evlist and evsel. Start from `struct perf_session` and `struct machine`.

## perf.libperf-split: libperf and the tool

- section: Finding your way
- relevance: 3 - decides where a new field or function goes
- words: 80

How is `tools/lib/perf` related to the evlist, evsel, cpu map and thread map
code in `tools/perf/util`: how does a tool structure embed the library one,
which headers are public and which internal, and what fixes the exported
symbols? Start from `struct evsel` and `tools/lib/perf/libperf.map`.

## perf.naming-conventions: Naming conventions

- section: Finding your way
- relevance: 3 - a reviewer reads a function's contract from its name
- words: 80

What do the suffixes on perf's method-style function names promise about
allocation and ownership: new, delete, init, exit, get, put, zput? Which
helpers free a pointer and clear it? Start from `thread__zput()` and
`zfree()`.

# Delivering events

## perf.tool-init: Setting up the callbacks

- section: The tool callbacks
- relevance: 5 - the first thing every command that reads events does
- words: 80

How does a command prepare its `struct perf_tool` before creating a session:
which function must run, what does its boolean argument select, and in what
order are the command's own handlers installed? Is a statically initialised
struct with only some members set still valid? Start from `perf_tool__init()`.

## perf.tool-defaults: Callbacks left unset

- section: The tool callbacks
- relevance: 5 - decides whether a missing handler is a bug
- words: 90

What happens to an event whose callback the command did not set: is it
dropped, handled by a default, or an error? Say which callbacks default to a
stub, and for each default that is not a stub what it does to the session or
machine, reading the function it ends in and not only its name. What does a
stub print under the dump option? Start from `perf_tool__init()`.

## perf.tool-mmap-pair: The two mmap records

- section: The tool callbacks
- relevance: 4 - a file can hold either kind
- words: 70

When does a perf.data file hold `PERF_RECORD_MMAP` events and when
`PERF_RECORD_MMAP2`, which callback does each reach, and what is lost if a
command handles one and not the other? Name the usual handler for each. Start
from `machines__deliver_event()`.

## perf.tool-ordering: Ordered events

- section: The tool callbacks
- relevance: 4 - wrong setting gives events out of time order
- words: 80

What do the ordering members of `struct perf_tool` do, which records flush the
queue, and when does session creation switch ordering off by itself? Start
from `perf_session__queue_event()` and `perf_event__process_finished_round()`.

## perf.tool-delegate: Wrapping a tool

- section: The tool callbacks
- relevance: 2 - a handful of users
- words: 50

How does one tool wrap another so that it can intercept some events and pass
the rest on, and what has to be added there when `struct perf_tool` gains a
callback? Start from `struct delegate_tool`.

## perf.event-dispatch: Dispatch by record type

- section: The tool callbacks
- relevance: 4 - where a new check or record type goes
- words: 80

Which function dispatches records produced by the kernel and which dispatches
records synthesized by user space, which of them bypass the ordering queue,
and what is returned for a record type neither knows? Start from
`perf_session__process_user_event()` and `machines__deliver_event()`.

## perf.new-record-type: Adding a record type

- section: The tool callbacks
- relevance: 4 - several tables must stay in step
- words: 100

List every table, struct and file that has to be touched to add a new
user-space record type, from the type number through to the documentation.
Start from `perf_event__swap_ops`, `perf_tool__init()` and
`tools/lib/perf/include/perf/event.h`.

# perf.data

## perf.file-layout: File layout

- section: File and pipe formats
- relevance: 4 - needed to follow any header change
- words: 80

What are the parts of a perf.data regular file in order, what does the file
header record about each, and where are the feature sections relative to the
data? Start from `struct perf_file_header` and
`tools/perf/Documentation/perf.data-file-format.txt`.

## perf.pipe-mode: Pipe format

- section: File and pipe formats
- relevance: 5 - the mode in which missing handlers break everything
- words: 90

How does the pipe format differ from the file format, how does the reader
decide which one it has, and can a regular file on disk be in pipe format?
Which operations are unavailable on pipe input? Start from
`perf_session__read_header()` and `perf_data__is_pipe()`.

## perf.pipe-attrs-features: Attributes and features over a pipe

- section: File and pipe formats
- relevance: 5 - a command that skips this sees no events
- words: 100

In pipe format, how do the event attributes and the header features reach the
reader, which `struct perf_tool` callbacks must a command set for them and to
which functions, and what is the state of the session's evlist before they
arrive? Start from `perf_event__synthesize_for_pipe()` and
`perf_event__process_attr()`.

## perf.header-features: Feature table

- section: File and pipe formats
- relevance: 4 - every feature is one row of this table
- words: 90

How is a header feature defined: what are the members of its operations
entry, what is the difference between the two macros that declare a row, and
which features have no reader or no printer? Start from `feat_ops` and
`struct perf_header_feature_ops` in `tools/perf/util/header.c`.

## perf.new-feature: Adding a header feature

- section: File and pipe formats
- relevance: 4 - old and new tools must keep reading each other's files
- words: 100

What must a patch that adds a header feature touch, where in the numbering
does the new feature go, and what keeps an old perf reading a file that has
it and a new perf reading a file that lacks it? Start from
`HEADER_LAST_FEATURE` and `record__init_features()`.

## perf.unknown-features: Unknown and missing features

- section: File and pipe formats
- relevance: 4 - the compatibility rule in practice
- words: 70

What does the reader do with a feature number it does not know, in a file and
in a pipe, and how does code find out that a file lacks a feature it wants?
Start from `perf_event__process_feature()` and `perf_header__has_feat()`.

## perf.env-ownership: Environment ownership

- section: The recorded environment
- relevance: 5 - the wrong env describes the wrong machine
- words: 90

Where is the `struct perf_env` of a session stored, how does code reach it,
and who fills it in for a regular file, for pipe input, and for a live command
such as perf top or perf trace that has no file? Is there a global one? Start
from `perf_session__env()` and `__perf_session__new()`.

## perf.env-usage: Reading perf_env fields

- section: The recorded environment
- relevance: 5 - fields are absent on old files and early in a pipe
- words: 100

What usage of `struct perf_env` fields is unsafe, and what that looks similar
is correct? Say which fields can be NULL or zero and why, and which accessors
fill a field in lazily or bounds-check it. Name in-tree code that shows each.
Start from `perf_env__arch()`, `perf_env__nr_cpus_avail()` and
`perf_env__get_cpu_topology()`.

## perf.untrusted-input: Validating records

- section: Reading untrusted files
- relevance: 5 - a perf.data file is attacker-controlled input
- words: 110

What checks does the session layer make on a record before a handler sees it
(size against type, string termination, counts against the record's size), and
what is left for the handler to check? When a check fails is the record
skipped or is processing aborted? Start from `perf_event__too_small()` and
`machines__deliver_event()`.

## perf.byte-swap: Cross-endian files

- section: Reading untrusted files
- relevance: 3 - a new field that is not swapped reads as garbage
- words: 70

How is a file written on a machine of the other endianness read: where is
that detected, which table swaps each record, how are samples and attributes
swapped, and why can a native file not be fixed up in place? Start from
`perf_event__swap_ops` and `perf_event__attr_swap()`.

# Cross-platform analysis

## perf.arch-dir: The arch directory

- section: Host and recorded architecture
- relevance: 5 - code put here exists only in a binary built for that host
- words: 90

How much of `tools/perf/arch` is compiled into one perf binary, and what kinds
of code are in it in this tree? List the kinds that belong there. Start from
`tools/perf/arch/Build`.

## perf.arch-analysis-code: Per-architecture analysis code

- section: Host and recorded architecture
- relevance: 5 - these directories are recent
- words: 110

Where does code live that decodes or reports data for a particular
architecture (annotation, register names, DWARF register numbers, unwinding,
KVM exit reasons), is it built for every architecture or only the host, and
how is the right one chosen at run time? A table of directory and selecting
function. Start from `arch__find()` and `perf_reg_name()`.

## perf.e-machine: Finding the recorded architecture

- section: Host and recorded architecture
- relevance: 5 - the accessors are new
- words: 100

Which functions return the ELF machine of the data being analysed, at the
level of the environment, session, thread, dso and evsel, and what does each
fall back to when the file does not record it? Is it a header feature? Start
from `perf_env__e_machine()` and `thread__e_machine()`.

## perf.arch-usage: Host assumptions in analysis code

- section: Host and recorded architecture
- relevance: 5 - breaks reporting an ARM file on x86
- words: 90

What usage of host-only constructs in code that analyses recorded data is
unsafe (preprocessor tests on the compiler's target, functions under the arch
directory, the host's `uname`), and what that looks similar is correct? Name
in-tree code on each side.

# Reference counting

## perf.rc-mechanism: Reference count checking

- section: Checked reference counts
- relevance: 5 - explains rules that otherwise look arbitrary
- words: 100

What does reference count checking do to a counted struct, what does each of
a missed put, a double put and a use after put turn into, and what switches it
on: a make variable, a define, a sanitizer? Start from
`tools/lib/perf/include/internal/rc_check.h`.

## perf.rc-structs: Checked structs

- section: Checked reference counts
- relevance: 4 - the list has grown
- words: 50

Which structs are declared with `DECLARE_RC_STRUCT` in this tree, and which
counted structs (for example evsel, symbol, cgroup) are not?

## perf.rc-access: Touching a checked struct

- section: Checked reference counts
- relevance: 5 - compiles and runs without checking, fails with it
- words: 100

What usage of a pointer to a checked struct is unsafe when checking is on, and
what that looks similar is correct? Cover reading a member, comparing two
pointers, storing a pointer in a second place, and freeing. Start from
`RC_CHK_ACCESS`, `RC_CHK_EQUAL` and the accessors in
`tools/perf/util/thread.h`.

## perf.rc-new-struct: Making a struct checked

- section: Checked reference counts
- relevance: 3 - done a few times a year
- words: 70

What are the steps to put an existing reference-counted struct under
checking: the declaration, the constructor, get, put and the final free? Start
from `ADD_RC_CHK`, `RC_CHK_GET`, `RC_CHK_PUT` and `RC_CHK_FREE`.

## perf.lookup-references: Lookups that return a reference

- section: Ownership
- relevance: 5 - each one is a leak if the caller forgets
- words: 100

Which common lookup functions return a new reference the caller must put
(finding a thread in a machine, a map in maps, a dso), and which return a
borrowed pointer (a thread's maps, a map's dso, a symbol)? A table. Start from
`machine__find_thread()`, `maps__find()`, `map__dso()` and `thread__maps()`.

## perf.location-lifetime: Locations and samples

- section: Ownership
- relevance: 5 - stack structs that hold references
- words: 90

Which stack-allocated structs hold references and so need an init and exit
pair, what does exit release for each, and how is one copied? Start from
`addr_location__exit()`, `map_symbol__copy()` and `perf_sample__exit()`.

## perf.evlist-lifetime: Event list lifetime

- section: Ownership
- relevance: 4 - the free functions changed
- words: 70

How are an evlist and its evsels created and released in this tree: is either
reference counted, which function frees each, and who owns an evsel once it is
added to a list? Start from `evlist__new()`, `evlist__add()` and
`evsel__new()`.

## perf.shared-state-locks: Locks on shared state

- section: Ownership
- relevance: 3 - only some commands are multi-threaded
- words: 90

Which locks protect a machine's thread table, a maps, a dso and the open-file
cache for dso data, which commands touch them from more than one thread, and
how are lock requirements annotated for the compiler? Start from
`struct threads`, `dso__lock()` and `tools/perf/util/mutex.h`.

# Build

## perf.feature-flow: Feature detection flow

- section: Optional features
- relevance: 5 - four files must agree
- words: 110

Trace one optional library from its feature test to the C code: where the
test program is, how it is run and what variable it sets, where that becomes
a compiler define and a `CONFIG_` value, and what the all-in-one test does.
Start from `tools/build/Makefile.feature`, `tools/build/feature/test-all.c`
and `tools/perf/Makefile.config`.

## perf.new-feature-test: Adding a feature test

- section: Optional features
- relevance: 4 - a missed list gives a silently disabled feature
- words: 90

List every file and list a patch must touch to add a new optional library to
the perf build, including the lists that feed the all-in-one test, the status
display, the feature table of perf check and the build matrix. Start from
`FEATURE_TESTS_BASIC` and `supported_features` in
`tools/perf/builtin-check.c`.

## perf.feature-guards: Guarding optional code

- section: Optional features
- relevance: 5 - the usual way a build without a library breaks
- words: 110

What usage of code that depends on an optional library is unsafe, and what
that looks similar is correct? Cover preprocessor guards, conditional objects
in the `Build` files, and what a header offers callers when the feature is
off, with what the stubs return. Name an in-tree header that shows it.

## perf.optin-features: Default-off features

- section: Optional features
- relevance: 3 - the defaults have moved
- words: 70

Which optional libraries are off unless asked for, which are marked
deprecated, and what make variable turns each on or off? Start from
`tools/perf/Makefile.config` and `tools/perf/tests/make`.

## perf.build-matrix: Build test matrix

- section: Optional features
- relevance: 3 - how a build change is tested
- words: 60

How is perf built across its option combinations for testing, which target
runs that, and which combinations does it include (minimal, static, reference
count checking, no libbpf)? Start from `tools/perf/tests/make`.

## perf.libc-portability: C library portability

- section: Portability
- relevance: 4 - breaks only on the other C library
- words: 100

Which C libraries is perf built against, does any rule on including libc
headers keep it building on all of them, and is such a rule written down or
checked anywhere in the tree? Which libc functions does the build feature-test
and supply fallbacks for rather than assume? Start from `FEATURE_TESTS_BASIC`.

## perf.kernel-header-copies: Copies of kernel headers

- section: Portability
- relevance: 4 - kernel patches and tool patches treat the copies differently
- words: 80

Why does `tools/include` carry copies of kernel headers, what reports that a
copy is out of date, is that fatal to the build, and who updates the copy
when a kernel patch changes the original? Start from
`tools/perf/check-headers.sh` and `tools/include/uapi/README`.

## perf.bpf-skeletons: BPF skeletons

- section: Portability
- relevance: 3 - a second compiler and a second guard
- words: 70

How are the BPF programs perf carries built and linked in, what do they need
on the build machine, which define guards the code that uses them, and what
must that code do when skeletons are off? Start from
`tools/perf/util/bpf_skel` and `tools/perf/Makefile.perf`.

# Conventions

## perf.error-returns: Error returns from constructors

- section: Errors and output
- relevance: 4 - a NULL test on an error pointer passes
- words: 100

Which functions in perf that return a pointer report failure with an error
pointer and which with NULL, how must callers of each check, and is any
preference for new code written down in the tree? Start from
`perf_session__new()`, `evsel__newtp()` and `evlist__new()`.

## perf.output-logging: Messages and verbosity

- section: Errors and output
- relevance: 3 - the wrong call corrupts a TUI or a pipe
- words: 80

Which calls should perf code use for errors, warnings and debug messages,
what verbosity does each need, where does the output go when a TUI is active,
and what are `ui__error()` and `dump_printf()` for? Start from
`tools/perf/util/debug.h`.

## perf.dir-iteration: Walking directories

- section: Errors and output
- relevance: 3 - file descriptor leaks on the error path
- words: 90

Which helpers does perf use to walk a directory such as one under /proc or
sysfs, who owns the file descriptor after it is handed to `fdopendir()`, and
what usage on the error path of a callback-driven walk is unsafe and what is
correct? Start from `tools/lib/api/io_dir.h` and `tools/perf/util/drm_pmu.c`.

# Events and PMUs

## perf.event-parsing: Parsing event strings

- section: Events
- relevance: 3 - where a new term or modifier goes
- words: 80

How does an event string become evsels: the lexer and grammar files, the
entry function, where terms and modifiers are handled, and how errors are
reported to the user? Start from `parse_events()` and
`tools/perf/util/parse-events.y`.

## perf.pmu-kinds: Kinds of PMU

- section: Events
- relevance: 4 - several are not kernel PMUs at all
- words: 90

What kinds of PMU does perf know: those read from sysfs, those described by
JSON, and those implemented inside the tool itself? For the in-tool ones say
what each counts and which file implements it. Start from
`tools/perf/util/pmus.c` and `tools/perf/util/tool_pmu.c`.

## perf.open-fallback: Opening on older kernels

- section: Events
- relevance: 4 - a new attr bit must degrade, not fail
- words: 90

What does perf do when the kernel rejects an event attribute it does not
know: how are missing kernel features detected and remembered, and what has
to be added when perf starts setting a new attribute bit? Start from
`struct perf_missing_features` and `evsel__detect_missing_features()`.

## perf.sample-format: Adding a sample field

- section: Events
- relevance: 4 - parser, synthesizer and test must agree
- words: 90

What must change together when a new sample type bit or attribute field is
supported: the parser, the size calculation, the synthesizer, the byte swap,
the attribute printer, the test? Start from `evsel__parse_sample()`,
`perf_event__synthesize_sample()` and `tools/perf/tests/sample-parsing.c`.

## perf.pmu-events-json: Generated event tables

- section: Events
- relevance: 3 - a checked-in generated file must be regenerated
- words: 80

How do the JSON files under `tools/perf/pmu-events/arch` become C tables,
which generated file is checked into the tree and how is it kept in step, and
where do generated metrics come from? Start from
`tools/perf/pmu-events/jevents.py` and `tools/perf/pmu-events/Build`.

# Testing and change

## perf.test-suites: C test suites

- section: Tests
- relevance: 4 - new code is expected to come with one
- words: 90

How is a C test defined and registered, what do the return values mean, what
does marking a case exclusive do, and where do architecture-specific tests
go? Start from `DEFINE_SUITE`, `TEST_CASE` and
`tools/perf/tests/builtin-test.c`.

## perf.shell-tests: Shell tests and workloads

- section: Tests
- relevance: 4 - most end-to-end coverage is here
- words: 90

How are shell tests found and described, which exit status means skip, how do
they find a temporary directory and clean up, and what are the built-in
workloads for and how is one run? Start from `tools/perf/tests/shell` and
`tools/perf/tests/workloads`.

## perf.change-checklist: Changing shared code

- section: Tests
- relevance: 4 - breakage shows up in a build the author did not run
- words: 100

What must a change under `tools/perf/util` keep working besides the default
build: the Python module, builds with libraries switched off, reference count
checking, pipe input, files from the other endianness, files from an older
perf? Say how each is exercised.
