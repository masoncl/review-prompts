- Written rule: none found in `tools/perf` or `tools/build`; what exists
  are comments such as the one on `<linux/stddef.h>` in
  `tools/perf/util/event.h`.

| Feature | Macro | Fallback |
|---|---|---|
| `gettid` | `HAVE_GETTID` | `static inline gettid()` repeated in each file that needs it, for example `tools/perf/builtin-record.c` |
| `setns` | `HAVE_SETNS_SUPPORT`, `CONFIG_SETNS` | `tools/perf/util/setns.c`, built when `CONFIG_SETNS` is unset |
| `sched_getcpu` | `HAVE_SCHED_GETCPU_SUPPORT` | `sched_getcpu()` in `tools/perf/util/util.c` |
| `scandirat` | `HAVE_SCANDIRAT_SUPPORT` | `scandirat()` in `tools/perf/util/util.c` |
| `reallocarray` | `COMPAT_NEED_REALLOCARRAY`, set when the test fails | `tools/include/tools/libc_compat.h`; the file must include it |
| `pthread-attr-setaffinity-np` | `HAVE_PTHREAD_ATTR_SETAFFINITY_NP` | stub returning 0 in `tools/perf/bench/bench.h` |

- No fallback, code compiled out: `pthread-barrier`, `eventfd`,
  `backtrace`, `timerfd`, `file-handle`.
- `strlcpy()`: not feature-tested; `__weak` definition in
  `tools/lib/string.c`.
- get_current_dir_name: no feature test and no fallback file in this tree.
- `glibc`: `feature-glibc` is read only to pick the error message when
  libelf is missing.
- `bionic`: in `FEATURE_TESTS_EXTRA`, tested by `feature_check` in
  `Makefile.config`; sets `LACKS_SIGQUEUE_PROTOTYPE` and
  `LACKS_OPEN_MEMSTREAM_PROTOTYPE`, and drops `-lrt` and `-lpthread` from
  `EXTLIBS`.
