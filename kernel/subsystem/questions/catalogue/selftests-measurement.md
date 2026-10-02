# Questions: Kernel selftests (measurement set)

- guide: selftests.md
- title: Selftests Subsystem Details

A wide set of questions about `tools/testing/selftests` as a framework: the
make machinery in `lib.mk`, installing and the runner, the C reporting header,
the test harness, the shell and Python helpers, the documented rules for
tests, and the shared libraries of the larger test directories. It is used to
measure what a model already knows before deciding what the built guide should
spend its words on. The hand-written guide it will replace is 2,292 words, most
of them rules for reviewing a new test; it also carries a KVM selftest section
and a network namespace section, which are asked about here too. No one
subsystem's tests are covered beyond the helper libraries new tests are
expected to use. Format: `../../../docs/subsystem-questions.md`.

# The framework

## selftests.core-files: Core files

- section: Finding your way
- relevance: 4 - the framework is a dozen small files that reviewers rarely open
- words: 110

Which files make up the selftest framework itself, as opposed to any one
subsystem's tests: the common make rules, the top-level Makefile, the C
reporting header, the C test harness, the runner scripts, the shell and Python
reporting helpers, the helper for tests that are kernel modules, and the
scripts for installing and packaging? A table of file and job. Start from
`tools/testing/selftests/lib.mk` and `tools/testing/selftests/kselftest/`.

## selftests.docs: Documentation

- section: Finding your way
- relevance: 3 - the rules a reviewer quotes live in two files
- words: 70

Which files under `Documentation/dev-tools/` describe how selftests are built,
run, installed and written, and the output format they must produce? Does that
documentation name any example file or directory that is not in this tree?
Which `MAINTAINERS` entry covers the framework files, and which mailing list
does it give?

## selftests.top-make-targets: Top-level make targets

- section: Building and running
- relevance: 3 - these are what CI invokes
- words: 80

Which targets in the kernel's top-level `Makefile` build, run, install, clean
and prepare a config for the selftests, what does each one run, and which of
them depend on the exported kernel headers being installed first?

## selftests.selftests-make-targets: Targets of the selftests Makefile

- section: Building and running
- relevance: 3 - each target is a loop over the chosen directories
- words: 80

Which targets does `tools/testing/selftests/Makefile` provide, and for each,
what does it do in every selected test directory? Include the ones for the
hotplug tests and for packaging.

## selftests.target-selection: Selecting test directories

- section: Building and running
- relevance: 4 - decides whether a new test is ever built
- words: 80

How does the selftests Makefile decide which test directories to build and
run: which variables can a user set, which directories are left out by default
and why, and which directory is added automatically when networking tests are
selected? Start from `TARGETS` and `SKIP_TARGETS`.

## selftests.build-failure-status: Build failures across directories

- section: Building and running
- relevance: 3 - a partial build can look like success
- words: 60

When one test directory fails to build, does `make -C tools/testing/selftests`
fail? State how the exit status of the `all` and `install` targets is computed
from the per-directory results, and which variable changes that.

## selftests.new-directory-checklist: Adding a test directory

- section: Building and running
- relevance: 4 - the steps are spread over the documentation and two Makefiles
- words: 90

What does adding a new test directory under `tools/testing/selftests/`
involve: the files the directory needs, the line that has to be added
elsewhere, and the set of make invocations the documentation says every change
must still pass? Start from the detailed contributing section of
`Documentation/dev-tools/kselftest.rst`.

## selftests.kernel-headers: Kernel and tools headers

- section: Building and running
- relevance: 4 - a test of a new uAPI must not build against the distribution's headers
- words: 80

How does a test get the uAPI headers of the tree it is built from rather than
those installed on the build machine? Say what `KHDR_INCLUDES` and
`TOOLS_INCLUDES` expand to, who sets them, whether `lib.mk` adds either to
`CFLAGS` by itself, and what has to be run first.

## selftests.out-of-tree-build: Separate output directory

