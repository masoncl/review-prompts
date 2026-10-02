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
