- `MAX_CALL_FRAMES`: 16, in `include/linux/bpf_verifier.h`.
- `MAX_CALL_FRAMES` is checked at load in three places: `setup_func_entry()`
  during the main pass, `check_max_stack_depth_subprog()`, and
  `analyze_subprog()` in `kernel/bpf/liveness.c`, which returns `-EINVAL` at
  that depth for a callee that gets a frame-pointer-derived argument.
- `check_max_stack_depth_subprog()`: restarts its frame count at 0 when it
  enters a global subprog. `check_func_call()` pushes no frame for a global
  call. Neither bounds a chain through global subprogs by `MAX_CALL_FRAMES`;
  the stack sum still applies to it.
- Tail call with bpf2bpf calls: on entry to a non-main subprog that has a tail
  call, the summed stack of its callers must be below the literal 256, or the
  load fails with `-EACCES`. It is not a cap on each frame.
- `round_up_stack_depth()`: rounds a frame to 16 bytes when `jit_requested`,
  and to 32 otherwise.
- Private stack: a subprog in mode `PRIV_STACK_ADAPTIVE` is checked alone
  against `MAX_BPF_STACK` and is not added to the chain sum. The mode is given
  only on the walk from the main program, when `bpf_enable_priv_stack()`
  returns `PRIV_STACK_ADAPTIVE`, no subprog has a tail call, the subprog was
  not already marked `NO_PRIV_STACK` by an async callback walk, it has no
  stack arguments (`stack_arg_cnt`) under `CONFIG_X86_64`, and its rounded
  depth is at least `BPF_PRIV_STACK_MIN_SIZE` (64).
- **Potentially unsafe usage**: a rewrite pass that adds to `stack_depth`
  after `check_max_stack_depth()` has run.
  - Unsafe: when the program is JITed and the amount added is not a small
    constant per subprog. The rechecks against `MAX_BPF_STACK`, in
    `bpf_do_misc_fixups()` and `bpf_patch_call_args()`, run only for a
    program that is not JITed, so nothing rejects the frame.
  - Safe: a constant per subprog, as `bpf_optimize_bpf_loop()` (24 to 31
    bytes), `bpf_convert_ctx_accesses()` (8) and `bpf_do_misc_fixups()` (8 or
    16) add. For an interpreted program the recheck in `bpf_do_misc_fixups()`
    rejects a depth above 512, and `bpf_prog_select_interpreter()` in
    `kernel/bpf/core.c` tests the index before it reads `interpreters[]`.
- `BPF_COMPLEXITY_LIMIT_INSNS`: compared with `env->insn_processed`, which is
  never reset; it counts the main pass plus every global subprog pass.
- `BPF_COMPLEXITY_LIMIT_JMP_SEQ`: 8192 pending states in `push_stack()` and
  `push_async_cb()`; over it the load fails with `-E2BIG`.
- `BPF_COMPLEXITY_LIMIT_STATES`: 64. It applies only when `env->bpf_capable`
  is false, and it stops `bpf_is_state_visited()` adding a checkpoint when
  the list it searched holds more than 64 states. It rejects nothing.
