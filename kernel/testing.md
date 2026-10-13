# Testability and Test Review

General rules for answering two questions about a patch, whether or not it
touches any tests:

- Should there be a test for what this patch changes?
- Do the tests it adds or changes give meaningful coverage: would each one fail
  if the behavior it covers broke?

Framework-specific rules live in `subsystem/kunit.md` and
`subsystem/selftests.md`, which load when the patch touches those frameworks.

## Finding the Tests That Already Exist

Before judging whether a test is missing, find the tests that already cover the
changed code, since a patch that leaves them untouched is the easiest gap to
miss. Search for:

- KUnit tests beside the changed code: a `tests/` directory at the same level,
  or a file in the same directory whose name marks it as a test (`*_kunit.c`,
  `*_test.c`, `*-test.c`, and similar).
- KUnit tests anywhere that call the changed functions.
- kselftests under `tools/testing/selftests/` that exercise the interface the
  changed code implements: its syscalls, ioctls, sysfs files, or netlink
  families.

Where such tests exist, the framework is at hand and extending it is cheap. A
behavior change to code they cover should normally update or extend them, and
a patch that changes such code without touching its tests is worth a question:
do the existing tests still pass, and does any of them pin the behavior that
changed? If one should now fail and does not, the suite has a hole; if none
covers the changed behavior, name the case that would.

## When Absent Tests Are Worth Raising

Most kernel patches ship without tests, and that is a normal state rather than a
defect. Raise a concern about missing tests only where one is both practical and
would have caught something:

- A behavior change in code that existing tests already cover, or that sits
  beside a test suite that could cover it, as found above.
- A bug fix whose commit message describes a concrete reproducer, in code that
  an existing test suite already reaches.
- A new UAPI surface: a syscall, an ioctl, a sysfs file, or a netlink attribute.
  Interfaces that userspace will depend on are the highest-value place for a
  test, because a regression there is a contract break.
- A change to a pure, self-contained algorithm (parsing, allocation policy,
  hashing, or bitmap and list manipulation) where a unit test is cheap.
- A patch that fixes a bug in code that already has a test suite, where the
  existing suite passed both before and after. That is direct evidence the
  suite has a hole.

Do not raise it for:

- Refactors with no behavioral change, comment and typo fixes, or cleanups.
- Driver code for hardware with no emulation or model available.
- Changes whose only failure mode needs a specific machine, timing window, or
  physical device to observe.
- Error paths reachable only under allocation failure, unless the subsystem has
  established fault-injection coverage.

When you do raise it, say what the test would check. "No test" is not review
feedback; "nothing exercises the new `E2BIG` path, which the previous version
returned `EINVAL` for" is.

## What Test Review Adds

Memory lifetime, locking, and overflow bugs in test code are found the same way
as anywhere else in the patch. Test review asks what the rest of the review
does not: whether the tests are worth having.

- whether each one would fail if the code it covers were wrong
- whether two of them prove the same thing
- whether the inputs reach the interesting values or only comfortable ones
- whether a passing run means anything

## Step-by-Step Test Review Method

Work these in order against the test body and the code it exercises. **None
can be answered from the diff alone.** Read the functions under test, at the
revision under review, before judging the tests.

### Step 1: Name what each test case pins down

For every test case, state in one sentence the property it establishes. If you
cannot, that is itself the finding: a case whose purpose you cannot name is one
the next maintainer cannot name either.

### Step 2: Look for cases that prove the same thing

Compare the sentences from Step 1. Two cases differing only in their input
values, where both take the same path through the code, are one test written
twice. Say which pair, and what a genuinely different second case would cover.

### Step 3: For each property, name the bug it would catch

Construct the mutation: the plausible wrong version of the code this test
exists to reject. Then check the test's *input data* against the branches you
read, and ask whether it would actually fail on that mutation.

A test passes vacuously whenever the inputs cannot distinguish right from
wrong. If two different orderings, comparisons, or code paths produce the same
result on this data, nothing is being verified. Sorting is the classic case:
when the secondary key is proportional to the primary key, both orders yield
the same permutation and the comparison function is never really exercised.

State such a finding as the mutation that survives: "if `sort_idmaps()` sorted
both arrays by `first`, this test would still pass."

### Step 4: Find the values nobody tested

Against the branches from your reading, and the conditionals the patch adds,
identify what is missing. "Does it cover both directions?" below is the
checklist for this step.

### Step 5: Ask what a green run would prove

If every case passes, what does the reader now know that they did not before?
If the honest answer is "that the code compiles and does not crash on one
typical input," say so.

## Reviewing Tests That Are Present

Treat test code as code. The bar is not lower because a bug there does not
panic the kernel; a broken test is worse than no test, because it advertises
coverage that does not exist.

### Assertions that cannot fail

Step 3 asks whether a test would catch its bug. Some cannot catch anything at
all: checking that a function returns without error while ignoring what it
returned, comparing a value to itself, or asserting a condition the setup code
just established.

