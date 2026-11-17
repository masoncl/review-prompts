# KUnit Subsystem Details

In-kernel unit testing framework. Tests are built into the kernel or as modules
and run in-kernel, typically under UML or QEMU via
`./tools/testing/kunit/kunit.py run`.

Distinct from kselftest (`tools/testing/selftests/`), which runs in userspace
and tests the kernel from outside. A patch may touch both; they have different
rules.

`Documentation/dev-tools/kunit/` is the authority on KUnit. Read the relevant
file at the revision under review when a finding turns on how KUnit behaves:

- `style.rst`: naming, Kconfig entries, and file placement.
- `usage.rst`: expectations and assertions, suites, memory and cleanup
  actions, parameterized tests, and testing static functions.
- `start.rst`, "Writing Your First Test": the Kconfig, Makefile, and
  `.kunitconfig` wiring a new test needs.
- `api/test.rst` and `api/resource.rst`: the macro and function reference.

This guide covers what those documents do not: which mistakes matter for
review, and why.

## What this review is for

Reviewing a KUnit test means answering, above all, whether each test would
catch the bug it is supposed to catch. Naming and file placement matter too,
but they are the smallest part of it.

**A review that reports only naming, Kconfig, and placement has failed**, no
matter how correct those observations are. Those come from reading one
document. Whether the tests are worth having comes from reading code, and the
method for that is in `testing.md` at the top of the prompt directory: work
through it as well as this guide.

## REQUIRED: read the in-tree style guide

**You MUST read `Documentation/dev-tools/kunit/style.rst` at the revision
under review before reporting any finding about naming, configuration, or file
placement.** It is short. Reading it at the reviewed revision also means a
patch that amends the style guide is judged against its own updated rules.

Do not answer from memory. Memory of this document is unreliable, and the
people reading your review will cite the real text back at you. If the file is
not in the tree, the tree predates the document or is not Linux: fall back to
the conventions visible in neighboring tests, and say so in the finding.

Reading it is a prerequisite for the style half of the review, not a substitute
for the rest of it.

### Questions it answers: answer each one

Once you have read it, work through this list rather than reporting only what
happens to catch your eye. Each question has an answer in that document; find
it and compare it to the patch.

- Where does a test source file belong, relative to the code it tests, and is
  this file there?
- What should the file itself be named?
- What should the module be named, if it builds as one?
- What should the suite be named, given the subsystem it belongs to?
- What should the individual test cases be named?
- What should the Kconfig symbol be named, and what should its entry contain?

Its recommendations count as much as its requirements: they describe the
convention new tests are expected to follow.

These conventions are routinely missed, which is much of why this review
exists. The tree is full of tests named and placed some other way, and new
ones keep landing that way. Neighboring files that disagree with `style.rst`
are not precedent, so judge a **new** test file against the document rather
than against the tests around it. File placement needs the most care, because
the document phrases it as advice and nothing enforces it: raise a new file
that lands outside the recommended location unless it fits one of the
exceptions `style.rst` itself allows.

## Assertions vs. Expectations

`usage.rst`, "Expectations" and "Assertions," defines the two families:
`KUNIT_EXPECT_*` marks the test failed and continues, and `KUNIT_ASSERT_*`
marks it failed and aborts the case. The most common review finding is an
expectation guarding code that is invalid if the check fails:

```c
/* WRONG: on failure the test continues and dereferences NULL */
KUNIT_EXPECT_NOT_ERR_OR_NULL(test, obj);
KUNIT_EXPECT_EQ(test, obj->field, 42);

/* CORRECT: abort before the dereference */
KUNIT_ASSERT_NOT_ERR_OR_NULL(test, obj);
KUNIT_EXPECT_EQ(test, obj->field, 42);
```

Anything the rest of the case depends on must be an assertion: allocation
results, setup success, non-NULL pointers, and successful lookups. Assertions
do not belong in a suite's `exit()` function or in a resource's free function,
as `usage.rst` warns.

## Suite Structure

`usage.rst`, "Test Suites," describes the structure. Mistakes in it fail
quietly:

- The `kunit_case` array must end with an empty `{}` entry. Without it, the
  runner walks off the end of the array.
