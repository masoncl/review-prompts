- `is_trusted_reg()` is true in three cases:
  - the register passes `reg_is_referenced()`;
  - its base type is in `reg2btf_ids` (socket types under `CONFIG_NET`,
    `CONST_PTR_TO_MAP`) and `bpf_type_has_unsafe_modifiers()` is false;
  - it has a `BPF_REG_TRUSTED_MODIFIERS` flag (`MEM_ALLOC`, `PTR_TRUSTED`,
    `NON_OWN_REF`) and `bpf_type_has_unsafe_modifiers()` is false.
- KF_TRUSTED_ARGS is defined nowhere in this tree. `check_kfunc_args()`
  requires every `KF_ARG_PTR_TO_BTF_ID` argument whose register is
  `PTR_TO_BTF_ID` or a `reg2btf_ids` type to pass `is_trusted_reg()` with no
  unsafe modifier; with `KF_RCU` a register that fails must pass
  `is_rcu_reg()`.
- Kfunc return of a struct pointer: `check_kfunc_call()` sets `PTR_TRUSTED`
  whether or not the kfunc is `KF_ACQUIRE`. Exceptions: `KF_RCU_PROTECTED` and
  the next method of an RCU iterator give `MEM_RCU`; `bpf_get_kmem_cache()`
  gives `PTR_UNTRUSTED`; see `check_special_kfunc()` for the rest.
- Program arguments: `prog_args_trusted()` in `kernel/bpf/btf.c` gives
  `PTR_TRUSTED` for `BPF_PROG_TYPE_TRACING` only with `BPF_TRACE_RAW_TP` or
  `BPF_TRACE_ITER`, for LSM only if `bpf_lsm_is_trusted()`, and for struct_ops.
  Other tracing arguments are `PTR_TO_BTF_ID` without `PTR_TRUSTED`.
- `in_rcu_cs()`: true when `env->cur_state->in_sleepable` is false, and also
  while `active_rcu_locks`, `active_preempt_locks`, `active_locks` or
  `active_irq_id` is set.
- `invalidate_rcu_protected_refs()`: runs only when `in_rcu_cs()` is false
  afterwards, so never while `env->cur_state->in_sleepable` is false. It is
  called after `bpf_rcu_read_unlock()`, `bpf_preempt_enable()`, an IRQ
  restore and a spin unlock.
- `invalidate_rcu_protected_refs()`: clears `MEM_RCU`, `PTR_MAYBE_NULL` and
  `NON_OWN_REF`, and sets `PTR_UNTRUSTED`.
- Field walk in `check_ptr_to_btf_access()`, parent trusted or `MEM_RCU`,
  tested in this order:

| Field | Result flags |
|---|---|
| on `BTF_TYPE_SAFE_TRUSTED()` list | `PTR_TRUSTED` |
| on `BTF_TYPE_SAFE_TRUSTED_OR_NULL()` list | `PTR_TRUSTED \| PTR_MAYBE_NULL` |
| `in_rcu_cs()`, on `BTF_TYPE_SAFE_RCU()` list | `MEM_RCU` |
| `in_rcu_cs()`, `__rcu` tag or `BTF_TYPE_SAFE_RCU_OR_NULL()` list | `MEM_RCU \| PTR_MAYBE_NULL` |
| `in_rcu_cs()`, `__percpu` or `__user` tag | flag kept as is |
| `in_rcu_cs()`, any other field | none (flagless `PTR_TO_BTF_ID`) |
| not `in_rcu_cs()` | `PTR_UNTRUSTED` |

- Parent is flagless `PTR_TO_BTF_ID` and not referenced: no trust flag is
  added and `clear_trusted_flags()` removes `MEM_RCU`, so an untagged field
  outside a union gives a flagless `PTR_TO_BTF_ID`.
- Other walk results, from `btf_struct_walk()` and `btf_struct_access()`:
  - through a union with more than one member: `PTR_UNTRUSTED`;
  - pointer to a non-struct: `PTR_TO_MEM | MEM_RDONLY | PTR_UNTRUSTED`;
  - pointer to a struct, parent is `MEM_ALLOC`: `SCALAR_VALUE`.
- Flagless `PTR_TO_BTF_ID` versus `PTR_UNTRUSTED`: both are read through
  `BPF_PROBE_MEM` and reject writes (`bpf_may_fault_on_deref()`). A
  `KF_ARG_PTR_TO_BTF_ID` kfunc argument rejects both, the flagless one unless
  it passes `reg_is_referenced()`. Helpers taking `ARG_PTR_TO_BTF_ID` accept
  the flagless type and reject `PTR_UNTRUSTED` (`btf_ptr_types`).
- `PTR_TO_MEM | MEM_RDONLY | PTR_UNTRUSTED`: `check_mem_access()` allows reads
  with no bounds check and requires `env->allow_ptr_leaks`.
- Map kptr load: tags are "kptr", "kptr_untrusted" and "percpu_kptr"; there
  is no __kptr_ref. `btf_ld_kptr_type()` gives `PTR_MAYBE_NULL` plus `MEM_RCU`
  when `rcu_safe_kptr()` and `in_rcu_cs()`, else plus `PTR_UNTRUSTED`.
- Map "uptr" load: `mark_uptr_ld_reg()` gives `PTR_TO_MEM | PTR_MAYBE_NULL`,
  not `PTR_TO_BTF_ID`.
- **Unsafe usage**: adding a struct to a `BTF_TYPE_SAFE_RCU()` or
  `BTF_TYPE_SAFE_TRUSTED()` style list without a `BTF_TYPE_EMIT()` line.
  - Unsafe: `btf_nested_type_is_trusted()` finds the type by name in BTF;
    when the name is not found it returns false and the field is silently
    treated as not on the list.
  - Safe: add the `BTF_TYPE_EMIT()` line to the matching function, as
    `type_is_trusted()` does for `struct file`.
