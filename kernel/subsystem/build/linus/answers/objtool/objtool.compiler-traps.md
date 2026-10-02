- `arch/loongarch/Makefile`: passes `-mno-check-zero-division` and
  `-fno-isolate-erroneous-paths-dereference` in `cflags-y`, under no
  configuration option; the line is after the `ifdef CONFIG_OBJTOOL` block,
  which holds only jump-table flags.
- Both flags are one `cc-option` argument: a compiler that rejects either
  gets neither.
- `arch/x86/Makefile` and `arch/powerpc/Makefile`: pass no flag of this kind.
- Top-level `Makefile`, under `CONFIG_RUST_INLINE_HELPERS`:
  `CC_FLAGS_RUST_INLINE_HELPERS` is `-mllvm -trap-unreachable -mllvm
  -no-trap-after-noreturn`; it asks for traps on unreachable paths, so the
  walk does not run into the next function, and for none after a noreturn
  call.
- `ignore_unreachable_insn()`, unvisited `INSN_BUG`: its type exempts it only
  when `prev_insn_same_sec()` has `dead_end`; an `INSN_JUMP_UNCONDITIONAL`
  whose `jump_dest` is `INSN_BUG` is treated the same.
- That `INSN_BUG` test is after `if (!func) return false`: an unvisited
  `INSN_BUG` outside any function gets no exemption from following a
  `dead_end` instruction.
- **Potentially unsafe usage**: a compiler or asm trap typed `INSN_BUG` that
  no path reaches.
  - Unsafe: when the instruction before it in the section is not `dead_end`,
    or the trap is outside any function, and no other test in
    `ignore_unreachable_insn()` returns true;
    `validate_reachable_instructions()` warns "unreachable instruction".
  - Safe: directly after a `dead_end` instruction inside a function, such as
    the `ud2` of `BUG()` or a call that `dead_end_function()` accepted;
    `ignore_unreachable_insn()` defines the test.