- section: Building and running
- relevance: 3 - the out-of-tree run is where missing files show up first
- words: 80

How do `O=`, `KBUILD_OUTPUT` and `OUTPUT` interact when selftests are built
outside the source tree: where do objects go, and what does `run_tests` copy
into the output directory before running when `building_out_of_srctree` is
set?

## selftests.cross-compile: Cross compiling and clang

- section: Building and running
- relevance: 2 - matters when a test adds its own compiler flags
- words: 60

How does `lib.mk` choose the compiler for `CROSS_COMPILE`, `LLVM` and `ARCH`,
and what happens for clang when the architecture has no entry in its target
table? Which variables let a user add compiler and linker flags from the
command line?

# The make machinery

## selftests.test-variables: Test list variables

- section: The lib.mk variables
- relevance: 5 - a file in the wrong variable, or in none, is missing after install
- words: 130

Give a table of the variables a test Makefile sets to tell `lib.mk` about its
files (`TEST_PROGS`, `TEST_GEN_PROGS`, `TEST_FILES` and the rest): for each,
is the file built by the common rule, run by `run_tests`, listed for the
installed runner, copied by `install`, and removed by `clean`?

## selftests.extended-variables: Programs not run by default

- section: The lib.mk variables
- relevance: 3 - helpers that a test script invokes belong here
- words: 50

Which variables hold executables that are built or installed with the tests
but not run by `run_tests`, and what are they typically used for? Name a
Makefile in the tree that uses one.

## selftests.test-includes: Files from other directories

- section: The lib.mk variables
- relevance: 4 - shared libraries cross directory boundaries
- words: 70

How does a test directory declare that it needs files that live in another
selftests directory, so that they are present after `install` and in an
out-of-tree run? How does that variable differ from `TEST_FILES` in where the
copies land, and what does it refuse? Start from `INSTALL_INCLUDES` in
`tools/testing/selftests/lib.mk`.

## selftests.support-file-usage: Sourced and imported files

- section: The lib.mk variables
- relevance: 5 - works from the source tree, fails once installed
- words: 90

A test script sources a shell library, imports a Python module, or reads a
data file. What usage leaves the test working from the source tree but failing
from an installed copy, and what is the correct declaration for a file in the
same directory and for one in another directory? Name in-tree Makefiles that
show each.

## selftests.module-directory: Test kernel modules

- section: The lib.mk variables
- relevance: 2 - a few directories carry their own modules
- words: 50

How does a test directory have kernel modules built, installed and cleaned
along with it? Start from `TEST_GEN_MODS_DIR` and name a directory that uses
it.

## selftests.custom-build-rules: Custom build rules

- section: The lib.mk variables
- relevance: 3 - the escape hatches change what lib.mk still does
- words: 70

When a test cannot use the common compile rule, what are the two mechanisms
`lib.mk` offers, one per program and one for the whole Makefile, and what does
each leave the Makefile responsible for? Start from `TEST_CUSTOM_PROGS` and
`OVERRIDE_TARGETS`.

## selftests.default-compile-rule: Common compile rule

- section: The lib.mk variables
- relevance: 3 - most test Makefiles are three lines because of it
- words: 80

What does the common rule in `lib.mk` build a generated program from, which
headers does every such program depend on, which flags does `lib.mk` add for
everyone, and how does a Makefile add libraries, extra source files or extra
header dependencies? Start from `LOCAL_HDRS` and `LDLIBS`.

## selftests.output-prefixing: Generated file paths

- section: The lib.mk variables
- relevance: 4 - a rule written for the bare name never fires in an out-of-tree build
- words: 60

What does including `lib.mk` do to the values of `TEST_GEN_PROGS`,
`TEST_GEN_PROGS_EXTENDED` and `TEST_GEN_FILES`, and how must a Makefile that
adds its own rule or prerequisite for one of those files after the include
name the target? Does the same happen to `TEST_PROGS`?

## selftests.install-layout: Installed tree layout

