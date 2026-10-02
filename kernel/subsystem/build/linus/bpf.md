# BPF Subsystem

## Main structures

### Objects and how they relate

- Verifier code: split across files, not only `kernel/bpf/verifier.c`; for
  example `do_check()` is in `kernel/bpf/verifier.c` and the static
  `jit_subprogs()` is in `kernel/bpf/fixups.c`.
- `struct bpf_map`: it is the member embedded first in each concrete map, for
  example `struct bpf_array` and `struct bpf_htab`; `struct bpf_map_ops` is
  reached through the `ops` pointer and is not embedded.
- Subprograms: after `jit_subprogs()` every function, the main body included
  (`func[0]`), is its own `struct bpf_prog` with its own
  `struct bpf_prog_aux`.
- Subprogram aux: its pointers (BTF, func_info, line info, kfunc and poke
  tables) alias the main aux and are not freed with the subprogram; it has no
  id and no stats, and `used_maps` is cleared after JIT.
- `main_prog_aux`: leads from any aux to the main one. `bpf_prog_ksym_find()`
  can return a subprogram, so code that needs the loaded program goes through
  `aux->main_prog_aux->prog`, as `find_from_stack_cb()` does.
- `struct bpf_tramp_node`: this, not the link or the prog, is what hangs on
  `progs_hlist` of a `struct bpf_trampoline`; it points back to its
  `struct bpf_link` and carries the cookie.
- `struct bpf_tramp_link`: a `struct bpf_link` plus one node.
- `struct bpf_tracing_link`: adds a second node, `fexit`. A
  `BPF_TRAMP_FSESSION` program is put on both the fentry and the fexit list;
  see `fsession_exit()`.
- `struct bpf_tracing_multi_link`: one link and one prog, with one
  `struct bpf_tracing_multi_node` per target function, each holding its own
  trampoline reference; see `bpf_trampoline_multi_attach()`.
- `struct bpf_trampoline` key: `bpf_trampoline_compute_key()` combines the
  target prog id or the BTF object id with the BTF type id.
  `bpf_trampoline_lookup()` also puts the trampoline in a second table hashed
  by `ip`.
- `link->prog` may be NULL: `bpf_struct_ops_link_create()` builds a
  `struct bpf_struct_ops_link` with no prog; that link holds a reference on a
  struct_ops map. `bpf_link_free()` calls the `release` op only when
  `link->prog` is set.
- Struct_ops map: holds in `links[]` one `struct bpf_tramp_link` per function
  member that was given a program. These links carry the prog reference, are
  of type `BPF_LINK_TYPE_STRUCT_OPS`, and never get an fd or an id.
- Struct_ops registration: a map created with `BPF_F_LINK` is registered by
  `bpf_struct_ops_link_create()`. Without the flag,
  `bpf_struct_ops_map_update_elem()` calls `reg` itself and takes a map
  reference.
- `aux->st_ops_assoc`: a prog-to-struct_ops-map pointer set by
  `bpf_prog_assoc_struct_ops()`, from map update or from the
  `BPF_PROG_ASSOC_STRUCT_OPS` command. It holds a map reference only for
  programs that are not `BPF_PROG_TYPE_STRUCT_OPS`. A struct_ops prog used in
  a second map gets `BPF_PTR_POISON`.
- Link's prog reference: dropped in `bpf_link_dealloc()`, when the link is
  freed. The `detach` op reached from `link_detach()` detaches from the hook
  and leaves the link and its prog reference in place, for example
  `bpf_cgroup_link_detach()`.
- `used_maps`: not fixed at load. `bpf_prog_bind_map()` appends a map later,
  under `used_maps_mutex`.
- Tracepoint links: a non-sleepable raw tracepoint link is freed through
  `call_tracepoint_unregister_atomic()`, an SRCU grace period on
  `tracepoint_srcu`, not through `call_rcu()`; see `bpf_link_free()`.
- Pinning: only progs, maps and links can be pinned in bpffs (`enum bpf_type`
  in `kernel/bpf/inode.c`). BTF objects and tokens cannot be pinned, and a
  token has no id.
- `struct btf_record`: describes only the kinds in `enum btf_field_type`.
  Dynptrs are not among them; they are verifier stack-slot state
  (`STACK_DYNPTR`). `struct bpf_mem_alloc` is an allocator embedded in map
  structs such as `struct bpf_htab`, not a special field.
- `BPF_MAP_TYPE_INSN_ARRAY`: a map of instruction offsets claimed by one
  program during verification. `bpf_insn_array_init()` requires the map to be
  frozen and returns `-EBUSY` if another program has already claimed it.

## Where to look

**Core files**

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

## The verifier

**Verifier phases**

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

**State pruning and precision**

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

**New fields and state comparison**

- `struct bpf_reg_state` field order, in `include/linux/bpf_verifier.h`:
  `type`, `delta`, the union, `var_off`, `r64`, `r32`, `id`, `parent_id`,
  `map_uid`, `precise`. There is no ref_obj_id. Bounds are the circular
  numbers `r64` and `r32`.
- Where each `memcmp()` in `kernel/bpf/states.c` stops:

| Function or case | Compares bytes before | Then |
|---|---|---|
| `regs_exact()`: every type under `EXACT`, else `PTR_TO_STACK` and `default:` | `id` | `check_ids()` on `id`, `parent_id`, `map_uid` |
| `SCALAR_VALUE` when `env->explore_alu_limits` | `id` | `check_scalar_ids()` on `id` |
| `PTR_TO_MAP_KEY`, `PTR_TO_MAP_VALUE`, `PTR_TO_MEM`, `PTR_TO_BUF`, `PTR_TO_TP_BUFFER` | `var_off` | `range_within()`, `tnum_in()`, same three `check_ids()` |
| `PTR_TO_INSN` | `var_off` | `range_within()`, `tnum_in()`, no ids |
| `states_maybe_looping()` | `precise` | nothing; ids compared raw |

- **Potentially unsafe usage**: adding a field before `id` and relying on
  `memcmp()` to compare it.
  - Unsafe: when the field matters for `SCALAR_VALUE`, `PTR_TO_PACKET`,
    `PTR_TO_PACKET_META` or `PTR_TO_ARENA`. Outside `EXACT` those cases in
    `regsafe()` call no `memcmp()` (`SCALAR_VALUE` does only when
    `env->explore_alu_limits`); `PTR_TO_ARENA` returns true once the types
    match.
  - Unsafe: when the field sits at or after `var_off` and matters for a case
    in the table that stops at `var_off`.
  - Safe: when the field matters only for `PTR_TO_STACK` or a type that
    reaches `default:`, which call `regs_exact()`.
- **Potentially unsafe usage**: adding a field after `id` with no explicit
  comparison.
  - Unsafe: when the field is program state; `regs_exact()` compares nothing
    after `map_uid`.
  - Safe: `precise`, which is a mark; `regsafe()` reads it from the old state
    only, to choose the comparison.
- `SCALAR_VALUE` case outside `EXACT`: compares `delta` only when the old `id`
  has `BPF_ADD_CONST` (always when `env->explore_alu_limits`), and does not
  compare `parent_id` or `map_uid`.
- `stacksafe()` per slot type: `STACK_DYNPTR` compares `dynptr.type`,
  `dynptr.first_slot`, `id`, `parent_id`. `STACK_ITER` compares `type`,
  `iter.btf`, `iter.btf_id`, `iter.state`, `id`, and on purpose not
  `iter.depth`. `STACK_IRQ_FLAG` compares `id` and `irq.kfunc_class`.
- New `slot_type` value: the `default:` of the switch in `stacksafe()` returns
  false, so states holding it never prune until a case is added.
- **Potentially unsafe usage**: state that the verifier reads from a slot or
  register which liveness reports dead.
  - Unsafe: when `__clean_func_state()` is not told about it. It overwrites
    the dead register with `bpf_mark_reg_not_init()` or the dead half slot
    with `STACK_POISON` before any comparison.
  - Safe: `STACK_DYNPTR`, `STACK_ITER` and `STACK_IRQ_FLAG` slots, which
    `__clean_func_state()` skips.
- Reset: `bpf_mark_reg_unknown_imprecise()` zeroes the whole structure, and
  `bpf_mark_reg_not_init()` goes through it. `__mark_reg_known()` zeroes only
  the bytes between `type` and `var_off`, then `id`, `parent_id` and `map_uid`
  by name; a new field at or after `var_off` needs its own line there.
  mark_reg_not_init() and __mark_reg_not_init() do not exist.
- Copy: `bpf_copy_verifier_state()` -> `copy_func_state()` ->
  `copy_stack_state()` copy registers, slots and `stack_arg_regs` bytewise. A
  plain field needs no change; a field that owns memory does.
- `stack_arg_regs`: holds `struct bpf_reg_state` too. `stack_arg_safe()` runs
  `regsafe()` on it, and `bpf_mark_chain_precision()` marks it.