- `.init` and `.exit` run around *each* case; `.suite_init` and `.suite_exit`
  run once per suite. State that must not leak between cases belongs in the
  per-case pair. The suite-level pair receives the suite rather than a
  `struct kunit`, so test-managed allocation is not available there.
- A suite that is never registered with `kunit_test_suite()` never runs. A
  `static` suite at least draws a "defined but not used" warning; a non-static
  one draws nothing.

## Memory and Cleanup

`usage.rst`, "Allocating Memory" and "Registering Cleanup Actions," covers the
test-managed allocators (`kunit_kzalloc()` and friends) and
`kunit_add_action()`. What to look for:

- Plain `kmalloc()` in a test is not tracked by KUnit and leaks whenever an
  assertion aborts the case before the matching `kfree()`, because the abort
  does not unwind.
- An allocation result must be checked with an assertion, such as
  `KUNIT_ASSERT_NOT_NULL()`, not an expectation.
- A function cast to `kunit_action_t` breaks Control Flow Integrity; use
  `KUNIT_DEFINE_ACTION_WRAPPER()` instead.
- A `kunit_add_action()` whose failure is ignored leaks the resource; use
  `kunit_add_action_or_reset()` when the cleanup must run regardless.

## Why the Build Wiring Matters

The exact Kconfig form belongs to `style.rst`, and `start.rst` shows the full
wiring. What matters for review is the consequence of getting it wrong, because
none of these failures is loud:

- A test whose Kconfig entry does not follow the `KUNIT_ALL_TESTS` convention
  is skipped by every all-tests build, including the default configuration of
  `kunit.py run` and the CI systems that rely on it. It compiles, it is
  correct, and it rarely runs.
- A new test file with no `obj-$(CONFIG_...)` line in the Makefile is never
  built at all. Nothing warns.
- A tristate test built as a module needs `MODULE_LICENSE()` and
  `MODULE_DESCRIPTION()`. modpost raises an error for a missing license and a
  warning for a missing description, so the first breaks the build for whoever
  enables the test as a module, often not the author, who built it in.

So when a patch adds a test, check that it is reachable: a Kconfig entry
matching the documented pattern, a Makefile line referring to the same symbol,
and, where the subsystem uses one, an entry in the relevant `.kunitconfig`.

## Parameterized Tests

`usage.rst`, "Parameterized Testing," describes `KUNIT_CASE_PARAM()` and the
array helpers. The generator should write a description of each parameter into
the `desc` buffer it is handed; `KUNIT_ARRAY_PARAM()` with a `get_desc`
function, or `KUNIT_ARRAY_PARAM_DESC()`, does this for an array. Without one,
KUnit names each run by index alone, so a failure says which run failed but not
which input.

## Skipping

`kunit_skip()` marks a case skipped and stops it; `kunit_mark_skipped()` marks
it skipped but continues (`api/test.rst`). Use these when a precondition is
genuinely unavailable, such as a required feature not compiled in. Do not
silently `return` from a test when its preconditions are missing, since that
reports a pass for something that never ran.

## Quick Checks

- **`KUNIT_EXPECT_*` before a dereference**: should be `KUNIT_ASSERT_*`
- **Assertions in `exit()` or a resource free function**
- **Missing `{}` terminator** in the `kunit_case` array
- **Suite never registered with `kunit_test_suite()`**, especially a
  non-static one, which draws no warning
- **`kmalloc()` in a test** where `kunit_kzalloc()` would free on abort
- **Function cast to `kunit_action_t`** instead of
  `KUNIT_DEFINE_ACTION_WRAPPER()`
- **Kconfig missing the `KUNIT_ALL_TESTS` idiom**, so all-tests runs skip it
- **New test file with no `obj-$(CONFIG_...)` Makefile line**, so it never
  builds
- **Missing `MODULE_LICENSE()`** in a test that can build as a module: modpost
  errors out. A missing `MODULE_DESCRIPTION()` warns
- **File placement**: is the test source where `style.rst` wants it, relative
  to the code under test?
- **Naming and Kconfig form**: check `style.rst` as read from the tree, not
  memory, and answer each of its questions above rather than only the obvious
  one
- **Early `return` instead of `kunit_skip()`** when a precondition is missing
- **`.init` used for setup that should be once per suite** (`.suite_init`)
