- `pr_warn()`, `pr_info()`, `pr_debug()`: do not change `errno`;
  `libbpf_print()` in `tools/lib/bpf/libbpf.c` saves it before the print
  callback and restores it after.
- `free()` is treated as leaving `errno` alone: `bpf_prog_load()` in
  `tools/lib/bpf/bpf.c` calls `free()` and then `libbpf_err_errno(fd)` without
  saving `errno`.
- Save-first, `err = -errno;` before the cleanup call and the code handed on
  after it: see `bpf_link__pin()` and `btf_parse_raw_mmap()`.
- Internal `int` function ending in `libbpf_err()` or `libbpf_err_errno()`:
  it still returns a negative code (`libbpf_err()` returns its argument,
  `libbpf_err_errno()` returns `-errno`), so internal callers are not affected.
  `btf_load_into_kernel()` ends in `libbpf_err()` and is called both by
  `btf__load_into_kernel()` and by internal
  `bpf_object__sanitize_and_load_btf()`.
- `bpf_object_load()` (static) ends in `libbpf_err()`; its only caller is
  `bpf_object__load()`.
- **Potentially unsafe usage**: ending an internal pointer-returning function
  in `libbpf_err_ptr()` or `libbpf_ptr()`.
  - Unsafe: when an internal caller tests the result with `IS_ERR()`; the
    result is `NULL` on failure and `IS_ERR()` is false for it.
  - Safe: when every internal caller that tests the result uses
    `libbpf_get_error()` or a `NULL` test, as `libbpf_find_prog_btf_id()` does
    for `btf_load_from_kernel()` and `bpf_program__attach_usdt()` does for
    `usdt_manager_attach_usdt()`; `libbpf_get_error()` accepts both a `NULL`
    and an `ERR_PTR()` value.
- **Unsafe usage**: `libbpf_ptr()` around a callee that can return plain
  `NULL` on failure; `NULL` is returned with whatever `errno` held before.
  - Safe: the callee returns `ERR_PTR()` on every failure path, as `btf_new()`,
    `btf_parse_elf()` and `bpf_object_open()` do.
  - Safe: for a `NULL`-returning callee, read `-errno` and use
    `libbpf_err_ptr()` or `ERR_PTR()`; `btf_parse_elf()` does this after
    `btf_ext__new()`.
- **Unsafe usage**: `libbpf_err()` on a raw `-1` from a syscall or libc call;
  `errno` becomes 1.
  - Safe: `libbpf_err_errno(ret)`, as `bpf_map_update_elem()` does.
  - Safe: `libbpf_err(-errno)`, as `ring_buffer__poll()` does after
    `epoll_wait()`.
- **Potentially unsafe usage**: a call between the failing call and the read
  of `errno` (`libbpf_err_errno()`, `-errno`, or `libbpf_get_error()` on
  `NULL`).
  - Unsafe: when the call in between can set `errno`, such as `close()`, and
    `errno` is not saved before it and restored after it.
  - Safe: save and restore around it, as `ensure_good_fd()` in
    `tools/lib/bpf/libbpf_internal.h` does around `close()`.
  - Safe: plain stores such as `OPTS_SET()`, as in `bpf_prog_query_opts()`.
  - Safe: a helper that takes the code (`libbpf_err()`, `libbpf_err_ptr()`,
    `libbpf_ptr()`) applied after the cleanup; `btf_load_from_kernel()` calls
    `close()` and then `libbpf_ptr(btf)`.