- Printing: `print_reg_state()` and `slot_type_char[]` in `kernel/bpf/log.c`.

**Stack, call and tail-call limits**

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

**Changing the verifier**

- All selftest paths below are under `tools/testing/selftests/bpf/`.
- Log text has two sources: the `verbose()` line, and next to it a call into
  `kernel/bpf/diagnostics.c` such as `bpf_diag_policy()`. Both write to the
  same log when the level has a `BPF_LOG_LEVEL` bit. `__msg()` and
  `__msg_unpriv()` match either; for example `progs/verifier_unpriv.c`
  expects "policy check failed for".
- `__msg()` order: each pattern is searched for after the end of the previous
  match, so reordering two log lines fails a test. `__not_msg()` must be
  absent between its neighbouring `__msg()` matches.
- Alignment tests: `progs/verifier_align.c`; there is no prog_tests/align.c.
- There are no verifier_spectre files; Spectre expectations are `__xlated()`
  and `__xlated_unpriv()` lines in files such as `progs/verifier_unpriv.c` and
  `progs/verifier_bounds.c`.
- Unprivileged expectations in `test_loader.c`: a test with an `_unpriv`
  annotation that sets `UNPRIV` in `mode_mask` also runs unprivileged;
  `__stderr_unpriv()` and `__stdout_unpriv()` do not set it. Whatever it does
  not state for unprivileged mode (result, messages, xlated, jited) is copied
  from the privileged expectation. A change in unprivileged acceptance fails
  such a test though it has no `__failure_unpriv`.
- Unprivileged in `test_loader.c`: `drop_capabilities()` drops `CAP_SYS_ADMIN`,
  `CAP_NET_ADMIN`, `CAP_PERFMON` and `CAP_BPF`; `__caps_unpriv()` gives some
  back.
- `test_verifier.c`: runs a test unprivileged only when `test_as_unpriv()`
  holds: `prog_type` unset, `BPF_PROG_TYPE_SOCKET_FILTER` or
  `BPF_PROG_TYPE_CGROUP_SKB`.
- `test_verifier.c` rewrite checks: `.expected_insns` and `.unexpected_insns`,
  for example in `verifier/bpf_loop_inline.c`.
- Level 2 log output is matched literally: for example
  `progs/verifier_live_stack.c`, `progs/compute_live_registers.c`,
  `progs/verifier_subprog_topo.c`, `progs/verifier_precision.c`.
- Prologue and epilogue rewrites: `progs/pro_epilogue.c`, run from
  `prog_tests/pro_epilogue.c`.

## Register state

**Register types and type flags**

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

**Scalar bounds**

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

**Acquired references**

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

**Trusted, RCU and untrusted pointers**

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

## Programs

**Sleepable programs**

- `can_be_sleepable()` in `kernel/bpf/verifier.c`: besides fentry, fexit,
  fmod_ret and iter, accepts `BPF_PROG_TYPE_TRACING` with `BPF_TRACE_RAW_TP`,
  `BPF_TRACE_FSESSION`, `BPF_TRACE_FENTRY_MULTI`, `BPF_TRACE_FEXIT_MULTI` and
  `BPF_TRACE_FSESSION_MULTI`.
- `BPF_PROG_TYPE_RAW_TRACEPOINT` and `BPF_PROG_TYPE_TRACEPOINT`: accepted by
  `can_be_sleepable()`, like `BPF_PROG_TYPE_KPROBE` and
  `BPF_PROG_TYPE_STRUCT_OPS`.
- `BPF_PROG_TYPE_LSM`: accepted unless `expected_attach_type` is
  `BPF_LSM_CGROUP`.
- `BPF_PROG_TYPE_EXT` and `BPF_PROG_TYPE_RAW_TRACEPOINT_WRITABLE`: not
  accepted, so a sleepable program of either type fails to load.
- `BPF_PROG_TYPE_SYSCALL`: never reaches `can_be_sleepable()`;
  `check_attach_btf_id()` returns first, and rejects one that is not
  sleepable.
- Message from `check_attach_btf_id()` when `can_be_sleepable()` is false:
  "Program of this type cannot be sleepable".
- `btf_id_allow_sleepable()`: returns `-EINVAL` unless `btf_is_kernel()`, so a
  sleepable fentry, fexit or fsession program cannot attach to another BPF
  program.
- `check_attach_sleepable()` with `CONFIG_FUNCTION_ERROR_INJECTION`: accepts a
  target that is on the error-injection list and not in
  `btf_non_sleepable_error_inject`.
- `check_attach_sleepable()` without `CONFIG_FUNCTION_ERROR_INJECTION`: accepts
  only names that pass `has_arch_syscall_prefix()`.
- Multi attach types: the load-time placeholder id passes
  `btf_id_allow_sleepable()`; each real target is checked by
  `bpf_check_attach_btf_id_multi()` when the link is created.
- Checks made at attach:

| Program | Where | Sleepable program accepted when |
|---|---|---|
| `BPF_PROG_TYPE_KPROBE` | `__perf_event_set_bpf_prog()` | event is a uprobe |
| `BPF_PROG_TYPE_KPROBE` | `bpf_kprobe_multi_link_attach()` | never |
| `BPF_PROG_TYPE_TRACEPOINT` | `__perf_event_set_bpf_prog()` | syscall tracepoint |
| `BPF_PROG_TYPE_RAW_TRACEPOINT`, `BPF_TRACE_RAW_TP` | `bpf_raw_tp_link_attach()` | `tracepoint_is_faultable()` |
| `BPF_TRACE_ITER` | `bpf_iter_link_attach()` | `bpf_iter_target_support_resched()` |

- `BPF_TRACE_RAW_TP`: `bpf_check_attach_target()` also tests
  `tracepoint_is_faultable()` at load.
- `in_sleepable()`: returns only `env->cur_state->in_sleepable`; it does not
  read `prog->sleepable`.
- `env->cur_state->in_sleepable`: set per verification state, in
  `do_check_common()` from its `is_sleepable` argument (`prog->sleepable` in
  `do_check_main()`) and in `push_async_cb()` from `is_async_cb_sleepable()`.
- `is_async_cb_sleepable()`: false for a `struct bpf_timer` callback, true for
  a `struct bpf_wq` or task-work callback, whatever `prog->sleepable` is.
- Global subprogs: `do_check_subprogs()` verifies one once for each context
  (sleepable, non-sleepable) it is called from, taken from
  `in_sleepable_context()` at the call; see `called[]` and `verified[]` in
  `struct bpf_func_info_aux`.
- `in_sleepable_context()`: `!in_rcu_cs()`; false in a non-sleepable state and
  also inside an RCU, preempt-disabled or IRQ-saved region or with a lock held.
- `check_helper_call()`: tests `might_sleep` against `in_sleepable_context()`,
  not `in_sleepable()`.
- `check_kfunc_call()`: tests `KF_SLEEPABLE` twice, first against
  `in_sleepable()` and, after the RCU and preempt counters are updated,
  against `in_sleepable_context()`.
- `bpf_copy_from_user_proto`: `bpf_base_func_proto()` returns it whatever
  `prog->sleepable` is; only the `might_sleep` test rejects the call.
- Proto chosen by `prog->sleepable`: for example `BPF_FUNC_get_task_stack` in
  `bpf_base_func_proto()` picks `bpf_get_task_stack_sleepable_proto`.
- `specialize_kfunc()`: a third marking; a kfunc with no `KF_SLEEPABLE` gets
  its implementation chosen from `insn_aux_data[].non_sleepable`, for example
  `bpf_arena_alloc_pages()` and `bpf_arena_alloc_pages_non_sleepable()`.
- Maps: the switch in `check_map_prog_compatibility()` is wider than its
  error message, for example `BPF_MAP_TYPE_PROG_ARRAY`, `BPF_MAP_TYPE_QUEUE`
  and `BPF_MAP_TYPE_LPM_TRIE` are allowed.
- `__bpf_prog_map_compatible()` in `kernel/bpf/core.c`: an owner-tracked map
  such as a prog array takes only programs whose `sleepable` matches the first
  one.

**Object lifetime while sleepable**

- `__bpf_prog_enter_sleepable()`: makes no recursion check;
  `__bpf_prog_enter_sleepable_recur()` adds it with
  `bpf_prog_get_recursion_context()`, and `bpf_trampoline_enter()` picks by
  `bpf_prog_check_recur()`.
- Tasks Trace RCU: is SRCU on `rcu_tasks_trace_srcu_struct`; see
  `include/linux/rcupdate_trace.h`, where `call_rcu_tasks_trace()` is
  `call_srcu()`.
- Free paths such as `__bpf_prog_array_free_sleepable_cb()`,
  `bpf_selem_free_trace_rcu()` and `__free_rcu()` in `kernel/bpf/memalloc.c`:
  run from `call_rcu_tasks_trace()` and free in that callback, with no chained
  `call_rcu()`.
