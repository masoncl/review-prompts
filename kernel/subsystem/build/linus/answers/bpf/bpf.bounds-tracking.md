- `struct bpf_reg_state` has no smin_value, umax_value, s32_min_value or
  similar members. The range is `struct cnum64 r64` and `struct cnum32 r32`,
  defined in `include/linux/cnum.h` and implemented in
  `kernel/bpf/cnum_defs.h` and `kernel/bpf/cnum.c`.
- Three representations must agree: `var_off`, `r64` and `r32`.
- A cnum is one arc on the number circle (`base`, `size`). The same arc gives
  the signed and the unsigned bounds, so there is no signed/unsigned pair to
  keep in step.
- Reading: `reg_umin()`, `reg_umax()`, `reg_smin()`, `reg_smax()`,
  `reg_u32_min()`, `reg_u32_max()`, `reg_s32_min()`, `reg_s32_max()` in
  `include/linux/bpf_verifier.h`.
- Unsigned accessors return 0 and the type maximum when the arc crosses the
  maximum/0 boundary; signed accessors return the full signed range when it
  crosses the signed maximum/minimum boundary.
- Setting: `reg_set_urange64()`, `reg_set_srange64()`, `reg_set_urange32()`,
  `reg_set_srange32()`. Each replaces the whole arc, so a signed set after an
  unsigned set discards the unsigned one.
- Narrowing an existing range: `cnum64_intersect_with_urange()`,
  `cnum64_intersect_with_srange()` and the 32-bit forms, as
  `regs_refine_cond_op()` does.
- Signed and unsigned bounds both known:
  `cnum64_intersect(cnum64_from_urange(), cnum64_from_srange())`, as
  `scalar_min_max_mul()` does.
- `cnum64_from_urange()` and `cnum64_from_srange()` with min > max: return a
  wrapping arc, not an error. Neither tests the order of its arguments.
- `cnum64_intersect()`: when the arcs overlap in two pieces it returns the
  smaller input, an over-approximation.
- Invalid range: `CNUM64_EMPTY` or `CNUM32_EMPTY`, tested by
  `range_bounds_violation()`. There is no min > max state to test.
- `reg_bounds_sync()`: returns at once if either range is empty.
- `__reg_deduce_bounds()`: only `deduce_bounds_32_from_64()` and
  `deduce_bounds_64_from_32()`. There is no __reg32_deduce_bounds(),
  __reg64_deduce_bounds(), __reg_deduce_mixed_bounds() or
  __reg_assign_32_into_64().
- **Potentially unsafe usage**: writing one of `var_off`, `r64`, `r32` and
  calling `reg_bounds_sync()` with the other two unchanged.
  - Unsafe: when the new value is not contained in the old one.
    `reg_bounds_sync()` only intersects the three with each other, so the
    stale representation wrongly narrows the result or empties the range.
  - Safe: reset what was not computed, as `scalar_min_max_udiv()` does with
    `reset_reg32_and_tnum()` and `scalar32_min_max_lsh()` with
    `__mark_reg64_unbounded()`.
  - Safe: compute all three, as `BPF_ADD` in `adjust_scalar_min_max_vals()`.
  - Safe: the new value only narrows the old, as the `BPF_JLE` case of
    `regs_refine_cond_op()` does with `cnum64_intersect_with_urange()`.
- Branch refinement: there is no reg_set_min_max(). `check_cond_jmp_op()`
  copies both operands into `true_reg1`, `true_reg2`, `false_reg1`,
  `false_reg2` of `struct bpf_verifier_env`, then calls `is_branch_taken()`.
- `simulate_both_branches_taken()`, reached from `is_scalar_branch_taken()`:
  runs `regs_refine_cond_op()` and `reg_bounds_sync()` on those copies. An
  empty range there means that branch is dead, and the function returns 1
  or 0.
- `regs_refine_cond_op()` must never exclude a possible value: an unsound
  refinement prunes a live branch instead of failing a sanity check.
- `check_cond_jmp_op()` when both branches are live: calls
  `regs_bounds_sanity_check_branches()`, then copies the refined registers
  into the two states, then `sync_linked_regs()`.
- `reg_bounds_sanity_check()` failure: returns `-EFAULT` if
  `env->test_reg_invariants`; otherwise `__mark_reg_unbounded()` resets `r64`
  and `r32` and leaves `var_off`.
