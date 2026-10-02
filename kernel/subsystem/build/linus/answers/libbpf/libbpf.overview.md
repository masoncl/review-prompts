- `struct bpf_program`: one per `STT_FUNC` symbol, so `.text` subprograms are
  entries of `obj->programs` too; `prog_is_subprog()` in
  `tools/lib/bpf/libbpf.c` tells them apart.
- Subprogram entries: hidden by `bpf_object__next_program()` and
  `bpf_object__for_each_program()`, skipped by `bpf_object__load_progs()`;
  internal loops over `obj->programs[i]` see them.
- `prog->insns`: a private malloc'd copy per program, made in
  `bpf_object__init_prog()`; there is no instruction array shared by the
  object.
- `obj->maps` and `obj->programs`: arrays of structs, not arrays of pointers;
  inside `bpf_object_open()` `obj->programs` is realloc'd while
  `bpf_object__elf_collect()` runs and `obj->maps` while
  `bpf_object__init_maps()` runs, so element pointers are stable only after
  those steps; `struct reloc_desc` stores `map_idx`, not a pointer.
- `map->inner_map`: a separately allocated `struct bpf_map` template that is
  not in `obj->maps`; `bpf_object__create_map()` destroys it once the outer
  map is created.
- `enum bpf_object_state`: three states, `OBJ_OPEN`, `OBJ_PREPARED`,
  `OBJ_LOADED`; `bpf_object__prepare()` is an exported step between open and
  load.
- `bpf_object_prepare()`: resolves externs, relocates (subprogram code is
  appended here), loads BTF and creates maps; program fds are the only kernel
  objects made by `bpf_object_load()` itself.
- ELF state: `bpf_object__elf_finish()` runs at the end of `bpf_object_open()`,
  so `efile.elf`, `efile.symbols` and `efile.secs` are gone at prepare and load
  time; scalar indexes such as `efile.text_shndx` survive and are still read.
- `enum libbpf_map_type`: the maps libbpf makes from data sections; besides
  data, bss, rodata and kconfig it has `LIBBPF_MAP_PERCPU` for `PERCPU_SEC`,
  a `BPF_MAP_TYPE_PERCPU_ARRAY` that is never mmapable.
- `bpf_map__is_internal()`: false for struct_ops maps and for the arena map;
  both keep `LIBBPF_MAP_UNSPEC`.
- struct_ops map: holds pointers to the `struct bpf_program` of each member;
  `bpf_object_adjust_struct_ops_autoload()` overwrites those programs'
  `autoload` from the maps' `autocreate`.
- `obj->jumptable_maps`: `BPF_MAP_TYPE_INSN_ARRAY` fds made by
  `create_jt_map()` during relocation; owned and closed by the object, with no
  `struct bpf_map` behind them.
- `obj->btf_vmlinux` and `obj->btf_modules`:
  `bpf_object_post_load_cleanup()` frees them at the end of
  `bpf_object_load()`, and they are never loaded when `obj->gen_loader` is set.
- `obj->btf_custom_path`: when set, CO-RE matches against
  `obj->btf_vmlinux_override` instead of vmlinux BTF.
- `struct bpf_gen` (`obj->gen_loader`): BTF load, map creation and program
  load are recorded instead of sent to the kernel; maps and programs are
  referred to by array index, map fds stay placeholders, program fds stay -1.
- `struct bpf_link`: also made from a map, by `bpf_map__attach_struct_ops()`;
  `struct bpf_map_skeleton` has a `link` slot for it.
- Links that reach into the object: `struct bpf_link_usdt` points at the
  object's `struct usdt_manager`, which `bpf_object__close()` frees; a
  struct_ops link without `BPF_F_LINK` borrows `map->fd`. Both detach paths
  use them, so these links have to go before the object.
- `bpf_object__destroy_skeleton()`: the one place libbpf ties links to an
  object; it destroys every link in the skeleton's slots, then closes the
  object.
- Subskeleton: there is no struct bpf_subskeleton; the type is
  `struct bpf_object_subskeleton` in `tools/lib/bpf/libbpf.h`.
