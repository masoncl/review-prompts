| Header | Guard | Stub returns |
|---|---|---|
| `tools/perf/util/bpf-filter.h` | `HAVE_BPF_SKEL` | `-EOPNOTSUPP`; `perf_bpf_filter__lost_count()` 0 |
| `tools/perf/util/bpf_counter.h` | `HAVE_BPF_SKEL` | 0; `bpf_counter__read()` `-EAGAIN` |
| `tools/perf/util/compress.h` | `HAVE_LZMA_SUPPORT` | -1, `false` |
| `tools/perf/util/compress.h` | `HAVE_ZSTD_SUPPORT` | 0 from all four stubs |
| `tools/perf/util/compress.h` | `HAVE_ZLIB_SUPPORT` | no stubs |
| `tools/perf/util/unwind.h` | `HAVE_LIBDW_SUPPORT`, `HAVE_LIBUNWIND_SUPPORT` | `pr_warning_once()`, then 0; `unwind__prepare_access()` 0 with no warning |
| `tools/perf/util/cs-etm.h` | `HAVE_CSTRACE_SUPPORT` | -1 |

- Stub return values: no tree-wide convention; a stub that returns 0 is
  indistinguishable from success, so a caller that must refuse the
  operation cannot rely on the stub.
- `unwind__get_entries()`: always declared and built (`unwind.o` is
  `perf-util-y`); the stubs in `unwind.h` that warn are
  `libdw__get_entries()` and `libunwind__get_entries()`.
- `tools/perf/util/demangle-java.h` and `tools/perf/util/auxtrace.h`: have
  no feature guard; there is no bpf-loader.h.
- `LIBCAPSTONE_DLOPEN`: `Makefile.config` then omits `-lcapstone` and
  `tools/perf/util/capstone.c` loads `libcapstone.so` with `dlopen()`, so
  the binary runs where the library is not installed.
- **Potentially unsafe usage**: calling a function whose prototype sits
  under `#ifdef HAVE_..._SUPPORT` with no `#else` stub.
  - Unsafe: from code that is compiled when the feature is off; only the
    builds without the library fail.
  - Safe: the call is under the same `#ifdef`, as the "gz" entry using
    `gzip_decompress_to_file()` in `tools/perf/util/dso.c` is under
    `HAVE_ZLIB_SUPPORT`, the guard `compress.h` puts on the prototype.
  - Safe: the caller is in a file that `tools/perf/util/Build` builds only
    when the feature is on, as `tools/perf/util/bpf_ftrace.c`, which calls
    `set_max_rlimit()`, is `perf-util-$(CONFIG_PERF_BPF_SKEL)`;
    `Makefile.config` sets `CONFIG_PERF_BPF_SKEL` and `HAVE_BPF_SKEL`
    together.
