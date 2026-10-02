- Mode: `spec->mode_mask` in `parse_test_spec()` in
  `tools/testing/selftests/bpf/test_loader.c`; `process_subtest()` runs one
  subtest per bit set.
- `__retval()`: sets the privileged bit; `__retval_unpriv()` and
  `__caps_unpriv()` set the unprivileged bit.
- `__stderr()`, `__stdout()`, `__stderr_unpriv()`, `__stdout_unpriv()`,
  `__log_level()`, `__flag()`, `__description()` and `__arch_x86_64`-style
  tags: select no mode.
- No annotation that sets the privileged bit, and one that sets the
  unprivileged bit: the program is not run privileged.
- No annotation at all: run privileged, and the load must succeed.
- There are no __priv, __unpriv, __msg_regex or __regex macros in
  `bpf_misc.h`; a regex is `{{...}}` inside any pattern, see
  `compile_regex()`.
- Tag text: `__test_tag()` puts `__COUNTER__` after `comment:`;
  `skip_decl_tag_pfx()` ignores a decl tag written without the number.
- `" @unpriv"`: appended to the program name for every unprivileged subtest,
  and to the `__description()` text too when there is one.
- Unprivileged covers the load only: `run_subtest()` calls
  `restore_capabilities()` before it dumps xlated or jited code and before
  `do_prog_test_run()`.
- Unprivileged subtest is skipped, not failed, when `get_unpriv_disabled()` in
  `unpriv_helpers.c` returns true (sysctl set, mitigations off, or kernel
  config unreadable), or for `BPF_F_ANY_ALIGNMENT` without
  `CONFIG_HAVE_EFFICIENT_UNALIGNED_ACCESS`.
- Unprivileged run: maps that `is_unpriv_capable_map()` rejects get
  `bpf_map__set_autocreate(map, false)`.
- Inheritance is per list and only into an empty list: one `__msg_unpriv()` or
  `__not_msg_unpriv()` stops every `__msg()` and `__not_msg()` from being
  copied to the unprivileged run.
- `__xlated()`, `__jited()`, `__stderr()`, `__stdout()`: each pattern must
  match on the line after the previous match, unless `"..."` stands between
  them; `__msg()` has no line rule.
- With no `__log_level()` and `test_progs` run without `-v`, the level is 0
  and a successful load leaves the log empty; a rejected load is logged at
  level 1.
- **Unsafe usage**: `__not_msg()` on a program that loads successfully, with
  no `__log_level()`.
  - Unsafe: the log is empty, so the pattern is absent whatever the verifier
    did.
  - Safe: with `__log_level(2)`, as in `progs/verifier_zext.c`.
- **Unsafe usage**: two or more `__not_msg()` in a row with no `__msg()`
  between them.
  - Unsafe: `match_negative_msgs()` searches for the first pattern of the run
    only; the later ones are never looked for.
  - Safe: one `__not_msg()` per gap between `__msg()` lines, as
    `__not_msg_unpriv()` between `__msg_unpriv()` lines in
    `unpriv_pseudo_func_policy()` in `progs/verifier_unpriv.c`.
- **Potentially unsafe usage**: `__stderr()` or `__stdout()` without
  `__retval()`.
  - Unsafe: when the program is tested only through `run_subtest()`; it reads
    the streams only inside the `should_do_test_run()` branch, so the
    patterns are never compared.
  - Safe: with `__success __retval(0)`, as in `progs/stream.c`.
  - Safe: `__stderr()` when the test runs the program itself and then calls
    `verify_test_stderr()`, as `run_libarena_asan_test()` in
    `prog_tests/libarena_asan.c` does.
- `__retval(POINTER_VALUE)`: the program is run but its return value is not
  compared.
