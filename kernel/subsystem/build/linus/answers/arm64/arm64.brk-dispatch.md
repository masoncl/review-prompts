- Path: `el1_brk64()` in `arch/arm64/kernel/entry-common.c` calls
  `do_el1_brk64()` in `arch/arm64/kernel/debug-monitors.c`, which calls
  the static `call_el1_break_hook()`.
- `call_el1_break_hook()`: an if-chain on `esr_brk_comment()`, most
  branches gated by `IS_ENABLED()`; it calls handlers named like
  `bug_brk_handler()` and `kasan_brk_handler()` directly.
- No match, or a handler returning anything but `DBG_HOOK_HANDLED`:
  `die("Oops - BRK", ...)`.
- There is no early BRK path: early_brk64 is only a leftover prototype in
  `arch/arm64/include/asm/traps.h`, with no definition and no caller.
- Handler prototypes sit outside the `#ifdef` of their option, as in
  `arch/arm64/include/asm/kprobes.h`, so the `IS_ENABLED()` branch compiles
  with the option off.
- `do_el1_brk64()` does not advance `regs->pc`; a handler that resumes
  after the BRK calls `arm64_skip_faulting_instruction()` itself, as
  `bug_brk_handler()` does.
- Annotations vary: `call_el1_break_hook()` and the kgdb handlers have
  `NOKPROBE_SYMBOL()`, the kprobes handlers are `__kprobes`, the handlers
  in `arch/arm64/kernel/traps.c` have neither.
- Masked ranges in `arch/arm64/include/asm/brk-imm.h`: `KASAN_BRK_MASK`,
  `UBSAN_BRK_MASK` and `CFI_BRK_IMM_MASK` each claim a block above their
  base; the kgdb range 0x400 - 0x7ff is reserved by the comment only.
- BRKs taken in nVHE hyp code do not reach `call_el1_break_hook()`;
  `nvhe_hyp_panic_handler()` in `arch/arm64/kvm/handle_exit.c` decodes the
  immediate itself.
- `tools/arch/arm64/include/asm/brk-imm.h` is a second copy of the header.
