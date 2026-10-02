- There is no struct btf_field_offs in this tree, and no separate offset
  table. `bpf_obj_memcpy()` and `bpf_obj_memzero()` in
  `include/linux/bpf.h` walk `rec->fields[]` directly and rely on it being
  sorted by offset.
- Map keys: no record describes a key; `map_check_btf()` parses only the
  value type.
- `struct btf_field`: one entry per occurrence, with offsets relative to the
  outermost value. Fields inside nested structs and arrays are flattened by
  `btf_find_nested_struct()` and `btf_repeat_fields()`, and every entry counts
  against `BTF_FIELDS_MAX`.
- `struct btf_struct_meta`: exists only for user-loaded BTF;
  `btf->struct_meta_tab` is set to a table only in `btf_parse()`, so kernel
  and module BTF have no table.
- Program to `struct btf_struct_meta`: `bpf_fixup_kfunc_call()` in
  `kernel/bpf/verifier.c` patches the address of the meta into the instruction
  stream as a hidden kfunc argument, for example for `bpf_obj_new()` and
  `bpf_obj_drop()`. A loaded program therefore points into the BTF's table.
- `struct btf_field_kptr`, BTF reference: held only when
  `btf_is_kernel(kptr.btf)`. For a local type `kptr.btf` is the BTF the record
  was parsed from, with no reference taken; see `btf_parse_kptr()`,
  `btf_record_dup()` and `btf_record_free()`.
- `struct btf_field_kptr`, module reference: taken only for `BPF_KPTR_REF`
  whose type is in module BTF; `kptr.module` is NULL for the other kptr kinds.
- Copies of a map record: two places call `btf_record_dup()`.
  `bpf_map_meta_alloc()` in `kernel/bpf/map_in_map.c` makes the inner-map
  template. `bpf_ma_set_dtor()` in `kernel/bpf/hashtab.c` makes a copy held in
  `struct htab_btf_record`, used as the `struct bpf_mem_alloc` destructor
  context of non-preallocated hash maps and of `BPF_MAP_TYPE_RHASH` maps.
- A copied record still borrows from the program BTF: `graph_root.value_rec`
  and a local-type `kptr.btf` are copied as plain pointers.
  `btf_record_dup()` does not pin that BTF; `bpf_map_meta_alloc()` takes its
  own `btf_get()` on `inner_map->btf` for this reason.
- Ownership cycles: `btf_check_and_fixup_fields()` does not check them. It
  validates `BPF_UPTR` pointees and fills `graph_root.value_rec`.
- `btf_check_ownership_depth()` in `kernel/bpf/btf.c`: run by `btf_parse()`
  after every struct-meta record is fixed up; rejects cycles and chains deeper
  than `BTF_MAX_OWNERSHIP_DEPTH` with `-ELOOP`.
- Ownership edges counted by `btf_owned_type_idx()`: graph roots, and
  `BPF_KPTR_REF` or `BPF_KPTR_PERCPU` fields that point at a local type that
  has a `struct btf_struct_meta`.
- Map records are not part of the ownership-depth walk; it covers only the
  struct-meta table of the BTF being loaded.
