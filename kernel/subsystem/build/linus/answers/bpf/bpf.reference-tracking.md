- `struct bpf_reg_state` has no ref_obj_id member. A register holds an
  acquired reference when `reg->id` equals the `id` of a `REF_TYPE_PTR` entry
  in `refs` of `struct bpf_verifier_state`; the test is
  `reg_is_referenced()`.
- `reg->id` serves NULL-check propagation and reference identity at once.
  `mark_ptr_or_null_reg()` keeps `id` on the non-NULL branch;
  `mark_ptr_or_null_regs()` drops the reference on the NULL branch.
- **Potentially unsafe usage**: writing `reg->id` of a register that holds a
  reference.
  - Unsafe: while the entry is still in `refs`; the register no longer passes
    `reg_is_referenced()`, so it cannot be released.
  - Safe: after the entry is removed, as `ref_convert_owning_non_owning()`
    does following `release_reference_nomark()`.
  - Safe: assigning only when `id` is zero, as `check_kfunc_call()` does for
    `reg_may_point_to_spin_lock()`.
- Order on a call result: `check_kfunc_call()` sets the `KF_RET_NULL` id first
  and the `KF_ACQUIRE` id over it; `check_helper_call()` does the same.
- `parent_id` in `struct bpf_reg_state` and `struct bpf_reference_state`:
  names the object a register or reference was derived from, for example a
  dynptr slice or a kfunc memory return.
- `release_reference()`: invalidates every register and spilled slot whose
  `id` or `parent_id` matches, then repeats for the ids of the derived ones.
- `release_reference()` with a live reference whose `parent_id` is the
  released id: fails with "Leaking reference ... Release it first".
- `release_reference()` with an id that is not a reference: returns 0 and
  only invalidates. The "must be referenced" test is in `check_func_arg()`,
  `check_kfunc_args()` and `release_reg()`.
- `check_reference_leak()`: returns 0 in any frame other than frame 0, unless
  `exception_exit` is set, as for `bpf_throw()`.
- `BPF_PROG_TYPE_STRUCT_OPS` at a normal exit: the reference whose `id`
  equals R0's `id` may remain; `check_return_code()` checks its type.
- `is_acquire_function()`: also true for `BPF_FUNC_map_lookup_elem` on
  `BPF_MAP_TYPE_SOCKMAP` and `BPF_MAP_TYPE_SOCKHASH`.
- `is_ptr_cast_function()` with a referenced argument: R0 gets the same `id`
  and loses `PTR_MAYBE_NULL`; the NULL result is verified as a separate
  pushed state.
- `KF_RELEASE` argument: `check_kfunc_args()` requires `reg_is_referenced()`
  unless the register is NULL or the argument is a dynptr.
