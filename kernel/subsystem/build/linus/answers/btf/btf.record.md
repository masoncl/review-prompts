- `map->record`: built inside `map_check_btf()`, which `map_create_alloc()`
  calls after `ops->map_alloc()`; it is `NULL` while `map_alloc` runs.
- Map created without `attr->btf_value_type_id`: `map_check_btf()` is not
  called and `map->record` stays `NULL`.
- Map type that needs the record at setup: uses its `map_check_btf` op, as
  `htab_map_check_btf()` does.
- `struct btf_record`: also caches `res_spin_lock_off` and `task_work_off`;
  each cached offset is `-EINVAL` when the kind is absent.
- `btf_parse_struct_metas()`: gives a struct an entry only if a direct member
  has, as its type id, one of the structs named in `alloc_obj_fields` or a
  kptr-tagged pointer.
- `btf_find_struct_meta()`: returns `NULL` for any other type; callers such as
  `bpf_obj_free_fields()` and `reg_btf_record()` then use a `NULL` record.
- Record in a `struct btf_struct_meta`: never `NULL` or an error;
  `btf_parse_struct_metas()` fails the BTF load instead.
