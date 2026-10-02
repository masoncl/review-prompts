- Reader side, input in pipe format (a real pipe or a regular file):

| Place | On pipe input |
|---|---|
| `perf_session__open()` | returns before `evlist__valid_sample_type()`, `evlist__valid_sample_id_all()`, `evlist__valid_read_format()` |
| `__perf_session__new()` | skips `perf_session__set_id_hdr_size()`, `perf_session__set_comm_exec()` and the `evlist__sample_id_all()` fallback to unordered processing |
| `perf_session__process_events()` | tests pipe before directory; directory data is not read |
| `perf_session__peek_event()` | returns -1 from the branch taken when `session->one_mmap` is false or `needs_swap` is set |
| `auxtrace_queue_data()` | returns 0 and queues nothing |
| `auxtrace_queues__add_buffer()` | copies the data with `auxtrace_copy_data()` |
| `perf_header__fprintf_info()` | skips the "missing features" line |
| `report__setup_sample_type()` | skips the callchain, branch, `PERF_SAMPLE_DATA_SRC` and `HEADER_AUXTRACE` checks |
| `perf c2c report` in `tools/perf/builtin-c2c.c` | refuses, with only a `pr_debug()` |
| `perf inject --convert-callchain` | refuses pipe input and pipe output |

- `perf report --header` and `--header-only`: not refused. Features print as
  they arrive, because `cmd_report()` sets `show_feat_hdr`.
- `perf report --header-only` on pipe: calls `perf_session__process_events()`
  and stops when `process_feature_event()` sees the end marker.
- `perf inject` in-place update: refused only by name, when the input name is
  `-`.
- `tools/perf/builtin-inject.c`: has no pipe test tied to `--jit`.
- `perf record --switch-output` on pipe output: not refused;
  `switch_output_setup()` has no pipe test. Only `rec->timestamp_filename` is
  cleared, with a warning.
- Feature section table: always at `data.offset + data.size`. The reader
  computes that as `feat_offset`; the file header does not store it.
- Attrs before data is not guaranteed. `perf_session__do_write_header()` with
  `write_attrs_after_data` writes header, data, features, then ids and attrs.
- `write_attrs_after_data`: true in `perf inject` when input is pipe format
  and output is a file.
- `perf_file_header__read()`: accepts attrs before or after data; it rejects
  them only when they overlap.