### Does it cover both directions?

The most common gap in an otherwise sound test is that it only proves the happy
path: valid input produces the right answer, and nothing checks what invalid
input does. Both halves are needed, and the error half is where the bugs
usually are, because it is the half that runs least often in production.

- **Which refusals does no case trip?** Read the new conditionals in the diff:
  the bounds checks, validation branches, and early error returns the patch
  adds. A check that no test exercises is untested code that looks tested.
  Raise one only by the bar in "When Absent Tests Are Worth Raising": a case
  for it is practical and would catch something, as for validation of input
  from userspace. A path reachable only under allocation failure, or only on
  specific hardware, is not worth a case.
- **Does it assert the specific error, or only that one occurred?** Asserting
  `ret < 0` passes for any failure, including the wrong one. Assert the exact
  value: `-EINVAL`, not "negative." For anything reachable from userspace this
  matters twice over, since the errno is part of the interface, and a test that
  accepts any error will not notice when it changes out from under a caller.
- **Are the boundaries tested, or only the middle?** Where the code compares
  against a limit, the interesting values are the limit itself and one on each
  side of it. Zero, one, empty, and NULL are the other perennial gaps. An
  off-by-one lives exactly where a test built from typical values will not
  look.
- **Are the arithmetic edges covered where they apply?** Values that overflow
  when multiplied by an element size, negative values passed into unsigned
  parameters, and anything near `INT_MAX`, `SIZE_MAX`, or `PAGE_SIZE` are the
  cases that become exploitable bugs rather than merely wrong answers.

This asks for one or two more cases, not for exhaustive coverage. Name the
specific missing one ("nothing passes a length of zero, which the new
`if (len < 1)` rejects") rather than asking for "more negative testing."

### Does it test behavior or implementation?

Prefer tests that pin observable behavior: return values, errno, emitted
events, and resulting state visible through an interface. Tests that assert on
internal structure layout, call counts, or the exact order of internal
operations break on every legitimate refactor and get deleted rather than
fixed.

### Failure modes to look for

- **Silent skips.** A test that skips when its prerequisites are missing is
  correct; one that *passes* in that case is not. Check that unavailable
  dependencies produce a skip result, not success.
- **State left behind.** Beyond the leak itself, consider what it does to the
  run: a test that leaves a namespace, mount, module, or sysctl behind changes
  the environment every later test sees, so a failure three cases later has
  nothing to do with the code that caused it. Check that teardown happens on
  the failure path, since that is the path where it is usually forgotten and
  where the contamination starts.
- **Order dependence.** A test that only passes after another test has run, or
  that leaves global state behind, will fail confusingly when the suite is run
  in isolation or in parallel.
- **Timing.** `sleep` as synchronization is a flake generator. Look for a
  condition to wait on instead. Tests that assert on elapsed time will fail on
  loaded CI machines.
- **Hardcoded environment.** Absolute paths, fixed PIDs or ports, and
  assumptions about page size, core count, `CONFIG_` options, architecture word
  size, or running as root. Privileged operations should check for the
  capability and skip when it is absent.
- **Ignored return values.** Setup calls whose failure is not checked turn a
  broken environment into a confusing assertion failure much later.
- **Failures that say nothing.** An assertion reporting only "failed," with
  neither the expected nor the actual value, costs the next person a debugging
  session to learn what the test already knew.

## Where a Test Belongs in a Series

When the patch under review is part of a series, judge ordering only against the
other patches you can see, and say nothing about ordering when the patch is
reviewed on its own.

Two orderings are worth raising:

- **A test that lands before the fix it exercises.** If this patch adds a test
  for a bug and a later patch in the series fixes that bug, every commit
  between the two fails that test. That breaks bisection: someone landing on an
  intermediate commit sees a failure unrelated to what they are hunting. The
  fix should come first, or the fix and its test should be a single patch.

- **A refactor whose tests arrive afterward.** If this patch restructures code
  without intending a behavioral change, and a later patch adds tests for that
  same code, the series never demonstrates the property the refactor claims.
  Tests added first, passing against the original implementation and again
  after the restructuring, are what make "no functional change intended"
  checkable rather than asserted. Ask for the test patch to move ahead of the
  refactor.

The two rules point in opposite directions on purpose: a test for existing
behavior belongs before the change, and a test for behavior that does not work
yet belongs with or after the fix. What distinguishes them is whether the test
would pass at the commit it is introduced in. A test that cannot pass when it
lands is the problem in both cases.

Series ordering is low severity as a rule, since it is a question of hygiene
rather than correctness. Bisectability is a real cost, though, and worth a
sentence when a failing test would sit in the tree across several commits.

## Reporting

Testability findings are usually medium severity at most, and often low. A
test that passes when it should fail is the exception worth arguing for: it is
an active false signal, not merely a gap. Weigh a missing test against how much
of the subsystem already goes untested; consistency with surrounding practice
matters more than an absolute standard.
