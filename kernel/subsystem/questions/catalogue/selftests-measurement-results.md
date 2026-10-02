# What the selftests measurement found

Three models were asked the 86 questions in `selftests-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader C was the most current and the
most accurate, reader A close behind it, and reader B much weaker: 83 of its
86 answers were rewritten by 40% or more, and it invented files, variables
and macros. The hand-written guide was never checked against current sources,
so differences between it and the built guide are expected and are noted near
the end.

Readers A and C know the shape of the framework well: the `lib.mk` variables,
the harness macros, the timeouts, the settings file, what the runner does with
a missing file. What they get wrong is the fine print that decides a verdict:
which exit codes the runner gives a result of its own, what counts as success
at the end of a program, who prints the TAP header, what is and is not in the
default build. Reader B is wrong about the basics as well, so the build set
was chosen by importance and not only by dropping what readers know.

## What all three readers got wrong

- **The runner gives expected failure a result of its own.** All three said
  exit status 2 falls through to `not ok ... # exit=2`. The `case` in
  `run_one()` has a `KSFT_XFAIL` arm that prints `ok ... # XFAIL`. Only
  `KSFT_XPASS` (3) has no arm, so a program that exits through
  `ksft_exit_xpass()` is reported as failed.
- **Unexpected passes count as success inside a program.** `ksft_finished()`
  compares the plan with pass + xpass + xfail + skip. Readers A and C left
  xpass out and said it fails; reader B said every result is counted and
  failures checked separately. In the harness `__test_passed()` accepts any
  code up to `KSFT_SKIP` other than `KSFT_FAIL`, so an `XFAIL_ADD()` test that
  passes is `ok ... # XPASS` and the binary exits 0. All three said it fails.
- **Who prints the header.** `run_many()` prints no version line and no plan;
  only `run_kselftest.sh` does, through `ktap_print_header()` and
  `ktap_set_plan()`, so `make run_tests` has neither. Nothing in the tree sets
  `KSFT_TAP_LEVEL`; it is only read, in `ksft_print_header()`. Each reader
  named something that sets it.
- **The installed runner fails by default.** `run_kselftest.sh` exits
  `KSFT_FAIL` when any test failed, and `-f` turns that off. All three said it
  exits 0, and two named an option that does not exist. `make run_tests` does
  exit 0 whatever the tests did.
- **The check for low-level calls in a harness test.** After the test function
  returns, `__run_test()` fails the test with "Illegal usage of low-level ksft
  APIs in harness test" if the `kselftest.h` fail or error counter is
  non-zero. No reader knew it. It does not see a `TEST_F()` body, which runs
  in a grandchild.
- **Error results.** The only thing the tree says about how "error" differs
  from "fail" or "skip" is a TODO comment above `ksft_test_result_error()`
  asking that question. Eight files call it. Each reader supplied a meaning.
- **The documentation's missing example.** `kselftest.rst` gives
  tools/testing/selftests/android/config as its example of a config file;
  there is no android directory. No reader named it, and two named files that
  do exist.
- **The mm hugepage helpers** are in `mm/hugepage_settings.h`; all three gave a
  header that does not exist. `read_sysfs()` and `write_sysfs()` return 1 on
  error, not a negative code, while `read_num()`, `write_num()` and
  `write_file()` end the test.
- **KVM selftests on riscv** have their own `kvm_arch_has_default_irqchip()`,
  which returns `kvm_check_cap(KVM_CAP_IRQCHIP)`. All three put riscv under the
  weak default, which now serves loongarch alone. The s390 version returns true
  and the library sets nothing up.
- **BPF deny lists.** The files are `DENYLIST`, `DENYLIST.s390x`,
  `DENYLIST.riscv64` and `DENYLIST.asan`. All three named an aarch64 file that
  is not there, and the README says `vmtest.sh` does not apply the lists by
  itself.
- **What a harness test's failed ASSERT does.** `__bail()` calls the teardown
  wrapper and then `abort()`. Readers gave a longjmp, a goto and an exit. The
  teardown runs only for `TEST_F()`, only once setup has finished, and for a
  `FIXTURE_TEARDOWN_PARENT()` fixture it runs later in the waiting process.

