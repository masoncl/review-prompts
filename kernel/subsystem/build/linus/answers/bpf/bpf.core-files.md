| Job | File | Not where expected |
|---|---|---|
| Verifier main pass | `kernel/bpf/verifier.c` | `bpf_check()` drives every pass below; register bounds are `struct cnum64` and `struct cnum32` from `include/linux/cnum.h` |
| Control flow check | `kernel/bpf/cfg.c` | there is no check_cfg(); `bpf_check_cfg()`, `bpf_compute_postorder()`, `bpf_compute_scc()` |
| State pruning | `kernel/bpf/states.c` | not `verifier.c`; `bpf_is_state_visited()`, `states_equal()`, `regsafe()`; is_state_visited is only in comments |
| Precision backtracking | `kernel/bpf/backtrack.c` | `backtrack_insn()`, `bpf_mark_chain_precision()`; `verifier.c` keeps the wrapper `mark_chain_precision()` |
| Liveness, stack and registers | `kernel/bpf/liveness.c` | not computed in `verifier.c`; `bpf_compute_live_registers()` computes both before the main pass; `states.c` queries `bpf_stack_slot_alive()` |
| Rewrites after verification | `kernel/bpf/fixups.c` | not `verifier.c`; non-static names gained a `bpf_` prefix, as in `bpf_do_misc_fixups()`; `bpf_patch_insn_data()` is here too |
| Rewrites left in `verifier.c` | `kernel/bpf/verifier.c` | for example `sanitize_dead_code()`, `bpf_fixup_kfunc_call()` |
| Rewrite before the main pass | `kernel/bpf/const_fold.c` | `bpf_prune_dead_branches()` turns constant conditional jumps into `BPF_JMP_A()` |
| Program func_info, line_info, CO-RE | `kernel/bpf/check_btf.c` | not `verifier.c`; `bpf_check_btf_info()` for func_info and line_info; `bpf_check_core_relo()` for CO-RE, which calls `bpf_core_apply()` in `kernel/bpf/btf.c` |
| Verifier log | `kernel/bpf/log.c` | `verbose()` is a static function in `verifier.c`, and a macro for `bpf_verifier_log_write()` in the other files that define it, for example `states.c` |
| Structured failure reports | `kernel/bpf/diagnostics.c` | report functions, for example `bpf_diag_program_structure()` and `bpf_diag_policy()`, write to the same log |
| bpf system call | `kernel/bpf/syscall.c` | entry is `SYSCALL_DEFINE5(bpf, ...)`; the extra arguments carry `struct bpf_common_attr` |
| Helpers | `kernel/bpf/helpers.c` | tracing in `kernel/trace/bpf_trace.c`, networking in `net/core/filter.c` |
| Hash maps | `kernel/bpf/hashtab.c` | also holds `BPF_MAP_TYPE_RHASH` (`struct bpf_rhtab`, `rhtab_map_ops`) |
| Array maps | `kernel/bpf/arraymap.c` | `BPF_MAP_TYPE_INSN_ARRAY` is in `kernel/bpf/bpf_insn_array.c` |
| Element allocator | `kernel/bpf/memalloc.c` | `bpf_global_ma` is defined in `kernel/bpf/core.c` |
| BTF | `kernel/bpf/btf.c` | |
| Trampolines | `kernel/bpf/trampoline.c` | |
| struct_ops | `kernel/bpf/bpf_struct_ops.c` | `__register_bpf_struct_ops()` and `bpf_struct_ops_find()` are in `kernel/bpf/btf.c` |
| Arena | `kernel/bpf/arena.c` | with `kernel/bpf/range_tree.c`; both built only with `CONFIG_MMU` and `CONFIG_64BIT` |
| x86 JIT | `arch/x86/net/bpf_jit_comp.c` | |
| arm64 JIT | `arch/arm64/net/bpf_jit_comp.c` | |
| libbpf | `tools/lib/bpf/` | |
| Selftests | `tools/testing/selftests/bpf/` | |
| Verifier test loader | `tools/testing/selftests/bpf/test_loader.c` | paths under `tools/testing/selftests/bpf/`: runs programs such as `progs/verifier_align.c` from `prog_tests/verifier.c`; `test_verifier.c` with `verifier/` is still built |
