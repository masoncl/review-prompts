- Verifier code: split across files, not only `kernel/bpf/verifier.c`; for
  example `do_check()` is in `kernel/bpf/verifier.c` and the static
  `jit_subprogs()` is in `kernel/bpf/fixups.c`.
- `struct bpf_map`: it is the member embedded first in each concrete map, for
  example `struct bpf_array` and `struct bpf_htab`; `struct bpf_map_ops` is
  reached through the `ops` pointer and is not embedded.
- Subprograms: after `jit_subprogs()` every function, the main body included
  (`func[0]`), is its own `struct bpf_prog` with its own
  `struct bpf_prog_aux`.
- Subprogram aux: its pointers (BTF, func_info, line info, kfunc and poke
  tables) alias the main aux and are not freed with the subprogram; it has no
  id and no stats, and `used_maps` is cleared after JIT.
- `main_prog_aux`: leads from any aux to the main one. `bpf_prog_ksym_find()`
  can return a subprogram, so code that needs the loaded program goes through
  `aux->main_prog_aux->prog`, as `find_from_stack_cb()` does.
- `struct bpf_tramp_node`: this, not the link or the prog, is what hangs on
  `progs_hlist` of a `struct bpf_trampoline`; it points back to its
  `struct bpf_link` and carries the cookie.
- `struct bpf_tramp_link`: a `struct bpf_link` plus one node.
- `struct bpf_tracing_link`: adds a second node, `fexit`. A
  `BPF_TRAMP_FSESSION` program is put on both the fentry and the fexit list;
  see `fsession_exit()`.
- `struct bpf_tracing_multi_link`: one link and one prog, with one
  `struct bpf_tracing_multi_node` per target function, each holding its own
  trampoline reference; see `bpf_trampoline_multi_attach()`.
- `struct bpf_trampoline` key: `bpf_trampoline_compute_key()` combines the
  target prog id or the BTF object id with the BTF type id.
  `bpf_trampoline_lookup()` also puts the trampoline in a second table hashed
  by `ip`.
- `link->prog` may be NULL: `bpf_struct_ops_link_create()` builds a
  `struct bpf_struct_ops_link` with no prog; that link holds a reference on a
  struct_ops map. `bpf_link_free()` calls the `release` op only when
  `link->prog` is set.
- Struct_ops map: holds in `links[]` one `struct bpf_tramp_link` per function
  member that was given a program. These links carry the prog reference, are
  of type `BPF_LINK_TYPE_STRUCT_OPS`, and never get an fd or an id.
- Struct_ops registration: a map created with `BPF_F_LINK` is registered by
  `bpf_struct_ops_link_create()`. Without the flag,
  `bpf_struct_ops_map_update_elem()` calls `reg` itself and takes a map
  reference.
- `aux->st_ops_assoc`: a prog-to-struct_ops-map pointer set by
  `bpf_prog_assoc_struct_ops()`, from map update or from the
  `BPF_PROG_ASSOC_STRUCT_OPS` command. It holds a map reference only for
  programs that are not `BPF_PROG_TYPE_STRUCT_OPS`. A struct_ops prog used in
  a second map gets `BPF_PTR_POISON`.
- Link's prog reference: dropped in `bpf_link_dealloc()`, when the link is
  freed. The `detach` op reached from `link_detach()` detaches from the hook
  and leaves the link and its prog reference in place, for example
  `bpf_cgroup_link_detach()`.
- `used_maps`: not fixed at load. `bpf_prog_bind_map()` appends a map later,
  under `used_maps_mutex`.
- Tracepoint links: a non-sleepable raw tracepoint link is freed through
  `call_tracepoint_unregister_atomic()`, an SRCU grace period on
  `tracepoint_srcu`, not through `call_rcu()`; see `bpf_link_free()`.
- Pinning: only progs, maps and links can be pinned in bpffs (`enum bpf_type`
  in `kernel/bpf/inode.c`). BTF objects and tokens cannot be pinned, and a
  token has no id.
- `struct btf_record`: describes only the kinds in `enum btf_field_type`.
  Dynptrs are not among them; they are verifier stack-slot state
  (`STACK_DYNPTR`). `struct bpf_mem_alloc` is an allocator embedded in map
  structs such as `struct bpf_htab`, not a special field.
- `BPF_MAP_TYPE_INSN_ARRAY`: a map of instruction offsets claimed by one
  program during verification. `bpf_insn_array_init()` requires the map to be
  frozen and returns `-EBUSY` if another program has already claimed it.