## What readers A and B got wrong as well

- A plain `make -C tools/testing/selftests` does not build `bpf`:
  `SKIP_TARGETS ?= bpf sched_ext`, and the `override` also filters a `TARGETS`
  given on the command line. `net/lib` is not appended to `TARGETS`; it goes in
  `INSTALL_DEP_TARGETS`, so it is built, installed and cleaned but never run.
- `install` copies `run_kselftest.sh`, it does not generate it; it also copies
  `kselftest/ksft.py` and writes `VERSION`. A directory that failed to build is
  left out of `kselftest-list.txt`, which only `TEST_GEN_PROGS`,
  `TEST_CUSTOM_PROGS` and `TEST_PROGS` feed.
- `ksft_print_header()` makes stdout line buffered, not unbuffered, and its
  comment is about duplicated output after `fork()` and the last line before a
  crash.
- `ksft_exit()` in the networking Python library only exits; `ksft_run()`
  prints the totals, and it has no default prefix for collecting cases.
- In `net/lib.sh` the two merge orders differ: within a test fail beats skip
  beats xfail beats pass, across tests pass beats xfail. `setup_ns` also writes
  `rp_filter` to 0 in conf/all and conf/default of each namespace it makes.
- `ksft_min_kernel_version()` ends the test with `ksft_exit_fail_msg()` when it
  cannot parse the release; there is no branch for a smaller C library.
- `ktap.rst` accepts SKIP, TODO, XFAIL, TIMEOUT and ERROR and discourages only
  TODO. The helpers also print XPASS, and a lower-case "error".
- The harness's own test is a plain diff of stdout against
  `harness-selftest.expected`; nothing is filtered out first.

## What only reader B got wrong

Almost everything else, of which the parts that would change a review: one
failing directory fails the whole build (it takes all of them, unless
`FORCE_TARGETS` is set); the runner reads a test's TAP and falls back to the
exit status (it reads the exit status and nothing else); a missing test file is
skipped (it is `not ok`); `TEST_F()` runs in a single child (there is a
grandchild for setup, body and teardown); the harness timeout is an alarm
signal (it polls a pidfd and kills the process group); there are no exclude
filters; a run in which every test was skipped exits with the skip code (it
exits 0); `ksft_test_result_xfail()` prints "not ok"; `SKIP()` in
`FIXTURE_SETUP()` still runs teardown (it does not); IPv6 copies `init_net` at
the default sysctl value (it keeps compiled defaults, which is the whole point
of the namespace section); `TEST_INCLUDES` was called by the name of the macro
that copies it; `gen_tar` was said to call the old packaging script. It also
offered a make include file, a header-install rule, a timeout macro, a skip
function, a plan function and two header files that are nowhere in the tree.

## What only reader C got wrong

- `seccomp_bpf.c` as the model of probing for a feature and skipping. It mostly
  asserts that errno is not `ENOSYS`, which is the unsafe form.
  `namespaces/listns_test.c` does `SKIP(return, ...)` on `ENOSYS`, and
  `cachestat/test_cachestat.c` calls `ksft_exit_skip()` on it before setting a
  plan. `core/close_range_test.c` looks like an example and is not one: its
  `SKIP()` sits in the failure block of an `EXPECT_EQ(-1, ...)`, which does not
  run when the call fails with `ENOSYS`.
- That writing the per-device value afterwards is a correct alternative to
  pinning conf/all. `IN_DEV_RPFILTER()` takes the maximum of conf/all and the
  device and `IN_DEV_ACCEPT_LOCAL()` ORs them, so a per-device 0 does not undo
  a non-zero conf/all.
- An EXIT trap installed by `net/lib.sh` or `defer.sh`. Neither sets one; tests
  set their own.
- `kvm_arch_vm_finalize_vcpus()` as called only from `__vm_create_with_vcpus()`.
  That holds inside the library; `arm64/psci_test.c` and others call it by hand
  after adding vCPUs themselves.

## What the readers already knew

