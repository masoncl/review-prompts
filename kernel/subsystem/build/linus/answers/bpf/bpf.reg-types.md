- Exact `reg->type == X`: matches only the flagless type, and the tree uses
  that as a fail-closed test. `check_mem_access()` tests
  `PTR_TO_MAP_VALUE`, `PTR_TO_CTX` and `PTR_TO_STACK` exactly; a flagged
  register reaches the final else and is rejected with "invalid mem access".
- **Potentially unsafe usage**: an exact compare of `reg->type`.
  - Unsafe: where a match imposes a restriction or a rejection and a
    non-match is accepted, since a register with any flag set skips it.
  - Safe: where a match grants access and every non-match ends in rejection,
    as in `check_mem_access()` and the `compatible_reg_types` tables.
  - Safe: where the flag that must keep the restriction is tested beside the
    compare, as `bpf_may_fault_on_deref()` tests `PTR_UNTRUSTED`.
- `check_reg_type()`: compares the whole `reg->type`, flags included, with
  each table entry. It first clears only `MEM_RDONLY` and `PTR_MAYBE_NULL`
  (each when the argument type has it), `DYNPTR_TYPE_FLAG_MASK` for
  `ARG_PTR_TO_MEM`, and `MEM_ALLOC` and `MEM_PERCPU` for a `MEM_ALLOC` R2 of
  `BPF_FUNC_kptr_xchg`. A flag left on the register matches only an entry
  that lists the same flag.
- Flag test after a `base_type()` match: the fail-closed form is an
  allow-list, `type_flag(reg->type) & ~perm_flags` in `map_kptr_match_type()`
  and `bpf_type_has_unsafe_modifiers()`. A list of forbidden flags lets
  through every flag it does not name.
- `MEM_RDONLY` write check: made only for `PTR_TO_MEM` and `PTR_TO_BUF`, in
  `check_mem_access()` and `check_helper_mem_access()`; the message is
  "%s cannot write into %s".
- `MEM_RDONLY` on `PTR_TO_BTF_ID`: does not make the object read-only.
  `check_helper_call()` strips it for `RET_PTR_TO_MEM_OR_BTF_ID`, and
  `check_ptr_to_btf_access()` never tests it.
- `MEM_RDONLY` on `PTR_TO_MAP_VALUE`: not used. Writes to a read-only map are
  rejected by `check_map_access_type()` from the map flags.
- `PTR_TO_BTF_ID | PTR_TRUSTED` passed as helper memory (`mem_types`):
  `check_reg_type()` accepts it only if the argument type has `MEM_RDONLY`,
  else "may write into memory".
- `MEM_ALLOC` is not used for ringbuf memory; that is
  `PTR_TO_MEM | MEM_RINGBUF`.
- `type_is_alloc()` tests the `MEM_ALLOC` bit alone.
  `type_is_ptr_alloc_obj()` also needs base `PTR_TO_BTF_ID` and no
  `PTR_UNTRUSTED`; `check_ptr_to_btf_access()` requires it for a write,
  unless the program type has a `btf_struct_access` op and the register is
  not `MEM_ALLOC`, in which case the op decides. A write through a flagless
  or `PTR_UNTRUSTED` register is rejected before either test, by
  `bpf_may_fault_on_deref()`.
- `MEM_ALLOC | MEM_PERCPU`: `check_ptr_to_btf_access()` rejects every direct
  access ("access percpu memory").
- `MEM_ALLOC` register passed to a helper: `check_reg_type()` allows it only
  for `BPF_FUNC_spin_lock`, `BPF_FUNC_spin_unlock` and `BPF_FUNC_kptr_xchg`.
  For any other helper the table match fails with `-EACCES`; a table that
  did match is a `verifier_bug()`.
- `MEM_ALLOC` register on access: the register must pass
  `reg_is_referenced()`, or be `NON_OWN_REF`, `MEM_RCU` or `PTR_UNTRUSTED`.
  Otherwise `check_ptr_to_btf_access()` reports
  "allocated object must have a referenced id" as a `verifier_bug()`.
