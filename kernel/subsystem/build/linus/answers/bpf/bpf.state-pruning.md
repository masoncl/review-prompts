- `bpf_is_state_visited()`: non-static, in `kernel/bpf/states.c`; `do_check()`
  calls it at prune points. `states_equal()`, `regsafe()`, `stacksafe()` and
  `refsafe()` are static in the same file.
- `mark_chain_precision()` in `kernel/bpf/verifier.c`: a wrapper for
  `bpf_mark_chain_precision()` in `kernel/bpf/backtrack.c`, which holds
  `backtrack_insn()` too. There is no function named __mark_chain_precision;
  the name survives only in comments.
- Stored state with `branches > 0`: never prunes under `NOT_EXACT`. It is used
  only for loop convergence (`RANGE_WITHIN`) and for infinite loop detection
  (`EXACT`).
- Stored state with `branches == 0` whose SCC visit still has backedges
  (`incomplete_read_marks()`): compared under `RANGE_WITHIN`, and the current
  state is saved as a backedge for `propagate_backedges()`.
- `RANGE_WITHIN`: also used at instructions for which `bpf_calls_callback()`
  is true. Under it `regsafe()` checks scalar ranges whether or not the old
  register is `precise`; liveness still applies.
- Liveness: there are no read marks, no live member in
  `struct bpf_reg_state`, and nothing is propagated to parent states.
  REG_LIVE_READ, mark_reg_read() and propagate_liveness() do not exist.
- Register liveness and stack liveness: both computed once, before the main
  pass, by `bpf_compute_live_registers()` in `kernel/bpf/liveness.c`. The main
  pass does not update either.
- Stack liveness: `bpf_compute_subprog_arg_access()` fills one
  `struct func_instance` per (callsite, depth), in 4-byte units. States query
  it with `bpf_live_stack_query_init()` and `bpf_stack_slot_alive()`.
  bpf_mark_stack_read(), bpf_mark_stack_write() and bpf_update_live_stack() do
  not exist.
- `bpf_stack_slot_alive()`: returns true when no instance is found for the
  current frame or for a caller frame it walks, so an unanalysed frame is
  compared in full.
- `clean_verifier_state()`: runs on the current state at the start of every
  `bpf_is_state_visited()` call, so the copy stored as a checkpoint is already
  cleaned. There is no clean_live_states().
- `__clean_func_state()`: sets a dead register to `NOT_INIT` and a dead 4-byte
  half of a slot to `STACK_POISON`. It leaves `STACK_DYNPTR`, `STACK_ITER` and
  `STACK_IRQ_FLAG` slots alone, and also a `STACK_SPILL` slot whose upper half
  is dead and lower half is live when the spilled register is a pointer or
  passes `bpf_register_is_null()`.
- `stacksafe()`: treats `STACK_POISON` as `STACK_INVALID`.
- `func_states_equal()`: calls `regsafe()` only for registers set in
  `live_regs_before` of the old frame's instruction.
- `func_states_equal()`: also requires `stack_arg_safe()`, which runs
  `regsafe()` over `stack_arg_regs`, and rejects when the current frame has
  `no_stack_arg_load` and the old one does not.
- `range_within()`: compares `r64` and `r32` with `cnum64_is_subset()` and
  `cnum32_is_subset()`; `regsafe()` adds `tnum_in()`.
- Loader without `CAP_BPF`: `bpf_mark_chain_precision()` returns 0 at once
  when `env->bpf_capable` is false, `__mark_reg_unknown()` creates scalars
  with `precise` set, and `bpf_is_state_visited()` does not call
  `mark_all_scalars_imprecise()`. `regsafe()` then never skips such a scalar
  as imprecise.
