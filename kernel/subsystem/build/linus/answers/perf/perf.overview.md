- `DECLARE_RC_STRUCT()`: search for it to list the types that are checked
  under `REFCNT_CHECKING`. The surprising member is `struct evlist`: reach
  its libperf part with `evlist__core()`, not `evlist->core`.
- `struct maps`: defined only in `tools/perf/util/maps.c`, so every other
  file goes through accessors. Its `maps_by_address` array is sorted only
  while `maps_by_address_sorted` is true.
- `struct threads`: the per-machine thread table is an array of
  `struct threads_table_entry`, each a hashmap keyed by tid with its own
  lock; see `tools/perf/util/threads.h`.
- `struct perf_sample`: carries its `struct evsel` in `sample->evsel`, as a
  counted reference taken in `__evsel__parse_sample()`. The `sample`
  callbacks of `struct perf_tool` take no `struct evsel *` argument.
- `struct addr_location` and `struct map_symbol`: hold `thread`, `map` and
  `sym`. Neither has a `struct maps` or `struct dso` member; reach those
  with `thread__maps()` and `map__dso()`.
- `addr_location__exit()` and `map_symbol__exit()`: put only `thread` and
  `map`. `struct symbol` has no reference count; the `struct dso` behind
  the map owns it.
- Per-evsel cpu and thread maps: `evlist__open()` opens each evsel on its
  own `evsel->core.cpus` and `evsel->core.threads`, not on the evlist's maps.
  `__perf_evlist__propagate_maps()` in `tools/lib/perf/evlist.c` sets the
  evsel's `cpus`, mostly from the evlist's `user_requested_cpus` and the
  evsel's `pmu_cpus`.
- **Potentially unsafe usage**: calling `evsel__hists()` on an evsel.
  - Unsafe: in a command that has not called `hists__init()`. The evsel is
    then allocated as a bare `struct evsel`, and `evsel__hists()` returns
    an address past the end of that allocation.
  - Safe: after `hists__init()` ran before any evsel was created, as in
    `tools/perf/builtin-report.c`. `hists__init()` sets the allocation size
    to `sizeof(struct hists_evsel)` through `evsel__object_config()`.
  - Safe: in shared code, a call made only when `symbol_conf.skip_empty` is
    set, as in `evsel__group_desc()`. Only `cmd_report()` and
    `cmd_annotate()` set it, and both call `hists__init()` first.
