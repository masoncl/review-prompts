- `struct evlist`: reference counted and refcount-checked; `evlist__new()`
  returns it with a count of 1, released with `evlist__put()`.
- `struct evsel`: reference counted through `refcnt`, set to 1 by
  `evsel__new_idx()` and `evsel__newtp_idx()`; released with `evsel__put()`.
- There is no evlist__delete() or evsel__delete() in `tools/perf`;
  `evsel__exit()` and `evlist__exit()` are `static`.
- `evlist__add()`: takes over the caller's evsel reference (it does not
  call `evsel__get()`), and sets `entry->evlist` to an `evlist__get()`
  reference, so every evsel on a list holds a counted back-reference.
- `evlist__put()`: frees the list when the count reaches zero, or when
  every remaining reference is a back-reference from an evsel on the list
  whose own `refcnt` is 1.
- Evsel on a list with `refcnt` above 1: its back-reference counts as a real
  holder, so `evlist__put()` by the last outside holder does not free the
  list.
- `evlist__purge()`, run when the list is freed: unlinks each evsel, drops
  its back-reference, sets `evsel->evlist` to NULL, then calls
  `evsel__put()`; an evsel with another holder survives with a NULL
  `evlist`.
- `evlist__remove()`: unlinks, puts the back-reference and clears
  `evsel->evlist`; it does not call `evsel__put()`, so the list's reference
  passes to the caller.
- `perf_session__delete()`: puts `session->evlist` only when `session->data`
  is set and open for reading (the list made by `evlist__new()` in
  `tools/perf/util/header.c`); a tool that assigned its own list to
  `session->evlist` still owns it.
- **Unsafe usage**: dropping the last reference to an evsel that is still
  linked on an evlist, for example `evsel__put()` after `evlist__add()`
  when no `evsel__get()` was taken.
  - Unsafe: `evsel__exit()` asserts `list_empty(&evsel->core.node)` and
    `evsel->evlist == NULL`; the list still links the freed evsel.
  - Safe: keep an own reference by passing `evsel__get(evsel)` to
    `evlist__add()`, as `pyrf_evlist__add()` in `tools/perf/util/python.c`
    does.
  - Safe: unlink and clear `evsel->evlist` before the put, as
    `evlist__purge()` does.