- `srcu_readers_active_idx_check()` in `kernel/rcu/srcutree.c`: runs
  `synchronize_rcu()` or `synchronize_rcu_expedited()` for
  `SRCU_READ_FLAVOR_SLOWGP`, which is why one wait covers non-sleepable
  programs too.
- Hash map values: `htab_elem_free()` uses `bpf_mem_cache_free()`, so a value
  pointer held across a sleep stays valid memory but may now belong to another
  element.
- `KF_RCU` argument: a trusted register passes without any RCU region; see
  the `KF_ARG_PTR_TO_BTF_ID` case in `check_kfunc_args()`.
- Runners other than the trampoline: take `rcu_read_lock_trace()` or
  `rcu_read_lock_tasks_trace()`, and `migrate_disable()`, themselves, for
  example `bpf_iter_run_prog()` and `__bpf_trace_run()`; search for
  `rcu_read_lock_trace`, `rcu_read_lock_tasks_trace` and
  `guard(rcu_tasks_trace)`.
- `bpf_prog_run_array_sleepable()` and `bpf_prog_run_array_uprobe()`: take
  `rcu_read_lock()` around each non-sleepable program in the array.
- **Potentially unsafe usage**: a helper or kfunc dereferencing an
  RCU-protected pointer without taking `rcu_read_lock()` itself.
  - Unsafe: when a sleepable program can call it outside an RCU region and the
    object is freed after `call_rcu()` or `kfree_rcu()` alone; the caller holds
    only `rcu_read_lock_trace()`.
  - Safe: the callee takes `rcu_read_lock()` and pins the object before
    unlocking, as `bpf_task_from_pid()` does.
  - Safe: the kfunc is flagged `KF_RCU_PROTECTED`, as `bpf_iter_task_new()`
    is; `check_kfunc_call()` rejects the call unless `in_rcu_cs()`.
  - Safe: the memory returns to slab only after Tasks Trace and the callee
    asserts `bpf_rcu_lock_held()`, as `__htab_map_lookup_elem()` does for
    elements that `__free_rcu()` frees.
- **Potentially unsafe usage**: freeing with `kfree_rcu()` or `call_rcu()`
  alone an object of a kind sleepable programs use.
  - Unsafe: when the object was published where a running sleepable program
    can find it and the code that reads it there takes no `rcu_read_lock()`;
    `__bpf_prog_enter_sleepable()` holds no classic RCU.
  - Safe: the object was never published, as the `alloc_selem` that
    `bpf_local_storage_update()` passes to `bpf_selem_free()` with `reuse_now`
    true.
  - Safe: the reader takes `rcu_read_lock()` before it loads the pointer, as
    `bpf_task_work_acquire_ctx()` does for the ctx that
    `bpf_task_work_destroy()` frees with `kfree_rcu()`.
  - Safe: `call_rcu_tasks_trace()`, as `bpf_selem_free()` does with
    `reuse_now` false.

**Locks held by a program**

- Lock state: all three kinds (`REF_TYPE_LOCK`, `REF_TYPE_RES_LOCK`,
  `REF_TYPE_RES_LOCK_IRQ`) are `refs[]` entries and share `active_locks`,
  `active_lock_id` and `active_lock_ptr` in `struct bpf_verifier_state`.
- `active_lock_id` and `active_lock_ptr`: name the most recently taken lock;
  `release_lock_state()` resets them to the previous lock entry.
- Unlock order: last in, first out across both lock kinds;
  `process_spin_lock()` fails with "cannot be out of order" otherwise.
- `process_spin_lock()`: tests no nesting depth for res locks.
- Helper and kfunc calls while `active_locks` is nonzero, for either lock
  kind: `do_check_insn()` allows only helpers `BPF_FUNC_spin_unlock` and
  `BPF_FUNC_kptr_xchg`, and kfuncs flagged `KF_SPINLOCK_SAFE`.
- `kfunc_spin_allowed()`: tests the `KF_SPINLOCK_SAFE` flag, not a fixed list;
  search for the flag, which also marks for example `bpf_arena_alloc_pages()`
  and `bpf_stream_vprintk()`.
- Mixing: `bpf_spin_lock()` cannot be taken with any lock held, since
  `BPF_FUNC_spin_lock` is not an allowed helper; `bpf_res_spin_lock()` can be
  taken while a `struct bpf_spin_lock` is held.
- Sleepable kfunc with `KF_SPINLOCK_SAFE`: still rejected under a lock,
  because `in_sleepable_context()` is false.
- `check_resource_leak()`: called with `check_lock` true for tail call,
  `BPF_LD_ABS`, `BPF_LD_IND` and `bpf_throw()`, and for `BPF_EXIT` only in
  frame 0; it then rejects when `active_locks` is nonzero.
- `BPF_EXIT` from a static subprog with a lock held: allowed; the caller
  inherits the lock.
- Program types, in `check_map_prog_compatibility()`:

| Map value has | Rejected for |
|---|---|
| `BPF_SPIN_LOCK` or `BPF_RES_SPIN_LOCK` | `BPF_PROG_TYPE_SOCKET_FILTER` |
| `BPF_SPIN_LOCK` | types in `is_tracing_prog_type()` |

- `is_tracing_prog_type()`: does not include `BPF_PROG_TYPE_TRACING`.
- While a lock is held: `in_rcu_cs()` is true, so a pointer load is typed as
  inside an RCU region (`MEM_RCU` where the field allows it), even in a
  sleepable program.
- Unlock: after `invalidate_non_owning_refs()`, `process_spin_lock()` calls
  `invalidate_rcu_protected_refs()` if no RCU-like region remains.
- RCU region counter in `struct bpf_verifier_state`: the field is
  `active_rcu_locks`.

**Context access**

- `check_ctx_access()`: checks the register offset itself;
  `check_mem_access()` has not done it before the call.
- Register offset allowed, by program type:

| Program | Register offset |
|---|---|
| `BPF_PROG_TYPE_SYSCALL` (`is_var_ctx_off_allowed()`) | variable, bounded by `U16_MAX` |
| no `convert_ctx_access` in its ops | constant, not negative |
| has `convert_ctx_access` | zero |

- `struct bpf_reg_state`: has no off member; the register offset is in
  `var_off`, constant when `tnum_is_const()` and then read as
  `var_off.value`; see `__check_ptr_off_reg()`.
- `off` passed to `is_valid_access()`: `insn->off` plus `reg_umax()` of the
  register, so for a syscall program it is called once with the largest offset.
- `off` can be negative, except for `BPF_PROG_TYPE_SYSCALL`: only the register
  part is tested for sign, so `is_valid_access()` must reject `off < 0`, as
  `kprobe_prog_is_valid_access()` does.
- Alignment: `check_ptr_alignment()` tests a context access only under strict
  alignment; `is_valid_access()` must test `off % size`.
- Stored value: known not to be a pointer only when `env->allow_ptr_leaks` is
  false.
- `BPF_ST` into the context: checked like `BPF_STX`, as `BPF_WRITE`;
  `bpf_convert_ctx_accesses()` passes `BPF_ST` and `BPF_STX` to the converter
  as `BPF_WRITE`.
- `struct bpf_insn_access_aux`: the reference field is `ref_id`;
  `check_mem_access()` copies it to the loaded register's `id`.
- `__check_ctx_access()`: for a `PTR_TO_BTF_ID` result it does not record
  `ctx_field_size`, which shares a union with `btf`, `btf_id` and `ref_id`.
- `__check_ctx_access()`: fails with "Reference may already be released" when
  `ref_id` is set and no longer in the reference state.
- Narrow write, in a type with `convert_ctx_access`: if `is_valid_access()`
  leaves `ctx_field_size` larger than the size of a `BPF_WRITE`,
  `bpf_convert_ctx_accesses()` fails with a verifier bug.
- `kprobe_prog_is_valid_access()`: accepts `BPF_WRITE` and sets
  `prog->aux->kprobe_write_ctx`; the attach decides:
  `__perf_event_set_bpf_prog()` rejects such a program unless the event is a
  uprobe, and `bpf_kprobe_multi_link_attach()` always rejects it.
- `gen_prologue`: must be set if any path can set `env->seen_direct_write`;
  `bpf_convert_ctx_accesses()` reports a verifier bug otherwise.

**Program lifetime**

- `__bpf_prog_put()`: takes one argument and only decrements and dispatches;
  the deferral test is `in_hardirq() || irqs_disabled()`.
- Final put from softirq, or with preemption off and IRQs on:
  `bpf_prog_put_deferred()` runs in place, not on a workqueue.
- `bpf_prog_put_deferred()`: sends the perf and audit unload events and calls
  `bpf_prog_free_id()`; kallsyms removal is in `__bpf_prog_put_noref()`.
- Sleepable program: `__bpf_prog_put_noref()` calls `call_rcu_tasks_trace()`
  only, with no chained `call_rcu()`.
- `__bpf_prog_put_rcu()`: does not free used maps; it frees `func_info`, the
  uid and the security blob, then calls `bpf_prog_free()`.
