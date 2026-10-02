- Tests by name in `__dead_end_function()`: only `is_rust_noreturn()` and
  `global_noreturns[]`; `__stack_chk_fail` and `panic` are ordinary
  `NORETURN()` entries.
- `global_noreturns[]` lookup: linear `strcmp()` on the ELF symbol name; the
  order of `tools/objtool/noreturns.h` does not affect matching.
- Unlisted global, not weak, with a body in this object: gets the same body
  scan as a local function.
- Body scan: no path analysis; one `INSN_RETURN` anywhere in the function,
  reachable or not, means it returns.
- Sibling calls in the body scan: the first one met in the scan decides the
  result; later ones are not looked at.
- `ANNOTYPE_REACHABLE` on a call: clears the `dead_end` that
  `annotate_call_site()` set; `__annotate_late()` runs after
  `add_call_destinations()` for this reason. See the `ANNOTATE_REACHABLE`
  before `call \cfunc` in `arch/x86/entry/entry_64.S`.
- `__noreturn` function missing from `noreturns.h`, called from another
  object as the last instruction of the caller: the walk continues past the
  call; `do_validate_branch()` warns "falls through to next function" or
  "unexpected end of section".
- "%s() missing __noreturn in .c/.h or NORETURN() in noreturns.h": the
  opposite case; `validate_reachable_instructions()` prints it for unvisited
  code after a call that objtool already marked `dead_end`, so the compiler
  did not know the callee was noreturn.
- The two warnings never come from the same run:
  `validate_reachable_instructions()` is skipped when the walk warned.
