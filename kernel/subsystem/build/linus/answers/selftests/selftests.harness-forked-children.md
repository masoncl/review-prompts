| | `TEST()` | `TEST_F()` |
|---|---|---|
| `_metadata` | static object, private copy after `fork()` | `MAP_SHARED` mapping |
| `exit_code` and `trigger` set in the forked child | lost | seen by the body and the wrapper |
| `t->results` (reason of `SKIP()`) | shared | shared |
| `*no_teardown` | not used | shared |

- `EXPECT_*` or `ASSERT_*` failing in a child forked from a `TEST_F()` body:
  the test fails even if the body ignores the child's status.
- Shared verdict: read when the wrapper has returned and the child calls
  `_exit(t->exit_code)`; a forked child that fails later is not counted, so
  the body has to wait for it.
- `ASSERT_*` failing in a forked child: `abort()` ends that child only; the
  body carries on.
- `FIXTURE_TEARDOWN()` fixture: `__bail()` in the forked child runs the
  teardown there, on that child's copy of `self`; the body's own teardown is
  then skipped.
- `FIXTURE_TEARDOWN_PARENT()` fixture: `__bail()` in the forked child runs no
  teardown; the wrapper runs it once.
- `trigger` in a `TEST_F()`: shared, so a check that fails in one process can
  make a passing check in the other run its handler, and abort if it is an
  `ASSERT_*`.
- **Potentially unsafe usage**: `ASSERT_*` or `EXPECT_*` in a child forked from
  a `TEST()` body.
  - Unsafe: when the body does not check the child's wait status; the failure
    is logged and the test passes.
  - Safe: the child ends with `_exit(_metadata->exit_code)` and the body
    asserts on `waitpid()`, `WIFEXITED()` and `WEXITSTATUS()`, as
    `TEST(ruleset_fd_transfer)` in
    `tools/testing/selftests/landlock/base_test.c` does.
