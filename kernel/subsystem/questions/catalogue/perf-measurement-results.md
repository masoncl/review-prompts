# What the perf measurement found

Three models were asked the 54 questions in `perf-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; B is
the oldest and C the most current, and which models they were does not matter
here. The subject is the perf tool under `tools/perf`, not the perf events core
in the kernel. The hand-written guide was never checked against current
sources, so differences between it and the built guide are expected and are
noted below.

## What all three readers got wrong

- **Event lists and evsels are reference counted.** All three said neither is,
  and named evlist__delete() and evsel__delete(), which do not exist. `struct
  evlist` is declared with `DECLARE_RC_STRUCT` and has `evlist__get()` and
  `evlist__put()`; `struct evsel` has a plain `refcnt` with `evsel__get()` and
  `evsel__put()`. `evlist__add()` stores `evlist__get(evlist)` in
  `evsel->evlist` and `evlist__remove()` puts it. All three also left evlist
  off the list of checked structs, and two left off `comm_str`.
- **Stack structs that hold references.** All three said `struct
  addr_location` and `struct map_symbol` hold a maps. They hold a thread and a
  map, and `addr_location__exit()` and `map_symbol__exit()` put those two.
  None knew that `perf_sample__exit()` puts `sample->evsel`, a reference
  `__evsel__parse_sample()` takes, or that `addr_map_symbol__exit()` and
  `addr_map_symbol__copy()` exist.
- **The session layer validates records.** Readers A and B said there is no
  central check of string termination or of counts; reader C said
  `perf_event__too_small()` does not exist. The tree has `perf_event__min_size[]`
  behind `perf_event__too_small()`, `perf_event__check_nul()` for the MMAP,
  MMAP2, COMM, CGROUP, KSYMBOL and build-id records, and count checks for
  NAMESPACES, TEXT_POKE, THREAD_MAP, CPU_MAP, STAT_CONFIG and BPF_METADATA.
  Most failures skip the record; an unaligned size, a bad THREAD_MAP count and
  a sample that does not parse abort. A record type at or above
  `PERF_RECORD_HEADER_MAX` is skipped with a warning, not an error as readers
  A and B said.
- **The recorded architecture.** `HEADER_E_MACHINE` is a header feature, and
  `perf_session__e_machine()`, `evsel__e_machine()`, `dso__e_machine()` and
  `thread__e_machine()` exist. Reader B said none of these do, reader A thought
  there was probably no feature, and all three had the fallbacks wrong: the
  last resort of `perf_env__e_machine()` is `uname()` through
  `perf_env__e_machine_nocache()`, cached only when `env->arch` is set, and
  kernel, BPF and JIT dsos take the environment's value, not the host's.
- **What is under `tools/perf/arch`.** All three put annotation or register
  code there. In this tree it holds only host recording support (`header.c`,
  `pmu.c`, the auxtrace recorders), `tests`, `include` and the syscall tables;
  analysis code is in `util/annotate-arch`, `util/perf-regs-arch`,
  `util/dwarf-regs-arch`, `util/libunwind-arch` and `util/kvm-stat-arch`, built
  for every architecture and chosen at run time from the ELF machine. Reader B
  still had the whole older layout. Readers A and C invented a
  util/libunwind/ directory and a thread__get_arch().
- **Where the environment lives.** `struct perf_env` is embedded in `struct
  perf_header`, and `perf_session__env()` returns that one even in a live
  session, where `__perf_session__new()` puts the caller's `host_env` in
  `machines.host.env` only. Live perf trace creates no session at all. No
  reader had all of this, and reader B had the env embedded in the session.
- **`perf_env__get_cpu_topology()`.** Readers A and C said they did not
  recognise it; reader B described a field that does not exist. It is the
  bounds-checked accessor for `env->cpu`, needed because
  `process_cpu_topology()` frees `env->cpu` for old files while leaving
  `nr_cpus_avail` set.
- **Features on a pipe.** Nothing sets `adds_features` for pipe input, so
  `perf_header__has_feat()` is always false there. None said so.
  `perf_event__process_feature()` returns 0 for an unknown feature number and
  -1 only for `HEADER_RESERVED` or a negative one.
- **The two mmap records.** By default synthesized kernel and module maps are
  `PERF_RECORD_MMAP2`; they are `PERF_RECORD_MMAP` only when
  `symbol_conf.no_buildid_mmap2` is set. All three said the kernel map is
  usually MMAP.
- **`check-headers.sh` is not part of the build.** Only the `check-headers`
  target in `tools/perf/Makefile` runs it, and it always exits 0. All three
  said the normal build runs it, as `tools/include/uapi/README` still does.
- **Build details.** Reference count checking has no make variable; it is a
  define, passed as `EXTRA_CFLAGS="-DREFCNT_CHECKING=1"` by `tests/make` or set
  by the sanitizers. `make_static` is not in the `run` list of `tests/make`.
  get_current_dir_name() is not feature-tested. Skeletons are built by
  `bpf_skel.mak`, need libopenssl, and are switched off with
  `BUILD_BPF_SKEL=0`; reader C offered NO_BPF_SKEL, which does not exist.
  util/python-ext-sources is gone (readers A and B named it); the Python module
  is built from `util/python.c` by `util/setup.py` against the static
  libraries.

## What only some readers got wrong

Reader B, in addition:

- `attr`, `tracing_data`, `build_id` and `id_index` default to working
  handlers. They default to stubs. The defaults that are not stubs are
  `context_switch`, `ksymbol`, `bpf` and `text_poke`, which update the
  machine; `lost`, `lost_samples`, `aux`, `itrace_start` and
  `aux_output_hw_id`, whose functions only print under the dump option, though
  `machines__deliver_event()` counts losses only while they stay at the
  default; and `finished_round` and `compressed`, which are conditional. The
  measurement checker called all nine working, and so did the first builder;
  the question now asks what each default ends up doing.
- `perf_session__new()` returns NULL on failure. It returns an error pointer
  and every command checks `IS_ERR()`.
- A kernel patch that changes a header must also update the copy under
  `tools/include`. The README says not to touch the copy.
- Only thread and map are checked structs; the thread table is one red-black
  tree; `pr_info()` needs a verbose flag; the io_dir helpers are io_dir__open()
  and io_dir__read(); the feature macros are FEAT_OPA and FEAT_OPP; the pipe
  format is not detected from the magic; `record__init_features()` needs a line
  per feature. None of these is so.

Readers A and B:

- A regular file in pipe format is not detected unless asked for. It is:
  `perf_session__read_header()` tries `perf_header__read_pipe()` on every
  input.
- The session's evlist is NULL before the attributes arrive on a pipe. It is
  allocated empty by `perf_session__read_header()`.
- `evsel__detect_missing_features()` probes each feature once. It probes
  newest first, stops at the first the kernel accepts, and runs only after
  `-EINVAL`.

Reader C alone: `perf_env__arch()` fills in `env->arch` (it does not), and a
perf_env__raw_arch() that is not in the tree.

## What the readers already knew

Readers A and C answered these with little or nothing to correct: the entry
points, the documentation files, how to put a struct under reference count
checking, which lookups return a reference (`machine__find_thread()`,
`maps__find()`) and which a borrowed pointer, how optional code is guarded and
stubbed, the kinds of PMU, what changes with a new sample field, how C test
suites are declared, and `perf_tool__init()` itself. Reader B was rewritten by
more than 60% on every question except the entry points and lookups.

## Where the hand-written guide is stale

- It says omitted callbacks are silently dropped. Most default to a stub that
  prints "unhandled" under the dump option, but four default to handlers that
  update the machine and five more to handlers the session's loss accounting
  looks for, and nothing is filled in unless `perf_tool__init()` ran.
- It gives -ENOTSUPP as what a header stub returns. That name appears nowhere
  under `tools/perf`; stubs return 0 with a one-time warning, -1, -EOPNOTSUPP
  or -ENOTSUP.
- It says `perf_env` is populated by `perf_session__new()` and must be checked
  for initialisation, without naming the accessors that do the checking
  (`perf_env__get_cpu_topology()`, `perf_env__arch()`,
  `perf_env__nr_cpus_avail()`), and it predates `HEADER_E_MACHINE` and the
  per-object ELF machine accessors it recommends only in outline.
- It says where architecture code must not go but not where it goes; the five
  `util/*-arch` directories are not mentioned.
- It lists thread, maps and dso as the checked structs; evlist, map, nsinfo,
  mem_info, comm_str and the libperf cpu map are checked too. It does not
  mention `RC_CHK_ACCESS` or `RC_CHK_EQUAL`, which are what a patch most often
  gets wrong.
- It calls error pointers highly discouraged. Nothing in the tree says so, and
  `perf_session__new()` and `evsel__newtp()` return them to callers that check
  `IS_ERR()`.
- Its libc header rule is not written down in the tree either; the only
  evidence is a comment about musl in `util/event.h`.
- It says nothing about validating records from a file, which is now a large
  part of `util/session.c`.

## What was left out of the build set and why

Twenty-two of the 54 questions are in the build set. Left out because readers
A and C already answer them: entry points, documentation, the libperf split,
naming, `perf_tool__init()`, ordering, the delegate, making a struct checked,
lookups that return references, the feature detection flow, PMU kinds, a new
sample field, C test suites. Left out for space although readers were wrong:
the source layout (the new directories are in the analysis-code table), core
objects, record dispatch and adding a record type, the file layout, pipe
detection, the feature table, byte swapping, the arch directory (covered by
the analysis-code table and the rule), locks, default-off features, the build
matrix, skeletons, messages, event parsing, opening on older kernels, the JSON
tables and shell tests. Most of those are maps of code a reader can open.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader A          113        36%     12     28   6.10 to 6.18
reader B          141        77%      0     53   6.10 to 6.12
reader C          117        26%     16     13   6.12 to 7.0

question                       reader A      reader B      reader C
perf.source-layout             18% ( 3)      77% ( 3)      22% ( 4)
perf.entry-points               1% ( 1)      21% ( 2)       1% ( 1)
perf.docs                       0% ( 0)      66% ( 2)       0% ( 0)
perf.core-objects              38% ( 4)      76% ( 2)      18% ( 2)
perf.libperf-split             30% ( 1)      68% ( 1)      25% ( 1)
perf.naming-conventions        41% ( 2)      66% ( 1)      20% ( 1)
perf.tool-init                 11% ( 1)      74% ( 1)      14% ( 3)
perf.tool-defaults             57% ( 2)      79% ( 2)      34% ( 1)
perf.tool-mmap-pair            47% ( 1)      85% ( 3)      42% ( 1)
perf.tool-ordering             27% ( 1)      81% ( 3)       0% ( 0)
perf.tool-delegate             16% ( 1)      68% ( 1)      23% ( 1)
perf.event-dispatch            20% ( 2)      72% ( 1)      54% ( 1)
perf.new-record-type           14% ( 1)      78% ( 3)      45% ( 1)
perf.file-layout               36% ( 1)      85% ( 1)      14% ( 1)
perf.pipe-mode                 59% ( 3)      79% ( 3)      16% ( 1)
perf.pipe-attrs-features       53% ( 2)      76% ( 2)      11% ( 1)
perf.header-features           59% ( 1)      86% ( 2)       0% ( 0)
perf.new-feature               46% ( 1)      81% ( 1)      22% ( 1)
perf.unknown-features          65% ( 2)      88% ( 1)      65% ( 1)
perf.env-ownership             45% ( 3)      81% ( 5)      45% ( 5)
perf.env-usage                 59% ( 3)      90% ( 4)      32% ( 5)
perf.untrusted-input           64% ( 5)      89% ( 7)      75% ( 3)
perf.byte-swap                 33% ( 2)      88% ( 4)      28% ( 1)
perf.arch-dir                  40% ( 2)      94% ( 3)      50% ( 4)
perf.arch-analysis-code        50% ( 4)      62% ( 3)      28% ( 4)
perf.e-machine                 81% ( 3)      86% ( 1)      42% ( 4)
perf.arch-usage                45% ( 3)      81% ( 1)      22% ( 2)
perf.rc-mechanism              26% ( 4)      81% ( 5)      22% ( 5)
perf.rc-structs                45% ( 3)      88% ( 2)      22% ( 3)
perf.rc-access                 69% ( 1)      85% ( 2)       8% ( 2)
perf.rc-new-struct              8% ( 0)      72% ( 2)      10% ( 0)
perf.lookup-references          1% ( 1)      43% ( 1)       0% ( 0)
perf.location-lifetime         32% ( 4)      73% ( 3)      23% ( 3)
perf.evlist-lifetime           76% ( 3)      75% ( 2)      76% ( 3)
perf.shared-state-locks        28% ( 3)      75% ( 3)      32% ( 3)
perf.feature-flow              15% ( 4)      87% ( 7)      28% ( 4)
perf.new-feature-test           8% ( 1)      88% ( 1)      25% ( 1)
perf.feature-guards             0% ( 0)      76% ( 1)      13% ( 1)
perf.optin-features            35% ( 1)      87% ( 1)      28% ( 2)
perf.build-matrix              59% ( 1)      85% ( 1)      50% ( 2)
perf.libc-portability          66% ( 6)      81% ( 7)      53% ( 8)
perf.kernel-header-copies      59% ( 3)      73% ( 2)      55% ( 4)
perf.bpf-skeletons             54% ( 3)      82% ( 2)      50% ( 5)
perf.error-returns              8% ( 1)      81% ( 4)      27% ( 3)
perf.output-logging            43% ( 3)      92% ( 2)       3% ( 1)
perf.dir-iteration             55% ( 3)      77% ( 2)      22% ( 1)
perf.event-parsing             19% ( 1)      73% ( 4)      24% ( 3)
perf.pmu-kinds                 10% ( 1)      87% ( 2)       8% ( 2)
perf.open-fallback             72% ( 1)      79% ( 2)       3% ( 1)
perf.sample-format             21% ( 1)      64% ( 2)       8% ( 1)
perf.pmu-events-json           40% ( 2)      87% ( 3)      38% ( 2)
perf.test-suites                0% ( 0)      82% ( 5)      10% ( 1)
perf.shell-tests               49% ( 2)      80% ( 3)      37% ( 4)
perf.change-checklist          43% ( 5)      76% ( 7)      34% ( 2)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `perf.event-dispatch`, `perf.pipe-mode`, `perf.header-features`, `perf.arch-dir`, `perf.open-fallback`, `perf.shell-tests`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `perf.source-layout`, `perf.core-objects`, `perf.tool-init`, `perf.tool-ordering`, `perf.new-record-type`, `perf.file-layout`, `perf.rc-mechanism`, `perf.feature-flow`, `perf.pmu-kinds`, `perf.sample-format`, `perf.test-suites`.

## Questions reorganised

Organised by subject, 41 questions before and 36 after: recorded and host architecture, object
lifetime and reference counts, tool callbacks and records, file and pipe formats, the recorded
environment, events and PMUs, optional features and portable builds, tests.
Merged: `perf.arch-analysis-code` + `perf.arch-dir` into `perf.arch-code-placement`;
`perf.rc-mechanism` + `perf.rc-structs` into `perf.rc-checking`; `perf.file-layout` +
`perf.pipe-mode` into `perf.file-and-pipe`; `perf.header-features` into `perf.new-feature`;
`perf.feature-flow` + `perf.new-feature-test` into `perf.feature-detection`. Replaced, as an
inventory: `perf.change-checklist` by `perf.python-module`, the one thing in it readers had wrong.
