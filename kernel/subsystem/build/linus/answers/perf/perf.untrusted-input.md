- `perf_event__too_small()` in `tools/perf/util/session.c`: compares
  `header.size` with `perf_event__min_size[]`, indexed by type; an entry of 0
  means no minimum.
- `perf_event__min_size[]` values: can be below the size of the current
  struct, for example `offsetof(struct perf_record_time_conv, time_cycles)`,
  so a field added later still needs a size test, as `event_contains()` does
  for `time_cycles` in `perf_event__time_conv_swap()` and for
  `cap_user_time_short` in `perf_event__fprintf_time_conv()`.
- `PERF_RECORD_SAMPLE`, `PERF_RECORD_FINISHED_ROUND`,
  `PERF_RECORD_FINISHED_INIT` and `PERF_RECORD_COMPRESSED`: have no entry.
- Swap ops: return `int`; they bound or clamp embedded counts and locate
  strings with `strnlen()`. They run only for cross-endian input.

| Check | Where | On failure |
|---|---|---|
| `header.size` below the header size | `reader__read_event()` | abort |
| record too large to fit a remapped window | `prefetch_event()`, called from `fetch_mmaped_event()` | abort |
| `header.size` not a multiple of 8, except `PERF_RECORD_HEADER_TRACING_DATA`, `PERF_RECORD_COMPRESSED`, `PERF_RECORD_HEADER_FEATURE` | `perf_session__process_event()` | abort, `-EINVAL` |
| type at or above `PERF_RECORD_HEADER_MAX` | same | skip |
| `perf_event__too_small()` | same | skip |
| swap op returns non-zero | same | skip |
| no evsel for the record, or `evsel__parse_sample()` fails | `perf_session__deliver_event()` | abort |
| `sample.cpu` out of range, other than `(u32)-1` | same | set to 0, delivered |
| string has no NUL: `PERF_RECORD_MMAP`, `PERF_RECORD_MMAP2`, `PERF_RECORD_COMM`, `PERF_RECORD_CGROUP`, `PERF_RECORD_KSYMBOL` | `machines__deliver_event()` | skip |
| `nr_namespaces` or text poke lengths exceed the record | same | skip |
| `PERF_RECORD_THREAD_MAP` `nr` exceeds the record | `perf_session__process_user_event()` | abort, `-EINVAL` |
| counts of `PERF_RECORD_CPU_MAP`, `PERF_RECORD_STAT_CONFIG`, `PERF_RECORD_BPF_METADATA`; strings of `PERF_RECORD_HEADER_BUILD_ID` and `PERF_RECORD_BPF_METADATA` | same | skip |

- Skip means the function returns 0 without calling the callback; the reader
  advances by `header.size`.
- `PERF_RECORD_HEADER_ATTR`, `PERF_RECORD_EVENT_UPDATE`,
  `PERF_RECORD_ID_INDEX`: the bounds checks are in
  `perf_event__process_attr()`, `perf_event__process_event_update()` and
  `perf_event__process_id_index()`. A command whose handler does not call
  them gets none of them.
- Native-endian file input: `reader__mmap()` maps it `PROT_READ` unless
  `in_place_update` is set, so a handler cannot clamp or terminate a field in
  the record; the session skips where the swap op would clamp.
- `perf_session__peek_event()`: makes the alignment, range, size and swap
  checks itself; only `perf_session__peek_events()` skips on failure.
- **Potentially unsafe usage**: looping on a count or calling `strlen()` on a
  string taken from the record.
  - Unsafe: for a type with no check in the table above, when the handler
    does not compare against `header.size` first.
  - Safe: for the types the table lists, in a handler reached through
    `machines__deliver_event()` or `perf_session__process_user_event()`, as
    `process_stat_config_event()` in `tools/perf/builtin-stat.c` is for
    `nr`.
  - Safe: after the handler's own test, as `perf_event__process_id_index()`
    does for `nr`.
