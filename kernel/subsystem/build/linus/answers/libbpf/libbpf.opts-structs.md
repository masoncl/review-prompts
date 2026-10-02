- Size `OPTS_VALID()` treats as known: `offsetofend()` of the field named by
  the `<type>__last_field` define next to the struct (for example
  `bpf_prog_load_opts__last_field`), not `sizeof` the struct.
- Field added without updating the `__last_field` define:
  `libbpf_validate_opts()` counts it as extra bytes and rejects every caller
  that sets it non-zero, with the warning "has non-zero extra bytes".
- Struct with no `__last_field` define: `OPTS_VALID()` on it does not compile.
- Zero check range: from the end of the last known field to the caller's `sz`,
  so it includes the caller's tail padding even when caller and library match;
  `struct bpf_log_opts` has such bytes on 64-bit.
- `LIBBPF_OPTS()`: its `memset()` is what zeroes that padding.
- `size_t :0;`: not present in every options struct (`struct
  bpf_test_run_opts` has none); `OPTS_VALID()` does not depend on it.
- `OPTS_VALID()` returning true: does not show that `opts` is non-NULL or that
  `sz` covers any field after `sz`; it accepts NULL, and an `sz` as small as
  `sizeof(size_t)`.
- Function that requires the struct: tests NULL itself before `OPTS_VALID()`,
  as `bpf_tc_hook_create()` in `tools/lib/bpf/netlink.c` does.
- Nested options pointer: validated with its own `OPTS_VALID()`, as
  `bpf_map_create()` does for `log_opts` before `OPTS_GET()` on it.
- `OPTS_ZEROED(opts, field)`: true for NULL; otherwise checks that every byte
  after `field` up to `sz` is zero; `bpf_link_create()` uses it to reject
  fields that belong to another attach type.
- **Potentially unsafe usage**: `opts->field` read or written directly on a
  struct that came from the caller.
  - Unsafe: when nothing earlier on the path showed that `opts` is non-NULL
    and that `sz` covers the field; a passed `OPTS_VALID()` shows neither, and
    the access dereferences NULL or reads or writes past the caller's object.
  - Safe: after `OPTS_HAS()` was true for that field, as `bpf_xdp_query()`
    does for `feature_flags`.
  - Safe: after `OPTS_GET()` of that field returned a value that differs from
    the fallback, as `btf_dump__dump_type_data()` does for `indent_str`.
  - Safe: on a struct libbpf declared itself with `LIBBPF_OPTS()`, as
    `load_attr` in `bpf_object_load_prog()`, which
    `libbpf_prepare_prog_load()` then writes directly.
