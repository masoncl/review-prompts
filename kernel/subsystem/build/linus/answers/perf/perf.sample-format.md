- `evsel__parse_sample()`: an inline wrapper in `tools/perf/util/evsel.h`; the
  parser to change is `__evsel__parse_sample()` in `tools/perf/util/evsel.c`.
- `aslr_tool__process_sample()` in `tools/perf/util/aslr.c`: another walker of
  the raw sample layout; it steps through the original `sample_type` bit by
  bit, so a new field has to be copied or skipped there, in the same order.
- `ASLR_SUPPORTED_SAMPLE_TYPE` in `tools/perf/util/aslr.h`: the bits the ASLR
  tool keeps; `aslr_tool__strip_evlist()` masks every other bit out of
  `sample_type`.
- `__evsel__sample_size()`: counts only bits in `PERF_SAMPLE_MASK`
  (`tools/perf/util/event.h`); change it only if the new bit joins that mask.
- Fields outside `PERF_SAMPLE_MASK`: `perf_event__check_size()` does not bound
  them.
- **Unsafe usage**: a read of a field outside `PERF_SAMPLE_MASK` in
  `__evsel__parse_sample()` with no `OVERFLOW_CHECK()` or
  `OVERFLOW_CHECK_u64()` before it; the read can go past `header.size`.
  - Safe: `OVERFLOW_CHECK_u64(array)` before the read, as the
    `PERF_SAMPLE_DATA_SRC` block of `__evsel__parse_sample()` does;
    `overflow()` compares against `endp`, the event plus `header.size`.
- `perf_event__attr_swap()`: in `tools/perf/util/session.c`; a new sized field
  needs its own `bswap_field_64()`, `bswap_field_32()` or `bswap_field_16()`
  line.
- `swap_bitfield()`: covers only the 8 bytes after `read_format`.
- Attr test: there is no tools/perf/tests/attr.c and no tools/perf/tests/attr/
  here; `store_event()` is in `tools/perf/util/evsel.c` and writes a fixed
  list of fields with `WRITE_ASS()`.
- Attr test files: `tools/perf/tests/shell/attr.sh`,
  `tools/perf/tests/shell/lib/attr.py`, expected values under
  `tools/perf/tests/shell/attr/`.
- `do_test()` in `tools/perf/tests/sample-parsing.c`: of the functions that
  walk the sample layout it calls only `perf_event__sample_event_size()`,
  `perf_event__synthesize_sample()`, `__evsel__sample_size()` and
  `evsel__parse_sample()`.
- Not covered by that test: `evsel__parse_sample_timestamp()`,
  `perf_evsel__parse_id_sample()`, `perf_event__synthesize_id_sample()`,
  `evsel__id_hdr_size()`, `aslr_tool__process_sample()`.
- Swap in that test: the same unswapped event is parsed again with
  `needs_swap` set, and only when `sample_type` equals
  `PERF_SAMPLE_BRANCH_STACK`; swap handling of a new field is not tested.
- `samples_same()`: compares only the fields it names, so a new field that is
  not added there passes whatever the parser returns.
