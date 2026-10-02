# Selftests Subsystem Details

## Main structures

### Objects and how they relate

- Target: a path listed in `TARGETS` in `tools/testing/selftests/Makefile`,
  not every directory that has a Makefile; for example
  `tools/testing/selftests/kmod` and `tools/testing/selftests/drivers/net/hw`
  are not in the list, so `tools/testing/selftests/Makefile` builds them only
  when a user adds them to `TARGETS`.
- Nested target: `drivers/net/bonding` is a target of its own beside
  `drivers/net`; the target path is also the collection name in
  `kselftest-list.txt`.
- `KSFT_INSTALL_PATH`: read only by `tools/testing/selftests/Makefile`;
  `tools/testing/selftests/lib.mk` sees `INSTALL_PATH` set per target.
- `TEST_INCLUDES`: files in a subdirectory of selftests, the target's own or
  another, copied with their relative path kept; this is how shared shell
  and Python libraries reach an installed tree.
- `struct ksft_count`: `ksft_cnt` and `ksft_plan` are `static` in
  `tools/testing/selftests/kselftest.h`, so there is one copy per translation
  unit that includes the header, not one per process.
- `ksft_finished()`: the only exit helper in `kselftest.h` whose exit code
  depends on `ksft_plan`; `ksft_exit_pass()` and `ksft_exit_fail()` only
  print a comment on a mismatch, through `ksft_print_cnts()`.
- Python `ksft`: two unrelated modules share the name.
  `tools/testing/selftests/kselftest/ksft.py` is a thin KTAP printer with
  pass, fail and skip only. `tools/testing/selftests/net/lib/py/ksft.py` is a
  case runner (`ksft_run()`) with its own checks, variants and xfail.
- `__fixture_list`: the only global list in
  `tools/testing/selftests/kselftest_harness.h`; it is initialised to
  `&_fixture_global`.
- `struct __test_metadata`: registered on its fixture's `tests` list by
  `__register_test()`, not on a global list; one object per `TEST()` or
  `TEST_F()`, reset and reused for every variant by `__run_test()`.
- `struct __test_xfail`: hangs on a variant's `xfails` list; `XFAIL_ADD()`
  works only for a test defined through `__TEST_F_IMPL()` (`TEST_F()`,
  `TEST_F_SIGNAL()`, `TEST_F_TIMEOUT()`) under a `FIXTURE_VARIANT_ADD()`
  variant, not for a plain `TEST()`.
- `struct __test_results`: one `MAP_SHARED` object for the whole run, attached
  to `t->results` only while that test runs; it carries the `SKIP()` reason
  back to the harness.
- `TEST()` processes: two; the body runs in the child that `__run_test()`
  forks.
- `FIXTURE_TEARDOWN_PARENT()`: the teardown runs in the wrapper process, the
  parent of the grandchild; it does not run in the harness process.
- `TEST_F()` metadata: `mmap()`ed `MAP_SHARED` by its constructor, which is
  how the grandchild's `exit_code` reaches the wrapper.
- `TEST()` metadata: an ordinary static object, so writes made in the child
  are not seen by the harness.
- Result path to the harness: the child's wait status in both cases;
  `__wait_for_test()` overwrites `t->exit_code` on every path.

## Where to look

**Core files**

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

**Shared helper libraries**

| Directory (all paths under `tools/testing/selftests/`) | Shared helper | What differs from the usual expectation |
|---|---|---|
| `mm` | `mm/vm_util.h`, `mm/vm_util.c`; `mm/hugepage_settings.h`, `mm/hugepage_settings.c` | There is no thp_settings.h or thp_settings.c. `struct thp_settings`, `thp_read_settings()`, `default_huge_page_size()`, `detect_hugetlb_page_sizes()` are in `mm/hugepage_settings.h`. `mm/Makefile` links both `.c` files into every `TEST_GEN_FILES` binary. |
| `mm` (running) | `mm/run_vmtests.sh` | Test binaries are `TEST_GEN_FILES`, which `run_tests` in `lib.mk` does not run. `TEST_PROGS` holds wrapper scripts; for example `mm/ksft_thp.sh` runs `./run_vmtests.sh -t thp`. |
| `net` (shell) | `net/lib.sh` | `log_test()`, `check_err()`, `tests_run()`, `tc_rule_stats_get()` are defined here, not in `net/forwarding/lib.sh`. `defer()` comes from `net/lib/sh/defer.sh`, which `net/lib.sh` sources. |
| `net` (C) | `net/lib/ksft.h` (`ksft_ready()`, `ksft_wait()`); `net/ynl.mk`; `net/psock_lib.h`; `net/tuntap_helpers.h` | There is no net/lib.h. `net/lib/csum.c`, `net/lib/gro.c`, `net/lib/xdp_helper.c` each have `main()` and are built as `TEST_GEN_FILES`; they are programs, not library code. |
| `drivers/net` (Python) | `drivers/net/lib/py/` | Also exports `NetDrvContEnv` (netkit pair into a netns). `drivers/net/hw/lib/py/__init__.py` re-exports the environment classes for tests in `drivers/net/hw`. |
| `drivers/net` (shell) | `net/lib.sh` or `net/forwarding/lib.sh` | `drivers/net/lib/sh/` holds only `lib_netcons.sh`. With `DRIVER_TEST_CONFORMANT=yes`, `net/forwarding/lib.sh` sources drivers/net/net.config if that file exists (it is not in the tree) and fills `NETIFS` from `NETIF`, `REMOTE_TYPE`, `REMOTE_ARGS` and `REMOTE_V4` or `REMOTE_V6`. |
| `net/forwarding` | `net/forwarding/lib.sh` | Only `forwarding.config.sample` is in the tree; `lib.sh` sources forwarding.config only if that file exists. |
| `kvm` | `kvm/include/`, `kvm/lib/` | `processor.h` exists only per arch, for example `kvm/include/x86/processor.h`. The arch directories are `x86`, `arm64`, `s390`, `riscv`, `loongarch`; there is no x86_64 directory and no kvm_util_base.h. |
| `kvm` (harness) | `kvm/include/kvm_test_harness.h` | Wraps `kselftest_harness.h`: `KVM_ONE_VCPU_TEST_SUITE()`, `KVM_ONE_VCPU_TEST()`. |
| `cgroup` | `cgroup/lib/cgroup_util.c`, `cgroup/lib/include/cgroup_util.h`, built by `cgroup/lib/libcgroup.mk` | No `cgroup_util.h` directly in `cgroup/`. `kvm/Makefile.kvm` includes `libcgroup.mk` too. |
| `arm64` | none arm64-wide; helpers are per subdirectory | `arm64/fp/fp-ptrace.c` and `arm64/fp/sve-probe-vls.c` are test programs, not helpers. |
| `filesystems` | `filesystems/utils.h`, `filesystems/utils.c`; `filesystems/wrappers.h` | Shared, also outside `filesystems/`: `namespaces/Makefile` and `exec/Makefile` use `utils.c`, `mount_setattr/Makefile` uses only `wrappers.h`. A test links `utils.c` by naming it as a prerequisite in its Makefile: `../utils.c` from a subdirectory of `filesystems/`, `../filesystems/utils.c` from outside. |
| `filesystems` (names) | `filesystems/utils.h` | Has `get_userns_fd()`, `setup_userns()`, `enter_userns()`, `caps_down()`, `switch_ids()`, `wait_for_pid()`, `get_unique_mnt_id()`. `wrappers.h` does not define `sys_mount_setattr()`; `mount_setattr/mount_setattr_test.c` defines its own. There is no fs_util.h; `filesystems/overlayfs/` has `log.h` and uses `../wrappers.h`. |

## Makefiles, building and installing

**Test list variables**

- `TEST_GEN_MODS_DIR` (a directory of test modules): `all` builds it with a
  sub-make through `gen_mods_dir`; `install` copies only its `*.ko` files, into
  a subdirectory of the same name; `clean` runs the sub-make's `clean` through
  `clean_mods_dir`; not run, not listed. See `livepatch/Makefile` under
  `tools/testing/selftests/`.
- `TEST_CUSTOM_PROGS`: not a prerequisite of `all` in
  `tools/testing/selftests/lib.mk`. The Makefile adds
  `all: $(TEST_CUSTOM_PROGS)` itself, writes the `$(OUTPUT)/` prefix itself and
  lists the program in `EXTRA_CLEAN`, as `sync/Makefile` does.
- `clean`: `CLEAN` in `lib.mk` removes `TEST_GEN_PROGS`,
  `TEST_GEN_PROGS_EXTENDED`, `TEST_GEN_FILES` and `EXTRA_CLEAN`, with
  `$(RM) -r`, and nothing else.
- `TEST_GEN_FILES` and the other two prefixed lists: every entry is a
  prerequisite of `all`, but the common pattern rules only make
  `$(OUTPUT)/name` from `name.c` or `name.S`, and `$(OUTPUT)/name.o` from
  `name.S`. `lib.mk` has no rule for any other entry.
- `OVERRIDE_TARGETS` set: `lib.mk` defines no pattern rule at all; the entries
  stay prerequisites of `all`.

**Sourced and imported files**

- `INSTALL_INCLUDES` refusal: it resolves the directory of each
  `TEST_INCLUDES` entry with `readlink -e` and requires it to lie strictly
  below `$SRC_PATH`, the resolved `tools/testing/selftests`. Whether the entry
  is spelled absolute or relative does not matter.