- `bpf_prog_free()`: always schedules `bpf_prog_free_deferred()`; the used
  maps and the JIT images are never freed in the grace-period callback.
- `bpf_prog_free()`: puts `aux->dst_prog` before scheduling, so when reached
  from `__bpf_prog_put_rcu()` that put runs in the grace-period callback.
- `bpf_prog_free_deferred()`: drops used maps, used BTFs and
  `dst_trampoline`, and frees the JIT images.
- `aux->work`: used twice, first for `bpf_prog_put_deferred()` when deferred,
  then for `bpf_prog_free_deferred()`.
- Load failure: `bpf_prog_load()` passes `prog->aux->real_func_cnt` as
  `deferred`, so a program whose subprogs were JITed still waits a grace
  period.
- `bpf_link_free()` with `dealloc_deferred`: makes one wait before
  `bpf_link_dealloc()` puts the program; tested in this order:

| Link | Wait |
|---|---|
| `link->sleepable` or `link->prog->sleepable` | `call_rcu_tasks_trace()` |
| tracepoint link (`bpf_link_is_tracepoint()`) | `call_tracepoint_unregister_atomic()` |
| other | `call_rcu()` |

- `bpf_link_free()` with only `dealloc`: puts the program at once, with no
  wait of its own.
- Non-sleepable program behind a sleepable link (`bpf_link_init_sleepable()`):
  the link's Tasks Trace wait comes first, then, if that put is the last, the
  program's own `call_rcu()`.

## Helpers and kfuncs

**Helper prototypes**

- Size argument types: there is no ARG_CONST_SIZE or ARG_CONST_SIZE_OR_ZERO
  here; `ARG_MEM_SIZE` and `ARG_MEM_SIZE_OR_ZERO` in `enum bpf_arg_type`
  (`include/linux/bpf.h`) do that job, see `arg_type_is_mem_size()`.
- `ARG_CONST_ALLOC_SIZE_OR_ZERO`: unchanged; it is the one size type that must
  be a constant.
- `ARG_PTR_TO_UNINIT_MEM`, `ARG_PTR_TO_MEM_OR_NULL`,
  `ARG_PTR_TO_FIXED_SIZE_MEM`: still defined, as enum values composed from
  `ARG_PTR_TO_MEM` plus flags.
- `arg_type`, `arg_btf_id`, `arg_size` in `struct bpf_func_proto`: arrays of
  `MAX_BPF_FUNC_ARGS` (12); `check_helper_call()` checks only the first
  `MAX_BPF_FUNC_REG_ARGS` (5).
- `check_func_proto()`: also runs `check_mem_arg_rw_flag_ok()` and
  `check_proto_release_reg()`; a failure is reported as a verifier bug for
  every call of the helper.
- `check_mem_arg_rw_flag_ok()`: every `ARG_PTR_TO_MEM` must carry `MEM_WRITE`
  or `MEM_RDONLY`.
- `check_proto_release_reg()`: at most one argument may carry `OBJ_RELEASE`.
- `check_args_pair_invalid()`: only `ARG_PTR_TO_MEM` may precede a size
  argument; it needs either a following size argument, or `MEM_FIXED_SIZE`
  with a non-zero `arg_size`, never both.
- Access type: `check_func_arg()` checks the buffer as `BPF_WRITE` only when
  the memory argument has `MEM_WRITE`, otherwise as `BPF_READ`.
- **Unsafe usage**: a helper body that writes through a memory argument
  whose prototype has `MEM_RDONLY` and no `MEM_WRITE`; read-only memory
  passes the check.
  - Safe: tag the argument `MEM_WRITE`, as `ARG_PTR_TO_UNINIT_MEM` does and
    as `bpf_xdp_fib_lookup_proto` does for `params`; `check_func_arg()` then
    checks the buffer as `BPF_WRITE` in `check_helper_mem_access()`.
- `ARG_ANYTHING`: accepts a pointer register when `env->allow_ptr_leaks`;
  `ARG_SCALAR` requires `SCALAR_VALUE` (used by `bpf_loop_proto`).
- `ARG_PTR_TO_BTF_ID` and `ARG_PTR_TO_BTF_ID_SOCK_COMMON`: `btf_ptr_types` and
  `btf_id_sock_common_types` accept a plain `PTR_TO_BTF_ID`, which may come
  from walking a struct and may be NULL at run time; the helper is left to
  test it, as `bpf_skc_to_tcp_sock()` in `net/core/filter.c` does for its
  `ARG_PTR_TO_BTF_ID_SOCK_COMMON` argument.

**Defining and registering a kfunc**

- `__bpf_kfunc`: expands to `__used __retain __noclone noinline`, in
  `include/linux/btf.h`.
- BTF annotations: `btf2btf()` in `tools/bpf/resolve_btfids/main.c` emits the
  `bpf_kfunc` decl tag for each entry of a `BTF_SET8_KFUNCS` set, not pahole.
- Function missing from BTF: `collect_kfuncs()` only warns `no BTF func for
  kfunc` and skips the entry.
- Hooks: `bpf_prog_type_to_kfunc_hook()` in `kernel/bpf/btf.c` maps several
  program types to one hook, so registering for one type offers the kfunc to
  every type on that hook.
- Program type with no case in `bpf_prog_type_to_kfunc_hook()`: maps to
  `BTF_KFUNC_HOOK_MAX` and `register_btf_kfunc_id_set()` returns `-EINVAL`.
- Module: `btf_populate_kfunc_set()` accepts one set per hook per module; a
  second registration on the same hook warns and returns `-EINVAL`.
- Module kfunc name: `btf_check_kfunc_name()` rejects a name that is already a
  function in vmlinux BTF or in another module's BTF.
- Return value 0: `check_btf_kconfigs()` returns 0 with nothing registered when
  a module has no BTF, or when vmlinux has none and `CONFIG_DEBUG_INFO_BTF`
  is off.
- Filter call site: `__btf_kfunc_is_allowed()`, reached from
  `bpf_fetch_kfunc_arg_meta()` through `btf_kfunc_is_allowed()`;
  `btf_kfunc_flags()` runs no filter.
- **Unsafe usage**: a `.filter` callback that returns non-zero for a
  `kfunc_id` that is not in its own set; `__btf_kfunc_is_allowed()` calls
  every filter on the hook for every kfunc on that hook.
  - Safe: return 0 first when `btf_id_set8_contains()` misses the own set, as
    `bpf_session_filter()` in `kernel/trace/bpf_trace.c` does.

**Kfunc flags**

| Flag | In this tree |
|---|---|
| `KF_RELEASE` | released argument is always argument 1: `bpf_fetch_kfunc_arg_meta()` sets `release_regno` to `BPF_REG_1` |
| `KF_SLEEPABLE` | rejected where `in_sleepable()` is false, and where `in_sleepable_context()` is false: RCU, preempt-off, IRQ-off region or a held lock |
| `KF_RCU_PROTECTED` | call rejected unless `in_rcu_cs()`; a returned pointer gets `MEM_RCU`, a struct pointer in place of `PTR_TRUSTED` |
| `KF_SPINLOCK_SAFE` | kfunc may be called while `active_locks` is non-zero; any other kfunc is rejected there, see `kfunc_spin_allowed()` |
| `KF_PERFMON` | `check_kfunc_call()` returns `-EPERM` unless `env->allow_ptr_leaks` (`CAP_PERFMON`) |
| `KF_IMPLICIT_ARGS` | `fetch_kfunc_meta()` takes the argument list from the BTF function named with the `_impl` suffix; `check_kfunc_args()` skips the arguments that `is_kfunc_arg_implicit()` finds beyond the public prototype |
| `KF_ARENA_RET`, `KF_ARENA_ARG1`, `KF_ARENA_ARG2` | `kernel/bpf/verifier.c` does not test them; `tools/bpf/resolve_btfids/main.c` uses them to tag BTF pointers with `address_space(1)` |

- KF_TRUSTED_ARGS: not defined in `include/linux/btf.h` and not mentioned in
  `Documentation/bpf/kfuncs.rst`.
- KF_DEPRECATED: `Documentation/bpf/kfuncs.rst` describes it; no header
  defines it.
- No section in `Documentation/bpf/kfuncs.rst`: `KF_SPINLOCK_SAFE`, the three
  arena flags, `KF_FASTCALL` and the three iterator flags.
- `KF_IMPLICIT_ARGS` prototype: `process_kfunc_with_implicit_args()` in
  `tools/bpf/resolve_btfids/main.c` adds the `_impl` function and cuts the
  public prototype at the first implicit parameter, so implicit parameters
  must be last.
- Implicit types: `is_kf_implicit_arg()` in
  `tools/bpf/resolve_btfids/main.c` accepts pointers to
  `struct bpf_prog_aux` and `struct btf_struct_meta`; the documentation names
  only the first.
- Inconsistent `KF_IMPLICIT_ARGS` across a kfunc's hook sets:
  `btf_kfunc_check_flag()` returns `-EINVAL`.

