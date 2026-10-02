- `BPF_KPTR_REF` to a program-BTF type: `bpf_obj_free_fields()` calls
  `__bpf_obj_drop_impl()` with the pointee's record, not `field->kptr.dtor`,
  which is `NULL` for such a field.
- `BPF_KPTR_PERCPU` to a program-BTF type: `__bpf_obj_drop_impl()` with
  `percpu` true, which frees with `bpf_mem_free_rcu()` on
  `bpf_global_percpu_ma`.
- Pointee with `BPF_REFCOUNT`: the field holds one reference;
  `__bpf_obj_drop_impl()` decrements it and frees the object and its fields
  only when the count reaches zero.
- `field->kptr.dtor`: `btf_parse_kptr()` looks it up only for `BPF_KPTR_REF` to
  a kernel or module type; `BPF_KPTR_UNREF` and `BPF_KPTR_PERCPU` fields have
  none.
- `bpf_kptr_xchg()` body: not executed when `prog->jit_requested`, the kernel
  is 64-bit and `bpf_jit_supports_ptr_xchg()` is true; `kernel/bpf/fixups.c`
  replaces the call with a `BPF_XCHG` atomic instruction.
