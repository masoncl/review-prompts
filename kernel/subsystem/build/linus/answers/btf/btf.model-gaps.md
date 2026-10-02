- Models take `map->record` to be NULL or a valid record. After a
  `btf_parse_fields()` error `map_check_btf()` leaves an `ERR_PTR()` there;
  users such as `btf_record_has_field()` and `bpf_obj_free_fields()` test
  `IS_ERR_OR_NULL()` and treat the map as having no special fields.
- Models take `bpf_timer_cancel()` to work wherever a program runs. It returns
  `-EOPNOTSUPP` when `defer_timer_wq_op()` is true; `bpf_timer_cancel_async()`
  is the non-waiting kfunc.
- Models take non-preallocated hash map free to release kptrs element by
  element. `delete_all_elements()` and `rhtab_free_elem()` in
  `kernel/bpf/hashtab.c` do not call `bpf_obj_free_fields()`; kptrs are
  released by the `bpf_mem_alloc` destructor.
- Models take `pcpu_init_value()` to reset the special fields of the other
  CPUs' slots. It zeroes those slots with `zero_map_value()`, which leaves
  special fields alone.
- Models do not know `BPF_MAP_TYPE_RHASH`. `rhtab_map_update_elem()` in
  `kernel/bpf/hashtab.c` returns `-EBUSY` for the insert of a new key while
  `rhtab_map_free_internal_structs()` walks the table.
- Models take a kptr field to pin the pointee's `struct btf`. A program BTF
  is kept alive by `map->btf`, which `bpf_map_free()` in
  `kernel/bpf/syscall.c` puts after it frees the record.
- Models do not know the limits on nested and array fields.
  `btf_repeat_fields()` in `kernel/bpf/btf.c` lets only the kptr kinds,
  `BPF_UPTR`, `BPF_LIST_HEAD` and `BPF_RB_ROOT` repeat; more than
  `BTF_FIELDS_MAX` (11) entries makes `btf_parse_fields()` return
  `ERR_PTR(-E2BIG)`.
- Models do not know the ownership depth limit. `BTF_MAX_OWNERSHIP_DEPTH` in
  `kernel/bpf/btf.c` is 8.
- Models take the struct meta to be passed only to `bpf_obj_new_impl()` and
  `bpf_obj_drop_impl()`. Here `bpf_obj_new()` and `bpf_obj_drop()` are kfuncs
  with `KF_IMPLICIT_ARGS` that take `struct btf_struct_meta *`; the impl names
  are wrappers.
