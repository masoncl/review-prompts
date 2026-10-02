- Models take kfunc arguments to be classified inside `check_kfunc_args()`.
  Here `gen_kfunc_arg_proto()` first builds a `struct bpf_func_proto` of
  `enum kfunc_ptr_arg_type` values plus flags such as `PTR_MAYBE_NULL` and
  `MEM_FIXED_SIZE`.
- Models take subprograms and kfuncs to have at most five arguments. Here
  `MAX_BPF_FUNC_ARGS` is 12 for static subprograms and kfuncs: arguments past
  `MAX_BPF_FUNC_REG_ARGS` go in stack argument slots and need
  `bpf_jit_supports_stack_args()`; `check_max_stack_depth_subprog()` rejects
  a tail call when the subprogram that makes it, or a caller on its chain,
  has a nonzero `stack_arg_cnt`. A global subprogram stays at five.
- Models quote messages with "R%d" or "arg#%d". Here argument messages, for
  example in `check_kfunc_args()`, name the argument with `reg_arg_name()`,
  which prints a register argument as "R%d" and a stack argument as an
  R11-relative slot; `kernel/bpf/btf.c` still prints "arg#%d"; the helper
  sleep message is "sleepable helper %s#%d in %s".
- Models take `bpf_obj_new()` to be a macro over `bpf_obj_new_impl()`. Here
  it is a kfunc of its own flagged `KF_IMPLICIT_ARGS`, as is
  `bpf_wq_set_callback()`; see `kernel/bpf/helpers.c`.
- Models take `bpf()` to be a three-argument system call. Here `map_create()`
  takes a `struct bpf_common_attr` from the extra arguments and writes a log
  through it.
- Models do not know the register type `PTR_TO_INSN` or indirect jumps
  (`check_indirect_jump()`).