- Refused entries: a file outside selftests, a file directly in the selftests
  root, and a file whose directory does not exist.
- On refusal: prints `Error: TEST_INCLUDES entry ... not located inside
  selftests directory` and exits 1, which fails that directory's `install` or
  `run_tests`.
- Entries in the test's own directory or its subdirectories are accepted:
  `net/packetdrill/Makefile` (`defaults.sh`), `drivers/net/Makefile`
  (`lib/py/*.py`). This keeps a subdirectory layout that `TEST_FILES` flattens.
- `SRC_PATH` and `OBJ_PATH`: passed only by `tools/testing/selftests/Makefile`,
  on its `run_tests` and `install` sub-makes. `lib.mk` gives them no default.
- `OBJ_PATH`: the install root for `install`, `$(BUILD)` for `run_tests`.
- `TEST_FILES` directory entry: copied recursively under its last path
  component, as `test.d` in `ftrace/Makefile`.
- Symlinks: `TEST_FILES` is copied with `--copy-unsafe-links`, so a link that
  points outside the copied tree becomes a copy of its target. `TEST_INCLUDES`
  is copied with `rsync -aR`, which keeps the link.
- `TEST_FILES` accepts paths outside selftests; `net/lib/Makefile` lists
  `tools/net/ynl` and `Documentation/netlink/specs` that way.
- Copy to `$(OUTPUT)` before `run_tests`: `lib.mk` copies `TEST_PROGS`,
  `TEST_PROGS_EXTENDED`, `TEST_FILES` and `TEST_GEN_MODS_DIR`, and runs
  `INSTALL_INCLUDES`, only under `ifdef building_out_of_srctree`.
- `building_out_of_srctree`: exported only by the top-level `Makefile`. `make
  O=dir kselftest` gets the copy. `make -C tools/testing/selftests O=dir
  run_tests` does not: scripts run from the source directory while generated
  files sit in `$(OUTPUT)`.
- Working directory: `run_one()` in `kselftest/runner.sh` changes into the
  test's directory before it runs the test, so a cwd-relative `source lib.sh`
  works under both runners, as in `net/amt.sh`.
- Python: `drivers/net/lib/py/__init__.py` computes the selftests root from
  `__file__` and appends it to `sys.path`, so the imports rely on
  `TEST_INCLUDES` keeping the tree-relative layout.
- **Potentially unsafe usage**: a `TEST_FILES` entry with a directory part,
  such as `../lib.sh`.
  - Unsafe: when the test opens the file by the path it has in the source
    tree; `INSTALL_SINGLE_RULE` puts it at `<target>/<basename>`.
  - Safe: when the consumer looks in the flattened place once installed, as
    `net/lib/py/ynl.py` does: it tests for `kselftest-list.txt` in the root and
    then uses `net/lib/specs` and `net/lib/ynl`.
  - Safe: the file is inside selftests and is listed in `TEST_INCLUDES`
    instead, as `../lib.sh` in `net/forwarding/Makefile`.
- Examples of `TEST_FILES` for same-directory helpers: `net/mptcp/Makefile`
  (`mptcp_lib.sh`) and `net/Makefile` (`lib.sh`, `in_netns.sh`,
  `fcnal-test.sh`, `settings`; it lists no net_helper.sh).
- Examples of `TEST_INCLUDES` across directories: `net/forwarding/Makefile`,
  `drivers/net/bonding/Makefile`.

**Generated file paths**

- Prefixing is done with `patsubst` at the point of the include; in `lib.mk`,
  `addprefix` appears only where out-of-tree `run_tests` prefixes `TEST_PROGS`
  after copying them.
- Before the include the three variables hold bare names. A rule for a bare
  name defines a different target from the one `all` depends on.
- `landlock/Makefile` shows the consequence: it writes the same
  target-specific assignments twice, before the include for the bare names
  and after it for the prefixed ones.
- `OUTPUT` default: `lib.mk` sets `OUTPUT := $(shell pwd)` only under
  `ifeq (0,$(MAKELEVEL))`. A Makefile that recurses into subdirectories passes
  `OUTPUT=` itself, as `arm64/Makefile` does.
- **Potentially unsafe usage**: a rule or prerequisite written as
  `$(OUTPUT)/name` before the include.
  - Unsafe: when the directory is built directly with no `OUTPUT=`; `OUTPUT`
    is still empty when make reads the rule, so the target is `/name`.
  - Safe: when a parent make passes `OUTPUT=`, as
    `tools/testing/selftests/Makefile` does in each of its per-directory
    loops.
  - Safe: after the include, as in `net/Makefile` and `vDSO/Makefile`.
- Assigned after the include: an entry is not prefixed and is not a
  prerequisite of `all`. The `run_tests`, `install`, `emit_tests` and `clean`
  recipes still see it, because recipes expand when they run.
- `lkdtm/Makefile` assigns `TEST_GEN_PROGS` after the include; it writes
  `$(OUTPUT)/` itself and adds `all: $(TEST_GEN_PROGS)`.

**Kernel and tools headers**

- There is no KHDR_DIR in this tree.
- `KHDR_INCLUDES`: set and exported by `tools/testing/selftests/Makefile`.
  With `O=` or `KBUILD_OUTPUT` it is `-isystem ${abs_objtree}/usr/include`,
  otherwise `-isystem ${abs_srctree}/usr/include`.
- `lib.mk` assigns `KHDR_INCLUDES` only when it is empty, which is the case
  when a test directory is built directly.
- `kselftest` and `kselftest-%` in the top-level `Makefile` depend on
  `headers`. `make -C tools/testing/selftests` runs no header install.
- `headers` in `lib.mk`: a target that runs the top-level `headers` for the
  tree named by `KHDR_INCLUDES`. Nothing in `lib.mk` depends on it.
- A test opts in to `headers` with an order-only prerequisite, as
  `$(OUTPUT)/vdso_standalone_test_x86` does in `vDSO/Makefile`.
- **Potentially unsafe usage**: expanding `$(KHDR_INCLUDES)` with `:=` before
  the include.
  - Unsafe: when the directory is built directly; the variable is empty until
    `lib.mk` is read, so the flag is silently missing.
  - Safe: when built through `tools/testing/selftests/Makefile`, which exports
    the variable.
  - Safe: `:=` after the include, as in `x86/Makefile`.
  - Safe: `+=` or `=` before the include, on a variable not assigned with
    `:=`, as `CFLAGS` in `sync/Makefile`; the reference expands when the
    compiler runs.
- **Unsafe usage**: a header path into the source tree, such as
  `-I$(top_srcdir)/usr/include`, in place of `$(KHDR_INCLUDES)`. With `O=` the
  headers are under the object tree and the path misses them.
  - Safe: `CFLAGS += $(KHDR_INCLUDES)`, as in `sync/Makefile`;
    `tools/testing/selftests/Makefile` points it at the object tree.

**Selecting test directories**

- `SKIP_TARGETS ?= bpf sched_ext` in `tools/testing/selftests/Makefile` is the
  only reason those two are not built by default. No toolchain or config test
  is made there.
- `SKIP_TARGETS` uses `filter-out`, which matches whole words: `SKIP_TARGETS=net`
  leaves `net/forwarding` and the other `net/` directories selected.
- `quicktest=1`: drops `timers` from the default list.
- `cpu-hotplug` and `memory-hotplug`: in `TARGETS` as well as in
  `TARGETS_HOTPLUG`. The default run includes them; `run_hotplug` runs their
  `run_full_test` target instead.
- `INSTALL_DEP_TARGETS := net/lib`: set when `TARGETS` holds the exact word
  `net`, `drivers/net` or `drivers/net/hw` and does not hold `net/lib`.
  `TARGETS=net/forwarding` alone does not add it.
- `drivers/net/hw`: named in that filter but absent from the default
  `TARGETS`, so it is built only when a user names it.
- `INSTALL_DEP_TARGETS` is computed before the `SKIP_TARGETS` filter and is
  not filtered by it. `SKIP_TARGETS=net/lib` does not remove it, and skipping
  `net` leaves it in place.
- `net/lib` added this way: built by `all`, copied by `install`, cleaned by
  `clean`. The `run_tests` loop and the emit loop iterate `$(TARGETS)` only, so
  it is not run and not listed.

**Build failures across directories**

- Default: `all` exits with the product of the per-directory statuses,
  starting from `ret=1`. The status is zero as soon as one directory builds,
  so one failed directory does not fail make.
- `FORCE_TARGETS` set: each sub-make is followed by `|| exit`, so the first
  failing directory stops the loop and make fails.
- `FORCE_TARGETS` is tested with `$(if ...)`: any non-empty value enables it,
  `FORCE_TARGETS=0` included.
- Empty list: `ret` stays 1 and `all` fails. `make TARGETS=bpf` with the
  default `SKIP_TARGETS` ends this way.
- `install`: depends on `all`, then runs its own loop with the same product
  and the same `FORCE_TARGETS` test.
- A non-zero status from the `install` loop stops the recipe after
  `kselftest-list.txt` was removed and before it is written again.

**Installed tree layout**

- Helpers: every file in `tools/testing/selftests/kselftest/` is installed,
  `kselftest/ksft.py` included; see the `install -m 744` lines of `install` in
  `tools/testing/selftests/Makefile`.
- Listed by the `emit_tests` of `lib.mk` only if all hold: the test is in
  `TEST_GEN_PROGS`, `TEST_CUSTOM_PROGS` or `TEST_PROGS`; its directory is in
  `$(TARGETS)`; and `$(INSTALL_PATH)/<target>` exists when the emit loop runs.
