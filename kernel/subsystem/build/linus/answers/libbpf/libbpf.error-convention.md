- Failure value of an `int` function is not always negative: `btf__align_of()`
  in `tools/lib/bpf/btf.c` returns `0` on failure, with `errno` set.
- `bpf_map__fd()` in `tools/lib/bpf/libbpf.c`: returns `-1` and does not write
  `errno` when the map is not created yet; for a `NULL` map it returns
  `libbpf_err(-EINVAL)`.
- The helpers are not the only accepted form. Public functions also use:
  - the comma form, `return errno = EINVAL, NULL;`, as in `btf__type_by_id()`;
  - returning `-errno` directly, right after a failing libc call or public
    libbpf call that already set `errno`, as in `bpf_link__unpin()` and
    `bpf_link__detach()`.
- `errno` can hold a libbpf code, not only a system one: `enum libbpf_errno` in
  `tools/lib/bpf/libbpf.h` starts at `__LIBBPF_ERRNO__START` (4000), and
  `bpf_object_load()` returns `libbpf_err(-LIBBPF_ERRNO__ENDIAN)`.
- Kerneldoc in `tools/lib/bpf/btf.h` for `btf__new()` and the functions next
  to it still says an error-encoded pointer is returned; the code returns
  `NULL` through `libbpf_ptr()`.