- section: Installing and packaging
- relevance: 4 - tests are usually run from an installed copy
- words: 90

What does `make -C tools/testing/selftests install` produce: the directory
layout, the framework scripts copied in, the per-directory files, and the
generated files at the top? Which per-directory files that are not named in
any `TEST_` variable are installed automatically?

## selftests.test-list: Installed test list

- section: Installing and packaging
- relevance: 3 - a test missing from the list is never run
- words: 60

How is the list of tests that the installed runner can run generated, what is
the format of an entry, which `TEST_` variables contribute to it, and what
happens to a directory that failed to build? Start from the `emit_tests`
target.

## selftests.install-path: Install location

- section: Installing and packaging
- relevance: 2 - two variables with nearly the same name
- words: 50

Where do the selftests install by default, and which variables override that?
Explain why there are two variables and which one a caller going through the
kernel's top-level `Makefile` has to use.

## selftests.packaging: Packaging

- section: Installing and packaging
- relevance: 2 - rarely touched
- words: 50

How is a tarball of the installed tests made, which variable picks the
compression, and what is the status of the `kselftest_install.sh` and
`gen_kselftest_tar.sh` scripts relative to the make targets?

# The runner

## selftests.runner-flow: Running one test

- section: The runner
- relevance: 4 - what a test sees when it starts
- words: 100

What happens between `run_tests` (or the installed runner) and one test
program executing: which script and functions are involved, what is the
working directory, what happens to the test's stdout and stderr, and what line
does the runner print for the result? Start from `run_many()` and `run_one()`
in `tools/testing/selftests/kselftest/runner.sh`.

## selftests.exit-codes: Exit codes

- section: The runner
- relevance: 5 - the runner looks at nothing else
- words: 90

What are the kselftest exit codes and their values, and how does the runner
turn each exit status of a test program, including a timeout and any other
value, into a result line? Is every defined code given its own result? Start
from `KSFT_PASS` in `tools/testing/selftests/kselftest.h` and the `case` in
`run_one()`.

## selftests.runner-timeouts: Per-test timeout

- section: The runner
- relevance: 4 - long tests are killed unless they say otherwise
- words: 80

What is the default time limit the runner gives each test program, how does a
test directory change it, how does a user override it, what value disables it,
how is an expiry reported, and what happens if the `timeout` utility is
missing?

## selftests.settings-file: Settings file

- section: The runner
- relevance: 3 - the file is evaluated, not just read
- words: 50

Where does the runner look for a test directory's `settings` file, how is each
line parsed and turned into a variable, and which keys does anything in the
runner actually read?

## selftests.unrunnable-tests: Missing and non-executable tests

- section: The runner
- relevance: 4 - the symptom of a file left out of the Makefile or committed without its mode
- words: 70

What does the runner do when a listed test file does not exist, when it exists
but has no execute bit, and when the directory has a `ksft_runner.sh`? Which
directory in the tree uses `ksft_runner.sh`?

## selftests.test-arguments: Arguments for a test

- section: The runner
- relevance: 2 - a convenience few know about
- words: 50

Can a user pass command line arguments to one test program through the runner?
If so, how is the name of the environment variable derived from the test's
file name?

## selftests.installed-runner-options: Installed runner options

- section: The runner
- relevance: 2 - the script's own help text covers it
- words: 80

Which options does `run_kselftest.sh` take, how are a collection and a test
named on its command line, and what do the options for running each test in
its own network namespace and for logging per test do?

## selftests.summary-logging: Summary output

- section: The runner
- relevance: 1 - a logging convenience
- words: 40

What does setting the make variable `summary` change about where each test's
output goes, and does the documentation describe that accurately?

## selftests.runner-exit-status: Runner exit status

- section: The runner
- relevance: 4 - automation that checks only the exit status of make sees nothing
- words: 60

When tests fail, what is the exit status of `make run_tests` (or of
`make kselftest`), and of the installed `run_kselftest.sh`? Which option
changes the latter?