- A directory whose install produced nothing is skipped with `Skipping
  non-existent dir`.
- `emit_tests` output: the sub-make's stdout is appended to
  `kselftest-list.txt` as is. Anything a test Makefile prints on stdout
  during that goal becomes a list entry.
- `bpf/Makefile` skips its feature checks for the `emit_tests` goal;
  `arm64/Makefile` defines its own `emit_tests`, which prints nothing off
  arm64.
- Listed name: `emit_tests` prints the basename. `run_kselftest.sh` changes
  into `<collection>/` and runs `./<basename>`, so the file must sit at the top
  of the installed target directory.
- `config` and `settings`: installed through `$(wildcard config settings)` in
  `INSTALL_RULE` of `lib.mk`, with no `TEST_` variable. The test Makefile is
  not in that list.
- `tools/testing/selftests/seccomp/Makefile`: has no `TEST_FILES` entry for
  its `settings` file; the wildcard installs it.
- `settings` in the installed tree: `run_one()` reads it from
  `<install root>/<collection>/settings`; `run_kselftest.sh` sets `BASE_DIR`
  to its own directory.

**Adding a test directory**

- Required invocations in `Documentation/dev-tools/kselftest.rst`: the four
  goals `all`, `install`, `clean`, `gen_tar`, each with no `O=`, with an
  absolute `O=` and with a relative `O=`, from both entry points.
- The two entry points: the top-level `kselftest-all`, `kselftest-install`,
  `kselftest-clean`, `kselftest-gen_tar`, and
  `make -C tools/testing/selftests` with the bare goal.
- `kselftest-merge` is not in that list.
- `MAINTAINERS`: the section does not ask for an entry.
- `settings`: not mentioned in the section; the "Timeout for selftests"
  section of the same file describes it.
- Nested directory: `tools/testing/selftests/Makefile` does not recurse. A
  subdirectory needs its own `TARGETS` line with the path, as
  `filesystems/binderfs` has, or a parent Makefile that recurses, as
  `arm64/Makefile` does.

## The runner

**Working directory, stdout and stderr**

- `run_many()`: calls `run_one "$DIR" "$TEST"` directly unless `RUN_IN_NETNS`
  is set (`run_kselftest.sh -n`); the pipeline that captures the output is
  inside `run_one()`.
- Working directory: ``cd `dirname $TEST` `` in the runner's own shell, then
  `cd -`; `DIR` is not the `cd` target, it only builds the test name and
  the `settings` path.
- `TEST_PROGS` under make: bare names, so they run in the directory make
  entered, unless `building_out_of_srctree` is defined; then `run_tests` in
  `tools/testing/selftests/lib.mk` rsyncs them to `$(OUTPUT)` and they run
  there, like `TEST_GEN_PROGS`.
- stderr: merged into stdout with `2>&1` before the prefixing.
- Program output: appended to `$logfile`, which is the runner's stdout only by
  default.

  | Invocation | `logfile` |
  |---|---|
  | default | `/dev/stdout` |
  | `make summary=1`, `run_kselftest.sh -p` | `$per_test_log_dir/$BASENAME_TEST`, truncated per test |
  | `run_kselftest.sh -s` | `$BASE_DIR/output.log`, truncated once at option parsing |

- `per_test_log_dir`: `/tmp` by default; `run_kselftest.sh -p DIR` sets it and
  creates `DIR` if needed; make has no way to change it.
- `run_kselftest.sh -s`: does not set `per_test_logging`.
- `logfile`, `per_test_logging`, `per_test_log_dir`, `RUN_IN_NETNS`: assigned
  when `runner.sh` is sourced, so a value from the environment is overwritten.

**Exit codes**

- `KSFT_XFAIL` (2): has its own arm in `run_one()`; `ktap_test_xfail()` prints
  `ok N selftests: DIR: NAME # XFAIL`.
- `KSFT_FAIL` (1) and `KSFT_XPASS` (3): no arm; the `*` arm prints
  `not ok N ... # exit=1` and `# exit=3`.
- Arm labels: the shell variables `KSFT_PASS`, `KSFT_SKIP`, `KSFT_XFAIL` from
  `tools/testing/selftests/kselftest/ktap_helpers.sh`, plus `timeout_rc`;
  there is no skip_rc in this tree.
- Timeout (124): one line, `not ok N ... # TIMEOUT <secs> seconds`; no bare `#`
  line before it.
- Result lines: all printed by `__ktap_test()` in `ktap_helpers.sh`, which
  also advances `KTAP_TESTNO`.
- Failure bookkeeping: `ktap_test_fail()` increments `KTAP_CNT_FAIL`; there is
  no kselftest_failures_file in this tree.

**Runner exit status**

- `run_kselftest.sh`: exits `KSFT_FAIL` (1) by default when `KTAP_CNT_FAIL` is
  not 0; `ERROR_ON_FAIL=true` is the default.
- `-f` / `--no-error-on-fail`: sets `ERROR_ON_FAIL=false`, so the script exits
  0 whatever failed.
- -e / --error-on-fail: not an option here; an unknown option reaches
  `usage 1`, which exits 1 before any test runs.
- What counts as a failure: every `not ok` from `run_one()`, since each is
  printed by `ktap_test_fail()`; that includes timeouts, missing files and
  non-executable files that `run_one()` cannot run.
- `# SKIP` and `# XFAIL` results: do not increment `KTAP_CNT_FAIL`.
- `make run_tests`, `make kselftest`: exit 0 on test failures; `RUN_TESTS` in
  `tools/testing/selftests/lib.mk` does not read `KTAP_CNT_FAIL`, and there is
  no make equivalent of `ERROR_ON_FAIL`.

**Per-test timeout**

- `settings`: read inline by `run_one()` from `$BASE_DIR/$DIR/settings`; there
  is no kselftest_get_timeout() helper.
- `settings` under make: `BASE_DIR` is `$(selfdir)`, so the file is read from
  the source tree, even with a separate `$(OUTPUT)`.
- `tap_timeout()`: two nested calls,
  `/usr/bin/timeout --foreground "$kselftest_timeout" /usr/bin/timeout
  "$kselftest_timeout" $1`.
- `kselftest_override_timeout` under make: there is no make option, but
  `runner.sh` does not reset the variable, so a value in the environment takes
  effect; `run_kselftest.sh` clears it before parsing `-o`.
- `# timeout set to N` and `# overriding timeout to N`: appended to
  `$logfile`, which is the runner's stdout only by default.
- Missing utility: the test is `[ -x /usr/bin/timeout ]`, an absolute path, not
  a `$PATH` lookup; if it fails the program runs with no limit and no
  warning, and `# timeout set to N` is still printed.

**Missing and non-executable tests**

- Missing file: `# Warning: file $TEST is missing!`, then a plain
  `not ok N selftests: DIR: NAME`; it is a failure with `rc=$KSFT_FAIL`, not
  a `# SKIP`.
- No execute bit: not reported as a skip either; `run_one()` tries these in
  order:
  1. `./ksft_runner.sh` is executable: runs
     `./ksft_runner.sh ./$BASENAME_TEST`, with no warning.
  2. Otherwise prints `# Warning: file $TEST is not executable`; if the first
     line starts with `#!`, runs the file with that interpreter.
  3. Otherwise prints a plain `not ok N ...` and returns `KSFT_FAIL`.
- `ksft_runner.sh`: tried only after `[ -x "$TEST" ]` failed; an executable
  test in the same directory is run directly.
- `$kselftest_cmd_args` (from `KSELFTEST_<NAME>_ARGS`): appended only when the
  test itself is executable; the `ksft_runner.sh` and interpreter commands
  drop it.
- Directory with one: `tools/testing/selftests/net/packetdrill` is the only
  one; its `TEST_PROGS` are the `*.pkt` scripts, and its `Makefile` ships
  `ksft_runner.sh` through `TEST_INCLUDES`.

**Nested test output**

- `run_many()`: prints no `TAP version 13` line and no plan.
- `make run_tests`, `make kselftest`: nothing prints a version line, a plan or
  a totals line for the run; the stream holds `# selftests: ...` headers,
  `# `-prefixed program output and result lines.
- `run_kselftest.sh`: calls `ktap_print_header` and `ktap_set_plan "$total"`
  once for the whole run, before the first collection, and
  `ktap_print_totals` at the end.
- `$total`: the number of tests selected after `-t`, `-c` and `-S`, over all
  collections.
- Test numbers under `run_kselftest.sh` without `-n`: `KTAP_TESTNO` is one
  counter in one shell, so numbering continues across collections.
- Test numbers under make: each target directory's recipe sources
  `ktap_helpers.sh` afresh, so numbering restarts at 1 per directory.
- `KSFT_TAP_LEVEL`: nothing in this tree sets it; the only occurrence is the
  `getenv()` in `ksft_print_header()` in `tools/testing/selftests/kselftest.h`.
- Under either runner a C test therefore prints its own version line, which
  appears as `# TAP version 13`.
- `ktap_print_header()` in `kselftest/ktap_helpers.sh` and `print_header()` in
  `kselftest/ksft.py`: do not read `KSFT_TAP_LEVEL`; they print the version
  line unconditionally.

## Reporting from plain C

**Plain C test structure**

- Top comment of `tools/testing/selftests/kselftest.h`: calls the file the
  "low-level kselftest framework" and says "When possible, please use
  kselftest_harness.h instead."
