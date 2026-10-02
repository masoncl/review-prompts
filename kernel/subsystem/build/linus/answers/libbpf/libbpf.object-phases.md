- Phase record: `obj->state` (`enum bpf_object_state` in
  `tools/lib/bpf/libbpf.c`) is the only one; there is no bpf_object__loaded()
  and no loaded field in `struct bpf_object`.
- `map_is_created()`: returns `map->obj->state >= OBJ_PREPARED || map->reused`;
  it does not read `map->fd`.
- `map->fd` in `OBJ_OPEN`: already an open descriptor, a memfd from
  `create_placeholder_fd()` in `bpf_object__add_map()`; `bpf_map__fd()` returns
  -1 until `map_is_created()` is true.
- `bpf_object_prepare()` order: `bpf_object__relocate()` runs before
  `bpf_object__sanitize_and_load_btf()` and `bpf_object__create_maps()`;
  relocation uses the placeholder fd numbers, and `reuse_fd()` puts the created
  map on the same number.
- Failed `bpf_object_prepare()` or `bpf_object_load()`, once past the state
  test and the endianness test at entry: leaves `obj->state` at `OBJ_LOADED`,
  not `OBJ_OPEN`, with every `map->fd` and `prog->fd` at -1. `OBJ_LOADED`
  therefore means "may not be loaded again", not "is loaded": a later
  `bpf_object__load()` returns `-EINVAL` from the state test in
  `bpf_object_load()`.
- `bpf_object__prepare()` on a prepared or loaded object: `-EINVAL`.
- Setter tests and error codes (search `map_is_created(` and `>= OBJ_LOADED`
  for the members):

| Test | Rejected from | Error | Exceptions |
|---|---|---|---|
| `map_is_created()` | `OBJ_PREPARED`, or earlier if `map->reused` | `-EBUSY` | `bpf_map__set_exclusive_program()`: `-EINVAL` |
| `obj->state >= OBJ_LOADED` | `OBJ_LOADED` | `-EBUSY` | `bpf_program__set_autoload()`, `bpf_program__set_attach_target()`, `bpf_object__set_kversion()`: `-EINVAL` |

- `bpf_map__set_inner_map_fd()`: does not call `map_is_created()`; it returns
  `-EINVAL` for a map that is not map-in-map and when
  `map->inner_map_fd != -1`.
- `bpf_map__reuse_fd()`: has no phase test; it sets `map->reused`, after which
  the `map_is_created()` setters fail even in `OBJ_OPEN`.
- `bpf_program__fd()`: returns `-ENOENT` while `prog->fd` is negative, which
  includes all of `OBJ_PREPARED`; `-EINVAL` only for a NULL `prog`.
- `OBJ_PREPARED` or later is required by `bpf_program__clone()` (`-EINVAL`
  otherwise) and `bpf_object__pin_maps()` (`-ENOENT`);
  `bpf_object__pin_programs()` requires `OBJ_LOADED`.
- **Unsafe usage**: turning a program on with `bpf_program__set_autoload()`
  after `bpf_object__prepare()`. The setter returns 0 in `OBJ_PREPARED`, but
  `bpf_object__relocate()` and `obj_needs_vmlinux_btf()` have already skipped
  programs whose `prog->autoload` was false, and `bpf_object__load_progs()`
  loads by the flag.
  - Safe: set it in `OBJ_OPEN`, as `process_obj()` in
    `tools/testing/selftests/bpf/veristat.c` does before
    `bpf_object__prepare()`.
- **Potentially unsafe usage**: a map setter that does not test
  `map_is_created()`.
  - Unsafe: when the field is read only during prepare, by
    `bpf_object__create_map()` or earlier; the call returns 0 in
    `OBJ_PREPARED` and the map keeps the old value.
  - Safe: when the field is read after creation, as
    `bpf_map__set_autoattach()`, whose flag is read by
    `bpf_object__attach_skeleton()`.
  - Safe: `bpf_map__set_pin_path()`; `map->pin_path` is read again after
    creation, by `bpf_map__pin()` when its `path` is NULL.