## selftests.nested-output: Nested test output

- section: The runner
- relevance: 3 - parsers depend on it
- words: 70

How does the output of a test program appear inside the runner's own TAP
stream: is it indented as the KTAP specification describes or marked some
other way, which version line do the runner and `ksft_print_header()` print,
and what does the `KSFT_TAP_LEVEL` environment variable do and who sets it?

## selftests.config-fragments: Config fragments

- section: The runner
- relevance: 3 - the only record of what a test needs from the kernel
- words: 60

How does a test directory state which kernel config options it needs, which
file names are recognised, which make target merges them into a `.config`,
and does anything check at run time that the options are enabled?

# Reporting results

## selftests.ksft-call-order: Plain C test structure

- section: Reporting from C
- relevance: 4 - the skeleton every non-harness test follows
- words: 70

In a C test that does not use the harness, which `kselftest.h` calls are made
in which order, from the header to the exit? What does the comment at the top
of `kselftest.h` say about when to use it rather than the harness?

## selftests.ksft-result-functions: Result functions

- section: Reporting from C
- relevance: 4 - each prints a different TAP line
- words: 110

Give a table of the functions and macros in `kselftest.h` that report one test
case's result: for each, the TAP line it prints (ok or not ok, and any
directive) and the counter it increments. Include the ones that take a
condition or a kselftest exit code.

## selftests.ksft-exit-functions: Exit functions

- section: Reporting from C
- relevance: 4 - the exit code is what the runner records
- words: 90

List the `ksft_exit_*` functions and macros: for each, the process exit code
and what it prints before exiting. Which of them print "Bail out!"?

## selftests.ksft-finished-condition: Overall verdict

- section: Reporting from C
- relevance: 4 - the plan is part of the verdict
- words: 60

What exactly does `ksft_finished()` compare to decide between a passing and a
failing exit, which result kinds count as success, and what happens when fewer
or more results were reported than planned?

## selftests.ksft-exit-skip-usage: Skipping a whole program

- section: Reporting from C
- relevance: 4 - the most misused call in the header
- words: 70

What does `ksft_exit_skip()` print when called before any plan or result, and
what when a plan has been set or results reported? Which usage does the header
itself call a misuse, and what does it say those tests should call instead?

## selftests.ksft-error-result: Error results

- section: Reporting from C
- relevance: 3 - its meaning is easy to invent
- words: 60

What does `ksft_test_result_error()` print and count, how does it affect
`ksft_finished()`, and what does the tree say about how "error" differs from
"fail" or "skip"? Roughly how many test files call it?

## selftests.ksft-newlines: Message newlines

- section: Reporting from C
- relevance: 3 - a missing newline glues two TAP lines together
- words: 50

Which of the `kselftest.h` reporting functions append a newline themselves and
which need it in the caller's format string? Cover `ksft_print_msg()`,
`ksft_test_result_pass()`, `ksft_test_result_code()`, `ksft_exit_fail_msg()`
and `ksft_exit_skip()`.

## selftests.ksft-diagnostics: Diagnostic messages

- section: Reporting from C
- relevance: 2 - small, but every test uses them
- words: 50

Which functions print diagnostics from a C test, what prefix do they add, how
is `errno` treated across them, and how does `ksft_print_dbg_msg()` pass its
arguments on?

## selftests.ksft-stdout-buffering: Stdout buffering

- section: Reporting from C
- relevance: 3 - duplicated or lost lines are hard to trace back to this
- words: 50

What does `ksft_print_header()` do to stdout besides printing, and which two
problems does its comment say that avoids? What should a test that forks and
never calls it watch for?

## selftests.ksft-direct-exit-usage: Exiting from main

- section: Reporting from C
- relevance: 4 - the recorded result is the exit status
- words: 80

In a plain C selftest, what usage of `return` from `main()` or of `exit()` is
unsafe for the result the runner records, and what that looks similar is
correct? Consider a test that reports through `kselftest.h` and one that
prints nothing in TAP at all, and say what the runner reports for each.