- The comment gives no criterion beyond "when possible"; it does not mention
  fixtures, variants or test size.
- `ksft_print_header()`: sets stdout line buffered with `setvbuf()` before
  anything else, so a test that skips the call can duplicate buffered output
  across `fork()`.
- `ksft_print_header()`: prints `TAP version 13` only when the environment
  variable `KSFT_TAP_LEVEL` is unset.
- Whole-program skip for a missing prerequisite: `ksft_exit_skip()` goes
  after `ksft_print_header()` and before `ksft_set_plan()`, as `main()` in
  `tools/testing/selftests/mm/hugetlb-soft-offline.c` does; "Exit functions"
  says what it prints when called later.

**Result functions**

| Call | TAP line | Counter in `ksft_cnt` |
|---|---|---|
| `ksft_test_result_pass()` | `ok N msg` | `ksft_pass` |
| `ksft_test_result_fail()` | `not ok N msg` | `ksft_fail` |
| `ksft_test_result()` | pass line if the condition is true, else fail line | that function's |
| `ksft_test_result_skip()` | `ok N # SKIP msg` | `ksft_xskip` |
| `ksft_test_result_xfail()` | `ok N # XFAIL msg` | `ksft_xfail` |
| `ksft_test_result_xpass()` | `ok N # XPASS msg` | `ksft_xpass` |
| `ksft_test_result_error()` | `not ok N # error msg` | `ksft_error` |
| `ksft_test_result_report()` | line of the function it picks | that function's |
| `ksft_test_result_code()` | `ok N name # DIRECTIVE msg`; with no directive `ok N name #  msg` or `not ok N name #  msg` | by code |

- Directive position: the format-style functions print the directive before
  the message, never after it.
- `ksft_test_result_report()`: a macro `switch` over `KSFT_PASS`,
  `KSFT_FAIL`, `KSFT_XFAIL`, `KSFT_XPASS`, `KSFT_SKIP` that calls the
  matching format-style function; it does not call `ksft_test_result_code()`.
- `ksft_test_result_report()` with any other value: no `default` case, so
  nothing is printed and no counter moves; the result count then falls one
  short of the plan.
- `ksft_test_result_code()` with `KSFT_FAIL` or any unknown value: `not ok`,
  counts `ksft_fail`; it does not call `ksft_exit_fail_msg()`.
- `ksft_test_result_code()`: prints `test_name` before the directive, accepts
  a NULL `msg`, and appends `\n` itself.
- Every other result function prints the format as given, so the format must
  end in `\n`.
- Macros: only `ksft_test_result()` and `ksft_test_result_report()`; neither
  adds a function name to the output.

**Exit functions**

- `ksft_exit_pass()`, `ksft_exit_fail()`, `ksft_exit_xfail()`,
  `ksft_exit_xpass()`: each calls `ksft_print_cnts()` before `exit()`; none
  exits silently.
- `ksft_exit_fail_perror()`: prints totals too, because it calls
  `ksft_exit_fail_msg()`, which prints the bail-out line and then
  `ksft_print_cnts()`.
- `ksft_exit_skip()` exits with `KSFT_SKIP` in both branches:

| State when called | Prints | Counter | Totals |
|---|---|---|---|
| `ksft_plan` is 0 and no result reported | `1..0 # SKIP msg` | none | not printed |
| `ksft_plan` is nonzero or a result was reported | `ok N # SKIP msg` | `ksft_xskip` | printed |

- `ksft_exit_skip()` right after `ksft_set_plan(n)` with `n` above 1: the
  runner still records skip from the exit code, but the test's own output has
  one result line against a plan of `n`.

**ksft_finished pass condition**

- `ksft_finished()`: `ksft_exit(ksft_plan == ksft_cnt.ksft_pass +
  ksft_cnt.ksft_xpass + ksft_cnt.ksft_xfail + ksft_cnt.ksft_xskip)`.
- Success kinds: pass, xpass, xfail and skip; `ksft_xpass` is in the sum.
- Not in the sum: `ksft_fail` and `ksft_error`.
- `ksft_test_num()` is not what `ksft_finished()` compares; it gives the
  test number and the mismatch line in `ksft_print_cnts()`.
- Totals: `ksft_finished()` does not call `ksft_print_cnts()` itself;
  `ksft_exit_pass()` or `ksft_exit_fail()` does.
- A fail or error result within a full plan: the sum falls short, exit is
  `KSFT_FAIL`.
- More results than planned can hide a failure: with a plan of 3, three
  passes plus one fail make the sum equal the plan, so the exit is
  `KSFT_PASS`.
- `ksft_set_plan()` never called: `ksft_plan` is 0, so a run that reported
  only fail or error results exits `KSFT_PASS`; any successful result makes
  it exit `KSFT_FAIL`.
- `# Planned tests != run tests` in `ksft_print_cnts()`: tests `ksft_plan !=
  ksft_test_num()`, a different comparison from the exit condition, so it can
  appear on a `KSFT_PASS` exit and be absent on a `KSFT_FAIL` exit.

**Error results**

- `kselftest.h` on the meaning: the only text is the comment above
  `ksft_test_result_error()`, `/* TODO: how does "error" differ from "fail"
  or "skip"? */`; the header defines no distinction.
- `Documentation/dev-tools/ktap.rst`: lists an "ERROR" directive, meaning the
  execution of a test failed due to a specific error given in the diagnostic
  data, and says the result line should be "not ok".
- Case: `ksft_test_result_error()` prints the directive in lower case,
  `# error`, where `Documentation/dev-tools/ktap.rst` writes "ERROR".
- `ksft_test_num()`: adds `ksft_error` to the other five counters, so an error
  result takes a test number; "ksft_finished pass condition" says what it
  does to the exit status.
- Exit codes: there is no kselftest exit code for error, so
  `ksft_test_result_report()` and `ksft_test_result_code()` cannot produce an
  error result, and no `ksft_exit_*` function exits with one.

**Exiting from main**

- Exit status 3 (`KSFT_XPASS`): no case in `run_one()`, so it is recorded as
  `not ok ... # exit=3`; `ksft_exit_xpass()` is a failure to the runner,
  although `ksft_finished()` counts xpass results as success.
- `Documentation/dev-tools/kselftest.rst` names no exit code and does not
  mention `KSFT_SKIP`.
- `Documentation/dev-tools/kselftest.rst` has two rules that apply: "Don't
  cause the top-level "make run_tests" to fail if your feature is
  unconfigured", and output "must conform to the TAP standard" with the
  `kselftest.h` or `kselftest_harness.h` wrappers used "for pass, fail, exit,
  and skip messages".
- **Potentially unsafe usage**: ending `main()` with `return 0` or an
  unconditional `ksft_exit_pass()` after per-case results were reported.
  - Unsafe: when a `not ok` result can have been reported before that point;
    `run_one()` reads only the exit status and records `ok`.
  - Safe: end with `ksft_finished()` when no more results than planned can
    be reported, as `main()` in
    `tools/testing/selftests/mm/hugetlb-soft-offline.c` does.
  - Safe: test `ksft_get_fail_cnt()` and call `ksft_exit_fail_msg()` when it
    is nonzero, before `ksft_exit_pass()`, in a test that reports no error
    results, as `main()` in `tools/testing/selftests/mm/mkdirty.c` does.
- **Unsafe usage**: exiting with a nonzero status other than `KSFT_SKIP` or
  `KSFT_XFAIL` when a feature or config option is missing; `run_one()`
  records `not ok`, which breaks the "unconfigured" rule in
  `Documentation/dev-tools/kselftest.rst`.
  - Safe: call `ksft_exit_skip()` before `ksft_set_plan()`, as `main()` in
    `tools/testing/selftests/mm/hugetlb-soft-offline.c` does; `run_one()`
    records `ok ... # SKIP` for exit status 4.

## The test harness

**Harness macros**

- `FIXTURE_SETUP()` and one teardown macro: both required once a fixture has a
  `TEST_F()`; the wrapper from `__TEST_F_IMPL()` calls both functions and reads
  a flag that only `FIXTURE_TEARDOWN()` or `FIXTURE_TEARDOWN_PARENT()` defines.
- `TEST_F_SIGNAL()`: the fixture form of `TEST_SIGNAL()`.
- `FIXTURE_TEARDOWN_PARENT()`: the only parent form; setup has none.
- `FIXTURE_DATA()`: names the struct type of `self`, for a helper that takes
  `self` as a parameter; `FIXTURE()` expands to it.
- Signal plus timeout: no macro other than the internal `__TEST_F_IMPL()`
  takes both; `TEST_F_SIGNAL()` fixes the timeout at `TEST_TIMEOUT_DEFAULT`,
  `TEST_F_TIMEOUT()` fixes the signal at -1.
- `SIGABRT` as the expected signal of `TEST_SIGNAL()` or `TEST_F_SIGNAL()`:
  cannot pass; `__wait_for_test()` tests for `SIGABRT` before `t->termsig`.
- Missing from the `:functions:` list in
  `Documentation/dev-tools/kselftest.rst`: `TEST_F_SIGNAL()`,
  `TEST_F_TIMEOUT()`, `FIXTURE_TEARDOWN_PARENT()` and `XFAIL_ADD()`;
  `TEST_SIGNAL()` is in the list.
- `TEST_F_SIGNAL()` and `TEST_F_TIMEOUT()`: have no kernel-doc comment, so
  adding them to the list alone renders nothing.
- `FIXTURE_TEARDOWN_PARENT()`, `XFAIL_ADD()` and `SKIP()`: have a kernel-doc
  comment and are not listed.

