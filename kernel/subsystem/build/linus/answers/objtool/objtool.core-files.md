| Job | File in this tree |
|---|---|
| Main pass | `check()` in `tools/objtool/check.c` |
| Reading special sections | `tools/objtool/special.c` reads only `.altinstructions`, `__jump_table`, `__ex_table` |
| Reading annotation and hint sections | `tools/objtool/check.c`: `read_annotate()`, `read_unwind_hints()`; not `special.c` |
| ORC generation | `tools/objtool/orc_gen.c`, built only with `BUILD_ORC` (set in `tools/objtool/Makefile` for x86 and loongarch), else `orc_create()` is the stub in `tools/objtool/weak.c`; entry encoding in `tools/objtool/arch/x86/orc.c` and `tools/objtool/arch/loongarch/orc.c` |
| Livepatch subcommands | `tools/objtool/builtin-klp.c` dispatches `checksum`, `diff`, `post-link` to `tools/objtool/klp-checksum.c`, `tools/objtool/klp-diff.c`, `tools/objtool/klp-post-link.c`; `tools/objtool/klp-sympos.c` serves `klp-diff.c` |
| Livepatch subcommands, when built | only with `BUILD_KLP` (x86 and host xxhash, `tools/objtool/Makefile`); else `cmd_klp()` is the stub in `tools/objtool/weak.c` |
| `--klp-symids` (check pass, not a subcommand) | `tools/objtool/klp-symid.c`, always built |
| Kernel-side `ANNOTATE_` macros | `include/linux/annotate.h`, included by `include/linux/objtool.h` |
| `STACK_FRAME_NON_STANDARD()`, `ASM_REACHABLE` | `include/linux/objtool.h` |
| Tools copy of the type numbers | `tools/include/linux/objtool_types.h`, compared by `tools/objtool/sync-check.sh`; there is no tools copy of `annotate.h` |
| Unwind-hint macros | generic `UNWIND_HINT` in `include/linux/objtool.h`; named hints in `arch/x86/include/asm/unwind_hints.h` and `arch/loongarch/include/asm/unwind_hints.h` |
| Documentation of the klp subcommands | no file; `tools/objtool/Documentation/objtool.txt` does not cover them; the driver script is `scripts/livepatch/klp-build` |
