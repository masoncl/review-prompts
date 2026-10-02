| Place in `tools/perf/util/` | When the new type is missing |
|---|---|
| `perf_event__min_size[]` in `session.c` | entry is 0: no minimum, the swap op and handler see records as short as the header |
| alignment exemption in `perf_session__process_event()` and `perf_session__peek_event()` | a record whose size is not a multiple of 8 aborts with `-EINVAL` in `perf_session__process_event()`, and makes `perf_session__peek_event()` return -1 |
| `perf_event__swap_ops[]` in `session.c` | NULL: `event_swap()` returns 0 and cross-endian payload is delivered unswapped |
| `switch` in `perf_session__process_user_event()` | `-EINVAL`, abort |
| `perf_tool__init()` in `tool.c` | member keeps whatever the storage held; a call through NULL or a stale pointer on the first record |
| `delegate_tool__init()` and its `CREATE_DELEGATE_OP2()` line in `tool.c` | wrapper member not set; the delegate's handler is never reached |
| `perf_event__names[]` in `event.c` | `perf_event__name()` returns "INVALID" for a type past the array end, "UNKNOWN" for a hole |
| `pyrf_event__type[]` in `python.c` | `pyrf_event__new()` raises `TypeError` |

- `perf_event__swap_ops[]`: sized by its `[PERF_RECORD_HEADER_MAX] = NULL`
  entry, so indexing a new type is in bounds.
- Swap op signature: returns `int`; non-zero makes
  `perf_session__process_event()` skip the record. It runs after
  `perf_event__too_small()`, so it may rely on the minimum size and nothing
  more.
- Counts and strings: the session-level check goes in the new `case` of
  `perf_session__process_user_event()`, where native-endian input is caught;
  the swap op covers only cross-endian input.
- `perf_event__fprintf()` in `event.c`: a type with no case prints its name
  only.
