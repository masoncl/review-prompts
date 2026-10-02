- There is no buildid_mmap2 field here; `symbol_conf.no_buildid_mmap2` in
  `tools/perf/util/symbol_conf.h` does that job, with the opposite sense.
- `__perf_event__synthesize_kernel_mmap()` and
  `perf_event__synthesize_modules()`: emit `PERF_RECORD_MMAP2` unless
  `symbol_conf.no_buildid_mmap2` is set.
- `symbol_conf.no_buildid_mmap2`: set only by `cmd_record()`, when
  `rec->buildid_mmap` is false; `buildid_mmap` defaults to `true` and is
  cleared when `perf_can_record_build_id()` fails.
- `perf_event__synthesize_extra_kmaps()` in
  `tools/perf/arch/x86/util/event.c`: always emits `PERF_RECORD_MMAP`, so a
  file can hold both types.
- Only `mmap2` handled: loses the x86_64 extra kernel maps, and the kernel and
  module maps of files recorded with `no_buildid_mmap2`, as well as the maps
  the kernel reports for an event opened without `attr.mmap2`.
- Only `mmap` handled: loses the kernel and module maps too in a default
  recording.
- `PERF_RECORD_MISC_PROC_MAP_PARSE_TIMEOUT`: counted in `nr_proc_map_timeout`
  for `PERF_RECORD_MMAP2` only.
- `machine__process_mmap_event()` and `machine__process_mmap2_event()`:
  return 0 when the map cannot be built, with a message under dump only.
