- `kernel_supports()`: defined in `tools/lib/bpf/libbpf.c`; it dereferences
  `obj` first, so it cannot take NULL.
- Code with no `struct bpf_object`: calls `feat_supported(NULL, ...)`, which
  uses the global cache, as `bpf_prog_load()` and `bpf_map_create()` in
  `tools/lib/bpf/bpf.c` do.
- Per-object cache: exists only when `bpf_object_prepare_token()` obtained a
  token, or a test installed one with `bpf_object_set_feat_cache()`.
- `obj->feat_cache` timing: set in the first step of `bpf_object_prepare()`;
  a `kernel_supports()` call before that probes without the token.
- `obj->gen_loader` set: `kernel_supports()` returns true for every feature
  and runs no probe, so the new path is always taken for a light skeleton.
- Probe return value: positive is supported, zero is missing, negative logs a
  warning and is cached as `FEAT_MISSING`.
- `feat_supported()`: takes no lock and uses `READ_ONCE()` and `WRITE_ONCE()`
  only; two threads can run the same probe at once.
- `enum kern_feature_id` value with no `feature_probes[]` entry:
  `feat_supported()` calls the NULL `probe` pointer without a test.
- Probe signature: takes `token_fd`; a probe that creates a map, a program or
  BTF passes it on and sets `BPF_F_TOKEN_FD` when it is non-zero, as
  `probe_kern_global_data()` does.
- **Unsafe usage**: a probe that reaches its own feature test through a
  `tools/lib/bpf/bpf.c` wrapper; the cache entry is still `FEAT_UNKNOWN` while
  the probe runs, so `feat_supported()` recurses without end.
  - Safe: issue the raw syscall, as `probe_kern_prog_name()` does with
    `sys_bpf_prog_load()` because `bpf_prog_load()` tests `FEAT_PROG_NAME`.
  - Safe: `probe_memcg_account()` uses `sys_bpf_fd()` because
    `bump_rlimit_memlock()` tests `FEAT_MEMCG_ACCOUNT`.
  - Safe: call a wrapper that tests a different feature, as
    `probe_kern_arg_ctx_tag()` does by passing a program name.
- `FEAT_ARRAY_MMAP`: tested in `bpf_object__sanitize_maps()`, which clears
  `BPF_F_MMAPABLE`; `bpf_object__init_internal_map()` does not test it.
- `bpf_object__create_map()`: gates only the map name on `FEAT_PROG_NAME`;
  `map_extra` is set unconditionally.
- Not every fallback uses a probe; some paths try and react to the failure:
  - `bpf_object__create_map()` retries `bpf_map_create()` without BTF ids
    after a failure.
  - `bpf_link_create()` falls back to `bpf_raw_tracepoint_open()` on `-EINVAL`
    only when `OPTS_ZEROED(opts, sz)` holds, no target is set, and the attach
    type is one of the five in its last `switch`, for example
    `BPF_TRACE_FENTRY`.
  - `bpf_program__attach_kprobe_opts()` picks the legacy path from
    `determine_kprobe_perf_type()`, which is not a `feature_probes[]` entry.
- Feature the caller asked for explicitly:
  `bpf_program__attach_perf_event_opts()` returns `-EOPNOTSUPP` when
  `bpf_cookie` is set and `FEAT_PERF_LINK` is missing, instead of dropping the
  cookie.
- Testing a fallback: `bpf_object_set_feat_cache()` installs a cache with a
  feature preset to `FEAT_MISSING`; see
  `tools/testing/selftests/bpf/prog_tests/btf_sanitize.c`.
