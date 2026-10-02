- Models take most objtool complaints to be warnings that only
  `CONFIG_OBJTOOL_WERROR` makes fatal. In `tools/objtool/check.c` a message
  printed with `ERROR()` or `ERROR_INSN()` and followed by `return -1` fails
  the run without `--werror`, for example "unannotated intra-function call",
  "unsupported call to non-function", "UNWIND_HINT_IRET_REGS without ENDBR",
  "unsupported unwind_hint sp base reg", "unsupported relocation in
  alternatives section".
- Models take `delay-objtool` to be LTO or IBT only. `scripts/Makefile.lib`
  also lists `CONFIG_KLP_BUILD`, which is `def_bool y` under `LIVEPATCH &&
  HAVE_KLP_BUILD` in `kernel/livepatch/Kconfig`, so those kernels have
  `delay-objtool` set.
- Models do not know that `opts_valid()` in `tools/objtool/builtin-check.c`
  rejects `--noinstr`, `--ibt`, `--unret` and `--klp-symids` without `--link`,
  and that `objtool_run()` fails with "Linked object requires --link" on an
  object with more than one file symbol.
- Models do not know `OBJTOOL_VERBOSE`: `cmd_parse_options()` in
  `tools/objtool/builtin-check.c` sets `opts.verbose` when that environment
  variable is `1`.
- Models do not know that `objtool klp diff` needs the size of every
  special-section entry in the patched object. `create_fake_symbols()` in
  `tools/objtool/klp-diff.c` takes it from `ANNOTATE_DATA_SPECIAL`, from
  `sh_entsize`, or from a plain array of pointers, and otherwise fails with
  "missing special section entsize or annotations"; for example `UNWIND_HINT`
  and x86 `_BUG_FLAGS_ASM()` emit the annotation for that reason.
- Models do not know what `objtool klp` does when objtool was built without
  `BUILD_KLP`: the weak `cmd_klp()` in `tools/objtool/weak.c` prints "klp not
  implemented".
- Models name a sync-check make target. There is none;
  `tools/objtool/Makefile` runs `./sync-check.sh` directly.
