- `perf_session__read_header()` in `tools/perf/util/header.c`: calls
  `perf_header__read_pipe()` first for every input, whatever
  `perf_data__is_pipe()` says.
- `perf_header__read_pipe()`: succeeds only when the magic passes
  `check_magic_endian()` and `size` equals
  `sizeof(struct perf_pipe_file_header)`.
- On success, or when `perf_data__is_pipe()` was already true,
  `perf_session__read_header()` sets `data->is_pipe = true` and returns the
  result of the pipe read.
- A regular file on disk in pipe format: opened by path as a normal file, then
  switched to pipe mode by that assignment.
- `perf_data__is_pipe()` on input: final only after `perf_session__new()`
  returns. Before that only `check_pipe()` in `tools/perf/util/data.c` has set
  it.
- `check_pipe()`: path `-` is a pipe; the `S_ISFIFO()` test on stdin or stdout
  runs only when `data->path` is NULL.
- Input that `check_pipe()` marked as a pipe and whose pipe header fails:
  `perf_session__read_header()` returns the error; `perf_file_header__read()`
  is not tried.
- `session->evlist`: allocated by `perf_session__read_header()` itself, before
  either header is read.
- Pipe path: leaves `data_offset`, `data_size`, `feat_offset` and
  `adds_features` of `struct perf_header` at zero, and sets `last_feat` to 0.
- File path: `perf_file_header__read()` sets `last_feat` to
  `HEADER_LAST_FEATURE`.
