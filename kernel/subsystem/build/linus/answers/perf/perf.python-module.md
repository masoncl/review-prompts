- There is no python-ext-sources file; `tools/perf/util/setup.py` lists
  only `util/python.c` as a source.
- Module contents: `LIBS_PY` in `tools/perf/Makefile.perf`, passed in
  `LDFLAGS`, links `PERFLIBS_PY` inside `-Wl,--whole-archive`, followed by
  `$(EXTLIBS)`.
- `PERFLIBS_PY`: `PERFLIBS` without `$(LIBPERF_BENCH)` and
  `$(LIBPERF_TEST)`; `libperf-util.a`, `libperf-ui.a` and
  `libpmu-events.a` are in it.
- `--whole-archive`: every object of those archives is in the module, so
  an unresolved symbol in any of them breaks `import perf`, even if
  `python.c` never reaches it.
- New file under `tools/perf/util`: any `perf-util-` entry in a `Build`
  file puts it in the module; it must not reference symbols defined only
  under `perf-y`, `perf-bench-y` or `perf-test-y` (`tools/perf/Build`).
- `tools/perf/util/python.c`: defines no stand-ins for perf internals; its
  only non-static function is `PyInit_perf()`.
- New optional library: add it to `EXTLIBS` in
  `tools/perf/Makefile.config`; `LIBS` for the perf binary and `LIBS_PY`
  both take `$(EXTLIBS)`.
- `CFLAGS`: `python.c` is compiled with the perf `CFLAGS`, so it sees the
  same `HAVE_` macros and header stubs.
- Test: `tools/perf/tests/shell/python-use.sh`, which only runs
  `import perf`; there is no tests/python-use.c.
- `make_python_perf_so` in `tools/perf/tests/make`: builds the module
  target and checks with `test -f` that the file exists; it does not
  import it.
- Module not built: when `import setuptools` fails, `Makefile.config`
  prints a warning and leaves the module out of `LANG_BINDINGS`.