## selftests.hand-rolled-output-usage: Hand-rolled result output

- section: Reporting from C
- relevance: 4 - the most common review comment on a new test
- words: 80

A C test prints its own pass and fail text with `printf()` and returns 0 or 1.
What does the kselftest runner make of it, what is lost compared with using
`kselftest.h` or the harness, and what does the documentation require? Are
there still such tests in the tree?

## selftests.harness-macros: Harness macros

- section: The harness
- relevance: 4 - the vocabulary of most new C tests
- words: 120

Give a table of the macros `kselftest_harness.h` provides for defining tests
and fixtures, including the signal, timeout, variant, expected-failure and
parent-teardown forms, saying in a few words what each defines. Which of them
are missing from the list rendered into `Documentation/dev-tools/kselftest.rst`?

## selftests.harness-process-model: Processes per test

- section: The harness
- relevance: 4 - explains what state survives between tests and who sees a crash
- words: 90

How many processes does the harness create to run one `TEST()` and one
`TEST_F()`, and in which of them do the fixture setup, the test body and the
teardown run? What is reset in the child before the test function is called?
Start from `__run_test()` and `__TEST_F_IMPL()`.

## selftests.harness-assert-expect: ASSERT and EXPECT

- section: The harness
- relevance: 4 - what runs after a failure differs
- words: 90

What does a failed `ASSERT_*` do that a failed `EXPECT_*` does not, step by
step, including whether the fixture teardown still runs? What is the optional
block or `TH_LOG()` that may follow either, and when does it execute? Start
from `__EXPECT()`, `OPTIONAL_HANDLER()` and `__bail()`.

## selftests.harness-argument-order: Operator arguments

- section: The harness
- relevance: 3 - reviewers ask for the order to be fixed
- words: 50

In `ASSERT_EQ()` and the other comparison operators, which argument is the
expected value and which the observed one, how are they printed on failure,
and does swapping them change the verdict or only the message?

## selftests.harness-skip: SKIP in the harness

- section: The harness
- relevance: 4 - a skip that does not leave the function keeps running
- words: 80

What does `SKIP(statement, fmt, ...)` set and print, what is the `statement`
for, and what is the result of a test that calls it and then carries on
because the statement did not leave the function? What happens to a fixture's
test when `SKIP()` is used in `FIXTURE_SETUP()`, and does teardown run?

## selftests.harness-timeout: Harness timeout

- section: The harness
- relevance: 4 - there are two timers and the inner one is shorter
- words: 70

What time limit does the harness apply to each test, how is it changed for one
test, what does the harness do to the test's processes when it expires, and
how is that reported? How does it relate to the runner's limit on the whole
program?

## selftests.harness-variants: Fixture variants

- section: The harness
- relevance: 3 - the way to avoid copies of a test
- words: 70

How do `FIXTURE_VARIANT()` and `FIXTURE_VARIANT_ADD()` work: what the test,
setup and teardown receive, how many times each `TEST_F()` runs and in what
order, and how the variant appears in the reported test name?

## selftests.harness-xfail: Expected failures

- section: The harness
- relevance: 3 - the runner treats the two outcomes differently
- words: 60

How does a harness test declare that one test of one fixture variant is
expected to fail, what is reported when that test then fails and when it
passes, and how do those two outcomes affect the program's exit status?

## selftests.harness-teardown-parent: Teardown in the parent

- section: The harness
- relevance: 3 - needed when the test drops privileges
- words: 60

What is `FIXTURE_TEARDOWN_PARENT()` for, in which process does that teardown
run, what changes about how `self` is allocated, and how is it guaranteed that
teardown runs only once?

## selftests.harness-signal-tests: Tests expecting a signal

- section: The harness
- relevance: 2 - used by a few security tests
- words: 50

How does `TEST_SIGNAL()` or `TEST_F_SIGNAL()` decide pass or fail: what if the
test exits normally, dies of a different signal, or dies of SIGABRT?

