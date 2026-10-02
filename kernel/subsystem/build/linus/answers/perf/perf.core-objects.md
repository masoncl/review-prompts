- There is no dsos__findnew() here; `dsos__findnew_id()` in
  `tools/perf/util/dsos.c` does that, and `machine__findnew_dso()` wraps it.
- Functions in `tools/perf/util/dsos.c` that return `struct dso *` return a
  reference the caller must `dso__put()`, for example `dsos__find()` and
  `dsos__findnew_module_dso()`.
- `maps__find_symbol()` and `maps__find_symbol_by_name()`: return an
  uncounted `struct symbol *`; the counted map comes back through `mapp`,
  and the caller must `map__put()` it; with `mapp` NULL there is nothing to
  put.
- `maps__find_symbol()`: stores the map in `*mapp` whenever a map covers the
  address, even when it returns NULL for the symbol.
- `maps__find_symbol_by_name()`: writes `*mapp` only when it returns a
  symbol.
- `machine__find_kernel_symbol()` and
  `machine__find_kernel_symbol_by_name()` in `tools/perf/util/machine.h`:
  inline wrappers with the same `mapp` rule.
- `thread__find_map()`: the returned map is the reference stored in
  `al->map`; it is released by `addr_location__exit()`, not by a separate
  `map__put()`.
- `machines__exit()`: exits only `machines->host`; guest machines are
  erased and passed to `machine__delete()` in
  `machines__destroy_kernel_maps()`, which `perf_session__delete()` reaches
  before `machines__exit()`.