**Kfunc argument name suffixes**

- There is no __opt suffix here; `__nullable` marks an optional buffer, as in
  `bpf_dynptr_slice()` (`buffer__nullable`, `buffer__szk`).
- There is no __prog or __aux suffix here; `is_kfunc_arg_prog_aux()` matches
  any parameter of type `struct bpf_prog_aux *`, and the verifier loads
  `prog->aux` into that register.

| Suffix | What `check_kfunc_args()` does |
|---|---|
| `__szk` | must be a known constant, then checked against the buffer like `__sz`; not compared with the pointee size |
| `__ign` | skipped before every per-argument check, including the NULL and register-type checks |
| `__uninit` | acted on only for a `struct bpf_dynptr` argument |
| `__const_map` | register must be `CONST_PTR_TO_MAP` |
| `__map` | `CONST_PTR_TO_MAP` or a trusted `PTR_TO_BTF_ID` of `struct bpf_map` |
| `__nullable` | a known-NULL register skips all further checks of that argument |
| `__alloc` | accepted only for `bpf_obj_drop()` and `bpf_percpu_obj_drop()` kfuncs; any other kfunc is rejected |
| `__irq_flag` | `process_irq_flag()` returns `-EFAULT` for any kfunc other than the four IRQ save and restore kfuncs |
| `__nonown_allowed` | on a `struct bpf_list_node` argument, also accepts a non-owning reference |
| `__iter` | marks an iterator argument of a kfunc that has no `KF_ITER_NEW`, `KF_ITER_NEXT` or `KF_ITER_DESTROY` flag; iterator must be initialised |
| `__arena`, `__arena__nullable` | register must be `PTR_TO_ARENA` or any `SCALAR_VALUE`; program needs an arena and `bpf_jit_supports_arena_args()` |

- `__sz` and `__szk`: `get_kfunc_arg_type()` classifies the scalar by its
  suffix alone; `check_kfunc_args()` then checks the register of the argument
  before it as the buffer.
- There is no check_kfunc_mem_size_reg() here; `check_mem_size_reg()` serves
  helpers and kfuncs, and for kfuncs checks `BPF_READ | BPF_WRITE` with zero
  size allowed.
- Pointer with no size suffix after it, to a scalar: checked as memory of the
  pointee size (`MEM_FIXED_SIZE`). A pointer to a scalar-only struct is
  checked that way only when the register is neither `PTR_TO_BTF_ID` nor a
  `reg2btf_ids` type.
- One constant per call: `process_const_arg()` returns `-EFAULT` on a second
  `__k` or `__szk` argument.
- `__arena`: `is_kfunc_arg_nullable()` treats it as nullable, so a constant 0
  is accepted; the documentation says the body must not test it for NULL.
- No section in `Documentation/bpf/kfuncs.rst`: `__ign`, `__alloc`,
  `__refcounted_kptr`, `__irq_flag`, `__iter`; `__szk` appears only inside
  the `__nullable` section.
- Documentation example for `__nullable`: shows `bpf_task_release()` with
  `task__nullable`; in `kernel/bpf/helpers.c` its parameter is `p`, and NULL
  is rejected.

**Kfunc pointer argument guarantees**

- Offset: a constant, non-negative offset is accepted on a `PTR_TO_BTF_ID`
  argument; `btf_struct_ids_match()` then looks for the expected type at
  that offset.
- Offset must be 0 for the released argument and for a `__refcounted_kptr`
  argument, see `__check_func_arg_reg_off()`.
- Type match: not strict by default; a struct that embeds the expected type at
  the given offset matches.
- Strict match: only for a referenced register passed to a `KF_RELEASE`
  kfunc, or a `___init` no-cast alias, see `process_kf_arg_ptr_to_btf_id()`.
- Pointer to a struct made only of scalars: if the register is neither a
  `PTR_TO_BTF_ID` nor a `reg2btf_ids` type, `check_kfunc_args()` checks it as
  readable and writable memory of that size, so the body may receive program
  stack or map memory.
- **Unsafe usage**: a kfunc body that treats a pointer to a scalar-only
  struct as a kernel object the program cannot write.
  - Safe: a struct with a pointer member, as `struct cgroup` in
    `bpf_cgroup_ancestor()`; `__btf_type_is_scalar_struct()` fails, so
    `check_kfunc_args()` rejects a register that is neither `PTR_TO_BTF_ID`
    nor a `reg2btf_ids` type.

**Kfunc scalar and enum arguments**

- Constant is guaranteed only for these, see `get_kfunc_arg_type()`:
  - a scalar with the `__k` suffix
  - a scalar with the `__szk` suffix
  - a scalar named exactly `rdonly_buf_size` or `rdwr_buf_size`
- `rdonly_buf_size` and `rdwr_buf_size`: `process_const_alloc_mem_size()` also
  rejects a value above `U32_MAX`; `process_const_arg()` puts no bound on a
  `__k` or `__szk` value.
- `__sz` and `__szk` with a buffer that is not NULL: `check_mem_size_reg()`
  rejects a negative minimum and a maximum of `BPF_MAX_VAR_SIZ` or more.
- `__sz` or `__szk` with a NULL `__nullable` buffer: `check_kfunc_args()`
  skips the size check, so the body must not trust the size.
- `array_index_nospec()`: no kfunc in `kernel/bpf/helpers.c` calls it;
  `bpf_cgroup_ancestor()` relies on the two bounds tests alone.
- **Unsafe usage**: indexing an array with a signed scalar argument after
  testing only the upper bound; `check_kfunc_args()` checks only that the
  register is `SCALAR_VALUE`.
  - Safe: test both bounds first, as `bpf_cgroup_ancestor()` in
    `kernel/bpf/helpers.c` does for `int level` before it reads
    `cgrp->ancestors[level]`.
  - Safe: `scx_bpf_cpu_curr()` in `kernel/sched/ext/ext.c` passes `s32 cpu`
    to `scx_cpu_valid()`, which through `__cpu_valid()` tests `cpu >= 0` and
    `cpu < nr_cpu_ids`.
- `scx_bpf_cpu_rq()` is not defined under `kernel/sched/`; it is only declared
  in `tools/sched_ext/include/scx/common.bpf.h`. There is no
  kernel/sched/ext.c here; sched_ext kfuncs are under `kernel/sched/ext/`.
- `bpf_task_from_vpid()`: takes `s32 vpid` and looks it up; it indexes no
  array.

## Maps

**Map operations table**

- There is no find_and_alloc_map() here; `map_create_alloc()` in
  `kernel/bpf/syscall.c` looks up `bpf_map_types[]`, runs the checks and calls
  `map_alloc`.
- `map_mem_usage` NULL: `map_create_alloc()` returns `-EINVAL`, with no
  warning. The test runs after `map_alloc_check`, and on
  `bpf_map_offload_ops` when `attr->map_ifindex` is set.
- New map type: needs a `case` in the `switch (map_type)` of
  `map_create_alloc()`; the `default:` does `WARN()` and returns `-EPERM`.
- While `map_alloc` runs: `map->ops`, `refcnt` and `usercnt` are not yet set;
  `map_create_alloc()` sets them after `map_alloc` returns.
- `map_free` on a creation error: `bpf_map_free()` calls it directly from
  `map_create_alloc()` and `map_create()`, in the calling task, with no
  workqueue and no grace period. The exception is a `bpf_map_new_fd()`
  failure, which goes through `bpf_map_put_with_uref()`.
- Ops the system call calls with no NULL test: `map_get_next_key`,
  `map_delete_elem`, and `map_lookup_elem` and `map_update_elem` unless
  `bpf_map_copy_value()` or `bpf_map_update_value()` routes the `map_type`
  elsewhere first.
- A type may omit `map_update_elem` only if routed that way; for example
  `prog_array_map_ops` and `reuseport_array_ops` have none.
- `map_btf_id`: optional; without it only direct access to the map pointer
  fails, with `-ENOTSUPP` in `kernel/bpf/verifier.c`.
- Ops a program calls through the generic map helpers: the nine that
  `bpf_do_misc_fixups()` in `kernel/bpf/fixups.c` patches, which include
  `map_redirect` and `map_lookup_percpu_elem`.
- Patched call: with `prog->jit_requested` on 64-bit the program calls
  `ops->map_update_elem` and the others directly, so the helper body in
  `kernel/bpf/helpers.c` and its `WARN_ON_ONCE()` do not run.
- Patched call has no NULL test: an op must be non-NULL for every type the
  verifier lets reach its helper.
- `check_map_func_compatibility()`: its first `switch` ends in
  `default: break`, so a type with no `case` there is accepted for
  `bpf_map_lookup_elem()`, `bpf_map_update_elem()` and
  `bpf_map_delete_elem()`.
- Sleepable programs: `check_map_prog_compatibility()` rejects every map type
  not in its `switch`; a new type needs a `case` to be usable there.
