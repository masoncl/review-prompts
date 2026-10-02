- The function names without a `bpf_` prefix in the "Remembered as" column
  are defined nowhere in this tree, except in the rows marked "same name".
- Order in `bpf_check()`:

| Step | Remembered as | This tree | File |
|---|---|---|---|
| 1 | check_btf_info_early() | `bpf_prepare_btf_info()` | `kernel/bpf/check_btf.c` |
| 2 | part of check_btf_info() | `bpf_check_core_relo()` | `kernel/bpf/check_btf.c` |
| 3 | add_subprog_and_kfunc() | `add_subprogs()` | `kernel/bpf/verifier.c` |
| 4 | same name | `check_subprogs()` | `kernel/bpf/verifier.c` |
| 5 | check_btf_info() | `bpf_check_btf_info()` | `kernel/bpf/check_btf.c` |
| 6 | resolve_pseudo_ldimm64() | `check_and_resolve_insns()` | `kernel/bpf/verifier.c` |
| 7 | add_subprog_and_kfunc() | `add_kfuncs()` | `kernel/bpf/verifier.c` |
| 8 | check_cfg() | `bpf_check_cfg()` | `kernel/bpf/cfg.c` |
| 9 | compute_postorder() | `bpf_compute_postorder()` | `kernel/bpf/cfg.c` |
| 10 | same name | `bpf_stack_liveness_init()` | `kernel/bpf/liveness.c` |
| 11 | same name | `check_attach_btf_id()` | `kernel/bpf/verifier.c` |
| 12 | none | `bpf_compute_const_regs()` | `kernel/bpf/const_fold.c` |
| 13 | none | `bpf_prune_dead_branches()` | `kernel/bpf/const_fold.c` |
| 14 | none | `sort_subprogs_topo()` | `kernel/bpf/verifier.c` |
| 15 | compute_scc() | `bpf_compute_scc()` | `kernel/bpf/cfg.c` |
| 16 | compute_live_registers() | `bpf_compute_live_registers()` | `kernel/bpf/liveness.c` |
| 17 | same name | `mark_fastcall_patterns()` | `kernel/bpf/verifier.c` |
| 18 | same names | `do_check_main()`, `do_check_subprogs()` | `kernel/bpf/verifier.c` |
| 19 | remove_fastcall_spills_fills() | `bpf_remove_fastcall_spills_fills()` | `kernel/bpf/fixups.c` |
| 20 | same name | `check_max_stack_depth()` | `kernel/bpf/verifier.c` |
| 21 | optimize_bpf_loop() | `bpf_optimize_bpf_loop()` | `kernel/bpf/fixups.c` |
| 22 | opt_hard_wire_dead_code_branches() | `bpf_opt_hard_wire_dead_code_branches()` | `kernel/bpf/fixups.c` |
| 23 | opt_remove_dead_code() | `bpf_opt_remove_dead_code()` | `kernel/bpf/fixups.c` |
| 24 | opt_remove_nops() | `bpf_opt_remove_nops()` | `kernel/bpf/fixups.c` |
| 22' | same name | `sanitize_dead_code()` | `kernel/bpf/verifier.c` |
| 25 | convert_ctx_accesses() | `bpf_convert_ctx_accesses()` | `kernel/bpf/fixups.c` |
| 26 | do_misc_fixups() | `bpf_do_misc_fixups()` | `kernel/bpf/fixups.c` |
| 27 | opt_subreg_zext_lo32_rnd_hi32() | `bpf_opt_subreg_zext_lo32_rnd_hi32()` | `kernel/bpf/fixups.c` |
| 28 | fixup_call_args() | `bpf_fixup_call_args()` | `kernel/bpf/fixups.c` |
| 29 | in `bpf_prog_load()` | `__bpf_prog_select_runtime()` | `kernel/bpf/core.c` |

- Steps 22 to 24 run only when `env->bpf_capable` is true; otherwise
  `sanitize_dead_code()` (row 22') runs in their place.
- Steps 19 to 29 run after the main pass; nothing verifies their output.
- `bpf_prune_dead_branches()`: rewrites a conditional jump whose operands
  `bpf_compute_const_regs()` proved constant into `BPF_JMP_A()`, then
  recomputes the postorder. It runs before the main pass, so the main pass
  verifies the rewritten instruction, not the one the loader passed.
- `sort_subprogs_topo()`: rejects a recursive call with "recursive call from"
  before the main pass starts.
- `bpf_compute_live_registers()`: also computes stack liveness, through
  `bpf_compute_subprog_arg_access()`, and sets `zext_dst`.
- `bpf_fixup_call_args()`: when `jit_requested`, calls `bpf_jit_subprogs()`,
  which for a program with subprograms blinds constants with
  `bpf_jit_blind_constants()` when `bpf_prog_need_blind()` and then calls the
  static `jit_subprogs()`.
- `bpf_jit_blind_constants()`: takes `env` and inserts through
  `bpf_patch_insn_data()`; it is one more rewrite whose output is not verified.
- `__bpf_prog_select_runtime()`: called at the end of `bpf_check()`, after
  `convert_pseudo_ld_imm64()` and `adjust_btf_func()`. The JIT of a program
  with one function runs inside `bpf_check()`; `bpf_prog_load()` in
  `kernel/bpf/syscall.c` does not call `bpf_prog_select_runtime()`.
- `bpf_fixup_kfunc_call()`: the kfunc call rewrites are in
  `kernel/bpf/verifier.c`, though `bpf_do_misc_fixups()` calls it.