Readers A and C: the framework files and what each is for, the `TEST_`
variables apart from the fine print above, that a rule for a generated file
written after the include needs the `$(OUTPUT)/` prefix, the 45 second runner
limit and the 30 second harness limit, the settings file, a missing or
non-executable test file, the harness macros and variants, the expected and
seen argument order, `ksft_exit_skip()` before and after a plan, the documented
contribution rules, the shell helpers (reader C), the VM creation helpers and
the device config table (reader A had the table, reader C all of it). All
three, reader B included, answered the question about negative tests that
cannot fail correctly, so it is not in the build set.

## Where the hand-written guide is stale

`selftests.md` is a list of review findings with no map of the framework.
Against this tree:

- Its table of `kvm_arch_has_default_irqchip()` gives riscv as false through
  the weak default. riscv has its own version that asks KVM for
  `KVM_CAP_IRQCHIP`; the weak default is loongarch only. The rest of the KVM
  section stands, with one refinement: before the vGIC is initialised
  `KVM_IRQFD` gets `-EAGAIN` from `kvm_irqfd_assign()`, while
  `kvm_vgic_inject_irq()` returns 0 and injects nothing.
- It says `ksft_test_result_error()` is "specifically for setup/environment
  failures". The header has only a TODO asking what error means.
- It says CI systems grep for ok and not ok, and tells reviewers to report any
  test that returns from `main()` or calls `exit()` directly. The kselftest
  runner never reads a test's output: the exit status is the result. A harness
  test returns `test_harness_run()` from `main()`, and a test that exits 0, 1
  or 4 by hand is recorded correctly. What is lost is the per-case detail.
- Its variable table has four of the nine variables and says a sourced or
  imported file must go in `TEST_FILES`. For a file in another directory the
  declaration is `TEST_INCLUDES`, which keeps the path below the selftests
  directory; thirteen Makefiles use it.
- The errno values it lists for "capability absent" are not from the
  documentation, which has one rule on the subject: do not make the top-level
  run fail when the feature is unconfigured.
- It lists `rp_filter` among the settings a test must write itself. A test that
  gets its namespaces from `setup_ns` has it written to 0 already; `forwarding`
  is not touched.
- It points at the BPF deny lists as the alternative to an architecture check
  without saying that `vmtest.sh` does not apply them.
- Its device config table is correct, and the two questions that rebuild it are
  kept.

## What was left out of the build set and why

Forty of the 86 questions are in the build set. Left out:

- The make targets, packaging, install location, cross compiling, the separate
  output directory, the common compile rule, custom build rules, the variables
  for programs not run by default and for test modules: readers A and C answer
  them, they are rarely what a patch gets wrong, and the variable table keeps
  the part that matters.
- Runner conveniences: arguments through the environment, the installed
  runner's options, the summary variable, how the settings file is parsed,
  config fragments.
- Harness options, logging, signal tests, variants, the argument order and
  parent teardown: answered correctly by readers A and C, or narrow. The
  macro table names each one.
- The message newline rules, diagnostics and stdout buffering in `kselftest.h`:
  real, but each is one line of the header.
- Module tests, the KTAP line format, skip reasons, older kernels: the
  documentation says it and the readers mostly repeat it.
- The networking shell status logic, deferred cleanup, the Python library,
  driver tests and the `net/lib` target, the mm helpers, the BPF build and deny
  lists, the KVM requirement macro: subsystem detail. The library table points
  at each file, and carries the two names every reader had wrong.
- Negative tests: every reader answered correctly.
- Hand-rolled output: folded into the question on exiting from `main()`.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A: 131 corrections, 29% rewritten on average, 27 answers at most 15% rewritten, 27 at least 40%, assumed kernel 6.12 to 6.18
reader B: 169 corrections, 75% rewritten on average, 1 answers at most 15% rewritten, 83 at least 40%, assumed kernel 6.10 to 6.16
reader C: 95 corrections, 17% rewritten on average, 46 answers at most 15% rewritten, 7 at least 40%, assumed kernel 6.12 to 6.19

