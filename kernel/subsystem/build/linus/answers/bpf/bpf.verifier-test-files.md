- `prog_tests/verifier.c` has two entry forms, and they differ in
  capabilities:

| Entry | Privileged subtests run with |
|---|---|
| `RUN(skel)` | `CAP_SYS_ADMIN` dropped by `run_tests_aux()` |
| `RUN_TESTS(skel)` | the full capabilities of `test_progs` |

- `RUN_TESTS()` in `verifier.c`: used by a few entries, for example
  `test_verifier_ctx()`; most use `RUN()`.
- `RUN()` passes no pre-execution callback; a test that needs map contents
  before a `__retval()` run calls `run_tests_aux()` itself, as
  `test_verifier_array_access()` does.
- `pre_execution_cb` runs only when the program is executed, after the load.
- Test collection: the `sed` rule for `tests.h` in
  `tools/testing/selftests/bpf/Makefile` matches only a line that starts
  with `void test_` or `void serial_test_`; a `static` function or a
  return type on its own line is not collected.
- Every `SEC()` program in the object becomes a subtest unless it is marked
  `__auxiliary` or `__auxiliary_unpriv`; an unannotated helper program is
  loaded privileged and must load.