## selftests.harness-options: Harness command line

- section: The harness
- relevance: 2 - useful when reproducing one failure
- words: 70

Which command line options does a harness-based test binary accept for
listing and filtering tests, how do include and exclude filters combine, and
what is the format of the name given to the option that runs a single test?

## selftests.harness-ksft-mixing: Low-level calls inside harness tests

- section: The harness
- relevance: 4 - the harness checks for it
- words: 70

Inside a `TEST()` or `TEST_F()` body, what usage of the `kselftest.h` result
or exit functions is unsafe, what does the harness do about it, and which
`kselftest.h` calls are fine there? Start from the check made after the test
function returns in `__run_test()`.

## selftests.harness-exit-status: Harness exit status

- section: The harness
- relevance: 3 - skipped tests count on the passing side
- words: 60

What does a harness-based binary exit with when all tests pass, when one
fails, and when every test was skipped? How is a test counted as passed for
that purpose? Start from `__test_passed()` and `test_harness_run()`.

## selftests.harness-logging: Harness logging

- section: The harness
- relevance: 2 - where the messages go matters to the runner's prefixing
- words: 40

Where does `TH_LOG()` write, with what prefix, and how is it switched off or
redirected at compile time?

## selftests.harness-own-test: Testing the harness

- section: The harness
- relevance: 3 - a change to the harness output has a reference file
- words: 50

Is there a test for `kselftest_harness.h` itself? If so, where is it, how does
it decide pass or fail, and what must a patch that changes the harness's
output also change?

## selftests.harness-forked-children: Assertions in forked children

- section: The harness
- relevance: 3 - many tests fork inside the body
- words: 70

When a harness test body forks, can the child use `ASSERT_*` and `EXPECT_*`
and have the parent's verdict reflect it? Say what is shared between the
processes and what is not, and what a failed `ASSERT_*` in such a child does.

## selftests.ktap-shell-helpers: Shell reporting helpers

- section: Shell, Python and module tests
- relevance: 4 - the shell counterpart of the C header
- words: 90

Which functions does `tools/testing/selftests/kselftest/ktap_helpers.sh` give
a shell test for the header, the plan, results, skipping everything and
finishing, and what decides the exit status at the end? How does a test script
locate and source it so that it works both in the source tree and installed?
Name a test that uses it.

## selftests.shell-exit-codes: Shell tests without helpers

- section: Shell, Python and module tests
- relevance: 3 - the skip code is a bare number in most scripts
- words: 50

How does a shell test that uses no helper library report a skip to the runner,
and what is the usual way scripts in the tree spell that value? Does the
runner parse a shell test's output for "ok" and "not ok" lines?

## selftests.ksft-python-module: Python reporting module

- section: Shell, Python and module tests
- relevance: 3 - there are two modules with the same name
- words: 70

What does `tools/testing/selftests/kselftest/ksft.py` provide, which result
kinds of the C header does it lack, and how does it differ from the `ksft.py`
under `tools/testing/selftests/net/lib/py/`? How does a test import the
former?

## selftests.module-tests: Kernel module tests

- section: Shell, Python and module tests
- relevance: 3 - the bridge from an in-kernel test to a kselftest result
- words: 80

How is a test that runs as a kernel module tied into kselftest: what
`tools/testing/selftests/kselftest/module.sh` does and returns, what
`kselftest_module.h` provides, and how the module comes to taint the kernel as
a test module?

# Writing tests

## selftests.contribution-rules: Documented rules

- section: Rules for tests
- relevance: 4 - the list reviewers cite
- words: 80

What are the general rules for selftests listed under "Contributing new tests"
in `Documentation/dev-tools/kselftest.rst`? List them as written, without
adding others.

## selftests.skip-usage: Skip or fail

- section: Rules for tests
- relevance: 5 - a false failure sends people hunting for a regression that is not there
- words: 100

