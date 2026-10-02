- `REFCNT_CHECKING`: defined by `tools/lib/perf/include/internal/rc_check.h`
  itself when `__SANITIZE_ADDRESS__`, `LEAK_SANITIZER` or `ADDRESS_SANITIZER`
  is defined, or `__has_feature(address_sanitizer)` or
  `__has_feature(leak_sanitizer)` is true; a `-fsanitize=address` build is
  a checked build with no further flag.
- Forcing it without a sanitizer: pass `-DREFCNT_CHECKING=1` in
  `EXTRA_CFLAGS`, as `make_refcnt_check` in `tools/perf/tests/make` does;
  no makefile variable of that name is handled anywhere.
- Finding out whether a struct is checked: search `tools/` for
  `DECLARE_RC_STRUCT(name)`, not only the struct's header; `struct maps` is
  declared in `tools/perf/util/maps.c` and `struct comm_str` in
  `tools/perf/util/comm.c`.
- `struct evlist`: checked, declared in `tools/perf/util/evlist.h`.
- `struct evsel`: counted (`refcount_t refcnt`) but a plain struct, so not
  checked; a missed or double `evsel__put()` gets no wrapper report.
