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
