| Job | File | Easy to miss |
|---|---|---|
| Runner entry point | `tools/testing/selftests/run_kselftest.sh` | Checked-in file; the `install` target of `tools/testing/selftests/Makefile` copies it. The generated file is `kselftest-list.txt`, built from each target's `emit_tests`. |
| Runner output prefix | `tools/testing/selftests/kselftest/prefix.pl` | Used by `tap_prefix()` in `tools/testing/selftests/kselftest/runner.sh`; falls back to `sed` when `/usr/bin/perl` is not executable. |
| Python reporting | `tools/testing/selftests/kselftest/ksft.py` | Functions have no `ksft_` prefix, for example `print_header()`, `set_plan()`, `test_result_pass()`, `finished()`. Counts only pass, fail, skip. |
| Python `ksft_run()`, `ksft_eq()`, `ksft_exit()` | `tools/testing/selftests/net/lib/py/ksft.py` | A separate module; it does not import `kselftest/ksft.py`. |
| Module test, script side | `tools/testing/selftests/kselftest/module.sh` | Only caller is `tools/testing/selftests/lib/bitmap.sh`. |
| Module test, module side | `tools/testing/selftests/kselftest_module.h` | Only includer is `lib/test_bitmap.c`, in the kernel's top-level `lib/`, not under selftests. |
| Modules built by selftests | `TEST_GEN_MODS_DIR` in `tools/testing/selftests/lib.mk` | Set by test Makefiles, for example `tools/testing/selftests/livepatch/Makefile`; modules built this way use neither `kselftest_module.h` nor `kselftest/module.sh`. |
| Packaging | `tools/testing/selftests/gen_kselftest_tar.sh`; `gen_tar` target in `tools/testing/selftests/Makefile` | The script calls `./kselftest_install.sh` and prints a hint to use `make gen_tar`. |
| Build dependency check | `tools/testing/selftests/kselftest_deps.sh` | Not install or packaging; no Makefile calls it. It link-tests each `LDLIBS` entry found in the test Makefiles. |
