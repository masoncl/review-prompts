# Selftests Subsystem Details

## Build System and Installation

When a new file is created in a selftests directory but not added to the
Makefile, tests fail with "No such file or directory" when run from an
installed location (via `make install`). Tests may appear to work when run
directly from the source tree because the file exists there.

The selftests build system uses several variables in each subsystem's Makefile
to control what gets installed:

| Variable | Purpose |
|----------|---------|
| `TEST_PROGS` | Executable test scripts that are run directly |
| `TEST_FILES` | Supporting files (libraries, data files, sourced scripts) |
| `TEST_GEN_FILES` | Generated binaries/files produced during build |
| `TEST_GEN_PROGS` | Generated executable test programs |

Key invariants:

- Any file referenced via `source <filename>` (bash) or `. <filename>` in
  test scripts must be added to `TEST_FILES`
- Any file referenced via `import <module>` (Python) in test scripts must be
  added to `TEST_FILES`
- Executable test scripts that are invoked directly go in `TEST_PROGS`
- Helper executables that are built during `make` go in `TEST_GEN_PROGS` or
  `TEST_GEN_FILES`

Common mistake: creating a new shared library or utility file (like
`_common.sh`, `utils.py`, `lib.sh`) that is sourced by test scripts but
forgetting to add it to `TEST_FILES`. The tests work in the source directory
but fail after `make install`.

## Result Reporting: Use the `kselftest.h` / `kselftest_harness.h` Wrappers

Hand-rolled `printf()`-based pass/fail output cannot be reliably parsed as TAP
by kselftest's own runners and by CI systems that grep for `ok`/`not ok`
lines, so failures get silently miscounted or missed by automation even
when a human reading the raw output would see them.

- Use `ksft_print_header()` and `ksft_set_plan(n)` at the start of a test
  binary, and `ksft_finished()` at the end to print the summary line — don't
  hand-format the plan/summary output.
- Report each test case via `ksft_test_result_pass()`, `ksft_test_result_fail()`,
  `ksft_test_result_skip()`, `ksft_test_result_xfail()`, or
  `ksft_test_result_xpass()` (all in `tools/testing/selftests/kselftest.h`),
  or the `ksft_test_result(condition, fmt, ...)` macro for a plain boolean.
  Use `ksft_test_result_error()` specifically for setup/environment failures
  that are distinct from the behavior under test failing.
- Exit via `ksft_exit_pass()`, `ksft_exit_fail()`, or `ksft_exit_skip(fmt, ...)`
  rather than calling `exit()` directly — these also flush the TAP summary
  first.
- For anything beyond a flat `main()` with sequential checks, use
  `TEST()`/`TEST_F()` plus `FIXTURE()`/`FIXTURE_SETUP()`/`FIXTURE_TEARDOWN()`
  and the `ASSERT_*`/`EXPECT_*` operators (`tools/testing/selftests/kselftest_harness.h`)
  instead of writing bespoke `if (...) { report failure }` blocks — the
  operators print the actual vs. expected values on failure automatically.
  `FIXTURE_VARIANT`/`FIXTURE_VARIANT_ADD` run the same test body across a
  parameter matrix instead of copy-pasting the test function per variant.

```c
// WRONG: not TAP, and the runner/CI can't tell this apart from stray stdout
if (ret != 0) {
	printf("FAIL: frobnicate returned %d\n", ret);
	return 1;
}

// CORRECT: parseable, counted, and consistent with every other test
ksft_test_result(ret == 0, "frobnicate\n");
```

**REPORT as bugs**: a test binary that prints its own ad hoc pass/fail text
instead of calling into `kselftest.h`/`kselftest_harness.h`, or that calls
`exit()`/`return` directly from `main()` without going through
`ksft_exit_*()`.

## Skip vs. Fail for Unsupported or Unconfigured Features

Treating a missing prerequisite (kernel config option, hardware feature,
filesystem capability) as a hard failure turns an environment difference
into a false regression signal, and — per documented kselftest policy —
a test that fails outright when unconfigured is also expected to not break
the top-level `make run_tests` run for everyone else.

- If a syscall or ioctl fails with `EOPNOTSUPP`/`ENOSYS`/`ENODEV` because the
  specific feature genuinely isn't present, that's a skip, not a failure:
  call `ksft_test_result_skip()` or the harness `SKIP()` macro, with a message
  explaining *what* was missing. KVM selftests can use `TEST_REQUIRE()` from
  their subsystem-specific test utilities to perform this check up front.
