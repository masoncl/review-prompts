- Walk structure: `validate_branch()` only wraps `do_validate_branch()`, which
  loops over `validate_insn()`; neither type has a `case` in `validate_insn()`.
- `dead_end` in the walk: `validate_insn()` returns it through `*dead_end`
  after the instruction is marked visited and given its CFI; the literal
  `if (insn->dead_end) return 0` is in `validate_unret()`, which stops there
  too.
- `INSN_TRAP` in the walk: not a dead end; the walk continues into the next
  instruction.
- `INSN_TRAP` reached as the last instruction of a function: the walk runs on
  and `do_validate_branch()` warns "falls through to next function", or
  "unexpected end of section" when the section ends there.
- `INSN_BUG` that continues at run time: keeps the type `INSN_BUG`;
  `ANNOTYPE_REACHABLE` on that instruction clears `dead_end` in
  `__annotate_late()`.
- Unvisited `INSN_BUG`: not exempt by type; see "Compiler-generated trap
  instructions" for the exemption.
- `validate_reachable_instructions()`: the name of the unreachable check
  here; there is no validate_unreachable_instructions().
- `validate_retpoline()` with `opts.cfi`: every instruction on
  `file->retpoline_call_list` inside an `STT_FUNC` or `STT_NOTYPE` symbol that
  is not `nocfi` needs `prev_insn_same_sym()` to be `INSN_BUG`, else "no-cfi
  indirect call!".