**Processes per test**

- `TEST_F()`: three processes; the harness forks a child in `__run_test()`, and
  the wrapper from `__TEST_F_IMPL()` forks a grandchild from that child.
- Grandchild of a `TEST_F()`: runs `FIXTURE_SETUP()`, the body and
  `FIXTURE_TEARDOWN()`.
- Child, before `t->fn()`: `setpgrp()`, then `ksft_reset_state()` in
  `kselftest.h`, which zeroes the `ksft_cnt` counters and `ksft_plan`.
- Crash in a `TEST_F()` body with `FIXTURE_TEARDOWN()`: teardown does not run.
- Crash in a `TEST_F()` body with `FIXTURE_TEARDOWN_PARENT()`: teardown runs in
  the wrapper before it re-raises the signal, if setup had completed.

**ASSERT and EXPECT**

- `__bail()`: does not call `longjmp()`; for an `ASSERT_*` it calls
  `t->teardown_fn`, then `abort()`.
- `FIXTURE_TEARDOWN()` after a failed `ASSERT_*`: runs inside `__bail()`, in
  the process that asserted, before the `abort()`.
- `FIXTURE_TEARDOWN_PARENT()` after a failed `ASSERT_*`: not run by
  `__bail()`; the wrapper runs it after the grandchild has died.
- `ASSERT_*` failing in `FIXTURE_SETUP()`: no teardown of either kind runs;
  `*no_teardown` is still true.
- `TEST()`: `teardown_fn` is NULL, so `__bail()` only aborts.
- `trigger`: set by a failed check, cleared only when the handler loop
  finishes, by `SKIP()`, or by `__run_test()`; a passing check does not clear
  it.
- **Potentially unsafe usage**: a handler block that leaves with `return`,
  `goto` or `break`.
  - Unsafe: when another `ASSERT_*` or `EXPECT_*` runs afterwards in the same
    test; `trigger` is still 1, so that check runs its handler and an
    `ASSERT_*` aborts even though it passed.
  - Unsafe: when the code relies on the `ASSERT_*` to stop the test;
    `__bail()` is skipped, so nothing aborts.
  - Safe: when no check follows before the test ends, as the `goto` handlers in
    `TEST(uevent_filtering)` in
    `tools/testing/selftests/uevent/uevent_filtering.c`; `__EXPECT()` has set
    `KSFT_FAIL` before the handler runs.
  - Safe: leaving through `SKIP()`, which clears `trigger`, as the handler of
    `EXPECT_EQ()` in `TEST(clone3_cap_checkpoint_restore)` in
    `tools/testing/selftests/clone3/clone3_cap_checkpoint_restore.c` does.
- **Potentially unsafe usage**: no `;` after an `ASSERT_*` or `EXPECT_*`;
  `OPTIONAL_HANDLER()` ends in a `for` with no body.
  - Unsafe: when the next statement is part of the test; it becomes the
    handler and runs only when the check failed.
  - Safe: when a block or `TH_LOG()` meant as the handler follows, as after
    `ASSERT_GT()` in `TEST(clone3_cap_checkpoint_restore)` in
    `tools/testing/selftests/clone3/clone3_cap_checkpoint_restore.c`.
- **Unsafe usage**: relying on a failed `EXPECT_*` to fail a `TEST_SIGNAL()` or
  `TEST_F_SIGNAL()` test that then dies by the expected signal;
  `__wait_for_test()` sets `KSFT_PASS`.
  - Safe: `ASSERT_*`; its `SIGABRT` is tested before `t->termsig`.

**Harness timeout**

- `__wait_for_test()`: uses no `alarm()` and no signal handler; it opens a
  pidfd with `__NR_pidfd_open` and waits in `poll()` for `t->timeout` seconds.
- pidfd open failure: the test fails with "unable to open pidfd" and the
  child is neither waited for nor killed.
- `timed_out`: a local of `__wait_for_test()`, not a field of
  `struct __test_metadata`.
- After the `SIGKILL`: `waitpid()` is called once with `WNOHANG`; its status is
  not used for a timed-out test.
- Wrapper child of a `TEST_F()`: in the killed group, so
  `FIXTURE_TEARDOWN_PARENT()` does not run either.
- Binary run directly: only the harness limit applies.
- `kselftest_override_timeout`: wins over the `settings` file.
- `timeout=0` in `settings`: `runner.sh` has no special case; the value is
  passed to `/usr/bin/timeout` unchanged.
- Harness and runner: neither reads the other's limit; a `TEST_F_TIMEOUT()`
  above the runner's value needs a `settings` file, as
  `tools/testing/selftests/rtc/settings` has.

**Timeout override and report**

- `TEST_F_TIMEOUT()`: the only macro that takes a limit, apart from the
  internal `__TEST_F_IMPL()` it expands to; `TEST()`, `TEST_SIGNAL()`,
  `TEST_F()` and `TEST_F_SIGNAL()` are fixed at `TEST_TIMEOUT_DEFAULT`.
- **Unsafe usage**: writing `_metadata->timeout` in a test body to change the
  limit; the harness process reads `t->timeout` in `__wait_for_test()` right
  after the fork, and a `TEST()` body writes a private copy.
  - Safe: `TEST_F_TIMEOUT()`, as in `tools/testing/selftests/rtc/rtctest.c`.
- Report for an expired limit: `KSFT_FAIL`, set in the `timed_out` branch of
  `__wait_for_test()`.

**Expected failures**

- Test that passed: `KSFT_XPASS`, printed `ok ... # XPASS`; `__test_passed()`
  counts it as passing.
- Test that skipped: also `KSFT_XPASS`, with the `SKIP()` reason as the
  diagnostic; `__test_passed()` is true for `KSFT_SKIP`.
- Test that failed in any way, including a timeout, an unexpected signal or a
  failed `ASSERT_*`: `KSFT_XFAIL`, printed `ok ... # XFAIL`.
- Diagnostic: "unknown" when the test stored no reason.
- `XFAIL_ADD()`: needs a variant from `FIXTURE_VARIANT_ADD()`; there is no
  form for `TEST()` or for a fixture without a named variant.
- `XFAIL_ADD()`: must come after the `TEST_F()` and the
  `FIXTURE_VARIANT_ADD()` it names; it refers to their static objects.

**Harness exit status**

- Every test skipped: exits 0; `test_harness_run()` has no special case and
  calls `ksft_exit(ret == 0)`.
- No test selected by the filters: also exits 0.
- `KSFT_XPASS`: on the passing side, with `KSFT_PASS`, `KSFT_XFAIL` and
  `KSFT_SKIP`.
- Exit 4 from `test_harness_run()`: only for `-l` and `-h`;
  `test_harness_argv_check()` returns `KSFT_SKIP` before any test runs.
- Unknown option: `test_harness_argv_check()` returns `KSFT_FAIL`.
- `test_harness_run()` after the tests: does not return; `ksft_exit()` calls
  `exit()`.

**Assertions in forked children**

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

**Low-level calls inside harness tests**

- Check in `__run_test()`: in the child, after `t->fn()` returns, if
  `__test_passed()` is true and `ksft_get_fail_cnt()` or
  `ksft_get_error_cnt()` is nonzero.
- On a hit: prints "Illegal usage of low-level ksft APIs in harness test" and
  sets `KSFT_FAIL`.
- Counters checked: only fail and error, counted from the
  `ksft_reset_state()` call made before `t->fn()`.
- `ksft_test_result_pass()`, `ksft_test_result_skip()`,
  `ksft_test_result_xfail()` and `ksft_test_result_xpass()` in a body: do not
  change the verdict; the test is reported as a plain pass, see
  `tools/testing/selftests/kselftest_harness/harness-selftest.expected`.
- Result line printed from a body: numbered from 1, since the counters were
  reset.
- `ksft_print_msg()` in a body: only prints; the harness calls it in the
  child itself.
- **Unsafe usage**: `ksft_test_result_fail()` or `ksft_test_result_error()` to
  fail a `TEST_F()` body or a `FIXTURE_SETUP()`; they run in the grandchild
  and the check reads the child's counters, so the test passes.
  - Safe: `ASSERT_*` or `EXPECT_*`, which set `_metadata->exit_code`.
- **Potentially unsafe usage**: `ksft_exit_skip()` in a body.
  - Unsafe: in a `TEST_F()` whose `FIXTURE_TEARDOWN()` must run; the process
    exits before it.
  - Safe: where no `FIXTURE_TEARDOWN()` has to run, as
    `test_clone3_supported()` called from
    `TEST(clone3_cap_checkpoint_restore)` in
    `tools/testing/selftests/clone3/clone3_cap_checkpoint_restore.c`; exit
    status 4 is read as `KSFT_SKIP` by `__wait_for_test()`.
  - Safe: `SKIP(return, ...)`, which stores the reason in `t->results` and
    returns through the teardown.
- `ksft_exit_skip()` in a body: prints a second plan line "1..0 # SKIP", and
  the harness reports the reason as "unknown".
- **Potentially unsafe usage**: `ksft_exit_fail_msg()` or `ksft_exit_fail()` in
  a body.
  - Unsafe: in a `TEST_F()` whose `FIXTURE_TEARDOWN()` must run; the process
    exits before it.
  - Safe: where no `FIXTURE_TEARDOWN()` has to run, as
    `TEST_F(guard_regions, uffd)` in
    `tools/testing/selftests/mm/guard-regions.c`, whose fixture uses
    `FIXTURE_TEARDOWN_PARENT()`; exit status 1 is read as `KSFT_FAIL` by
    `__wait_for_test()`, or copied to `exit_code` by the `TEST_F()` wrapper.