- `kernel/bpf/hashtab.c` bucket lock: an `rqspinlock_t`; `struct bpf_htab` has
  no `map_locked` member, and `htab_lock_bucket()` never returns `-EBUSY`.
- `htab_lock_bucket()` failure: returns `-EDEADLK` or `-ETIMEDOUT`; update and
  delete return that error, and `htab_lru_map_delete_node()` returns false.
- `map_gen_lookup`: may return `-EOPNOTSUPP` to fall back to the call; any
  other count `<= 0` or `>= INSN_BUF_SIZE` fails the load with `-EFAULT`.
- **Potentially unsafe usage**: `map_lookup_elem` returning `ERR_PTR()`.
  - Unsafe: when `check_map_func_compatibility()` admits
    `BPF_FUNC_map_lookup_elem` for the type; `bpf_map_lookup_elem_proto` is
    `RET_PTR_TO_MAP_VALUE_OR_NULL`, so the program tests for NULL only.
  - Safe: when the type's `case` excludes `BPF_FUNC_map_lookup_elem`, as for
    `fd_array_map_lookup_elem()`; `bpf_map_copy_value()` tests `IS_ERR()`.
- Context the system call gives each op:

| Op | Called under |
|---|---|
| `map_get_next_key` | `rcu_read_lock()` |
| `map_lookup_elem_sys_only`, `map_lookup_elem` | `rcu_read_lock()`, `bpf_disable_instrumentation()` |
| `map_lookup_and_delete_elem` | `rcu_read_lock()`, `bpf_disable_instrumentation()` |
| `map_update_elem`, default branch | `rcu_read_lock()`, `bpf_disable_instrumentation()` |
| `map_update_elem` for `BPF_MAP_TYPE_CPUMAP`, `BPF_MAP_TYPE_ARENA`, `BPF_MAP_TYPE_STRUCT_OPS` | neither; may sleep |
| `map_delete_elem` for prog array and `BPF_MAP_TYPE_STRUCT_OPS` | neither; may sleep |
| `map_delete_elem`, other types | `rcu_read_lock()`, `bpf_disable_instrumentation()` |
| `map_push_elem`, `map_peek_elem` | `bpf_disable_instrumentation()` only |
| `map_pop_elem` | neither |
| batch ops, `map_release_uref`, `map_mmap`, `map_poll` | neither |

- `bpf_disable_instrumentation()`: raises `bpf_prog_active`, which only the
  kprobe, tracepoint and perf event paths test; see `kernel/trace/bpf_trace.c`.

**Memory for map elements**

- Preallocated per-CPU hash: `prealloc_init()` also calls
  `bpf_map_alloc_percpu()` once per element, besides the one
  `bpf_map_area_alloc()`.
- `alloc_htab_elem()` errors: `-E2BIG` when `__pcpu_freelist_pop()` returns
  NULL or the map is full, `-ENOMEM` when `bpf_mem_cache_alloc()` returns
  NULL.
- LRU update ops: `prealloc_lru_pop()` failure gives `-ENOMEM`.
- `__pcpu_freelist_pop()`: skips a list whose `raw_res_spin_lock()` fails, so
  `-E2BIG` can occur on a map that is not full.
- `bpf_mem_cache_free()`: the object is reusable on that CPU at once;
  `htab_elem_free()` uses it. An element given to `pcpu_freelist_push()` is
  reusable at once too.
- `bpf_mem_cache_free_rcu()`: reuse waits for one RCU grace period;
  `rhtab_delete_elem()` uses it.
- `alloc_bulk()`: refills first from `free_by_rcu_ttrace` and
  `waiting_for_gp_ttrace`, so an object can be reused before the tasks-trace
  grace period ends.
- Objects freed with `bpf_mem_cache_free()` or `bpf_mem_cache_free_rcu()`:
  return to slab only from `__free_rcu()`, after `call_rcu_tasks_trace()`, or
  while draining.
- `bpf_mem_alloc_set_dtor()`: the destructor runs in `free_all()` when an
  object returns to slab, not when the element is deleted.
- `htab_map_check_btf()`: sets that destructor for a non-preallocated hash,
  since `map->record` is not yet set during `map_alloc`.
- `kmalloc_nolock()` and `kfree_nolock()`: implemented in `mm/slub.c`;
  `bpf_map_kmalloc_nolock()` in `kernel/bpf/syscall.c` adds the memcg switch.
- `bpf_selem_alloc()` in `kernel/bpf/bpf_local_storage.c`: uses
  `bpf_map_kmalloc_nolock()`, not `struct bpf_mem_alloc`.
- `kmalloc_nolock()` limits: returns NULL for a size above
  `KMALLOC_MAX_CACHE_SIZE` and when `can_spin_trylock()` fails; under
  `CONFIG_DEBUG_VM` it warns on gfp bits other than `__GFP_ACCOUNT`,
  `__GFP_ZERO`, `__GFP_NOWARN`, `__GFP_NOMEMALLOC`.
- Verifier: has no preallocation test; a tracing program may use a map
  created with `BPF_F_NO_PREALLOC`.
- `map->objcg`: set only by `bpf_map_save_memcg()`, which `map_create()`
  calls after `map_alloc` has returned.
- `bpf_map_get_memcg()`: returns `root_mem_cgroup` when `map->objcg` is NULL,
  which is the case for `bpf_map_kmalloc_node()` and its siblings called
  from `map_alloc`.
- `bpf_map_area_alloc()`: sets no active memcg and takes `__GFP_ACCOUNT` from
  `bpf_memcg_flags()`, so it is for the creation path only.
- `memcg_bpf_enabled()` false: `bpf_map_save_memcg()` leaves `objcg` NULL and
  `bpf_memcg_flags()` adds nothing.
- Without `CONFIG_MEMCG`: `bpf_map_kmalloc_node()` and its siblings are macros
  for the plain allocators in `include/linux/bpf.h`.
- `bpf_map_kmalloc_node()`: is `kmalloc_node()` plus the memcg switch; it is
  no safer in program context than `kmalloc_node()`.
- **Potentially unsafe usage**: `kmalloc()`, `bpf_map_kmalloc_node()` or
  `kfree()` in an op that a program can reach.
  - Unsafe: when the verifier admits the op for kprobe, tracepoint or perf
    event programs, which can run in NMI or inside the slab allocator;
    `unit_alloc()` and `kmalloc_nolock()` exist to handle that case.
  - Safe: `bpf_mem_cache_alloc()`, as `alloc_htab_elem()` and
    `lpm_trie_node_alloc()` do.
  - Safe: `bpf_map_kmalloc_nolock()` with `kfree_nolock()`, as
    `__bpf_async_init()` in `kernel/bpf/helpers.c` does.
  - Safe: when the verifier admits `map_update_elem` only for the program
    types that `may_update_sockmap()` lists, none of them kprobe, tracepoint
    or perf event, as for `sock_hash_alloc_elem()`.

**Map lifetime**

- `bpf_map_put()` with `free_after_mult_rcu_gp`: calls
  `call_rcu_tasks_trace()` only; no `call_rcu()` follows, and there is no
  bpf_map_free_mult_rcu_gp() or rcu_trace_implies_rcu_gp() in this tree.
- `bpf_map_put()` on an ordinary map: waits for no grace period and goes
  straight to `bpf_map_free_in_work()`.
- `free_after_mult_rcu_gp` and `free_after_rcu_gp`: set only by
  `bpf_map_fd_put_ptr()` in `kernel/bpf/map_in_map.c`, on an inner map, when
  `need_defer` is true.
- Choice of flag: by the outer map's `sleepable_refcnt`, not the inner
  map's.
- `need_defer` false: `fd_htab_map_free()` and the error path of
  `bpf_fd_htab_map_update_elem()` pass it, so those puts set neither flag.
- `sleepable_refcnt`: a third count; `__add_used_map()` and
  `bpf_prog_bind_map()` raise it for a sleepable program and
  `__bpf_free_used_maps()` drops it.
- `bpf_map_put()`: warns if `sleepable_refcnt` is nonzero at the last put.
- `bpf_map_free_in_work()`: queues on `system_dfl_wq` with `queue_work()`.
- `bpf_map_free_deferred()` order: `security_bpf_map_free()`,
  `bpf_map_release_memcg()`, `bpf_map_owner_free()`, `bpf_map_free()`.
- `bpf_map_free()`: runs `map_free` under `migrate_disable()`, then
  `btf_record_free()` and `btf_put()`.
- `usercnt` holders: besides fds and bpffs pins, map iterators and sockmap
  links; search for `bpf_map_get_with_uref()` and `bpf_map_inc_with_uref()`.
- `bpf_map_get_fd_by_id()`: calls `__bpf_map_inc_not_zero(map, true)` under
  `map_idr_lock`, which tests `refcnt` only.
- `usercnt` can therefore go from 0 back to 1 while a program holds `refcnt`,
  and `map_release_uref` can run more than once for one map.
- `bpf_map_inc_not_zero()`: takes no uref and asserts
  `rcu_read_lock_held()`.
