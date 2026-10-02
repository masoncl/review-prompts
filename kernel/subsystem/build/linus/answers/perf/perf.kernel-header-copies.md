- `tools/perf/check-headers.sh`: not run by any perf build;
  `tools/perf/Makefile.perf` never names it.
- Only caller: the `check-headers` target in `tools/perf/Makefile`, run as
  `make -C tools/perf check-headers`.
- Consequence: a perf build prints no warning when a copy has drifted from
  the original.
- `tools/include/uapi/README`: calls the script "part of the tools/ build
  process"; that does not match `Makefile.perf`.
- Exit status: 0 after printing the differences, so the `check-headers`
  target does not fail either.
- Working directory: the script tests `../../include`, so it must start in
  `tools/perf`.
- README on commits: says not to touch the copies when changing the
  originals, and that the update is done later, after `check-headers.sh`
  reports the change; it says nothing about how the later sync is split
  into commits.
- Scope: also compares the copies under `tools/perf/trace/beauty`
  (`BEAUTY_FILES`), and tolerates known differences through `diff -I`
  patterns and `tools/perf/check-header_ignore_hunks`.
