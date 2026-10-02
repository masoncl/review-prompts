- Models take a default perf.data to carry `HEADER_BUILD_ID`. `struct record`
  starts with `buildid_mmap` true; `cmd_record()` sets `no_buildid` while it
  is still true, so `record__init_features()` clears the feature.
- Models take `sample->cpu` to arrive as recorded.
  `perf_session__deliver_event()` sets it to 0 when it is at or above a
  bound taken from the env's `nr_cpus_avail`, at most `MAX_NR_CPUS`, except
  for the `(u32)-1` sentinel.
- Models do not know the newest header features. `HEADER_CPU_DOMAIN_INFO` and
  `HEADER_CLN_SIZE` are in `tools/perf/util/header.h`, before
  `HEADER_LAST_FEATURE`.
- Models take libunwind to be the unwinder. `unwind__prepare_access()` is an
  empty stub without `HAVE_LIBUNWIND_SUPPORT`; `unwind__get_entries()` in
  `tools/perf/util/unwind.c` tries libdw first when both are built in and
  `symbol_conf.unwind_style` is unset.
- Models list the record types and tool callbacks of an older tree. This tree
  has `PERF_RECORD_BPF_METADATA`, `PERF_RECORD_SCHEDSTAT_CPU`,
  `PERF_RECORD_SCHEDSTAT_DOMAIN` and `PERF_RECORD_CALLCHAIN_DEFERRED`, each
  with a member in `struct perf_tool`, and `PERF_RECORD_COMPRESSED2`, which
  goes to `tool->compressed`.
- Models take `compressed` in `struct perf_tool` to have the signature of the
  other session callbacks. It is an `event_op4`, which also takes a file
  offset and a path (`tools/perf/util/tool.h`).
- Models take libunwind, libperl, GTK2 and libbfd to be built in when
  detected. Each is opt-in in `tools/perf/Makefile.config`: `LIBUNWIND=1`,
  `LIBPERL`, `GTK2`, `BUILD_NONDISTRO`.
- Models list a libbabeltrace feature test. There is none in
  `tools/build/Makefile.feature`; the CTF test is `babeltrace2-ctf-writer`,
  in `FEATURE_TESTS_EXTRA`.
