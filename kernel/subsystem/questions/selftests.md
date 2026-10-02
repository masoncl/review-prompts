# Questions: Kernel selftests

- guide: selftests.md
- title: Selftests Subsystem Details

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/selftests-measurement.md` is the
wider set the readers were measured on and `catalogue/selftests-measurement-results.md` says what
they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## selftests.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## selftests.core-files: Core files

- section: Finding your way
- relevance: 4 - the framework is a dozen small files that reviewers rarely open

A table and nothing else, job to file, for the framework itself as opposed to any one subsystem's
tests: the common make rules; the top-level Makefile; the C reporting header; the C test harness;
the runner scripts; the shell and Python reporting helpers; the helper for tests that are kernel
modules; the scripts for installing and packaging. Start from `tools/testing/selftests/lib.mk`
and `tools/testing/selftests/kselftest/`.

## selftests.subsystem-libraries: Shared helper libraries

- section: Finding your way
- relevance: 4 - a new test that rewrites a helper is the usual review finding

A table and nothing else, test directory to the shared helper library that new tests in it are
expected to use, with one line on what it provides: mm, net (shell, Python and C), drivers/net,
net/forwarding, kvm, bpf, cgroup, arm64 and filesystems. Where a reader is likely to name a
header or a file that does not exist, say so in the row.

# Makefiles, building and installing

## selftests.test-variables: Test list variables

- section: Makefiles, building and installing
- relevance: 5 - a file in the wrong variable, or in none, is missing after install

A table of the variables to choose between when a test Makefile tells `lib.mk` about a file
(`TEST_PROGS`, `TEST_GEN_PROGS`, `TEST_FILES` and the rest): for each, is the file built by the
common rule, run by `run_tests`, listed for the installed runner, copied by `install`, and
removed by `clean`?

## selftests.support-files: Sourced and imported files

- section: Makefiles, building and installing
- relevance: 5 - works from the source tree, fails once installed

What are the requirements for the Makefile of a test script that sources a shell library, imports
a Python module or reads a data file, in order to assure that the test also runs from an installed
copy and from an out-of-tree build? How does `TEST_INCLUDES` differ from `TEST_FILES` in where the
copies land, and what does it refuse? Name in-tree Makefiles that show each. Start from
`INSTALL_INCLUDES` in `tools/testing/selftests/lib.mk`.

## selftests.output-prefixing: Generated file paths

- section: Makefiles, building and installing
- relevance: 4 - a rule written for the bare name never fires in an out-of-tree build

What does including `lib.mk` do to the values of `TEST_GEN_PROGS`, `TEST_GEN_PROGS_EXTENDED` and
`TEST_GEN_FILES`, and how must a Makefile that adds its own rule or prerequisite for one of those
files after the include name the target? Does the same happen to `TEST_PROGS`?

## selftests.kernel-headers: Kernel and tools headers

- section: Makefiles, building and installing
- relevance: 4 - a test of a new uAPI must not build against the distribution's headers

What are the requirements for a test Makefile in order to assure that the test builds against the
uAPI headers of the tree it is built from and not against those installed on the build machine,
and what has to be run first? Does `lib.mk` add `KHDR_INCLUDES` or `TOOLS_INCLUDES` to `CFLAGS` by
itself?

## selftests.target-selection: Selecting test directories

- section: Makefiles, building and installing
- relevance: 4 - decides whether a new test is ever built

What decides whether a test directory is built and run by default, and what still filters a
directory that a user names on the command line? What is added automatically when networking
tests are selected, and is it run? Start from `TARGETS` and `SKIP_TARGETS`.

## selftests.build-failure-status: Build failures across directories

- section: Makefiles, building and installing
- relevance: 3 - a partial build can look like success

When one test directory fails to build, does `make -C tools/testing/selftests` fail? State how
the exit status of the `all` and `install` targets is computed from the per-directory results,
and which variable changes that.

## selftests.install-layout: Installed tree layout

- section: Makefiles, building and installing
- relevance: 4 - tests are usually run from an installed copy

What does `make -C tools/testing/selftests install` produce that the installed runner depends
on, and what decides whether a test appears in the list that runner reads? What is installed
from a test directory without being named in any `TEST_` variable?

## selftests.new-directory-checklist: Adding a test directory

- section: Makefiles, building and installing
- relevance: 4 - the steps are spread over the documentation and two Makefiles

Which files must a new test directory under `tools/testing/selftests/` contain, and what outside
the directory must change for it to be built by default? Which make invocations does the
documentation say every change must still pass? Start from the detailed contributing section of
`Documentation/dev-tools/kselftest.rst`.

# The runner

## selftests.runner-flow: Working directory, stdout and stderr

- section: The runner
- relevance: 4 - what a test sees when it starts

What working directory does `run_one()` give a test program, and where do the program's stdout and
stderr go? Start from `run_many()` and `run_one()` in
`tools/testing/selftests/kselftest/runner.sh`.

## selftests.exit-codes: Exit codes

- section: The runner
- relevance: 5 - the runner looks at nothing else

How does `run_one()` turn each exit status of a test program, including a timeout and a value that
is no kselftest exit code, into a result line? Is every code defined beside `KSFT_PASS` given its
own result? Start from `KSFT_PASS` in `tools/testing/selftests/kselftest.h` and the `case` in
`run_one()`.

## selftests.runner-exit-status: Runner exit status

- section: The runner
- relevance: 4 - automation that checks only the exit status of make sees nothing

When tests fail, what is the exit status of `make run_tests` (or of `make kselftest`), and of the
installed `run_kselftest.sh`? Which option changes the latter?

## selftests.runner-timeouts: Per-test timeout

- section: The runner
- relevance: 4 - long tests are killed unless they say otherwise

What time limit does `runner.sh` give each test program, and how does a test directory, or a user,
change or disable it? What happens if the `timeout` utility is missing?

## selftests.unrunnable-tests: Missing and non-executable tests

- section: The runner
- relevance: 4 - the symptom of a file left out of the Makefile or committed without its mode

What does the runner do when a listed test file does not exist, when it exists but has no execute
bit, and when the directory has a `ksft_runner.sh`? Name a directory that has one.

## selftests.nested-output: Nested test output

- section: The runner
- relevance: 3 - parsers depend on it

How does the output of a test program appear inside the runner's own TAP stream: indented as the
KTAP specification describes, or marked some other way? Who prints the version line and the plan
when tests are run with `make run_tests` and when they are run with the installed runner, and
what does the `KSFT_TAP_LEVEL` environment variable do and who sets it?

# Reporting from plain C

## selftests.ksft-call-order: Plain C test structure

- section: Reporting from plain C
- relevance: 4 - the skeleton every non-harness test follows

In a C test that does not use the harness, which `kselftest.h` calls are made in which order,
from the header to the exit? What does the comment at the top of `kselftest.h` say about when to
use it rather than the harness?

## selftests.ksft-result-functions: Result functions

- section: Reporting from plain C
- relevance: 4 - each prints a different TAP line

A table of the functions and macros in `kselftest.h` to choose between when reporting one test
case's result: for each, the TAP line it prints (ok or not ok, and any directive) and the counter
it increments. Include the ones that take a condition or a kselftest exit code.

## selftests.ksft-exit-functions: Exit functions

- section: Reporting from plain C
- relevance: 4 - the exit code is what the runner records

A table of the `ksft_exit_*` functions and macros to choose between: for each, the process exit
code and what it prints before exiting. Which of them print "Bail out!"?

## selftests.ksft-finished-condition: ksft_finished pass condition

- section: Reporting from plain C
- relevance: 4 - the plan is part of the verdict

What exactly does `ksft_finished()` compare to decide between a passing and a failing exit, which
result kinds count as success, and what happens when fewer or more results were reported than
planned?

## selftests.ksft-error-result: Error results

- section: Reporting from plain C
- relevance: 3 - its meaning is easy to invent

What does `ksft_test_result_error()` print and count, how does it affect `ksft_finished()`, and
what does the tree say about how "error" differs from "fail" or "skip"?

## selftests.main-exit-usage: Exiting from main

- section: Reporting from plain C
- relevance: 4 - the recorded result is the exit status

What are the requirements for the exit status of a plain C selftest in order to assure that the
runner records the right result? What does the runner record for a test that prints its own pass
and fail text with `printf()` and returns 0 or 1, and what does the documentation require such a
test to use?

# The test harness

## selftests.harness-macros: Harness macros

- section: The test harness
- relevance: 4 - the vocabulary of most new C tests

When is each of the macros that `kselftest_harness.h` gives for defining a test or a fixture
chosen over the others? Which of them are missing from the list rendered into
`Documentation/dev-tools/kselftest.rst`?

## selftests.harness-process-model: Processes per test

- section: The test harness
- relevance: 4 - explains what state survives between tests and who sees a crash

In which process do a fixture's setup, the test body and the teardown run for a `TEST()` and for a
`TEST_F()`, and which process sees a crash in each? What is reset in the child before the test
function is called? Start from `__run_test()` and `__TEST_F_IMPL()`.

## selftests.harness-assert-expect: ASSERT and EXPECT

- section: The test harness
- relevance: 4 - what runs after a failure differs

What does a failed `ASSERT_*` do that a failed `EXPECT_*` does not, and does the fixture teardown
still run after it? What is the optional block or `TH_LOG()` that may follow either, and when
does it execute? Start from `__EXPECT()`, `OPTIONAL_HANDLER()` and `__bail()`.

## selftests.harness-timeout: Harness timeout

- section: The test harness
- relevance: 4 - there are two timers and the inner one is shorter

What time limit does `kselftest_harness.h` apply to each test, and how does that limit relate to
the runner's limit on the whole program? What does the harness do to the test's processes when the
limit expires?

## selftests.harness-timeout-report: Timeout override and report

- section: The test harness
- relevance: 4 - a test that needs longer than the limit is reported as failed unless it says so

How does a harness test change the time limit of one test, and what result does the harness report
for a test whose limit expired?

## selftests.harness-xfail: Expected failures

- section: The test harness
- relevance: 3 - the runner treats the two outcomes differently

How does a harness test declare that one test of one fixture variant is expected to fail, and
what is reported when that test then fails and when it passes?

## selftests.harness-exit-status: Harness exit status

- section: The test harness
- relevance: 3 - skipped tests count on the passing side

What does a harness-based binary exit with when all tests pass, when one fails, and when every
test was skipped? Which per-test outcomes, a test expected to fail that passed included, count
on the passing side? Start from `__test_passed()` and `test_harness_run()`.

## selftests.harness-forked-children: Assertions in forked children

- section: The test harness
- relevance: 3 - many tests fork inside the body

When a harness test body forks, can the child use `ASSERT_*` and `EXPECT_*` and have the parent's
verdict reflect it? Say what is shared between the processes and what is not, and what a failed
`ASSERT_*` in such a child does.

## selftests.harness-ksft-mixing: Low-level calls inside harness tests

- section: The test harness
- relevance: 4 - the harness checks for it

What are the requirements for calling the `kselftest.h` result and exit functions inside a
`TEST()` or `TEST_F()` body in order to assure safe usage? What does `__run_test()` check after
the test function returns, and what does it do when the check fails? Start from the check made
after the test function returns in `__run_test()`.

## selftests.harness-own-test: Testing the harness

- section: The test harness
- relevance: 3 - a change to the harness output has a reference file

Is there a test for `kselftest_harness.h` itself? If so, where is it, how does it decide pass or
fail, and what must a patch that changes the harness's output also change?

# Skipping

## selftests.ksft-exit-skip-usage: Skipping a whole program

- section: Skipping
- relevance: 4 - the most misused call in the header

What does `ksft_exit_skip()` print when called before any plan or result, and what when a plan
has been set or results reported? Which usage does the header itself call a misuse, and what
does it say those tests should call instead?

## selftests.harness-skip: SKIP in the harness

- section: Skipping
- relevance: 4 - a skip that does not leave the function keeps running

What does `SKIP(statement, fmt, ...)` do with its `statement`, and what is the result of a test
that calls it and then carries on because the statement did not leave the function? What happens
to a fixture's test when `SKIP()` is used in `FIXTURE_SETUP()`, and does teardown run?

## selftests.skip-usage: Missing prerequisites

- section: Skipping
- relevance: 5 - a false failure sends people hunting for a regression that is not there

What are the requirements for a plain C test, a harness test and a shell test whose prerequisite
is missing, in order to assure that an environment difference is not reported as a failure? Which
documented rule does this follow from? Name in-tree tests that show it.

## selftests.skip-absent-or-broken: Absent and broken features

- section: Skipping
- relevance: 5 - a test that skips on every error hides a feature that is present and broken

How does a test tell a feature that is absent from one that is present but broken, so that it
skips for the first and fails for the second? Name in-tree tests that show it.

# Shell and Python tests

## selftests.ktap-shell-helpers: Shell reporting helpers

- section: Shell and Python tests
- relevance: 4 - the shell counterpart of the C header

What does a shell test that reports through `tools/testing/selftests/kselftest/ktap_helpers.sh`
call, from the header to finishing, and what decides its exit status at the end? How does the
script locate and source the file so that it works both in the source tree and installed? Name a
test that shows it.

## selftests.net-shell-lib: Networking shell library

- section: Shell and Python tests
- relevance: 4 - nearly every networking shell test sources it

What does `setup_ns` in `tools/testing/selftests/net/lib.sh` guarantee about a namespace it makes,
and what removes the namespaces when the test exits? How does the library combine the results of
several checks within one test, and of several tests, into the exit status?

## selftests.net-python-lib: Networking Python library

- section: Shell and Python tests
- relevance: 4 - new networking tests are increasingly Python

In a Python networking selftest built on `tools/testing/selftests/net/lib/py/`, how does a test
report skip, expected failure and failure, and when does cleanup registered with `defer` run? What
do `ksft_run()` and `ksft_exit()` each contribute to the exit status?

# Network namespaces

## selftests.netns-devconf-inherit: Device config in new namespaces

- section: Network namespaces
- relevance: 5 - decides whether a test depends on the machine it runs on

When a network namespace is created, where do its IPv4 and IPv6 conf/all and conf/default values
come from? Give a table by value of the net.core sysctl `devconf_inherit_init_net` for each
family, and say what the default value is. Start from `devinet_init_net()` and
`addrconf_init_net()`.

## selftests.netns-devconf-usage: Pinning per-device sysctls

- section: Network namespaces
- relevance: 5 - passes in CI, fails on a developer's machine, or the reverse

What are the requirements for a test that relies on `forwarding`, `rp_filter`, `accept_local` or
another per-device setting inside its own namespace, in order to assure that the result does not
depend on the host? Does a write to the per-device value undo a value the namespace inherited?
Name an in-tree test or helper that shows it.

# KVM selftests

## selftests.kvm-vm-create: VM creation helpers

- section: KVM selftests
- relevance: 4 - which helper was used decides what state the VM is in

Which of the VM creation helpers in `tools/testing/selftests/kvm/include/kvm_util.h` create vCPUs
and which only create the VM? Which architecture hooks run at VM creation and which after the
vCPUs exist, and what has to call the latter when a test adds its vCPUs itself? Start from
`__vm_create()` and `__vm_create_with_vcpus()`.

## selftests.kvm-default-irqchip: Default interrupt controller

- section: KVM selftests
- relevance: 4 - differs by architecture and has changed

What does `kvm_arch_has_default_irqchip()` return on each architecture, and on what does that
depend? What does the library set up by default when it creates a VM?

## selftests.kvm-irqchip-usage: Interrupt ioctls after VM creation

- section: KVM selftests
- relevance: 4 - the outcome differs by ioctl and by architecture

What do `KVM_IRQFD`, `KVM_IRQ_LINE` and `KVM_SET_GSI_ROUTING` each return on arm64 when the VM's
interrupt controller is not initialised? What must a KVM selftest that created its VM without
vCPUs do before it issues them? Name the in-tree test that shows it. Start from
`kvm_irqfd_assign()` and `kvm_vgic_inject_irq()`.

# Model gaps

## selftests.model-gaps: Other mistakes models make

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