question                                  reader A      reader B      reader C
selftests.core-files                       0% ( 0)      40% ( 6)       0% ( 0)
selftests.docs                            26% ( 2)      75% ( 3)      42% ( 2)
selftests.top-make-targets                28% ( 2)      67% ( 4)       7% ( 2)
selftests.selftests-make-targets           9% ( 2)      64% ( 1)       0% ( 0)
selftests.target-selection                21% ( 4)      78% ( 1)      20% ( 4)
selftests.build-failure-status            12% ( 0)      89% ( 1)      11% ( 1)
selftests.new-directory-checklist         39% ( 1)      90% ( 2)       7% ( 1)
selftests.kernel-headers                  49% ( 3)      93% ( 2)      38% ( 1)
selftests.out-of-tree-build               33% ( 3)      80% ( 1)      35% ( 2)
selftests.cross-compile                   26% ( 2)      90% ( 1)      11% ( 1)
selftests.test-variables                   0% ( 2)      20% ( 5)       7% ( 2)
selftests.extended-variables              13% ( 1)      70% ( 1)       0% ( 0)
selftests.test-includes                   21% ( 1)      77% ( 1)      10% ( 1)
selftests.support-file-usage               5% ( 1)      79% ( 1)      13% ( 1)
selftests.module-directory                22% ( 1)      77% ( 1)      18% ( 1)
selftests.custom-build-rules              23% ( 1)      93% ( 1)       1% ( 1)
selftests.default-compile-rule            38% ( 1)      81% ( 1)       8% ( 1)
selftests.output-prefixing                20% ( 1)      50% ( 1)      24% ( 1)
selftests.install-layout                  34% ( 4)      83% ( 4)      16% ( 1)
selftests.test-list                       43% ( 2)      75% ( 5)       0% ( 0)
selftests.install-path                    66% ( 1)      81% ( 1)      18% ( 1)
selftests.packaging                       45% ( 1)      82% ( 3)      23% ( 1)
selftests.runner-flow                     20% ( 4)      79% ( 5)      30% ( 3)
selftests.exit-codes                      10% ( 1)      81% ( 1)      45% ( 1)
selftests.runner-timeouts                  0% ( 0)      58% ( 1)      14% ( 1)
selftests.settings-file                    0% ( 0)      75% ( 1)       0% ( 0)
selftests.unrunnable-tests                 0% ( 0)      84% ( 1)       0% ( 0)
selftests.test-arguments                  40% ( 1)      94% ( 1)      11% ( 0)
selftests.installed-runner-options        82% ( 1)      81% ( 6)      38% ( 4)
selftests.summary-logging                 68% ( 1)      77% ( 1)      49% ( 1)
selftests.runner-exit-status              51% ( 2)      75% ( 1)      58% ( 2)
selftests.nested-output                   38% ( 2)      76% ( 1)      28% ( 2)
selftests.config-fragments                15% ( 1)      82% ( 1)      13% ( 0)
selftests.ksft-call-order                 17% ( 3)      74% ( 4)       0% ( 1)
selftests.ksft-result-functions           20% ( 1)      31% ( 1)      22% ( 1)
selftests.ksft-exit-functions             22% ( 1)      46% ( 1)      27% ( 1)
selftests.ksft-finished-condition         44% ( 1)      86% ( 1)       4% ( 1)
selftests.ksft-exit-skip-usage            12% ( 1)      76% ( 1)       0% ( 0)
selftests.ksft-error-result               54% ( 1)      82% ( 1)      54% ( 1)
selftests.ksft-newlines                   23% ( 1)      72% ( 1)      13% ( 3)
selftests.ksft-diagnostics                39% ( 2)      81% ( 4)      11% ( 1)
selftests.ksft-stdout-buffering           85% ( 1)      69% ( 1)      20% ( 1)
selftests.ksft-direct-exit-usage          33% ( 3)      92% ( 3)      19% ( 1)
selftests.hand-rolled-output-usage        48% ( 1)      84% ( 1)      12% ( 1)
selftests.harness-macros                   0% ( 4)      51% ( 4)       0% ( 1)
selftests.harness-process-model           23% ( 2)      80% ( 1)      39% ( 3)
selftests.harness-assert-expect           18% ( 1)      81% ( 1)      24% ( 1)
selftests.harness-argument-order           0% ( 0)      67% ( 1)       2% ( 1)
selftests.harness-skip                    11% ( 1)      82% ( 1)      10% ( 1)
selftests.harness-timeout                  0% ( 0)      83% ( 1)       0% ( 0)
selftests.harness-variants                 0% ( 0)      56% ( 1)       0% ( 0)
selftests.harness-xfail                   40% ( 1)      91% ( 1)      22% ( 1)
selftests.harness-teardown-parent         56% ( 1)      78% ( 4)       0% ( 0)
selftests.harness-signal-tests            16% ( 1)      88% ( 1)       5% ( 1)
selftests.harness-options                 19% ( 1)      90% ( 1)       0% ( 0)
selftests.harness-ksft-mixing             52% ( 1)      83% ( 1)      68% ( 2)
selftests.harness-exit-status             44% ( 2)      75% ( 1)       9% ( 1)
selftests.harness-logging                  0% ( 0)      79% ( 1)       0% ( 0)
selftests.harness-own-test                42% ( 1)      83% ( 1)      39% ( 1)
selftests.harness-forked-children         62% ( 1)      85% ( 1)      33% ( 1)
selftests.ktap-shell-helpers              26% ( 3)      75% ( 6)       0% ( 0)
selftests.shell-exit-codes                14% ( 1)      70% ( 1)      21% ( 2)
selftests.ksft-python-module              45% ( 2)      81% ( 4)       7% ( 1)
selftests.module-tests                    26% ( 1)      82% ( 3)       7% ( 0)
selftests.contribution-rules               0% ( 1)      91% ( 4)       0% ( 0)
selftests.skip-usage                      11% ( 1)      88% ( 3)      28% ( 2)
selftests.skip-reason                     80% ( 4)      85% ( 1)      32% ( 1)
selftests.older-kernels                   49% ( 2)      77% ( 1)      21% ( 1)
selftests.ktap-format                     70% ( 2)      77% ( 1)      26% ( 2)
selftests.subsystem-libraries              8% ( 3)      46% ( 5)       4% ( 2)
selftests.mm-helpers                      48% ( 3)      86% ( 2)      16% ( 3)
selftests.net-shell-lib                   45% ( 3)      87% ( 2)      29% ( 3)
selftests.net-shell-status                58% ( 2)      77% ( 1)       0% ( 0)
selftests.net-defer                       62% ( 2)      84% ( 1)      37% ( 4)
selftests.net-python-lib                  36% ( 4)      72% ( 5)      10% ( 1)
selftests.net-driver-tests                13% ( 1)      82% ( 1)      10% ( 1)
selftests.net-lib-target                  34% ( 1)      89% ( 2)      33% ( 1)
selftests.bpf-denylist                    33% ( 1)      81% ( 1)      45% ( 1)
selftests.bpf-build                       46% ( 1)      86% ( 1)      12% ( 0)
selftests.kvm-vm-create                    0% ( 0)      82% ( 2)      13% ( 1)
selftests.kvm-default-irqchip             30% ( 2)      46% ( 4)      19% ( 1)
selftests.kvm-irqchip-usage               38% ( 4)      78% ( 3)      31% ( 1)
selftests.kvm-test-require                37% ( 1)      91% ( 1)      18% ( 0)
selftests.netns-devconf-inherit           13% ( 2)      76% ( 4)       0% ( 0)
selftests.netns-devconf-usage              8% ( 1)      76% ( 2)      34% ( 2)
selftests.negative-test-usage              8% ( 1)       0% ( 0)       6% ( 0)
```

## Questions put back

A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `selftests.runner-flow`, `selftests.ksft-call-order`, `selftests.hand-rolled-output-usage`, `selftests.net-python-lib`.

## Questions reorganised

Subjects: Makefiles, building and installing; the runner; reporting from plain C; the test harness;
skipping; shell and Python tests; network namespaces; KVM selftests. 47 questions became 44.
Merged: `selftests.test-includes` and `selftests.support-file-usage` into `selftests.support-files`;
`selftests.hand-rolled-output-usage` and `selftests.ksft-direct-exit-usage` into
`selftests.main-exit-usage`. Dropped: `selftests.contribution-rules`, a read-out of one list in the
documentation; the rules in it that change a review are asked for in `selftests.skip-usage` and
`selftests.main-exit-usage`. The shell, Python, runner-flow and install questions no longer ask for
functions and files by name but for what they guarantee, and the three skip questions sit together.
