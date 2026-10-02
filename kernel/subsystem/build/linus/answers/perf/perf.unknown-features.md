- File, bit at or above `HEADER_LAST_FEATURE`: skipped with no message.
  `perf_header__process_sections()` loops only up to `header->last_feat`.
- The `pr_debug()` for an unknown feature in `perf_file_section__process()` is
  not reached through that loop.
- Pipe, `perf_event__process_feature()` in `tools/perf/util/header.c`:

| `feat_id` | Result |
|---|---|
| `HEADER_RESERVED`, negative, or `INT_MAX` | `pr_warning()`, returns -1 |
| at or above `HEADER_LAST_FEATURE`, with payload | `pr_warning()` "unknown feature", returns 0 |
| at or above `HEADER_LAST_FEATURE`, no payload | taken as the end marker, silent, returns 0 |
| known, `process` hook is NULL | no warning, returns 0 |
| known, `process` hook fails, with payload | returns -1 |
| known and at or above `last_feat`, `process` hook fails, no payload | failure ignored, returns 0 |
| known and below `last_feat`, `process` hook fails, no payload | returns -1 |

- A return of -1: makes `__perf_session__process_pipe_events()` stop with
  `-EINVAL`.
- File, known feature whose `process` hook fails:
  `perf_session__read_header()` fails, so the session does not open.
- `last_feat` in `struct perf_header`: on pipe it starts at 0 and grows as
  `perf_event__process_feature()` handles features, capped at
  `HEADER_LAST_FEATURE`.
- End marker: recognised by `header.size ==
  sizeof(struct perf_record_header_feature)` and `feat_id >= last_feat`. A
  writer built from another version sends another `HEADER_LAST_FEATURE`.
- `perf_event__process_feature()` handles the end marker itself. Wrappers call
  it first and test for the marker afterwards, as `process_feature_event()` in
  `tools/perf/builtin-report.c` does.
- `perf_header__has_feat()` on pipe input: false for every feature the input
  carries, before and after the feature events.
  `perf_event__process_feature()` does not call `perf_header__set_feat()`.
- `perf_header__has_feat()` on a file whose header has `data.size == 0`: false
  for every feature. `perf_session__read_header()` zeroes the bitmap and skips
  the sections.
- **Potentially unsafe usage**: choosing a mode or failing on the result of
  `perf_header__has_feat()`.
  - Unsafe: when the input can be pipe format and nothing else tests for it;
    the feature may have arrived and the test still says absent.
  - Safe: combined with `!is_pipe`, as `report__setup_sample_type()` does for
    `HEADER_AUXTRACE`.
  - Safe: testing the value the `process` hook stored in `struct perf_env`, as
    `perf_session__process_compressed_event()` in `tools/perf/util/tool.c`
    does with `comp_mmap_len`; on pipe input the value is there only when
    `feature` is `perf_event__process_feature()` or a wrapper.
