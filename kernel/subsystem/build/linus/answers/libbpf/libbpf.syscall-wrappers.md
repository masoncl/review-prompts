- `bpf_map_create()` and `bpf_prog_load()` end in `libbpf_err_errno(fd)`;
  neither has a `close()` path nor captures `-errno`. `bpf_link_create()` is
  the wrapper that captures `err = -errno` and returns `libbpf_err(err)`.
- `sys_bpf_ext()` and `sys_bpf_ext_fd()` in `tools/lib/bpf/bpf.c`: a second raw
  entry to the system call, with the same raw `-1` and `errno` result; they
  pass a `struct bpf_common_attr` and its size as a fourth and fifth argument,
  so not every wrapper issues the three-argument call through `sys_bpf()`.
  `bpf_map_create()` uses `sys_bpf_ext_fd()` when `log_opts` is set and
  `feat_supported(NULL, FEAT_BPF_SYSCALL_COMMON_ATTRS)` is true; otherwise it
  uses `sys_bpf_fd()`.
- `bpf_prog_load()` writes `errno = E2BIG` by hand when
  `alloc_zero_tailing_info()` fails, so the final `libbpf_err_errno(fd)`
  reports `-E2BIG`.
- `sys_bpf()`, `sys_bpf_fd()` and `sys_bpf_prog_load()` return `-1`, not
  `-errno`. `sys_bpf_prog_load()` is not static and is called from
  `tools/lib/bpf/features.c`; a caller that wants the code must read `errno`.
- `sys_bpf_prog_load()`: retries while `fd < 0 && errno == EAGAIN`, bounded by
  its `attempts` argument; `bpf_prog_load()` passes `PROG_LOAD_ATTEMPTS` when
  the option is 0.
- `libbpf_err_errno()` on an already converted value: `bpf_prog_query()`
  applies it to the result of `bpf_prog_query_opts()`; the result is the same
  because only plain stores run in between.
