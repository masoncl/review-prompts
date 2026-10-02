# Questions: Perf Tools Subsystem

- guide: perf.md
- title: Perf Tools Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/perf-measurement.md` is the
wider set the readers were measured on and `catalogue/perf-measurement-results.md` says what they
got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## perf.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## perf.source-layout: Source layout

- section: Finding your way
- relevance: 4 - several directories are newer than most readers

A table and nothing else, directory to what is kept there: the top level of `tools/perf`, `util`,
`arch`, `tests`, `ui`, `pmu-events`, `scripts`, `python`, `trace` and `Documentation` under it,
and the directories under `tools/lib` and `tools/build` that perf is built with. Where a reader
is likely to look for a directory or file that does not exist in this tree, say so in the row.

# Recorded and host architecture

## perf.arch-code-placement: Placing architecture code

- section: Recorded and host architecture
- relevance: 5 - code put in the wrong place exists only in a binary built for that host

In which directories does code go that is needed only to record on the host, and in which does
code go that decodes or reports data for the recorded architecture? Which of the two is compiled
into every perf binary, and which function selects the analysis code for the recorded architecture
at run time? Start from `tools/perf/arch/Build`, `arch__find()` and `perf_reg_name()`.

## perf.e-machine: Finding the recorded architecture

- section: Recorded and host architecture
- relevance: 5 - the accessors are new

Which accessors return the ELF machine of the data being analysed, and what does each fall back to
when the input does not record it? Is the ELF machine recorded as a header feature? Start from
`perf_env__e_machine()` and `thread__e_machine()`.

## perf.arch-usage: Host assumptions in analysis code

- section: Recorded and host architecture
- relevance: 5 - breaks reporting an ARM file on x86

What are the requirements for code that analyses recorded data, in how it finds the architecture
of that data, in order to assure safe usage on a host of another architecture? Name in-tree code
that uses the recorded architecture, and in-tree code that is correct to use the host's.

# Object lifetime and reference counts

## perf.rc-checking: Reference count checking

- section: Object lifetime and reference counts
- relevance: 5 - explains rules that otherwise look arbitrary

What does each of a missed put, a double put and a use after put turn into when reference count
checking is on, and what switches checking on? How does a reader tell whether a given counted
struct is checked? Start from `tools/lib/perf/include/internal/rc_check.h` and
`DECLARE_RC_STRUCT`.

## perf.core-objects: Shared and owned objects

- section: Object lifetime and reference counts
- relevance: 4 - decides where a get and a put are needed

Of session, machines, machine, thread, maps, map, dso and symbol, which are shared between several
owners and so reached through a counted reference, and which belong to exactly one holder? Which
lookups hand back a reference the caller must put? Start from `struct perf_session` and
`struct machine`.

## perf.evlist-lifetime: evlist and evsel lifetime

- section: Object lifetime and reference counts
- relevance: 4 - the free functions changed

Is `struct evlist` or `struct evsel` reference counted, which function does a caller call to
release each, and who owns an evsel once `evlist__add()` has added it to a list? Start from
`evlist__new()`, `evlist__add()` and `evsel__new()`.

## perf.location-lifetime: addr_location and perf_sample references

- section: Object lifetime and reference counts
- relevance: 5 - stack structs that hold references

What are the requirements for a `struct addr_location` and a `struct perf_sample` declared on the
stack, from initialisation to the end of the scope, in order to assure safe usage? What do
`addr_location__exit()` and `perf_sample__exit()` each release, and how is a `struct map_symbol`
copied? Start from `addr_location__exit()`, `map_symbol__copy()` and `perf_sample__exit()`.

## perf.error-returns: Error returns from constructors

- section: Object lifetime and reference counts
- relevance: 4 - a NULL test on an error pointer passes

How do `perf_session__new()`, `evsel__newtp()` and `evlist__new()` each report failure, and which
test must a caller make on the pointer each returns? Does the tree write down a preference for new
code?

## perf.rc-access: Pointers to refcount-checked structs

- section: Object lifetime and reference counts
- relevance: 5 - compiles and runs without checking, fails with it

What are the requirements for code that holds a pointer to a struct declared with
`DECLARE_RC_STRUCT`, when reference count checking is on, in order to assure safe usage? When must
code go through `RC_CHK_ACCESS` and `RC_CHK_EQUAL`? Start from `RC_CHK_ACCESS`, `RC_CHK_EQUAL` and
the accessors in `tools/perf/util/thread.h`.

# Tool callbacks and records

## perf.tool-init: perf_tool initialisation

- section: Tool callbacks and records
- relevance: 5 - the first thing every command that reads events does

What are the requirements for a command's `struct perf_tool` before the command creates a session
in order to assure safe usage? What does the boolean argument of `perf_tool__init()` select, and
must the command install its own handlers before or after that call? Start from
`perf_tool__init()`.

## perf.tool-defaults: Callbacks left unset

- section: Tool callbacks and records
- relevance: 5 - decides whether a missing handler is a bug

What happens to a record whose callback in `struct perf_tool` the command left unset? Which of the
defaults change the session or the machine, and which defaults does the session treat differently
once a command replaces them? Start from `perf_tool__init()`.

## perf.event-dispatch: Dispatch by record type

- section: Tool callbacks and records
- relevance: 4 - where a new check or record type goes

Which function dispatches records produced by the kernel and which dispatches records synthesized
by user space, which records bypass the ordering queue, and what is returned for a record type
neither knows? Start from `perf_session__process_user_event()` and `machines__deliver_event()`.

## perf.tool-ordering: Ordered events

- section: Tool callbacks and records
- relevance: 4 - wrong setting gives events out of time order

What do the ordering members of `struct perf_tool` do, which records flush the queue, and when
does session creation switch ordering off by itself? Start from `perf_session__queue_event()` and
`perf_event__process_finished_round()`.

## perf.tool-mmap-pair: MMAP and MMAP2 records

- section: Tool callbacks and records
- relevance: 4 - a file can hold either kind

When does a perf.data file hold `PERF_RECORD_MMAP` events and when `PERF_RECORD_MMAP2`, including
for the kernel and module maps perf synthesizes, which callback does each reach, and what is lost
if a command handles one and not the other? Name the usual handler for each. Start from
`machines__deliver_event()`.

## perf.untrusted-input: Validating records

- section: Tool callbacks and records
- relevance: 5 - a perf.data file is attacker-controlled input

What checks does the session layer make on a record before a handler sees it, and what is left for
the handler to check? When a check fails, is the record skipped or is processing aborted? Start
from `perf_event__too_small()` and `machines__deliver_event()`.

## perf.new-record-type: Adding a record type

- section: Tool callbacks and records
- relevance: 4 - several tables must stay in step

Which tables and functions are indexed by a user-space record type, so that a patch that adds a
value to `enum perf_user_event_type` must change them? For each, what happens at run time when the
new type is missing from it? Start from `perf_event__swap_ops`, `perf_tool__init()` and
`tools/lib/perf/include/perf/event.h`.

# File and pipe formats

## perf.file-and-pipe: Headers and format detection

- section: File and pipe formats
- relevance: 5 - the mode in which missing handlers break everything

What does `struct perf_file_header` record that the pipe format has no place for? How does
`perf_session__read_header()` decide which format the input has, and can a regular file on disk be
in pipe format? Start from `perf_session__read_header()`, `perf_data__is_pipe()` and `struct
perf_file_header`.

## perf.pipe-limits: Limits of pipe input

- section: File and pipe formats
- relevance: 5 - a command that works on a file fails or gives less on a pipe

Which operations does perf refuse or skip when its input is in pipe format? Where in a regular
perf.data file do the feature sections sit relative to the data? Start from
`perf_data__is_pipe()`.

## perf.pipe-attrs-features: Attributes and features over a pipe

- section: File and pipe formats
- relevance: 5 - a command that skips this sees no events

In pipe format, how do the event attributes and the header features reach the reader, which
`struct perf_tool` callbacks must a command set for them and to which functions, and what is the
state of the session's evlist before they arrive? Start from
`perf_event__synthesize_for_pipe()` and `perf_event__process_attr()`.

## perf.unknown-features: Unknown and missing features

- section: File and pipe formats
- relevance: 4 - the compatibility rule in practice

What does the reader do with a feature number it does not know, in a file and in a pipe? How does
code find out that the input lacks a feature it wants, and what does that test say on pipe input?
Start from `perf_event__process_feature()` and `perf_header__has_feat()`.

## perf.new-feature: Adding a header feature

- section: File and pipe formats
- relevance: 4 - old and new tools must keep reading each other's files

When a patch adds a header feature, where in the numbering before `HEADER_LAST_FEATURE` does it
go, and when is its row of `feat_ops` declared with `FEAT_OPR` and when with `FEAT_OPN`? What must
`record__init_features()` do for the feature to be written? Start from `HEADER_LAST_FEATURE`,
`feat_ops` in `tools/perf/util/header.c` and `record__init_features()`.

# The recorded environment

## perf.env-ownership: Environment ownership

- section: The recorded environment
- relevance: 5 - the wrong env describes the wrong machine

Where is the `struct perf_env` of a session stored, how does code reach it, and who fills it in
for a regular file, for pipe input, and for a live command such as perf top or perf trace that
has no file? Is there a global one? Start from `perf_session__env()` and
`__perf_session__new()`.

## perf.env-usage: Reading perf_env fields

- section: The recorded environment
- relevance: 5 - fields are absent on old files and early in a pipe

What are the requirements for code that reads a field of `struct perf_env` in order to assure safe
usage? Which accessors fill a field in lazily or bounds-check it? Name in-tree code that shows
each. Start from `perf_env__arch()`, `perf_env__nr_cpus_avail()` and
`perf_env__get_cpu_topology()`.

# Events and PMUs

## perf.pmu-kinds: Kinds of PMU

- section: Events and PMUs
- relevance: 4 - several are not kernel PMUs at all

Which kinds of PMU does `tools/perf/util/pmus.c` create that are not kernel PMUs read from sysfs,
and in which file is each kind implemented? What does code that walks PMUs or opens their events
have to test before it treats a `struct perf_pmu` as a kernel PMU? Start from
`tools/perf/util/pmus.c` and `tools/perf/util/tool_pmu.c`.

## perf.open-fallback: Opening on older kernels

- section: Events and PMUs
- relevance: 4 - a new attr bit must degrade, not fail

When does `evsel__detect_missing_features()` run, and how is its result remembered in `struct
perf_missing_features`? What has to be added, and where in the order of the probes, when perf
starts setting a new attribute bit? Start from `struct perf_missing_features` and
`evsel__detect_missing_features()`.

## perf.sample-format: Adding a sample field

- section: Events and PMUs
- relevance: 4 - parser, synthesizer and test must agree

Which functions must a patch change together when it adds a bit to `enum perf_event_sample_format`
or a field to `struct perf_event_attr`, and which test checks them against one another? Start from
`evsel__parse_sample()`, `perf_event__synthesize_sample()` and
`tools/perf/tests/sample-parsing.c`.

## perf.dir-iteration: Walking directories

- section: Events and PMUs
- relevance: 3 - file descriptor leaks on the error path

Which helpers does perf use to walk a directory such as one under /proc or sysfs, and who owns the
file descriptor after it is handed to `fdopendir()`? What are the requirements for the descriptors
that `for_each_drm_fdinfo_in_dir()` opens, on the path where its callback returns an error, in
order to assure safe usage? Start from `tools/lib/api/io_dir.h` and `tools/perf/util/drm_pmu.c`.

# Optional features and portable builds

## perf.feature-detection: Feature detection

- section: Optional features and portable builds
- relevance: 5 - four files must agree, and a missed list gives a silently disabled feature

When a patch adds an optional library to perf, which lists in `tools/build/Makefile.feature`,
`tools/perf/Makefile.config` and `tools/perf/builtin-check.c` must name the feature, and where do
the names have to agree? What happens to the feature when each list is missed? Start from
`tools/build/Makefile.feature`, `tools/build/feature/test-all.c`, `tools/perf/Makefile.config` and
`supported_features` in `tools/perf/builtin-check.c`.

## perf.feature-test-all: All-in-one feature test

- section: Optional features and portable builds
- relevance: 5 - which test programs run decides whether a missing library is noticed

What does `tools/build/feature/test-all.c` change about which feature test programs run, and what
happens to a feature whose test is not part of it?

## perf.feature-guards: Guarding optional code

- section: Optional features and portable builds
- relevance: 5 - the usual way a build without a library breaks

What are the requirements for code that depends on an optional library in order to assure that
perf builds and runs when the library is absent? What does the header of such code give callers
when the feature is off, and what do its stubs return? Name an in-tree header that shows it.

## perf.python-module: The Python module

- section: Optional features and portable builds
- relevance: 3 - shared code is linked into it without the rest of perf

How does the build choose which code under `tools/perf/util` is linked into the Python module?
What does a new source file there, or a new dependency on an optional library, have to do so that
the module still links and loads, and which test exercises it? Start from
`tools/perf/util/python.c` and `tools/perf/util/setup.py`.

## perf.libc-portability: C library portability

- section: Optional features and portable builds
- relevance: 4 - breaks only on the other C library

Is any rule on including libc headers written down or checked in the tree, so that perf builds
against more than one C library? Which libc functions does the build feature-test and supply
fallbacks for? Start from `FEATURE_TESTS_BASIC`.

## perf.kernel-header-copies: Copies of kernel headers

- section: Optional features and portable builds
- relevance: 4 - kernel patches and tool patches treat the copies differently

When does `tools/perf/check-headers.sh` run, and is a difference it reports fatal to the build?
According to `tools/include/uapi/README`, who updates a copy under `tools/include` when a kernel
patch changes the original? Start from `tools/perf/check-headers.sh` and
`tools/include/uapi/README`.

# Tests

## perf.shell-tests: Shell tests and workloads

- section: Tests
- relevance: 4 - most end-to-end coverage is here

How does perf test find a shell test under `tools/perf/tests/shell` and get its description, and
which exit status means skip? How does a test run one of the built-in workloads under
`tools/perf/tests/workloads`? Start from `tools/perf/tests/shell` and
`tools/perf/tests/workloads`.

## perf.shell-temp-files: Shell script temporary files

- section: Tests
- relevance: 4 - a test that leaves files behind or reuses a fixed name breaks the tests that run beside it

What are the requirements for a shell test under `tools/perf/tests/shell` that creates temporary
files, in how it names them and when it removes them, in order to assure safe usage? Name an
in-tree test that shows it.

## perf.test-suites: C test suites

- section: Tests
- relevance: 4 - new code is expected to come with one

How is a C test suite defined with `DEFINE_SUITE` and `TEST_CASE` and registered in
`tools/perf/tests/builtin-test.c`? What do the return values of a test case mean, and what does
marking a case exclusive do? Start from `DEFINE_SUITE`, `TEST_CASE` and
`tools/perf/tests/builtin-test.c`.

# Model gaps

## perf.model-gaps: Other mistakes models make

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
