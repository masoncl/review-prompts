- `perf_session__new()`: returns `ERR_PTR()` on every failure, never NULL;
  test with `IS_ERR()`; see `__perf_session__new()` in
  `tools/perf/util/session.c`.
- `evsel__new()` and `evsel__new_idx()`: return NULL, unlike
  `evsel__newtp()`; test with `!evsel`.
- Release functions test for NULL only: `perf_session__delete()` and
  `evsel__put()` dereference an `ERR_PTR()` value, so a failed constructor
  result must not reach them.
- Written preference for new code: none in this tree; the comment above
  `evsel__newtp_idx()` only says the pointer carries an encoded error, and
  `tools/perf/Documentation` says nothing on it.
