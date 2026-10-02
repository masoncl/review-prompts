Rows only where this tree differs from the usual map; file names without a
directory are under `tools/lib/bpf/`, other paths start at the tree root.

| Job | File | Easy to miss |
|---|---|---|
| BTF handling, beyond `btf.c` and `btf_dump.c` | `btf_iter.c`, `btf_relocate.c` | Both are also built into the kernel under `CONFIG_BPF_SYSCALL`: `kernel/bpf/btf_iter.c` and `kernel/bpf/btf_relocate.c` `#include` them, as `kernel/bpf/relo_core.c` does `relo_core.c`. Each has a `#ifdef __KERNEL__` block, so a change must build both ways. |
| Probing the running kernel, internal | `features.c` | Holds `feature_probes[]`, the global `feature_cache` and `feat_supported()`. `kernel_supports()` is the per-object wrapper and is defined in `libbpf.c`. |
| `feature_probes[]` entries that are not defined in `features.c` | `bpf.c`, `libbpf.c` | `probe_memcg_account()` is in `bpf.c`; `probe_kern_syscall_wrapper()` is in `libbpf.c`. Both are entries of `feature_probes[]`. |
| Perf buffer | `libbpf.c` | `perf_buffer__new()` is not in `ringbuf.c`; `ringbuf.c` holds `ring_buffer__new()` and `user_ring_buffer__new()`. |
| Public headers | `SRC_HDRS` and `GEN_HDRS` in `Makefile` | That is the installed set. It includes `skel_internal.h` despite the name. `bpf_helper_defs.h` is not a file in the tree; `Makefile` generates it with `scripts/bpf_doc.py`. |
| Error strings | `libbpf_utils.c` | There is no str_error.c, str_error.h or libbpf_errno.c here. `libbpf_strerror()` and `libbpf_errstr()` are in `libbpf_utils.c`; `errstr()` is a macro in `libbpf_internal.h`. |
