| Flag | In this tree |
|---|---|
| `KF_RELEASE` | released argument is always argument 1: `bpf_fetch_kfunc_arg_meta()` sets `release_regno` to `BPF_REG_1` |
| `KF_SLEEPABLE` | rejected where `in_sleepable()` is false, and where `in_sleepable_context()` is false: RCU, preempt-off, IRQ-off region or a held lock |
| `KF_RCU_PROTECTED` | call rejected unless `in_rcu_cs()`; a returned pointer gets `MEM_RCU`, a struct pointer in place of `PTR_TRUSTED` |
| `KF_SPINLOCK_SAFE` | kfunc may be called while `active_locks` is non-zero; any other kfunc is rejected there, see `kfunc_spin_allowed()` |
| `KF_PERFMON` | `check_kfunc_call()` returns `-EPERM` unless `env->allow_ptr_leaks` (`CAP_PERFMON`) |
| `KF_IMPLICIT_ARGS` | `fetch_kfunc_meta()` takes the argument list from the BTF function named with the `_impl` suffix; `check_kfunc_args()` skips the arguments that `is_kfunc_arg_implicit()` finds beyond the public prototype |
| `KF_ARENA_RET`, `KF_ARENA_ARG1`, `KF_ARENA_ARG2` | `kernel/bpf/verifier.c` does not test them; `tools/bpf/resolve_btfids/main.c` uses them to tag BTF pointers with `address_space(1)` |

- KF_TRUSTED_ARGS: not defined in `include/linux/btf.h` and not mentioned in
  `Documentation/bpf/kfuncs.rst`.
- KF_DEPRECATED: `Documentation/bpf/kfuncs.rst` describes it; no header
  defines it.
- No section in `Documentation/bpf/kfuncs.rst`: `KF_SPINLOCK_SAFE`, the three
  arena flags, `KF_FASTCALL` and the three iterator flags.
- `KF_IMPLICIT_ARGS` prototype: `process_kfunc_with_implicit_args()` in
  `tools/bpf/resolve_btfids/main.c` adds the `_impl` function and cuts the
  public prototype at the first implicit parameter, so implicit parameters
  must be last.
- Implicit types: `is_kf_implicit_arg()` in
  `tools/bpf/resolve_btfids/main.c` accepts pointers to
  `struct bpf_prog_aux` and `struct btf_struct_meta`; the documentation names
  only the first.
- Inconsistent `KF_IMPLICIT_ARGS` across a kfunc's hook sets:
  `btf_kfunc_check_flag()` returns `-EINVAL`.
