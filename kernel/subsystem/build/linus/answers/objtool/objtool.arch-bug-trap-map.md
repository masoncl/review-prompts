| Decoder | `INSN_BUG` | `INSN_TRAP` |
|---|---|---|
| `tools/objtool/arch/x86/decode.c` | `ud2` (0f 0b), `ud1` (0f b9), `udb` (d6) | `int3` (cc) |
| `tools/objtool/arch/loongarch/decode.c` | `break 1`, `amswap.w $zero, $ra, $zero` | `break 0` |
| `tools/objtool/arch/powerpc/decode.c` | none | none |

- LoongArch `break` with any immediate other than 0 or 1: stays `INSN_OTHER`,
  for example `BRK_DIVZERO` (7).
- LoongArch `amswap.w`: typed `INSN_BUG` only with exactly those three
  registers; the tree does not say what emits it.
- powerpc: no trap instruction (tw, twi, trap) is typed; nothing in a
  powerpc object gets `dead_end` from the decoder.
