- `btf_parse_fields()` error: does not fail creation; the `ERR_PTR()` stays in
  `map->record`, the per-kind checks are skipped, and `map_check_btf()` goes on
  to the `map_check_btf` op.
- Examples that end this way: two `struct bpf_timer` members (`-E2BIG`), both
  lock kinds, a graph root with no lock, a `BPF_KPTR_REF` to a kernel type with
  no registered dtor.
- Value type: a struct or a datasec; any other kind makes `btf_find_field()`
  return `-EINVAL`, which is a parse error as above.
- Any valid record, whatever the kinds: needs
  `bpf_token_capable(token, CAP_BPF)`, else `-EPERM`.
- `BPF_F_RDONLY_PROG` or `BPF_F_WRONLY_PROG` with a valid record: `-EACCES`.
- Order of the checks: `-EPERM`, then `-EACCES`, then the per-kind
  `-EOPNOTSUPP`.
- `btf_check_and_fixup_fields()` errors: `-EFAULT` when a graph root's value
  type has no struct meta; `-EINVAL` when a `BPF_UPTR` points to a kernel type
  or a type of size 0; `-E2BIG` when the `BPF_UPTR` type is larger than
  `PAGE_SIZE`.
- `bpf_local_storage_map_check_btf()`: checks only that the key is a 32-bit
  int.
- Not checked in `map_check_btf()`: `BPF_F_MMAPABLE`, special fields in the
  key, use as an inner map.
- `bpf_map_mmap()` and `map_freeze()`: return `-ENOTSUPP` for a map with a
  valid record.