- `ksft_exit_fail_msg()` in a body: "Bail out!" and a "# Totals:" line enter
  the stream; `ksft_exit_fail()` adds only the "# Totals:" line.

**Testing the harness**

- `harness-selftest.sh`: applies no filter; it runs `diff -u` on the raw
  output, and the exit status of `diff` is the verdict.
- Captured: stdout only, into `harness-selftest.seen` in the current
  directory; `harness-selftest.c` defines `TH_LOG_STREAM` as `stdout` so the
  logs are included.
- Harness output written straight to `stderr`: not compared.
- `harness-selftest.expected`: holds the `__LINE__` of every `TH_LOG()` and
  failed check, so any edit that moves lines in `harness-selftest.c` must
  update it.
- `harness-selftest.expected`: also holds the plan, the "Starting ... tests"
  line and the "# Totals:" line, so a change to what `kselftest.h` prints, or
  an added test, must update it.
- Not exercised by `harness-selftest.c`: `SKIP()`, `FIXTURE_VARIANT_ADD()`,
  `XFAIL_ADD()`, `TEST_F_SIGNAL()` and a body that forks; a change to their
  output does not fail this test.

## Skipping

**Skipping a whole program**

- Newline: `ksft_exit_skip()` adds none; the message has to end in `\n`
  itself.
- Misuse named by the FIXME in `ksft_exit_skip()`: calling it when "some tests
  have already been run or a plan has been printed".
- Replacement named by the FIXME: `ksft_test_result_skip()` or
  `ksft_exit_fail_msg()`; it does not mention `ksft_finished()`.
- `test_membarrier_query()`, and `test_clone3_supported()` in the plain C
  clone3 programs such as `tools/testing/selftests/clone3/clone3.c`: `main()`
  calls `ksft_set_plan()` first, so their skip takes the `ok <n> # SKIP` form,
  which is the case the FIXME calls misuse.
- Skip before the plan, giving `1..0 # SKIP`: for example `main()` in
  `tools/testing/selftests/mm/soft-dirty.c` and
  `tools/testing/selftests/mm/mseal_test.c`.

**SKIP in the harness**

- Test that carries on after `SKIP()` with no later failure: reported
  `ok <n> <name> # SKIP <reason>`; see `__run_test()` in
  `tools/testing/selftests/kselftest_harness.h`.
- Kerneldoc above `SKIP()` says it forces a "pass"; the macro sets
  `_metadata->exit_code` to `KSFT_SKIP`, which `__test_passed()` counts as
  passed.
- Later failing `EXPECT_EQ()` or `ASSERT_EQ()` after `SKIP()`: the test is
  reported failed, in both `TEST()` and `TEST_F()`.
- `SKIP()` after a failed check: it overwrites `KSFT_FAIL` and clears
  `_metadata->trigger`, so the test is reported skipped.
- `SKIP(return, ...)` inside the block that follows `ASSERT_GE()` relies on
  that overwrite, as in `TEST(close_range_cloexec)` in
  `tools/testing/selftests/core/close_range_test.c`.
- `SKIP()` in `FIXTURE_SETUP()`: teardown does not run, for
  `FIXTURE_TEARDOWN()` and for `FIXTURE_TEARDOWN_PARENT()`.
- `SKIP(return, ...)` in a `TEST_F()` body: teardown does run.
- Placement in setup: before anything teardown would release, as
  `FIXTURE_SETUP(layout2_overlay)` in
  `tools/testing/selftests/landlock/fs_test.c` does.

**Missing prerequisites**

- Documented rule: `Documentation/dev-tools/kselftest.rst`, "Contributing new
  tests": "Don't cause the top-level "make run_tests" to fail if your feature
  is unconfigured", and "Do as much as you can if you're not root".
- `Documentation/dev-tools/kselftest.rst` does not give the value 4; it comes
  from `KSFT_SKIP` in `tools/testing/selftests/kselftest.h` and in
  `tools/testing/selftests/kselftest/ktap_helpers.sh`.
- `run_one()` in `tools/testing/selftests/kselftest/runner.sh`: maps
  `KSFT_PASS`, `KSFT_SKIP` and `KSFT_XFAIL` to an `ok` line; every other code
  becomes `not ok`.
- `ksft_finished()`: counts `ksft_cnt.ksft_xskip` towards the plan, so a C
  test that skipped every case with `ksft_test_result_skip()` exits
  `KSFT_PASS`.
- Shell variable names: `tools/testing/selftests/kselftest/ktap_helpers.sh`
  defines `KSFT_SKIP`; lowercase `ksft_skip` is defined by other libraries,
  for example `tools/testing/selftests/net/lib.sh`, or by the script itself.
- Shell, whole script: `prerequisite()` in
  `tools/testing/selftests/cpufreq/main.sh` calls `ktap_skip_all()` and then
  `exit "${KSFT_SKIP}"` for each missing prerequisite.
- `tools/testing/selftests/clone3/clone3.c` without root: `not_root()` is a
  per-test filter that gives `ksft_test_result_skip()`; it does not call
  `ksft_exit_skip()`.
- Harness, prerequisite checked in setup: `FIXTURE_SETUP(layout2_overlay)` in
  `tools/testing/selftests/landlock/fs_test.c`.

**Absent and broken features**

- Plain C, whole program: `test_clone3_supported()` in
  `tools/testing/selftests/clone3/clone3_selftests.h` skips on `ENOSYS`;
  `tools/testing/selftests/clone3/clone3.c` has no `ENOSYS` test of its own.
- Plain C, one case: `test_pidfd_send_signal_syscall_support()` in
  `tools/testing/selftests/pidfd/pidfd_test.c` gives `ksft_test_result_skip()`
  on `ENOSYS` and `ksft_exit_fail_msg()` on any other error.
- `tools/testing/selftests/pidfd/pidfd_open_test.c`: has no skip.
- Harness: `TEST_F(child, fetch_fd)` in
  `tools/testing/selftests/pidfd/pidfd_getfd_test.c` skips on `ENOSYS` from
  `sys_kcmp()`; any other result reaches `EXPECT_EQ(ret, 0)`.
- Harness, unknown flag: `TEST(close_range_cloexec)` in
  `tools/testing/selftests/core/close_range_test.c` skips on `ENOSYS` or
  `EINVAL` from a probe call; any other probe result carries on to the real
  calls, which `ASSERT_EQ(0, ret)` checks.
- `tools/testing/selftests/seccomp/seccomp_bpf.c`: `SKIP()` gated on `errno`
  inside the block after `ASSERT_EQ()`, for example around
  `unshare(CLONE_NEWPID)`.
- Landlock tests: no `SKIP()` under `tools/testing/selftests/landlock/` is
  gated on `ENOSYS` or `EOPNOTSUPP`.
- Probe without `errno`: `supports_filesystem()` in
  `tools/testing/selftests/landlock/fs_test.c` looks the name up in
  `/proc/filesystems`.
- openat2 tests: they are in `tools/testing/selftests/filesystems/openat2/`;
  `__detect_openat2_supported()` sets `openat2_supported` from `fd >= 0` and
  does not look at `errno`, so it does not separate absent from broken.
- `rseq_available()` in `tools/testing/selftests/rseq/rseq.c`: `ENOSYS` is
  false, `EINVAL` is true, anything else calls `abort()`; its caller in
  `tools/testing/selftests/rseq/syscall_errors_test.c` jumps to `error` and
  does not skip.

## Shell and Python tests

**Shell reporting helpers**

- `ktap_finished()` in `tools/testing/selftests/kselftest/ktap_helpers.sh`:
  exits `$KSFT_PASS` when `KTAP_CNT_PASS` + `KTAP_CNT_SKIP` +
  `KTAP_CNT_XFAIL` equals `KSFT_NUM_TESTS`, otherwise `$KSFT_FAIL`.
- `KTAP_CNT_FAIL`: not in the sum that `ktap_finished()` tests; a failure
  changes the exit status only because it leaves the sum short of the plan.
- `ktap_finished()` calls `ktap_print_totals()` and `exit`; it does not call
  `ktap_exit_fail_msg()`.
- `KSFT_NUM_TESTS` starts at 0, so a script that reports a pass without
  calling `ktap_set_plan()` and ends in `ktap_finished()` exits `$KSFT_FAIL`.
- `ktap_test_xfail()` and `ktap_test_result()`: both exist under those names.
- `ktap_skip_all()`: only prints `1..0 # SKIP ...`; the caller runs
  `exit "$KSFT_SKIP"` itself.
- There is no ktap_exit_pass() in this tree.
- Installed layout: the `install` target of
  `tools/testing/selftests/Makefile` copies `kselftest/ktap_helpers.sh` to
  `$(INSTALL_PATH)/kselftest/`, whatever `TARGETS` holds.
- `TEST_INCLUDES`: for the installed tree a test Makefile does not need to
  list the helper; only `tools/testing/selftests/net/packetdrill/Makefile`
  does.
- Example of the whole sequence ending in `ktap_finished()`:
  `tools/testing/selftests/power_supply/test_power_supply_properties.sh`.
- `tools/testing/selftests/dt/test_unprobed_devices.sh`: shows the `DIR` and
  `source` lines and `ktap_skip_all()`, but does not call `ktap_finished()`;
  it calls `ktap_print_totals()` and exits with its own `retval`.
