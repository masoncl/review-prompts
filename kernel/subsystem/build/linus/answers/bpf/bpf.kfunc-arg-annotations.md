- There is no __opt suffix here; `__nullable` marks an optional buffer, as in
  `bpf_dynptr_slice()` (`buffer__nullable`, `buffer__szk`).
- There is no __prog or __aux suffix here; `is_kfunc_arg_prog_aux()` matches
  any parameter of type `struct bpf_prog_aux *`, and the verifier loads
  `prog->aux` into that register.

| Suffix | What `check_kfunc_args()` does |
|---|---|
| `__szk` | must be a known constant, then checked against the buffer like `__sz`; not compared with the pointee size |
| `__ign` | skipped before every per-argument check, including the NULL and register-type checks |
| `__uninit` | acted on only for a `struct bpf_dynptr` argument |
| `__const_map` | register must be `CONST_PTR_TO_MAP` |
| `__map` | `CONST_PTR_TO_MAP` or a trusted `PTR_TO_BTF_ID` of `struct bpf_map` |
| `__nullable` | a known-NULL register skips all further checks of that argument |
| `__alloc` | accepted only for `bpf_obj_drop()` and `bpf_percpu_obj_drop()` kfuncs; any other kfunc is rejected |
| `__irq_flag` | `process_irq_flag()` returns `-EFAULT` for any kfunc other than the four IRQ save and restore kfuncs |
| `__nonown_allowed` | on a `struct bpf_list_node` argument, also accepts a non-owning reference |
| `__iter` | marks an iterator argument of a kfunc that has no `KF_ITER_NEW`, `KF_ITER_NEXT` or `KF_ITER_DESTROY` flag; iterator must be initialised |
| `__arena`, `__arena__nullable` | register must be `PTR_TO_ARENA` or any `SCALAR_VALUE`; program needs an arena and `bpf_jit_supports_arena_args()` |

- `__sz` and `__szk`: `get_kfunc_arg_type()` classifies the scalar by its
  suffix alone; `check_kfunc_args()` then checks the register of the argument
  before it as the buffer.
- There is no check_kfunc_mem_size_reg() here; `check_mem_size_reg()` serves
  helpers and kfuncs, and for kfuncs checks `BPF_READ | BPF_WRITE` with zero
  size allowed.
- Pointer with no size suffix after it, to a scalar: checked as memory of the
  pointee size (`MEM_FIXED_SIZE`). A pointer to a scalar-only struct is
  checked that way only when the register is neither `PTR_TO_BTF_ID` nor a
  `reg2btf_ids` type.
- One constant per call: `process_const_arg()` returns `-EFAULT` on a second
  `__k` or `__szk` argument.
- `__arena`: `is_kfunc_arg_nullable()` treats it as nullable, so a constant 0
  is accepted; the documentation says the body must not test it for NULL.
- No section in `Documentation/bpf/kfuncs.rst`: `__ign`, `__alloc`,
  `__refcounted_kptr`, `__irq_flag`, `__iter`; `__szk` appears only inside
  the `__nullable` section.
- Documentation example for `__nullable`: shows `bpf_task_release()` with
  `task__nullable`; in `kernel/bpf/helpers.c` its parameter is `p`, and NULL
  is rejected.