When a prerequisite is missing (a config option, a hardware feature, a system
call, a permission), what usage turns an environment difference into a
reported failure, and what is the correct handling? Say which documented rule
this follows from, which call to use in a plain C test, a harness test and a
shell test, and how to tell a feature that is absent from one that is present
but broken. Name in-tree tests that do it correctly.

## selftests.skip-reason: Skip reasons

- section: Rules for tests
- relevance: 3 - the reason is all a later reader has
- words: 60

Where does the reason given to `ksft_test_result_skip()`, `ksft_exit_skip()`
and the harness `SKIP()` end up in the TAP output, and what does the summary
printed at the end say when any test was skipped?

## selftests.older-kernels: Running on older kernels

- section: Rules for tests
- relevance: 3 - mainline tests are run against stable kernels
- words: 70

What does the documentation say about running the mainline selftests on older
stable kernels, and what does that require of a test for a new feature? Is
there a helper for checking the running kernel's version, and what does it do
when it cannot parse it?

## selftests.ktap-format: KTAP result lines

- section: Rules for tests
- relevance: 3 - the format the helpers exist to produce
- words: 80

What is the format of a KTAP test result line, which directives does
`Documentation/dev-tools/ktap.rst` accept and which does it discourage, and
how are lines that fit no format treated? Which of those directives do the
kselftest helpers actually emit?

# Shared libraries

## selftests.subsystem-libraries: Shared helper libraries

- section: Subsystem helper libraries
- relevance: 4 - a new test that rewrites a helper is the usual review finding
- words: 120

Which test directories have a shared helper library that new tests in them are
expected to use, and where is it? A table covering at least mm, net (shell,
Python and C), drivers/net, net/forwarding, kvm, bpf, cgroup, arm64 and
filesystems, with one line on what each provides.

## selftests.mm-helpers: mm helpers

- section: Subsystem helper libraries
- relevance: 3 - the error behaviour differs between the families
- words: 80

Which helpers does `tools/testing/selftests/mm/vm_util.h` declare for reading
and writing sysfs and other files, for numbers, and for reporting results, and
how do they behave on error (return a code, or end the test)? Where are the
transparent hugepage settings helpers?

## selftests.net-shell-lib: Networking shell library

- section: Subsystem helper libraries
- relevance: 4 - nearly every networking shell test sources it
- words: 110

What does `tools/testing/selftests/net/lib.sh` provide for creating and
removing network namespaces, for waiting on a condition, for netdevsim
devices, for checking required commands, and for logging results? Name the
functions. How does `setup_ns` name namespaces and arrange for them to be
removed?

## selftests.net-shell-status: Networking shell result logic

- section: Subsystem helper libraries
- relevance: 3 - two variables and two orderings
- words: 80

How does a test written on `net/lib.sh` compute its exit status: what are
`RET` and `EXIT_STATUS`, what do `check_err`, `log_test` and `log_test_skip`
do with them, and in what order of precedence do pass, skip, xfail and fail
combine within a test and across tests?

## selftests.net-defer: Deferred cleanup in shell

- section: Subsystem helper libraries
- relevance: 2 - newer tests use it instead of a trap
- words: 60

What does `tools/testing/selftests/net/lib/sh/defer.sh` provide, how does a
test schedule a cleanup with it, in what order do cleanups run, and what are
the helpers in `net/lib.sh` whose names start with adf_?

## selftests.net-python-lib: Networking Python library

- section: Subsystem helper libraries
- relevance: 4 - new networking tests are increasingly Python
- words: 100

How is a Python networking selftest structured with
`tools/testing/selftests/net/lib/py/`: how tests are collected and run, how a
test reports skip, expected failure and failure, the comparison helpers,
deferred cleanup, and what the final call does? Start from `ksft_run()` and
`ksft_exit()`.

## selftests.net-driver-tests: Driver tests

- section: Subsystem helper libraries
- relevance: 3 - the directory decides what a test must support
- words: 80