- `map_release_uref`: `cgroup_array_map_ops` and `perf_event_array_map_ops`
  have none; perf event array uses `map_release`, called per file from
  `bpf_map_release()`.
- `map_release_uref` on hash and array: `bpf_map_free_internal_structs()`
  frees `BPF_TIMER`, `BPF_WORKQUEUE` and `BPF_TASK_WORK` fields only, not
  kptrs.
- Per-CPU hash and per-CPU array ops: have no `map_release_uref`.
- `prog_array_map_clear()`: takes `bpf_map_inc()` and calls
  `schedule_work()`; the slots may still be set when `bpf_map_put_uref()`
  returns.
- `bpf_mem_alloc_destroy()`: with callbacks in flight, `destroy_mem_alloc()`
  copies the allocator and defers `rcu_barrier()` and
  `rcu_barrier_tasks_trace()` to a work item, so `map_free` does not wait.

**Per-CPU maps**

- `BPF_F_CPU` and `BPF_F_ALL_CPUS`: exist in `include/uapi/linux/bpf.h`; with
  either, `bpf_map_value_size()` returns `map->value_size`, one unrounded
  value.
- `BPF_F_CPU`: the CPU is `flags >> 32`; lookup copies that CPU's value,
  update writes that CPU only.
- `BPF_F_ALL_CPUS`: update only; writes the one value to every possible
  CPU.
- `bpf_map_check_op_flags()` in `include/linux/bpf.h`: `-EINVAL` for both
  flags together, for a map that is not per-CPU, or for upper bits without
  `BPF_F_CPU`; `-ERANGE` when the CPU is `>= nr_cpu_ids` or not possible.
- Allowed flags: lookup and lookup batch take `BPF_F_CPU`; update and update
  batch take both; see the callers of `bpf_map_check_op_flags()`.
- Lookup-and-delete: always uses the full layout, since
  `map_lookup_and_delete_elem()` calls `bpf_map_value_size(map, 0)`.
- `BPF_F_CPU` on a new hash element: `pcpu_init_value()` zeroes the other
  CPUs' values.
- From a program: per-CPU update ops return `-EINVAL` for flags above
  `BPF_EXIST`, so neither flag is available; see
  `htab_map_check_update_flags()`.
- `bpf_map_is_percpu_map()`: also lists
  `BPF_MAP_TYPE_PERCPU_CGROUP_STORAGE`, which uses the same system call
  layout; a program reaches it only through `bpf_get_local_storage()`.
- Full-layout lookup: copies `round_up(value_size, 8)` bytes per slot with
  `copy_map_value_long()`.
- Full-layout update: copies only `value_size` bytes from each slot with
  `copy_map_value()`; the padding in the buffer is ignored.
- Slot order: slot i is the i-th CPU of `for_each_possible_cpu()`, not the
  CPU number, when the possible mask has holes.
- Direct value access: for `BPF_MAP_TYPE_PERCPU_ARRAY` with
  `max_entries == 1`, `bpf_do_misc_fixups()` appends
  `BPF_MOV64_PERCPU_REG()` to the `ld_imm64`, giving this CPU's value with no
  lookup.
- That path needs `bpf_jit_supports_percpu_insn()`; otherwise
  `percpu_array_map_direct_value_addr()` returns `-EOPNOTSUPP`.
- Inlined `map_gen_lookup` on a per-CPU map: `bpf_do_misc_fixups()` sets
  `prog->jit_required`, so the program cannot fall back to the interpreter.
- `map_lookup_percpu_elem`: tests `cpu >= nr_cpu_ids` only, not
  `cpu_possible()`.
- Sleepable programs: also run with migration disabled; for example
  `__bpf_prog_enter_sleepable()` calls `migrate_disable()`.

## Stable ABI and conventions

**UAPI stability**

- Helper ids: not positional. Each `___BPF_FUNC_MAPPER` entry in
  `include/uapi/linux/bpf.h` carries its number as an explicit second
  argument, and `__BPF_ENUM_FN()` assigns it.