- Distinguish this from the feature being present but broken — that's a
  real failure and must still be reported as one.
- Always include a reason string in the skip message (e.g. "MADV_REMOVE not
  supported by filesystem") — a bare skip with no explanation is nearly as
  unhelpful to a future debugger as a silent pass.

```c
// WRONG: EOPNOTSUPP here means "prerequisite absent", not "test failed"
ret = madvise(addr, len, MADV_REMOVE);
ASSERT_EQ(ret, 0);

// CORRECT: treat the missing capability as a skip, with a reason
ret = madvise(addr, len, MADV_REMOVE);
if (ret == -1 && errno == EOPNOTSUPP)
	SKIP(return, "MADV_REMOVE not supported by filesystem");
ASSERT_EQ(ret, 0);
```

**REPORT as bugs**: a test that asserts/fails on `EOPNOTSUPP`, `ENOSYS`, or
similar "capability absent" errno values instead of skipping, or that skips
silently with no message.

## Reuse Existing Shared Test Libraries Instead of Reimplementing Them

Rewriting namespace setup/teardown, busy-wait polling, sysfs/file I/O, or
device-creation plumbing inside one test file instead of using the
subsystem's existing test-util header produces a second implementation with
different corner-case behavior (e.g. no error check on a short write, or a
namespace leak the shared version already guards against), and a bug fixed
in the shared version won't propagate to the reimplementation. Before
writing a small I/O or setup helper, check whether the subsystem's own test
utility header already has it.

- mm tests: `tools/testing/selftests/mm/vm_util.h` already provides sysfs
  I/O (`read_sysfs`, `write_sysfs`), general file I/O (`read_file`,
  `write_file`, `read_num`, `write_num`), and result reporting
  (`log_test_start`, `log_test_result`). A new mm test that hand-opens a
  sysfs path with `open()`/`write()`/`close()` instead of calling
  `write_sysfs()` is reimplementing something that already exists, usually
  without the existing error handling.
- Networking tests: `tools/testing/selftests/net/lib.sh` already provides
  namespace management (`setup_ns`, `cleanup_ns`, `cleanup_all_ns`),
  busy-wait polling (`busywait`, `busywait_for_counter`, `loopy_wait`),
  structured result reporting (`log_test`, `log_test_result`,
  `log_test_skip`, `handle_test_result_*`, `ksft_status_merge`), and
  netdevsim helpers (`create_netdevsim`, `cleanup_netdevsim`). A new net/
  shell test that hand-rolls any of these is very likely duplicating
  something already hardened against the common failure modes.
- BPF tests: `tools/testing/selftests/bpf/README.rst` documents the
  `DENYLIST` mechanism for excluding tests on architectures that lack a
  feature, and `vmtest.sh` for running under a matched kernel — check there
  before adding an ad hoc per-architecture skip.
- More generally: any subsystem's `tools/testing/selftests/<subsys>/` tree
  tends to have its own `*_util.h`/`lib.sh`/`lib.mk`-style header collecting
  helpers new tests are expected to use — don't assume none exists just
  because a given helper isn't in `net/lib.sh` or `mm/vm_util.h`.

**REPORT as bugs**: a test that hand-rolls sysfs/file I/O, namespace
setup/teardown, or a polling loop instead of using the subsystem's existing
test-util header (`vm_util.h` for mm, `lib.sh` for net, etc.) for something
that header already provides.

## Test the Interface, Not the Implementation Detail; Extend Before Adding

A test written against a specific implementation detail (an internal batching
strategy, a particular code path taken to reach a result) breaks or needs a
rewrite whenever that implementation changes, even when the behavior it's
supposed to guard is still correct — and a new standalone test file for one
narrow case usually duplicates setup/teardown an existing, more general test
in the same directory already has.

- Test the interface/contract (e.g. "GUP returns the right pages and content
  for this mapping shape") rather than how the kernel currently gets there
  internally (e.g. "GUP batches N contiguous PTEs in one internal loop
  iteration"). A test at the interface level exercises whatever
  implementation sits underneath, present or future, without being coupled
  to it.
- Before adding a new, narrow test file for one specific case, check whether
  an existing test in the same directory already exercises the same
  interface and could be extended with one more case/parameter instead. In
  mm, for example, `gup_test.c` and `cow.c` already exercise
  `get_user_pages()` content and COW correctness at other folio sizes; a new
  size or mapping variant is naturally a new case in one of those, not a new
  standalone binary.

**REPORT as bugs**: a new selftest file added for a narrow variant (a
specific size, a specific internal code path) of behavior an existing test
in the same directory already covers more generally — ask whether it should
be a new case in the existing test instead.

## KVM Selftests: IRQ Chip Setup and `vm_create` vs `vm_create_with_one_vcpu`

Tests that use `KVM_IRQFD`, `KVM_IRQ_LINE`, or IRQ routing APIs after
`vm_create()` fail because `vm_create()` does not create vCPUs, and on arm64
VGIC finalization (`KVM_DEV_ARM_VGIC_CTRL_INIT`) requires all vCPUs to be
created first. On architectures without any in-kernel IRQ chip support (riscv,
loongarch), these ioctls fail with `-ENODEV`.

`vm_create(nr_runnable_vcpus)` allocates a VM and sizes memory for the given
number of vCPUs, but does **not** create any vCPUs. IRQ chip setup is
initiated during `vm_create()` via `kvm_arch_vm_post_create()`, but
finalization (via `kvm_arch_vm_finalize_vcpus()`) only happens in functions
that also create vCPUs, such as `vm_create_with_one_vcpu()` and
`__vm_create_with_vcpus()`.

`kvm_arch_has_default_irqchip()` returns whether the architecture sets up an
in-kernel IRQ chip by default:

| Architecture | Return value |
|--------------|-------------|
| x86 | `true` (creates IOAPIC/PIC/LAPIC via `vm_create_irqchip()`) |
| s390 | `true` |
| arm64 | `true` when GICv3 is supported and not disabled via `test_disable_default_vgic()` |
| riscv, loongarch | `false` (weak default in `lib/kvm_util.c`) |

Tests that need an in-kernel IRQ chip must:

1. Call `TEST_REQUIRE(kvm_arch_has_default_irqchip())` to skip on architectures
   that lack IRQ chip support.
2. Use `vm_create_with_one_vcpu()` (or `__vm_create_with_vcpus()`) rather than
   bare `vm_create()`, so that vCPUs are created and IRQ chip finalization
   completes before issuing IRQ-related ioctls.

```c
// WRONG: vm_create() does not create vCPUs or finalize the IRQ chip
vm = vm_create(1);
kvm_irqfd(vm, gsi, eventfd, 0);

// CORRECT: Skip unsupported architectures, then create VM with vCPU
TEST_REQUIRE(kvm_arch_has_default_irqchip());
vm = vm_create_with_one_vcpu(&vcpu, NULL);
kvm_irqfd(vm, gsi, eventfd, 0);
```

## Network Namespace Tests: Device Config Inherited from init_net

A new network namespace does not start from compiled defaults for IPv4. It
copies `conf/all` and `conf/default` from `init_net`. A test that asserts on a
device config knob it never sets is therefore asserting on the config of the
machine running the test.

The behavior is controlled by `net.core.devconf_inherit_init_net`, and IPv4 and
IPv6 disagree at the default value of 0:

| `devconf_inherit_init_net` | IPv4 (`devinet_init_net`) | IPv6 (`addrconf_init_net`) |
|----------------------------|---------------------------|----------------------------|
| 0 (default) | copy from `init_net` | compiled defaults |
| 1 | copy from `init_net` | copy from `init_net` |
| 2 | compiled defaults | compiled defaults |
| 3 | copy from current netns | copy from current netns |

So on any host with `net.ipv4.conf.all.forwarding=1` (a router, a container
host, most developer workstations that have ever run docker), devices created
inside a test's netns come up with forwarding already enabled. The same test on
a CI VM, where forwarding is off, sees the opposite. IPv6 is unaffected at the
default, which is why this class of bug often shows up in the IPv4 arms only.

This produces two distinct failures.

**False failure.** A test that expects an operation to be refused because
forwarding is off will see it succeed instead, and fail. It passes in CI and
fails for developers, which sends people looking for a kernel regression that
is not there.

**False pass.** A negative test asserting error code X can become a tautology
if the bug it targets would also produce X, for an unrelated reason. The
inherited config decides which gate the buggy path stops at, and therefore
which error code comes back. When the host makes an earlier gate fire, the test
discriminates; when it does not, the same test passes whether or not the kernel
is broken.

```c
// WRONG: forwarding is whatever the host had, so the arms below only mean
// what they say on a host with forwarding off
SYS(fail, "ip link add veth1 type veth peer name veth2");

// CORRECT: pin the state the assertions depend on, then enable per device
err = write_sysctl("/proc/sys/net/ipv4/conf/all/forwarding", "0");
if (!ASSERT_OK(err, "write_sysctl(net.ipv4.conf.all.forwarding)"))
	goto fail;
err = write_sysctl("/proc/sys/net/ipv4/conf/default/forwarding", "0");
if (!ASSERT_OK(err, "write_sysctl(net.ipv4.conf.default.forwarding)"))
	goto fail;

SYS(fail, "ip link add veth1 type veth peer name veth2");
```

For a negative test, the check that catches the tautology is to ask what a
kernel with the targeted bug would actually return, and whether that value
differs from the asserted one. If both the correct kernel and the broken kernel
can produce the asserted code, the test pins nothing. The fix is usually to
give the buggy path something to succeed at, so the two outcomes separate:
adding a route, an address, or an enabled device turns the broken kernel's
answer into a success code that the assertion then catches.

## The kselftest Harness and Result Protocol

`Documentation/dev-tools/kselftest.rst` covers running, installing and
contributing tests, and is the authority on the Makefile variables and the
per-directory `settings` timeout.

**You MUST read that file before reporting on how a test is wired in.** Call
`git_read_files` with `Documentation/dev-tools/kselftest.rst` at the revision
under review, and check such findings against that text rather than against
this guide or against memory. If the read fails because the file is not in the
tree, say so in the finding and fall back to the conventions in neighbouring
tests.

One caveat about that document: its harness sections are `kernel-doc`
directives rather than prose, so the macros themselves are not in it. They live
in `tools/testing/selftests/kselftest_harness.h`, and the exit codes in
`tools/testing/selftests/kselftest.h`. Read those headers with `git_read_files`
when a finding turns on exactly what a macro does.

What follows is the part that decides whether a test reports the truth.

kselftests run in userspace and report results as TAP. The result of a test is
its **exit code**, and getting that wrong is the most common way a broken test
reports success.

| Exit code | Meaning | Constant |
|-----------|---------|----------|
| 0 | All tests passed | `KSFT_PASS` |
| 1 | A test failed | `KSFT_FAIL` |
| 2 | Test result is unknown | `KSFT_XFAIL` |
| 3 | Test was not run | `KSFT_XPASS` |
| 4 | Test was skipped | `KSFT_SKIP` |

The critical case: a test whose prerequisites are unavailable must exit with
`KSFT_SKIP` (4), **not** 0. Exiting 0 reports a pass for something that never
ran, which hides a regression for as long as the prerequisite stays missing.
For shell tests, `ksft_exit_skip` or an explicit `exit $ksft_skip` with
`ksft_skip=4` is the idiom.

Common reasons to skip rather than fail: not running as root, a required
`CONFIG_` option absent, a kernel feature not present on the running kernel,
missing hardware, or an unavailable dependency such as a specific `iproute2`
version.

### C tests: `kselftest.h` and `kselftest_harness.h`

`kselftest.h` provides the reporting API directly:

- `ksft_print_header()`, `ksft_set_plan(n)` -- emit the TAP header and plan.
  The plan count must match the number of results actually reported.
- `ksft_test_result_pass/fail/skip/xfail(fmt, ...)` -- one call per test.
- `ksft_exit_pass()`, `ksft_exit_fail()`, `ksft_exit_skip(fmt, ...)` -- exit
  with the right code and final TAP summary.
- `ksft_exit_fail_msg(fmt, ...)` for a fatal setup failure.

`kselftest_harness.h` provides a fixture-based framework instead, and manages
plan counting and exit codes itself. Its full macro list is in that header;
three properties matter for review:

- `ASSERT_*` aborts the test, `EXPECT_*` records a failure and continues. The
  same rule as KUnit applies: anything the following lines depend on must be an
  `ASSERT_*`, particularly a non-NULL check before a dereference.
- `FIXTURE_TEARDOWN` runs even when a test fails, so it is the right place for
  cleanup. Cleanup written at the end of the test body is skipped on the paths
  that need it most.
- `TEST_HARNESS_MAIN` supplies `main()`. A harness-based test that writes its
  own `main()` and calls tests directly bypasses the result reporting, so
  failures may not reach the exit code.

Do not mix the two styles: a file that includes `kselftest_harness.h` should
not also hand-roll `ksft_test_result_*` calls, since the harness is already
counting.

### Shell tests

Source `tools/testing/selftests/kselftest/ktap_helpers.sh` where available
rather than hand-printing TAP lines. Shell tests must still exit 4 to skip.
Note that `set -e` interacts badly with tests that check failing commands
deliberately, and that a cleanup `trap` is the only reliable way to release
resources when a test aborts partway.

## Per-Directory Support Files

A test directory carries more than its Makefile:

- **`config`** -- the `CONFIG_` fragment listing kernel options the tests need.
  A new test that depends on a config option must add it here, or automated
  runners will build a kernel that cannot run the test. This is frequently
  forgotten and produces mysterious skips or failures in CI.
- **`settings`** -- optional, holds `timeout=<seconds>` for suites that need
  longer than the default. A long-running test without it is killed and
  reported as a failure. `kselftest.rst` documents the current default; do not
  quote a number from memory.
- **`.gitignore`** -- generated binaries must be listed, or `git status` is
  dirty after a build.

## Portability and Environment

- Do not assume root. Check the capability actually needed and skip when it is
  absent, rather than failing.
- Do not hardcode page size, `HZ`, core count, architecture word size, or
  network interface names. Query them.
- Cross-compilation must work: respect `$(CC)`, `$(CFLAGS)` and `$(LDLIBS)`
  from the selftest Makefile machinery rather than invoking `gcc` directly.
- Tests must be runnable individually and in any order. State left behind
  (network namespaces, mounts, loaded modules, sysctl changes, created files)
  must be cleaned up on both the success and failure paths.
- Avoid `sleep` as synchronisation. Poll for the condition instead, with a
  bounded retry, or the test will flake on loaded machines.

## Quick Checks

- **New shared files**: When a commit creates a file that is sourced or
  imported by test scripts, verify it is added to `TEST_FILES` in the Makefile
- **`TEST_PROGS` vs `TEST_FILES`**: Executable tests go in `TEST_PROGS`;
  supporting files go in `TEST_FILES`. Mixing these up causes either execution
  failures or missing installations
- **KVM IRQ chip tests**: When tests use `KVM_IRQFD`, `KVM_IRQ_LINE`, or IRQ
  routing, verify `vm_create_with_one_vcpu()` is used and
  `TEST_REQUIRE(kvm_arch_has_default_irqchip())` is present
- **netns config assumptions**: When a test asserts an outcome that depends on
  `forwarding`, `rp_filter`, `accept_local` or any other `conf/{all,default}`
  knob, verify the test writes that knob itself. IPv4 inherits it from
  `init_net`, so an unwritten knob makes the assertion depend on the test host
- **Negative tests**: When a test asserts an error code for a condition that
  should be refused, verify a kernel missing that check would return a
  different code. If the missing check and an unrelated missing precondition
  both yield the asserted code, the test passes whether or not the kernel is
  correct
- **Hardcoded constants**: flag hardcoded filenames, IPs, or magic numbers
  where a loop/glob/table would cover future additions for free (e.g. a
  hardcoded `*.BTF` filename instead of a `*.BTF` glob in an install rule) —
  ask whether the specific value has a documented rationale or is just the
  first one the author tried
- **`Fixes:` tag accuracy on bugfix patches**: for a patch fixing a bug in
  existing test code, verify the `Fixes:` tag points at the commit that
  actually introduced the bug, not just the commit that added the general
  area of code — this is checked mechanically by CI bots on some lists
  (e.g. bpf) and gets flagged when wrong
- **Skip vs pass**: A test that cannot run its prerequisites must exit 4
  (`KSFT_SKIP`), never 0. Exiting 0 reports a pass for a test that never ran
- **`EXPECT_*` before a dereference**: should be `ASSERT_*`, which aborts
- **New `CONFIG_` dependency**: must be added to the directory's `config`
  fragment, or CI builds a kernel that cannot run the test
- **Long-running suite**: needs `timeout=` in `settings`, or it is killed at 45
  seconds and reported as a failure
- **Cleanup on the failure path**: namespaces, mounts, modules and temporary
  files must be released when a test aborts, not only when it succeeds
- **Root assumed**: check the specific capability and skip when absent
