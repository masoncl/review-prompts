- `sec->noinstr`: set in `decode_instructions()` in `tools/objtool/check.c` for
  `.noinstr.text`, `.entry.text`, `.cpuidle.text` and every section whose name
  starts with `.text..__x86.`.
- Sections walked: with `--noinstr` alone, `validate_noinstr_sections()` walks
  the first three only; when `validate_branch_enabled()` is true,
  `validate_functions()` walks every text section and `init_insn_state()`
  takes `state->noinstr` from `sec->noinstr`.
- Retpoline thunk call: not an allowed target. `add_retpoline_call()` makes it
  `INSN_CALL_DYNAMIC`, `insn_call_dest()` returns NULL, and it is checked as an
  indirect call.
- Indirect call: `noinstr_call_dest()` has one exemption, `pv_call_dest()`;
  there is no jump-table or IBT exemption.
- `pv_call_dest()`: accepts only a reloc against the symbol named `pv_ops`; a
  call through `pv_ops_lock` gets no exemption.
- `pv_ops` targets recorded: static initialisers (`add_pv_ops()`) and, in the
  x86 `arch_decode_instruction()`, `mov` stores in sections whose name starts
  with `.init.text`.
- `objtool_pv_add()`: skips targets named `_paravirt_nop` or
  `_paravirt_ident_64`; the kernel defines no symbol `_paravirt_nop` in this
  tree, `paravirt_nop` is `nop_func`, which is recorded.
- Static call: any global symbol whose name starts with
  `STATIC_CALL_TRAMP_PREFIX_STR` is accepted (`classify_symbols()`);
  `noinstr_call_dest()` does not look at what the trampoline calls.
- `__ubsan_handle_` name prefix: accepted from noinstr code.
- Calls to names starting `__sanitizer_cov_` from a noinstr section: with
  `--hacks=noinstr` (`CONFIG_HAVE_NOINSTR_HACK`), `annotate_call_site()`
  rewrites them to a NOP, or a RET for a tail call, so `validate_call()` never
  sees them.
- Encoding: there are no .discard.instr_begin or .discard.instr_end sections;
  `instrumentation_begin()` and `instrumentation_end()` add an entry to
  `.discard.annotate_insn` with type `ANNOTYPE_INSTR_BEGIN` or
  `ANNOTYPE_INSTR_END`, through `ANNOTATE_INSTR_BEGIN()` and
  `ANNOTATE_INSTR_END()` in `include/linux/annotate.h`.
- Without `CONFIG_NOINSTR_VALIDATION`: both macros are empty statements.
- Count: `instr` is an `s8` in `struct instruction` and `struct insn_state`;
  the only tests in `tools/objtool/check.c` are `state->instr <= 0` in
  `validate_call()` and `state->instr > 0` in `validate_return()`.
- Unmatched `instrumentation_end()`: no warning of its own, and not
  "unexpected end of section"; the count goes negative and a later single
  begin brings it only to 0, where calls are still checked by
  `noinstr_call_dest()`.
- Revisits: `validate_insn()` returns before adding `insn->instr` when the
  instruction was already visited with the same `uaccess` value, so it is not
  walked again for a different count.
