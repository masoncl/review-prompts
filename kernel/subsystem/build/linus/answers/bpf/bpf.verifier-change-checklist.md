- All selftest paths below are under `tools/testing/selftests/bpf/`.
- Log text has two sources: the `verbose()` line, and next to it a call into
  `kernel/bpf/diagnostics.c` such as `bpf_diag_policy()`. Both write to the
  same log when the level has a `BPF_LOG_LEVEL` bit. `__msg()` and
  `__msg_unpriv()` match either; for example `progs/verifier_unpriv.c`
  expects "policy check failed for".
- `__msg()` order: each pattern is searched for after the end of the previous
  match, so reordering two log lines fails a test. `__not_msg()` must be
  absent between its neighbouring `__msg()` matches.
- Alignment tests: `progs/verifier_align.c`; there is no prog_tests/align.c.
- There are no verifier_spectre files; Spectre expectations are `__xlated()`
  and `__xlated_unpriv()` lines in files such as `progs/verifier_unpriv.c` and
  `progs/verifier_bounds.c`.
- Unprivileged expectations in `test_loader.c`: a test with an `_unpriv`
  annotation that sets `UNPRIV` in `mode_mask` also runs unprivileged;
  `__stderr_unpriv()` and `__stdout_unpriv()` do not set it. Whatever it does
  not state for unprivileged mode (result, messages, xlated, jited) is copied
  from the privileged expectation. A change in unprivileged acceptance fails
  such a test though it has no `__failure_unpriv`.
- Unprivileged in `test_loader.c`: `drop_capabilities()` drops `CAP_SYS_ADMIN`,
  `CAP_NET_ADMIN`, `CAP_PERFMON` and `CAP_BPF`; `__caps_unpriv()` gives some
  back.
- `test_verifier.c`: runs a test unprivileged only when `test_as_unpriv()`
  holds: `prog_type` unset, `BPF_PROG_TYPE_SOCKET_FILTER` or
  `BPF_PROG_TYPE_CGROUP_SKB`.
- `test_verifier.c` rewrite checks: `.expected_insns` and `.unexpected_insns`,
  for example in `verifier/bpf_loop_inline.c`.
- Level 2 log output is matched literally: for example
  `progs/verifier_live_stack.c`, `progs/compute_live_registers.c`,
  `progs/verifier_subprog_topo.c`, `progs/verifier_precision.c`.
- Prologue and epilogue rewrites: `progs/pro_epilogue.c`, run from
  `prog_tests/pro_epilogue.c`.
