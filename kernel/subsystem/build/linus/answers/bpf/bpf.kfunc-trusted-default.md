- Offset: a constant, non-negative offset is accepted on a `PTR_TO_BTF_ID`
  argument; `btf_struct_ids_match()` then looks for the expected type at
  that offset.
- Offset must be 0 for the released argument and for a `__refcounted_kptr`
  argument, see `__check_func_arg_reg_off()`.
- Type match: not strict by default; a struct that embeds the expected type at
  the given offset matches.
- Strict match: only for a referenced register passed to a `KF_RELEASE`
  kfunc, or a `___init` no-cast alias, see `process_kf_arg_ptr_to_btf_id()`.
- Pointer to a struct made only of scalars: if the register is neither a
  `PTR_TO_BTF_ID` nor a `reg2btf_ids` type, `check_kfunc_args()` checks it as
  readable and writable memory of that size, so the body may receive program
  stack or map memory.
- **Unsafe usage**: a kfunc body that treats a pointer to a scalar-only
  struct as a kernel object the program cannot write.
  - Safe: a struct with a pointer member, as `struct cgroup` in
    `bpf_cgroup_ancestor()`; `__btf_type_is_scalar_struct()` fails, so
    `check_kfunc_args()` rejects a register that is neither `PTR_TO_BTF_ID`
    nor a `reg2btf_ids` type.
