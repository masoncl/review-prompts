- `check_map_kptr_access()`: reached only for a `PTR_TO_MAP_VALUE` register.
- Kptr field in an allocated object: `btf_struct_access()` rejects every direct
  load and store that overlaps it with `-EACCES`; `bpf_kptr_xchg()` is the only
  access.
- Load from `BPF_KPTR_REF` or `BPF_KPTR_PERCPU`, `rcu_safe_kptr()` and
  `in_rcu_cs()` both true: `btf_ld_kptr_type()` gives
  `PTR_MAYBE_NULL | MEM_RCU`, plus `MEM_PERCPU` for percpu, or else `MEM_ALLOC`
  for a program-BTF type.
- Same load, pointee record has `BPF_GRAPH_NODE`: `NON_OWN_REF` is added too.
- Same load, either test false: `PTR_MAYBE_NULL | PTR_UNTRUSTED` and nothing
  else, also for percpu.
- `in_rcu_cs()`: true when `env->cur_state->in_sleepable` is false, and in a
  sleepable state while `active_rcu_locks`, `active_preempt_locks`,
  `active_locks` or `active_irq_id` is set.
- `rcu_safe_kptr()`: true for every `BPF_KPTR_REF` to a program-BTF type;
  `rcu_protected_types` is consulted only for kernel types.
- Store into `BPF_KPTR_UNREF`, kernel-BTF register: `PTR_MAYBE_NULL`,
  `PTR_TRUSTED`, `MEM_RCU` and `PTR_UNTRUSTED` are all permitted flags.
- Store into `BPF_KPTR_UNREF`, register offset: a constant non-zero offset is
  accepted; `btf_struct_ids_match()` runs non-strict and walks the struct.
- `BPF_KPTR_REF` and `BPF_KPTR_PERCPU` through `bpf_kptr_xchg()`: strict type
  match and offset 0.
- `map_kptr_match_type()`: rejects a register whose `MEM_PERCPU` flag does not
  match whether the field is `BPF_KPTR_PERCPU`.