- `tools/testing/selftests/cpufreq/main.sh` and
  `tools/testing/selftests/mm/ksft_kmemleak_confirm.sh` source the helper;
  no script under the pidfd or watchdog selftests does.

**Networking shell library**

- `tools/testing/selftests/net/lib.sh` installs no `trap`; sourcing it removes
  nothing at exit.
- Namespace removal at exit is set up by each test; in-tree forms include:
  - `trap cleanup_all_ns EXIT`, for example
    `tools/testing/selftests/net/hsr/hsr_ping.sh`
  - `defer cleanup_all_ns` plus `trap defer_scopes_cleanup EXIT`, for example
    `tools/testing/selftests/net/protodown.sh`
  - a `cleanup` function of the test that calls `cleanup_all_ns()`
- `defer` in `tools/testing/selftests/net/lib/sh/defer.sh`: commands run in
  `defer_scope_pop()`, which `in_defer_scope()` and `defer_scopes_cleanup()`
  call; `defer.sh` installs no trap.
- `tests_run()` wraps each test in `in_defer_scope()`, so a `defer` made inside
  a test function runs when that function returns.
- `setup_ns()` also sets `net.ipv4.conf.all.rp_filter` and
  `net.ipv4.conf.default.rp_filter` to 0 in each namespace.
- `setup_ns()` when `ip netns add` fails: removes the namespaces made earlier
  in the same call and returns `$ksft_skip`; it does not exit.
- `setup_ns()` does not check the result of the `lo` up command or of the two
  sysctl writes.
- `ret_set_ksft_status()`: `RET` becomes the higher-ranked of the old and new
  status, so a later fail replaces an earlier xfail or skip.
- `retmsg`: replaced only when the new status strictly outranks `RET`.
- `check_err()` records `$ksft_xfail` in place of `$ksft_fail` when
  `FAIL_TO_XFAIL` is `yes`; `xfail()` sets it, and `xfail_on_slow()` and
  `xfail_on_veth()` set it when their condition holds.
- `log_test()`: merges `RET` into `EXIT_STATUS` with
  `ksft_exit_status_merge()`, returns `$RET`, and does not reset `RET`.
- The two merges rank differently:

  | Merge | Used for | Rank, low to high |
  |---|---|---|
  | `ksft_status_merge()` | checks into `RET` | pass, xfail, skip, fail |
  | `ksft_exit_status_merge()` | `RET` into `EXIT_STATUS` | xfail, pass, skip, fail |

- `EXIT_STATUS` starts at 0 and xfail ranks below pass, so xfail results alone
  never change it; a script that ends with `exit $EXIT_STATUS` exits 0, not 2.
- `EXIT_STATUS` is the name of the global; there is no ksft_exit_status
  variable.

**Networking Python library**

- `ksft_eq()`, `ksft_true()` and the other checks in
  `tools/testing/selftests/net/lib/py/ksft.py`: do not raise; `_fail()` prints
  and sets `KSFT_RESULT` to False, and the case keeps running.
- There is no ksft_false() in this tree.
- A check that fails before the case raises `KsftSkipEx` or `KsftXfailEx`:
  the line is `not ok ... # SKIP` or `not ok ... # XFAIL`, the totals count
  it as skip or xfail, and the exit status is 1.
- A deferred callback that raises after a skip or xfail gives the same
  `not ok` line with the directive.
- `defer()` outside a test case: raises `Exception`, because
  `GLOBAL_DEFER_ARMED` is False; see `defer.__init__()` in
  `tools/testing/selftests/net/lib/py/utils.py`.
- `ksft_run()` arms the queue only around the call of each case, so `defer()`
  in `main()` or in environment setup is not available.
- `tools/testing/selftests/drivers/net/lib/py/` re-exports `defer` and does
  not call it; environment teardown is `__exit__()` of the environment class.
- `ksft_run()` prints the `# Totals:` line; `ksft_exit()` prints nothing.
- `ksft_exit()`: `sys.exit(0 if KSFT_RESULT_ALL else 1)`; the Python library
  defines no named exit constants.
- A run in which every case skipped exits 0, not 4.
- `ksft_exit()` inside the `with` block of the environment: `__exit__()` still
  runs, because `sys.exit()` raises;
  `tools/testing/selftests/drivers/net/hw/nic_timestamp.py` does this.

## Network namespaces

**Device config in new namespaces**

- Source of `conf/all` and `conf/default` in a namespace other than `init_net`:

| `devconf_inherit_init_net` | IPv4, `devinet_init_net()` | IPv6, `addrconf_init_net()` |
|---|---|---|
| 0 (default) | copy of `init_net`'s current values | compiled `ipv6_devconf`, `ipv6_devconf_dflt` |
| 1 | copy of `init_net`'s current values | copy of `init_net`'s current values |
| 2 | compiled `ipv4_devconf`, `ipv4_devconf_dflt` | compiled `ipv6_devconf`, `ipv6_devconf_dflt` |
| 3 | copy of `current->nsproxy->net_ns` | copy of `current->nsproxy->net_ns` |

- Value 0 is not "compiled defaults" for IPv4: `case 0` and `case 1` share one
  branch in `devinet_init_net()`, so host IPv4 tuning reaches every new
  namespace by default.
- Value 3 is valid: the entry in `net_core_table` in
  `net/core/sysctl_net_core.c` has `.extra2 = SYSCTL_THREE`.
- `sysctl_devconf_inherit_init_net`: one global int, not per namespace.
- `net_core_table` is registered for `init_net` only, in `sysctl_core_init()`;
  a test inside its own namespace cannot read or write the file.
- IPv6 `conf/default` `autoconf` and `disable_ipv6`: set from `ipv6_defaults`
  (module parameters in `net/ipv6/af_inet6.c`) after the switch, for every
  value of the sysctl; they are never inherited.
- IPv6 `stable_secret.initialized`: cleared in both copies after the switch,
  for every value.
- IPv4 copy: a `memcpy()` of the whole `struct ipv4_devconf`, so the `state`
  bitmap of the source is inherited along with `data`; see "Pinning per-device
  sysctls" for what that changes.

**Pinning per-device sysctls**

- `setup_ns()` in `tools/testing/selftests/net/lib.sh`: writes
  `net.ipv4.conf.all.rp_filter=0` and `net.ipv4.conf.default.rp_filter=0`, and
  pins nothing else; `forwarding`, `accept_local` and every IPv6 value stay as
  they were when the namespace was created.
- `lo` after `setup_ns()`: keeps the `rp_filter` it copied when the namespace
  was created; `setup_ns()` sets `lo` up first, `inetdev_event()` then calls
  `ipv4_devconf_setall()`, and `devinet_copy_dflt_conf()` skips it.
- `test_global_init()` in
  `tools/testing/selftests/bpf/prog_tests/flow_dissector_classification.c`:
  writes `default`, `all` and `lo` `rp_filter`; that pins `rp_filter` for `lo`
  and for devices created afterwards.
- IPv4 `conf/default/X` write: reaches an existing device only while that
  device's bit for X in `state` is clear (`devinet_copy_dflt_conf()`).
- IPv4 `conf/default/forwarding` write: reaches no existing device;
  `devinet_sysctl_forward()` does not call `devinet_copy_dflt_conf()`.
- `state` bit for X on a new device: copied from `conf/default` by
  `inetdev_init()`; it is already set if `devinet_conf_proc()` set it on a
  `conf/default/X` write in this namespace or in the namespace the values
  were inherited from. A `forwarding` write sets no bit in `conf/default`.
- IPv4 `conf/default` write: a test can rely on it only for devices created
  or moved in afterwards.
- Device moved into the namespace: `__dev_change_net_namespace()` in
  `net/core/dev.c` sends `NETDEV_UNREGISTER` then `NETDEV_REGISTER`;
  `inetdev_event()` destroys the `struct in_device` and builds a new one from
  the destination's `conf/default`, so IPv4 per-device values written before
  the move are lost.
- IPv4 `conf/all/forwarding` or `ip_forward` written with the value it already
  has: `devinet_sysctl_forward()` skips `inet_forward_change()`, so no device
  is rewritten.
- `forwarding_enable()` in `tools/testing/selftests/net/forwarding/lib.sh`:
  not a namespace example; that library creates no namespace, the helper
  writes the namespace the script runs in and relies on
  `forwarding_restore()` to put the saved value back.
- No selftest under `tools/` reads or sets `devconf_inherit_init_net`.
- **Potentially unsafe usage**: in a new namespace, writing only
  `conf/<dev>/rp_filter=0` or `conf/<dev>/accept_local=0` to get 0 in effect
  on that device.
  - Unsafe: when nothing has written `conf/all` for that setting in the
    namespace; `IN_DEV_RPFILTER()` and `IN_DEV_ACCEPT_LOCAL()` in
    `include/linux/inetdevice.h` still see the inherited `conf/all` value.
  - Safe: for `rp_filter`, in a namespace made by `setup_ns()`, which already
    wrote `conf/all/rp_filter=0`; `test_tun()` in
    `tools/testing/selftests/net/netfilter/ipvs.sh` writes only
    `conf.tunl0.rp_filter=0` after `setup_ns`.
  - Safe: the test writes `conf/all` for the setting itself, as
    `test_global_init()` does.

## KVM selftests

**VM creation helpers**