- New helpers: the list ends at `cgrp_storage_delete`, 211, followed by a
  comment that the list is "effectively frozen" and a kfunc should be added
  instead. `Documentation/bpf/bpf_design_QA.rst` words it more weakly ("generally
  added through the use of kfuncs"). Nothing in the build enforces the freeze;
  it is a review rule.
- `enum bpf_cmd`: `__MAX_BPF_CMD` is not the last enumerator.
  `BPF_COMMON_ATTRS = 1 << 16` follows it and is a flag ORed into `cmd`, which
  `__sys_bpf()` in `kernel/bpf/syscall.c` strips before the `switch`. A new
  command goes before `__MAX_BPF_CMD`.
- `bpf()` takes five arguments here (`SYSCALL_DEFINE5` in
  `kernel/bpf/syscall.c`); the last two are read only when `BPF_COMMON_ATTRS`
  is set.
- Enum size limit: `bpf_token_show_fdinfo()` in `kernel/bpf/token.c` has
  `BUILD_BUG_ON()` that `__MAX_BPF_CMD`, `__MAX_BPF_MAP_TYPE`,
  `__MAX_BPF_PROG_TYPE` and `__MAX_BPF_ATTACH_TYPE` are each below 64, because
  token and bpffs delegation masks are `u64` bitmaps indexed by enum value.
- `enum bpf_attach_type`: has 62 values here, so `__MAX_BPF_ATTACH_TYPE` is 62;
  a patch series that adds two or more attach types trips that
  `BUILD_BUG_ON()`.
- cgroup attach arrays: not indexed by `enum bpf_attach_type`. They are sized
  `MAX_CGROUP_BPF_ATTACH_TYPE` and indexed by `enum cgroup_bpf_attach_type`,
  mapped by `to_cgroup_bpf_attach_type()` in `include/linux/bpf-cgroup.h`. A
  new cgroup attach type needs an entry in both enums.
- `enum bpf_link_type`: values are written explicitly. A new value also needs a
  `BPF_LINK_TYPE()` line in `include/linux/bpf_types.h`, or
  `bpf_link_show_fdinfo()` (built under `CONFIG_PROC_FS`) hits `WARN_ONCE()`.
- Companion updates for a new prog, map, attach or link type:
  - `tools/include/uapi/linux/bpf.h` must match; `tools/lib/bpf/Makefile` only
    prints a warning when it differs.
  - name tables in `tools/lib/bpf/libbpf.c` (for example `attach_type_name[]`);
    `tools/testing/selftests/bpf/prog_tests/libbpf_str.c` walks the kernel BTF
    enum and fails on a missing name.
  - bpftool help and man pages, for a map type or a cgroup attach type;
    `tools/testing/selftests/bpf/test_bpftool_synctypes.py` compares them with
    `tools/include/uapi/linux/bpf.h`. It compares no prog type or link type
    with the header.

**Comment style**

- Style to use in new BPF code: the general kernel form, with `/*` alone on the
  first line, ` * ` on each following line and ` */` alone on the last.
- Written rule: `Documentation/process/coding-style.rst`, which shows that
  one form. The English file has no exception for `net/` or `drivers/net/`.
- Translations: `Documentation/translations/sp_SP/process/coding-style.rst` and
  `Documentation/translations/zh_TW/process/coding-style.rst` describe a
  separate `net/` form with text on the opening line; they do not match the
  English file.
- BPF documentation: no file under `Documentation/bpf/` states a comment style
  for kernel code. `Documentation/bpf/bpf_devel_QA.rst` and
  `Documentation/process/maintainer-netdev.rst` do not mention it.
- `Documentation/bpf/libbpf/libbpf_naming_convention.rst`: its `/**` rule is
  for libbpf API documentation comments only.
- `scripts/checkpatch.pl`: has no networking-specific comment-style check, and
  no comment check that tests the path for `kernel/bpf/`. Its
  `BLOCK_COMMENT_STYLE` warnings cover the leading `*`, its alignment and the
  trailing `*/`; they accept either opening line.
- Existing code is mixed: files such as `kernel/bpf/liveness.c` and
  `kernel/bpf/rqspinlock.c` mostly use the bare `/*` opening; files such as
  `kernel/bpf/core.c` and `kernel/bpf/verifier.c` mostly put text on the
  opening line. Text on the opening line in surrounding code is not a model
  for new comments.

## Selftests

**Test loader annotations**

- Mode: `spec->mode_mask` in `parse_test_spec()` in
  `tools/testing/selftests/bpf/test_loader.c`; `process_subtest()` runs one
  subtest per bit set.
- `__retval()`: sets the privileged bit; `__retval_unpriv()` and
  `__caps_unpriv()` set the unprivileged bit.
- `__stderr()`, `__stdout()`, `__stderr_unpriv()`, `__stdout_unpriv()`,
  `__log_level()`, `__flag()`, `__description()` and `__arch_x86_64`-style
  tags: select no mode.
- No annotation that sets the privileged bit, and one that sets the
  unprivileged bit: the program is not run privileged.
- No annotation at all: run privileged, and the load must succeed.
- There are no __priv, __unpriv, __msg_regex or __regex macros in
  `bpf_misc.h`; a regex is `{{...}}` inside any pattern, see
  `compile_regex()`.
- Tag text: `__test_tag()` puts `__COUNTER__` after `comment:`;
  `skip_decl_tag_pfx()` ignores a decl tag written without the number.
- `" @unpriv"`: appended to the program name for every unprivileged subtest,
  and to the `__description()` text too when there is one.
- Unprivileged covers the load only: `run_subtest()` calls
  `restore_capabilities()` before it dumps xlated or jited code and before
  `do_prog_test_run()`.
- Unprivileged subtest is skipped, not failed, when `get_unpriv_disabled()` in
  `unpriv_helpers.c` returns true (sysctl set, mitigations off, or kernel
  config unreadable), or for `BPF_F_ANY_ALIGNMENT` without
  `CONFIG_HAVE_EFFICIENT_UNALIGNED_ACCESS`.
- Unprivileged run: maps that `is_unpriv_capable_map()` rejects get
  `bpf_map__set_autocreate(map, false)`.
- Inheritance is per list and only into an empty list: one `__msg_unpriv()` or
  `__not_msg_unpriv()` stops every `__msg()` and `__not_msg()` from being
  copied to the unprivileged run.
- `__xlated()`, `__jited()`, `__stderr()`, `__stdout()`: each pattern must
  match on the line after the previous match, unless `"..."` stands between
  them; `__msg()` has no line rule.
- With no `__log_level()` and `test_progs` run without `-v`, the level is 0
  and a successful load leaves the log empty; a rejected load is logged at
  level 1.
- **Unsafe usage**: `__not_msg()` on a program that loads successfully, with
  no `__log_level()`.
  - Unsafe: the log is empty, so the pattern is absent whatever the verifier
    did.
  - Safe: with `__log_level(2)`, as in `progs/verifier_zext.c`.
- **Unsafe usage**: two or more `__not_msg()` in a row with no `__msg()`
  between them.
  - Unsafe: `match_negative_msgs()` searches for the first pattern of the run
    only; the later ones are never looked for.
  - Safe: one `__not_msg()` per gap between `__msg()` lines, as
    `__not_msg_unpriv()` between `__msg_unpriv()` lines in
    `unpriv_pseudo_func_policy()` in `progs/verifier_unpriv.c`.
- **Potentially unsafe usage**: `__stderr()` or `__stdout()` without
  `__retval()`.
  - Unsafe: when the program is tested only through `run_subtest()`; it reads
    the streams only inside the `should_do_test_run()` branch, so the
    patterns are never compared.
  - Safe: with `__success __retval(0)`, as in `progs/stream.c`.
  - Safe: `__stderr()` when the test runs the program itself and then calls
    `verify_test_stderr()`, as `run_libarena_asan_test()` in
    `prog_tests/libarena_asan.c` does.
- `__retval(POINTER_VALUE)`: the program is run but its return value is not
  compared.

**Verifier test files**

- `prog_tests/verifier.c` has two entry forms, and they differ in
  capabilities:

| Entry | Privileged subtests run with |
|---|---|
| `RUN(skel)` | `CAP_SYS_ADMIN` dropped by `run_tests_aux()` |
| `RUN_TESTS(skel)` | the full capabilities of `test_progs` |

- `RUN_TESTS()` in `verifier.c`: used by a few entries, for example
  `test_verifier_ctx()`; most use `RUN()`.
- `RUN()` passes no pre-execution callback; a test that needs map contents
  before a `__retval()` run calls `run_tests_aux()` itself, as
  `test_verifier_array_access()` does.
- `pre_execution_cb` runs only when the program is executed, after the load.
- Test collection: the `sed` rule for `tests.h` in
  `tools/testing/selftests/bpf/Makefile` matches only a line that starts
  with `void test_` or `void serial_test_`; a `static` function or a
  return type on its own line is not collected.
- Every `SEC()` program in the object becomes a subtest unless it is marked
  `__auxiliary` or `__auxiliary_unpriv`; an unannotated helper program is
  loaded privileged and must load.

**Assertion macros**

- Every `ASSERT_*` macro in `test_progs.h` expands to `CHECK()` with its own
  `static int duration`; both families fail through the same `_CHECK()` and
  `test__fail()`.
- `ASSERT_*` on success: prints the same PASS line as `CHECK()`.
- `ASSERT_*` on failure: prints `__func__`, the `name` argument, and, for
  the comparison macros such as `ASSERT_EQ()`, the values cast to
  `long long`; the expression is not stringified and the test name is not
  printed.
- **Potentially unsafe usage**: `ASSERT_FAIL()` as the only thing that marks
  a failure.
  - Unsafe: when nothing else fails the test; `ASSERT_FAIL()` expands to
    `CHECK(false, ...)`, which takes the pass branch of `_CHECK()`: no
    `test__fail()`, and the format string is not printed.
  - Safe: when the caller fails the test itself, as `process_subtest()` does
    with `PRINT_FAIL()` after `parse_test_spec()` returns an error.
  - Safe: `PRINT_FAIL()`, which calls `test__fail()` unconditionally.

**Skeleton file descriptors after load**

- Programs: after a successful load, `bpf_program__autoload()` true means
  `bpf_program__fd()` is a loaded program; `bpf_object__load_progs()` skips
  only subprograms and programs with autoload off.
- libbpf drops no program for being unreferenced or for a missing attach
  target; such an error fails the whole load.
- `bpf_program__fd()` on a program that was not loaded: returns `-ENOENT`.
- struct_ops programs: libbpf rewrites autoload during load.
  `bpf_object_adjust_struct_ops_autoload()` turns it on for a
  `SEC("?struct_ops")` program used by an autocreated map and off when no map
  that uses it is autocreated; `bpf_map__init_kern_struct_ops()` turns it off
  when the member is absent from kernel BTF or the slot was repointed.
- Maps with autocreate off: `bpf_map__fd()` still returns a non-negative fd
  after load. It is the memfd from `create_placeholder_fd()`, not a BPF map.
- Internal maps such as `.rodata` and `.bss`: `bpf_object__create_maps()`
  clears autocreate itself when the kernel lacks `FEAT_GLOBAL_DATA` or
  `FEAT_PERCPU_DATA`, so these can be placeholders without any call to
  `bpf_map__set_autocreate()`.
- **Potentially unsafe usage**: taking `bpf_map__fd(map) >= 0` after load as
  proof that the map exists in the kernel.
  - Unsafe: for a map with autocreate off the test passes and the fd is the
    placeholder.
  - Safe: test `bpf_map__autocreate()` first, as `run_subtest()` in
    `tools/testing/selftests/bpf/test_loader.c` does before
    `bpf_map__attach_struct_ops()`; `map_is_created()` in
    `tools/lib/bpf/libbpf.c` is what lets `bpf_map__fd()` return the
    placeholder.
  - Safe: a `SEC(".maps")` map of a skeleton that is opened and loaded in one
    call, as in `check_stack()` in
    `tools/testing/selftests/bpf/prog_tests/bpf_loop.c`;
    `bpf_object__add_map()` sets autocreate and nothing clears it.

## Model gaps

### Other mistakes models make

- Models take kfunc arguments to be classified inside `check_kfunc_args()`.
  Here `gen_kfunc_arg_proto()` first builds a `struct bpf_func_proto` of
  `enum kfunc_ptr_arg_type` values plus flags such as `PTR_MAYBE_NULL` and
  `MEM_FIXED_SIZE`.
- Models take subprograms and kfuncs to have at most five arguments. Here
  `MAX_BPF_FUNC_ARGS` is 12 for static subprograms and kfuncs: arguments past
  `MAX_BPF_FUNC_REG_ARGS` go in stack argument slots and need
  `bpf_jit_supports_stack_args()`; `check_max_stack_depth_subprog()` rejects
  a tail call when the subprogram that makes it, or a caller on its chain,
  has a nonzero `stack_arg_cnt`. A global subprogram stays at five.
- Models quote messages with "R%d" or "arg#%d". Here argument messages, for
  example in `check_kfunc_args()`, name the argument with `reg_arg_name()`,
  which prints a register argument as "R%d" and a stack argument as an
  R11-relative slot; `kernel/bpf/btf.c` still prints "arg#%d"; the helper
  sleep message is "sleepable helper %s#%d in %s".
- Models take `bpf_obj_new()` to be a macro over `bpf_obj_new_impl()`. Here
  it is a kfunc of its own flagged `KF_IMPLICIT_ARGS`, as is
  `bpf_wq_set_callback()`; see `kernel/bpf/helpers.c`.
- Models take `bpf()` to be a three-argument system call. Here `map_create()`
  takes a `struct bpf_common_attr` from the extra arguments and writes a log
  through it.
- Models do not know the register type `PTR_TO_INSN` or indirect jumps
  (`check_indirect_jump()`).
