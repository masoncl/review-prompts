- `struct addr_location`: has no maps field; the counted fields are
  `thread` and `map`, and maps are reached with `thread__maps(al->thread)`.
- `addr_location__exit()`: `map__zput()` and `thread__zput()`, nothing else.
- `addr_location__init()`: sets fields one by one and leaves `latency`
  unset.
- `struct map_symbol`: fields are `thread`, `map` and `sym`; `thread` and
  `map` are counted.
- `map_symbol__copy()`: `thread__get()` and `map__get()`, `sym` copied as a
  plain pointer; released by `map_symbol__exit()`, which puts both.
- `map_symbol__copy()` does not release what `dst` held;
  `addr_location__copy()` puts `dst->thread` and `dst->map` first.
- Reusing one `struct addr_location`: `thread__find_map()` puts the old
  `map` and `thread` before it fills them, so no exit is needed between
  fills; garbage in an uninitialised one is put there.
- `perf_sample__exit()`: calls `evsel__put(sample->evsel)`, frees
  `user_regs` and `intr_regs`, and frees `callchain` only when
  `merged_callchain` is set; it never frees `branch_stack`.
- `perf_sample__init()` with `all` false: clears `evsel`, `user_regs`,
  `intr_regs`, `merged_callchain` and `callchain`.
- `__evsel__parse_sample()`: calls `perf_sample__init()` with `all` true and
  then `evsel__get()` into `data->evsel` before any check, so the sample
  needs `perf_sample__exit()` after a failed parse too.
- `evlist__parse_sample()` with no matching evsel: initialises the sample
  and returns `-EFAULT`, so exit is still safe.
- **Unsafe usage**: `map_symbol__copy()` into a `dst` that already holds
  references.
  - Unsafe: the old `thread` and `map` references are overwritten and leak.
  - Safe: `map_symbol__exit()` on `dst` first, as
    `callchain_cursor_append()` does.
  - Safe: `dst` freshly zeroed or just struct-assigned from `src`, as
    `callchain_node__make_parent_list()` does.
- **Unsafe usage**: parsing into a `struct perf_sample` that still holds a
  previous parse.
  - Unsafe: the re-initialisation drops the `evsel` reference and the
    allocated registers without releasing them.
  - Safe: `perf_sample__exit()` between parses, as the loop in
    `session__flush_deferred_samples()` does.
- **Potentially unsafe usage**: assigning `sample->evsel` without
  `evsel__get()`.
  - Unsafe: when the sample reaches `perf_sample__exit()` with that value,
    which puts a reference nobody took.
  - Safe: save the old value and restore it before returning, as
    `deliver_sample_value()` in `tools/perf/util/session.c` does.
  - Safe: a local sample that never reaches `perf_sample__exit()`, as in
    `evsel__parse_sample_timestamp()`.
- **Potentially unsafe usage**: struct assignment of a
  `struct addr_location`, of a `struct map_symbol`, or of a struct that
  embeds a `struct map_symbol`.
  - Unsafe: when nothing then takes references for the copy and the copy is
    later released with `map_symbol__exit()` or `addr_location__exit()`;
    both copies put the same `thread` and `map`.
  - Safe: assignment followed at once by a get on each counted field, as
    `addr_location__copy()` and `callchain_node__make_parent_list()` do.
  - Safe: a borrowed copy that is never released and is dropped before its
    source, as `seen[]` in `c2c_function__process_cl()` in
    `tools/perf/util/c2c-function.c`, which is only compared and then
    passed to `free()`.