What do the tests under `tools/testing/selftests/drivers/net/` have to
support, how is a real device and remote endpoint described to them, and where
do tests that only work on software devices or only on real hardware belong?
Start from `tools/testing/selftests/drivers/net/README.rst`.

## selftests.net-lib-target: Networking library target

- section: Subsystem helper libraries
- relevance: 3 - a target that holds no tests
- words: 60

What is the `net/lib` selftests target, how does it get built and installed
when only `net` or `drivers/net` is selected, and how do its shell and Python
files reach the install tree?

## selftests.bpf-denylist: BPF test exclusions

- section: Subsystem helper libraries
- relevance: 3 - the alternative to an ad hoc architecture check
- words: 70

How are BPF selftests excluded on an architecture or everywhere without
editing the test, which files hold the lists, who reads them, and what is
`vmtest.sh` for? Start from `tools/testing/selftests/bpf/README.rst`.

## selftests.bpf-build: BPF selftests build

- section: Subsystem helper libraries
- relevance: 3 - the largest directory is outside the default build
- words: 60

Are the BPF selftests built by a plain `make -C tools/testing/selftests`? Say
why or why not, and how `tools/testing/selftests/bpf/Makefile` relates to
`lib.mk`.

## selftests.kvm-vm-create: VM creation helpers

- section: KVM selftests
- relevance: 4 - which helper was used decides what state the VM is in
- words: 90

Which of the VM creation helpers in
`tools/testing/selftests/kvm/include/kvm_util.h` create vCPUs and which only
create the VM? Which architecture hooks run at VM creation and which after the
vCPUs exist, and from which helper is the latter called? Start from
`__vm_create()` and `__vm_create_with_vcpus()`.

## selftests.kvm-default-irqchip: Default interrupt controller

- section: KVM selftests
- relevance: 4 - differs by architecture and has changed
- words: 80

For each architecture with KVM selftests, what does
`kvm_arch_has_default_irqchip()` return and on what does it depend, and what
does the library set up by default? A table. Include the weak default.

## selftests.kvm-irqchip-usage: Interrupt ioctls after VM creation

- section: KVM selftests
- relevance: 4 - fails on one architecture and passes on another
- words: 80

What usage of `KVM_IRQFD`, `KVM_IRQ_LINE` or interrupt routing right after
creating a VM in a selftest fails on some architectures, and what is the
correct sequence? Explain with the arm64 hooks, and name the in-tree test that
shows the correct form.

## selftests.kvm-test-require: KVM requirement checks

- section: KVM selftests
- relevance: 3 - the KVM way to skip
- words: 50

What do `TEST_REQUIRE()` and `__TEST_REQUIRE()` in the KVM selftests do when
the condition is false: what is printed and what is the exit code?

## selftests.netns-devconf-inherit: Device config in a new namespace

- section: Network namespace tests
- relevance: 5 - decides whether a test depends on the machine it runs on
- words: 110

When a network namespace is created, where do its IPv4 and IPv6 conf/all and
conf/default values come from? Give a table by value of the net.core sysctl
`devconf_inherit_init_net` for each family, and say what the default value
is. Start from `devinet_init_net()` and `addrconf_init_net()`.

## selftests.netns-devconf-usage: Asserting on inherited settings

- section: Network namespace tests
- relevance: 5 - passes in CI, fails on a developer's machine, or the reverse
- words: 90

What usage of `forwarding`, `rp_filter`, `accept_local` or another per-device
setting in a test that runs in its own namespace makes the result depend on
the host, and what is the correct form? Say why the IPv4 and IPv6 arms of such
a test can behave differently, and name an in-tree test that pins the setting
first.

## selftests.negative-test-usage: Negative tests

- section: Network namespace tests
- relevance: 3 - a test that cannot fail protects nothing
- words: 70

A test asserts that an operation is refused with a particular error code. What
makes such an assertion unable to tell a correct kernel from one missing the
check, and what change to the test's setup makes it discriminate?
