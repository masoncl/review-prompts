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
