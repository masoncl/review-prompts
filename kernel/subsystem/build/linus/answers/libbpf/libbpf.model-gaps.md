- Models take an integer-returning public function never to return a bare
  `-1`. `bpf_object__btf_fd()` without BTF and `bpf_object__token_fd()`
  without a token return `-1` and do not write `errno`.
- Models take libbpf to accept any modern C. `tools/lib/bpf/Makefile` adds
  `-std=gnu89` and `-Werror`, and `EXTRA_WARNINGS` in
  `tools/scripts/Makefile.include` adds `-Wdeclaration-after-statement`, so a
  declaration after a statement breaks the build.
- Models take kernel typedefs and libc `reallocarray()` to be usable.
  `tools/lib/bpf/libbpf_internal.h` poisons `u8`, `u16`, `u32`, `u64`, `s8`,
  `s16`, `s32`, `s64` and `reallocarray`; use `__u32` style types and
  `libbpf_reallocarray()`.
- Models take a BPF token to exist only when the caller asks for one.
  `bpf_object_prepare_token()` is the first step of `bpf_object_prepare()` for
  every object and tries `BPF_FS_DEFAULT_PATH` when no path is set;
  `bpf_object_open()` takes the path from `bpf_token_path` or else from the
  `LIBBPF_BPF_TOKEN_PATH` environment variable; only an empty path skips the
  attempt.
- Models take the object to own only map and program fds.
  `bpf_object__close()` also closes `obj->token_fd` and the `fd` of each
  `obj->jumptable_maps` entry.
- Models take the internal maps to be `.data`, `.rodata`, `.bss` and
  `.kconfig`. A `LIBBPF_MAP_PERCPU` map is internal too; without
  `FEAT_PERCPU_DATA` `bpf_object__create_maps()` clears its `autocreate`
  instead of failing.
- Models take options structures to be the only size-versioned ABI.
  `struct bpf_object_skeleton` carries `map_skel_sz` and `prog_skel_sz`;
  libbpf steps through skeleton arrays by those sizes and must test them before
  reading a newer field, as `bpf_object__attach_skeleton()` does for `link` in
  `struct bpf_map_skeleton`.
- Models take the `EAGAIN` retry count of `sys_bpf_prog_load()` to be fixed.
  `attempts` in `struct bpf_prog_load_opts` overrides `PROG_LOAD_ATTEMPTS`;
  with a negative value `bpf_prog_load()` fails with `-EINVAL`.
- Models take the doc comments in `tools/lib/bpf/btf.h` as the contract. Those
  above `btf__new()` and the three functions after it name
  `libbpf_set_strict_mode()` as what selects the return form; it is a no-op in
  `tools/lib/bpf/libbpf.c`.
- Models format an error code for a message with libbpf_strerror_r(). There is
  no libbpf_strerror_r() here; `errstr()` does the job.