- Hook names: the library has no hook named kvm_arch_vm_create() and no helper
  named vm_create_shape(). `kvm_arch_vm_post_create()` is the last call in
  `__vm_create()`; `kvm_arch_vm_finalize_vcpus()` is the last call in
  `__vm_create_with_vcpus()`; both in
  `tools/testing/selftests/kvm/lib/kvm_util.c`.
- `____vm_create()`, `vm_create_barebones()`, `vm_create_barebones_type()`:
  run neither hook.
- `vm_recreate_with_one_vcpu()`: runs neither hook; it calls
  `kvm_vm_restart()` and `vm_vcpu_recreate()`.
- `nr_runnable_vcpus` of `__vm_create()`: on arm64 it is also the
  redistributor count of the default GICv3, through
  `kvm_arch_vm_post_create()` and `__vgic_v3_setup()`.
- `vm_create(0)`: fails the assertion in `vm_nr_pages_required()`.
- Comment above `____vm_create()` in
  `tools/testing/selftests/kvm/include/kvm_util.h`: says the irqchip is
  "x86 only"; arm64 `kvm_arch_vm_post_create()` creates one too.
- **Potentially unsafe usage**: `vm_create()` or `__vm_create()`, then
  `vm_vcpu_add()` or `aarch64_vcpu_add()`, with no call to
  `kvm_arch_vm_finalize_vcpus()`.
  - Unsafe: on arm64 while the default vGIC is enabled. The first `KVM_RUN`
    returns `-EBUSY` from `vgic_v3_map_resources()`, and
    `kvm_vgic_map_resources()` then calls `kvm_vm_dead()`. The test need not
    use interrupts for this to fail.
  - Safe: call `kvm_arch_vm_finalize_vcpus()` after the last vCPU, as
    `setup_vm()` in `tools/testing/selftests/kvm/arm64/psci_test.c` and
    `create_vm()` in `tools/testing/selftests/kvm/dirty_log_test.c` do.
  - Safe: the test called `test_disable_default_vgic()` before creating the
    VM, as `main()` in `tools/testing/selftests/kvm/arm64/vgic_init.c` does;
    `vm->arch.has_gic` stays false and the hook does nothing.
  - Safe: the VM comes from `____vm_create()`, as in
    `tools/testing/selftests/kvm/arm64/page_fault_test.c`; no default vGIC
    exists.
  - Safe: the test is built only for architectures that use the weak empty
    hook, as `hardware_disable_test` is in
    `tools/testing/selftests/kvm/Makefile.kvm`. Only arm64 overrides
    `kvm_arch_vm_finalize_vcpus()`.
- **Potentially unsafe usage**: on arm64, adding a vCPU after
  `kvm_arch_vm_finalize_vcpus()` has run.
  - Unsafe: when the VM has the default vGIC; the hook initialised it, and
    `kvm_arch_vcpu_precreate()` in `arch/arm64/kvm/arm.c` returns `-EBUSY`
    once the vGIC is initialised.
  - Safe: add every vCPU first, then finalize once, as
    `__vm_create_with_vcpus()` does.
  - Safe: the test called `test_disable_default_vgic()` and has not yet
    initialised a vGIC of its own, as `test_vgic_then_vcpus()` in
    `tools/testing/selftests/kvm/arm64/vgic_init.c` does; the hook did
    nothing, so `vgic_initialized()` is still false.

**Default interrupt controller**

| Architecture | `kvm_arch_has_default_irqchip()` | Library creates at `__vm_create()` |
|---|---|---|
| x86 | true | `vm_create_irqchip()` |
| arm64 | `request_vgic && kvm_supports_vgic_v3()` | GICv3, same condition |
| s390 | true | nothing |
| riscv | `kvm_check_cap(KVM_CAP_IRQCHIP)` | nothing |
| loongarch | false (weak default) | nothing |

- riscv: overrides the weak default in
  `tools/testing/selftests/kvm/lib/riscv/processor.c`; the kernel answers
  `KVM_CAP_IRQCHIP` with `kvm_riscv_aia_available()`.
- riscv, s390, loongarch: the library has no `kvm_arch_vm_post_create()`
  override, so a true return does not mean the library created a device.
- arm64 result: process-wide, not per VM. It reads the static `request_vgic`
  and probes a throwaway VM in `kvm_supports_vgic_v3()`; it does not read
  `vm->arch.has_gic`.
- x86 `vm_create_irqchip()`: if `KVM_CREATE_IRQCHIP` fails with `ENOTTY` it
  enables `KVM_CAP_SPLIT_IRQCHIP` with 24 pins instead, so the VM may have
  no in-kernel IOAPIC or PIC.
- `__vgic_v3_setup()`: its comment says it must run after all vCPUs exist;
  the library calls it from `kvm_arch_vm_post_create()` before any vCPU.
  Only `vgic_v3_setup()` asserts the vCPU count.
- **Unsafe usage**: on arm64, creating a vGIC with `vgic_v3_setup()` or
  `kvm_create_device()` on a VM from `__vm_create()` while the default vGIC
  is enabled; `kvm_vgic_create()` returns `-EEXIST`.
  - Safe: call `test_disable_default_vgic()` before the VM is created, as
    `main()` in `tools/testing/selftests/kvm/arm64/vgic_irq.c` does.
  - Safe: create the VM with `vm_create_barebones()`, as
    `vm_gic_create_barebones()` in
    `tools/testing/selftests/kvm/arm64/vgic_init.c` does.

**Interrupt ioctls after VM creation**

| ioctl on arm64 | No vGIC created | GICv3 created, not initialised |
|---|---|---|
| `KVM_IRQFD` assign | `-EAGAIN` | `-EAGAIN` |
| `KVM_IRQ_LINE`, PPI or SPI type | `-ENXIO` | `-EBUSY` |
| `KVM_SET_GSI_ROUTING`, valid table | 0 | 0 |

- `KVM_IRQFD`: `-EAGAIN` is the first test in `kvm_irqfd_assign()`
  (`virt/kvm/eventfd.c`), taken when `kvm_arch_intc_initialized()` is false;
  arm64 uses the weak `kvm_arch_irqfd_allowed()`, which returns true.
- `KVM_IRQFD` with `KVM_IRQFD_FLAG_DEASSIGN`: not gated; `kvm_irqfd()` sends
  it to `kvm_irqfd_deassign()`.
- `KVM_IRQ_LINE`: both errors are returned by `kvm_vm_ioctl_irq_line()` in
  `arch/arm64/kvm/arm.c`; the `-EBUSY` is the result of its own call to
  `vgic_lazy_init()`.
- `kvm_vgic_inject_irq()`: does not call `vgic_lazy_init()`; on an
  uninitialised vGIC it returns 0 and injects nothing.
- `KVM_IRQ_LINE` with `KVM_ARM_IRQ_TYPE_CPU`: `-ENXIO` when a vGIC exists.
- `KVM_SET_GSI_ROUTING`: no initialisation test; arm64 uses the weak
  `kvm_arch_can_set_irq_routing()`, which returns true.
- Routing table written before initialisation: replaced when `vgic_init()`
  calls `kvm_vgic_setup_default_irq_routing()`.
- VM from `vm_create_barebones()`: has no vGIC, so the "No vGIC created"
  column applies.
- **Potentially unsafe usage**: on arm64, `KVM_IRQFD` assign or
  `KVM_IRQ_LINE` on a VM from `vm_create()` or `__vm_create()` before
  `kvm_arch_vm_finalize_vcpus()` has run.
  - Unsafe: when the VM has the default vGIC; `kvm_arch_vm_post_create()`
    created it and nothing has initialised it yet, so `kvm_irqfd_assign()`
    returns `-EAGAIN` and `vgic_lazy_init()` returns `-EBUSY`.
  - Safe: after `TEST_REQUIRE(kvm_arch_has_default_irqchip())`, create the
    VM with `vm_create_with_one_vcpu()` and an unused vCPU with NULL guest
    code, as `main()` in `tools/testing/selftests/kvm/irqfd_test.c` does;
    `kvm_irqfd_assign()` needs `vgic_initialized()`.
  - Safe: add the vCPUs, call `kvm_arch_vm_finalize_vcpus()`, then issue the
    ioctls; the hook calls `__vgic_v3_init()` when `vm->arch.has_gic` is set.
  - Safe: after `test_disable_default_vgic()`, the test initialises a vGIC of
    its own before the ioctl: with `vgic_v3_setup()`, which calls
    `__vgic_v3_init()`, as `tools/testing/selftests/kvm/arm64/vgic_irq.c`
    does, or with `KVM_DEV_ARM_VGIC_CTRL_INIT` on its own device, as
    `test_vgic_v5_ppis()` in `tools/testing/selftests/kvm/arm64/vgic_v5.c`
    does without ever calling the hook.

## Model gaps

### Other mistakes models make

- Models take a selftest to include `"../kselftest.h"`. Here `lib.mk` adds
  `-I${top_srcdir}/tools/testing/selftests` to `CFLAGS`, and tests include
  `"kselftest.h"` and `"kselftest_harness.h"` from any depth; both spellings
  are in the tree.
- Models know KVM selftests with the types vm_vaddr_t and vm_paddr_t and with
  vm_vaddr_alloc(). None is in this tree: the types are `gva_t` and `gpa_t` in
  `tools/testing/selftests/kvm/include/kvm_util_types.h`, the allocator is
  `vm_alloc()`, and the library uses `u64` and `u32`.
- Models take `tools/testing/selftests/net/forwarding/lib.sh` to install an
  `EXIT` trap when sourced. Here it sets no trap.
