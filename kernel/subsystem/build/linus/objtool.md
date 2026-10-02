# Objtool

## Main structures

### Objects and how they relate

- `objtool klp`: a second job besides checking and annotating objects.
  `main()` in `tools/objtool/objtool.c` sends it to `cmd_klp()` in
  `tools/objtool/builtin-klp.c`, which has three subcommands (`checksum`,
  `diff`, `post-link`) that build a livepatch module from an original and a
  patched object.
- `BUILD_KLP`: set by `tools/objtool/Makefile` only for x86 with xxhash
  present; otherwise `cmd_klp()` is the weak stub in `tools/objtool/weak.c`
  and returns `ENOSYS`, and `struct checksum` is empty.
- `struct objtool_file`: one static instance in `tools/objtool/objtool.c`;
  used by `check()` and `cmd_klp_checksum()` only.
- `cmd_klp_diff()` and `cmd_klp_post_link()`: work on bare `struct elf`
  with no `struct objtool_file` and no decoded instructions; `struct elfs` in
  `tools/objtool/klp-diff.c` holds three at once (`orig`, `patched`, `out`).
- `decode_file()`: builds instructions, destinations, alternatives and hints;
  `check()` calls it and then validates; `cmd_klp_checksum()` calls it
  without `check()`, so no branch walk has run on what it reads.
- `struct instruction`: on no list of all instructions and not owned by its
  section; `call_node` only links it into one of the site lists of
  `struct objtool_file`. Allocated in arrays of `INSN_CHUNK_SIZE` and found
  through `file->insn_hash` with `find_insn()`.
- `fake` instruction: `handle_group_alt()` makes an `INSN_NOP` to pad a
  replacement shorter than the original; it has no bytes in the object and is
  not in `insn_hash`.
- `insn->_sym`: the symbol at the instruction's real location, set only in
  `decode_instructions()`; there is no sym field. `insn_sym()` and
  `insn_func()` map replacement code to the original's symbol at lookup
  time; `tools/objtool/klp-checksum.c` reads `_sym` directly to avoid that.
- `ALT_TYPE_JUMP_TABLE`: a `__jump_table` (jump label) entry, not a switch
  table. A switch table is recorded on the jumping instruction
  (`insn_jump_table()`) and `add_jump_table()` adds its targets to
  `insn->alts`.
- `alts_needed()` in `tools/objtool/check.c`: when false,
  `add_special_section_alts()` is skipped, so no `struct alt_group` exists
  and `insn->alts` holds switch-table targets only.
- `struct insn_state`: every instance is a local or a parameter of the walk;
  an instruction keeps only `insn->cfi` and the `insn->visited` bits.
- `df` in `struct insn_state`: the direction flag (`INSN_STD`, `INSN_CLD`);
  there is no IRQ-disable flag.
- `struct cfi_init_state`: the CFI at function entry, filled once by
  `arch_initial_func_cfi_state()` into `initial_func_cfi`; not a stack
  effect of an instruction.
- `struct orc_entry` inside an `alt_group`: `orc_create()` in
  `tools/objtool/orc_gen.c` builds it from `alt_group->cfi[]`, one slot per
  byte offset, not from `insn->cfi`.
- `orc_create()`: emits entries in section and offset order and does not
  sort them.
- `pfunc` and `cfunc` in `struct symbol`: never NULL; `elf_add_symbol()`
  points both at the symbol itself, so a function with no `.cold` part has
  `func == func->cfunc`.
- `struct symbol`: objtool's adjusted view, not a copy of the ELF entry.
  `type` is forced to `STT_FUNC` for `.cold` symbols, `len` of a parent can
  be smaller than `st_size`, and `name` has `KLP_TOMBSTONE_PREFIX` stripped;
  see `elf_add_symbol()` and `read_symbols()` in `tools/objtool/elf.c`.
- `twin` in `struct symbol`: links the same symbol in the `orig` and
  `patched` files, both ways; set by `correlate_symbols()`.
- `clone` in `struct symbol`: links a `patched` symbol and its copy in `out`,
  both ways; set by `__clone_symbol()`. `clone_reloc_klp()` also sets it, to
  the undefined weak tombstone symbol it creates in `out`, which is not a
  copy.
- `struct reloc`: stores no offset, addend or type; `reloc_offset()`,
  `reloc_addend()` and `reloc_type()` read the entry at `reloc_idx()` in the
  relocation section's data buffer.
- On-disk records that pass data between objtool runs:

| Structure | Section | Written by | Read by |
|---|---|---|---|
| `struct sym_checksum` | `.discard.sym_checksum` | `create_sym_checksum_section()` | `read_sym_checksums()` |
| `struct klp_reloc` | `KLP_RELOCS_SEC` plus `.` and object name | `cmd_klp_diff()` | `fix_klp_reloc_sec()` |
| `struct klp_symid` | `KLP_SYMID_SEC` | `klp_create_symid_sections()` | `klp_sympos_init()` |

- `klp_create_symid_sections()`: runs from `check()` under `--klp-symids`
  and does nothing unless `objname` ends in `vmlinux.o`.

## Where to look

**Core files**

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

**Build integration**

- `delay-objtool` in `scripts/Makefile.lib`: set by `CONFIG_LTO_CLANG`,
  `CONFIG_X86_KERNEL_IBT` or `CONFIG_KLP_BUILD`.
- `cmd_objtool`, `cmd_cc_o_c` and `cmd_as_o_S`: defined in
  `scripts/Makefile.lib`, not `scripts/Makefile.build`.
- `scripts/Makefile.build`: holds `is-standard-object`, the target-specific
  `objtool-enabled` settings, `cmd_ld_multi_m` and `cmd_rustc_o_rs`.
- Run points with `delay-objtool` set:

| Object | Where objtool runs |
|---|---|
| Built-in code | once on `vmlinux.o`, `scripts/Makefile.vmlinux_o` |
| Multi-object module | on the linked module `.o`, `$(multi-obj-m)` rule in `scripts/Makefile.build` |
| Single-object module | at compile time, through `is-single-obj-m` |

- `scripts/Makefile.modfinal`: has no module-wide objtool run and does not
  use `vmlinux-objtool-args-y`; nothing named prelink exists in `scripts/`.
- `objtool-enabled := y` in `scripts/Makefile.lib` is the default for
  makefiles that do not override it: `scripts/Makefile.modfinal` runs objtool
  on each `%.mod.o` and on `.module-common.o` (with `--module`),
  `scripts/Makefile.vmlinux` on, for example, `.vmlinux.export.o`.
- Rust objects: `cmd_rustc_o_rs` in `scripts/Makefile.build` and
  `cmd_rustc_library` in `rust/Makefile` end with `$(cmd_objtool)`.
- `arch/x86/boot/startup/Makefile`: sets `objtool-enabled` and
  `objtool-args` itself for `$(pi-objs)`; they run per object with `--noabs`
  even under `delay-objtool`, then with `--dry-run` in place of
  `objtool-args-y`.
- **Potentially unsafe usage**: `OBJECT_FILES_NON_STANDARD` to keep objtool
  off an object.
  - Unsafe: with `delay-objtool` set, for an object that is linked into
    `vmlinux.o` or into a multi-object module; the `vmlinux.o` and
    `$(multi-obj-m)` runs do not consult `is-standard-object`, so the code is
    still processed.
  - Safe: for an object that is linked into neither `vmlinux` nor a module,
    as the `lib-y` objects in `arch/x86/boot/startup/Makefile`, whose `lib.a`
    is in neither `KBUILD_VMLINUX_OBJS` nor `KBUILD_VMLINUX_LIBS` (top-level
    `Makefile`); the only run left is the per-object one, which
    `is-standard-object` in `scripts/Makefile.build` gates.
- `--prefix=`: gated by `CONFIG_CALL_PADDING`, value
  `CONFIG_FUNCTION_PADDING_BYTES`; there is no PREFIX_SYMBOLS Kconfig symbol.
- `--noinstr` and `--unret`: added only in `scripts/Makefile.vmlinux_o`,
  never in `objtool-args-y`; objtool rejects both without `--link`
  (`opts_valid()`).
- Without `delay-objtool`, the `vmlinux.o` run gets only `--werror`,
  `--noinstr`, `--unret`, `--klp-symids` and `--link`; `objtool-args-y` is
  not passed.
- objtool has no --vmlinux option; the linked-object mode is `--link`.
- `objtool-args-` block in `scripts/Makefile.lib`: also has `--cfi` and
  `--fineibt` (inside `ifdef CONFIG_CALL_PADDING`), `--hacks=skylake`, and
  `--no-unreachable` for `CONFIG_GCOV_KERNEL` or `CONFIG_KCOV`.
- `--klp-symids`: added in `scripts/Makefile.vmlinux_o` from the make
  variable `KLP_SYMIDS`, which `scripts/livepatch/klp-build` passes; no
  Kconfig symbol.
- `--backtrace`: passed by no kbuild file; extra options reach objtool
  through the `OBJTOOL_ARGS` environment variable, read by
  `cmd_parse_options()` in `tools/objtool/builtin-check.c`.

## Annotations

**Annotation sections**

- `decode_file()` in `tools/objtool/check.c`: does all the reading; there is no
  decode_sections() in this tree.
- `include/linux/annotate.h`: defines `ASM_ANNOTATE()`, `ASM_ANNOTATE_LABEL()`,
  the asm `ANNOTATE` macro and every generic `ANNOTATE_` macro; x86
  `ANNOTATE_UNRET_SAFE` is an alias in `arch/x86/include/asm/nospec-branch.h`.
- `include/linux/objtool.h`: includes `include/linux/annotate.h` and defines
  `UNWIND_HINT`, `STACK_FRAME_NON_STANDARD`, `STACK_FRAME_NON_STANDARD_FP`,
  `ASM_REACHABLE` and `VALIDATE_UNRET_BEGIN`.
- `read_unwind_hints()`: runs after `read_annotate()` with `__annotate_early()`
  and with `__annotate_ifc()`, and before `read_annotate()` with
  `__annotate_late()`.
- `read_unwind_hints()` tests `insn->noendbr`, which only `__annotate_early()`
  sets; moving `ANNOTYPE_NOENDBR` to `__annotate_late()` breaks that test.
- `.discard.annotate_data`: a second annotation section with the same 8-byte
  entry layout and its own type numbers; `ANNOTATE_DATA_SPECIAL` writes it.

**Annotation types**

| Type | Macro | What objtool does |
|---|---|---|
| `ANNOTYPE_NOENDBR` (1) | `ANNOTATE_NOENDBR`, `ANNOTATE_NOENDBR_SYM()` | sets `insn->noendbr`; `validate_ibt()` accepts references to it; also passes the ENDBR test in `read_unwind_hints()` |
| `ANNOTYPE_RETPOLINE_SAFE` (2) | `ANNOTATE_RETPOLINE_SAFE`; x86 `ANNOTATE_UNRET_SAFE`, `VALIDATE_UNRET_END` | error unless the instruction is an indirect jump, indirect call, return or NOP; `validate_retpoline()` and `validate_sls()` skip it; on a NOP it ends the `validate_unret()` walk |
| `ANNOTYPE_INSTR_BEGIN` (3) | `ANNOTATE_INSTR_BEGIN()`, from `instrumentation_begin()` | `insn->instr++` |
| `ANNOTYPE_INSTR_END` (4) | `ANNOTATE_INSTR_END()`, from `instrumentation_end()` | `insn->instr--` |
| `ANNOTYPE_UNRET_BEGIN` (5) | `ANNOTATE_UNRET_BEGIN`, `VALIDATE_UNRET_BEGIN` | sets `insn->unret`; `validate_unrets()` starts there under `--unret` |
| `ANNOTYPE_IGNORE_ALTS` (6) | `ANNOTATE_IGNORE_ALTERNATIVE` | marks one alternative arm as not followed; see below |
| `ANNOTYPE_INTRA_FUNCTION_CALL` (7) | `ANNOTATE_INTRA_FUNCTION_CALL` | error unless `INSN_CALL`; the call becomes `INSN_JUMP_UNCONDITIONAL` and keeps its stack op |
| `ANNOTYPE_REACHABLE` (8) | `ANNOTATE_REACHABLE` | clears `insn->dead_end` |
| `ANNOTYPE_NOCFI` (9) | `ANNOTATE_NOCFI_SYM` | sets `nocfi` on the symbol that contains the instruction; error "dodgy NOCFI annotation" if there is none |
| `ANNOTYPE_DATA_SPECIAL` (1) | `ANNOTATE_DATA_SPECIAL` | goes to `.discard.annotate_data`; marks the start of a special-section entry for `tools/objtool/klp-diff.c` |

- `ANNOTYPE_DATA_SPECIAL`: its value 1 is in a separate number space; it does
  not collide with `ANNOTYPE_NOENDBR` because the section differs.
- `ANNOTYPE_IGNORE_ALTS`: `handle_group_alt()` copies `insn->ignore_alts` of
  the first original instruction to the original `struct alt_group`, and of
  the first replacement instruction to the replacement group.
- `skip_alt_group()`: makes `validate_insn()` stop at an instruction whose
  group has `ignore` set; the other arms are still validated.
- Annotation on the original arm: the replacements are followed and the
  original is not, as `smap_save()` in `arch/x86/include/asm/smap.h` needs.
- Annotation on the replacement arm: the original is followed and that
  replacement is not, as `ASM_CLAC_UNSAFE` needs.
- Comment above `ANNOTATE_IGNORE_ALTERNATIVE` in `include/linux/annotate.h`:
  describes only the second case.
- `ANNOTYPE_NOCFI`: only `validate_retpoline()` tests `nocfi`, under
  `--retpoline` and `--cfi`, to suppress "no-cfi indirect call!" for calls
  inside that symbol.
- `ANNOTATE_INSTR_BEGIN()` and `ANNOTATE_INSTR_END()`: C only; the asm forms
  are commented out in `include/linux/annotate.h`.

**Reachability annotations**

- `ANNOTATE_REACHABLE`: goes on the dead-end instruction itself, the `ud2` or
  the `call` to a noreturn function, not on the instruction after it.
- C form `ANNOTATE_REACHABLE(label)`: `label` must be the label of the
  dead-end instruction; x86 `ARCH_WARN_REACHABLE` passes `1b`, the `ud2` in
  `_BUG_FLAGS()`.
- Asm form `ANNOTATE_REACHABLE`: takes no argument and annotates the next
  instruction emitted, as before `call \cfunc` in `arch/x86/entry/entry_64.S`.
- `dead_end` is set in two places: `decode_instructions()` for `INSN_BUG`, and
  `annotate_call_site()` for a non-sibling call when `dead_end_function()` is
  true.
- `__dead_end_function()`: matches `tools/objtool/noreturns.h` by name for
  non-local symbols only; it also treats any non-weak function defined in the
  object as noreturn when its body has no `INSN_RETURN` and no sibling call.
- Running off the end of a function: not a dead end; `do_validate_branch()`
  warns "falls through to next function".

**Sections that macros write**

- `ASM_REACHABLE`: writes `.discard.reachable`; no file under `tools/objtool`
  names that section, and the macro has no users.
- `UNWIND_HINT`: besides `.discard.unwind_hints` it writes
  `.discard.annotate_data` through `ANNOTATE_DATA_SPECIAL`; `check()` does not
  read that section.
- `.discard.annotate_data`: read only by `create_fake_symbols()` in
  `tools/objtool/klp-diff.c`, which `tools/objtool/Build` compiles only with
  `BUILD_KLP`.

**Callable and non-callable asm**

- ELF type: set by the END macro, not the START macro; `SYM_FUNC_END` passes
  `SYM_T_FUNC` and `SYM_CODE_END` passes `SYM_T_NONE` to `SYM_END()`.
- x86 `SYM_FUNC_START` in `arch/x86/include/asm/linkage.h`: emits no ENDBR;
  only `SYM_TYPED_FUNC_START` does.
- UNWIND_HINT_EMPTY: not in this tree; use `UNWIND_HINT_UNDEFINED` or
  `UNWIND_HINT_END_OF_STACK` from `arch/x86/include/asm/unwind_hints.h`.
- Warnings that fire only for code inside an `STT_FUNC` symbol (the test is
  `func` or `insn_func()`):
  - "return with modified stack frame"
  - "sibling call from callable instruction with modified stack frame"
  - "call without frame pointer save/setup"
  - "unsupported instruction in callable function"
  - "undefined stack state"
  - "redundant UACCESS disable" and "redundant CLD"
  - "falls through to next function"
  - "BP used as a scratch register"; `update_cfi_state()` sets `bp_scratch`
    only under `--stackval` for an instruction with `insn_func()`
  - "unsupported call to non-function", an error in `add_call_destinations()`
  - "is missing an ELF size annotation", from `validate_symbol()`, which
    `validate_section()` calls for `STT_FUNC` symbols only
- Not specific to either kind: "unsupported stack register modification",
  "unsupported stack pointer realignment", "stack state mismatch" and
  "unannotated intra-function call".

**Adding an annotation type**

- Unknown type in `.discard.annotate_insn`: `__annotate_late()` reports
  "Unknown annotation type: %d" with `ERROR_INSN()` and returns -1; objtool
  exits non-zero even without `--werror`.
- `__annotate_early()` and `__annotate_ifc()`: ignore types they do not
  handle, so a type handled there still needs a `case` in `__annotate_late()`.
- Unknown type in `.discard.annotate_data`: `create_fake_symbols()` in
  `tools/objtool/klp-diff.c` skips the entry silently.
- Unknown unwind hint type: `read_unwind_hints()` does not reject it; it
  copies `hint->type` to `cfi.type`.
- `init_orc_entry()`: the only place that reports "unknown unwind hint type",
  and it runs only under `--orc`; x86 and loongarch each have one, in
  `tools/objtool/arch/x86/orc.c` and `tools/objtool/arch/loongarch/orc.c`.
- `UNWIND_HINT_TYPE_FUNC`, `UNWIND_HINT_TYPE_SAVE`, `UNWIND_HINT_TYPE_RESTORE`:
  have no `ORC_TYPE_` value; `read_unwind_hints()` consumes them, so they never
  reach `init_orc_entry()`.
- Change to `struct unwind_hint`: `read_unwind_hints()` fails with
  "struct unwind_hint size mismatch" when the section size is not a multiple
  of the size in the copy.
- `tools/include/linux/objtool_types.h`: the only copy of the type header;
  `include/linux/objtool.h` and `include/linux/annotate.h` have no copy under
  `tools/`.
- `orc_types.h` copies: `tools/arch/x86/include/asm/orc_types.h` and
  `tools/arch/loongarch/include/asm/orc_types.h`.
- `tools/objtool/sync-check.sh`: run as the first recipe line of the
  `$(OBJTOOL_IN)` rule in `tools/objtool/Makefile`.

**Header copy comparison**

- `include/linux/objtool_types.h`: compared for every `SRCARCH`; every other
  file only when `SRCARCH` is `x86`.
- Files compared: read `FILES` and `SYNC_CHECK_FILES` in
  `tools/objtool/sync-check.sh`; the x86 list here also has
  `include/linux/interval_tree_generic.h` and
  `include/linux/livepatch_external.h`.
- A difference: prints "Warning: Kernel ABI header at ... differs from latest
  version at ..." to stderr and the build goes on.
- SKIP_SYNC_CHECK: not in this tree, and the script does not look at git.
- `tools/objtool/sync-check.sh`: exits 0 without comparing when `../../kernel`,
  `../../tools` or `../objtool` is not a directory.
- objtool is compiled against the copy (`-I$(srctree)/tools/include` in
  `tools/objtool/Makefile`), so a patch that changes only the kernel header
  builds with a warning and objtool keeps the old values.

**Skipping validation**

- `add_ignores()`: sets `ignore` on the function's `struct symbol` and on its
  `cfunc`; `struct instruction` has no ignore flag.
- Skipped for an ignored function: everything that runs through
  `validate_branch()` (stack and CFI rules, uaccess, noinstr), the
  "unannotated intra-function call" and "unsupported call to non-function"
  errors, and "unreachable instruction".
- Not skipped: `validate_retpoline()`, `validate_ibt()`, `validate_sls()`,
  `validate_unrets()` and the site sections that `check()` creates; none of
  them tests `ignore`.
- Relocation against a section symbol: `add_ignores()` uses
  `find_func_by_offset()`, and skips the entry without a message when no
  function starts there.
- **Unsafe usage**: `STACK_FRAME_NON_STANDARD` on a symbol that is not
  `STT_FUNC`, such as code closed with `SYM_CODE_END`.
  - Unsafe: `add_ignores()` fails with "unexpected relocation symbol type" for
    any symbol type other than `STT_FUNC` and `STT_SECTION`.
  - Safe: on a symbol closed with `SYM_FUNC_END`, as `clear_bhb_loop` in
    `arch/x86/entry/entry_64.S`.
- Asm `STACK_FRAME_NON_STANDARD_FP`: defined only under `CONFIG_OBJTOOL`; the
  other branch of `include/linux/objtool.h` gives empty asm macros for
  `UNWIND_HINT` and `STACK_FRAME_NON_STANDARD` only.
- `is-standard-object`: defined in `scripts/Makefile.build`; a per-file value
  of `n` overrides a directory value of `y`.
- `is-kernel-object` in `scripts/Makefile.lib`: also required by
  `is-standard-object`, so an object outside `real-obj-y`, `lib-y` and
  `real-obj-m` gets no per-object objtool run whatever the variable says,
  unless its Makefile sets `objtool-enabled` itself, as
  `arch/x86/boot/startup/Makefile` does.
- With `delay-objtool`: `OBJECT_FILES_NON_STANDARD` is still honoured for a
  single-object module (`is-single-obj-m`); it is not consulted for
  `vmlinux.o` or for `$(multi-obj-m)`, so built-in code is validated anyway.
- Without `delay-objtool` but with `CONFIG_NOINSTR_VALIDATION`:
  `scripts/Makefile.vmlinux_o` still runs objtool on `vmlinux.o` with
  `--noinstr`, and that run does not consult `OBJECT_FILES_NON_STANDARD`.
- `OBJECT_FILES_NON_STANDARD` users: a search finds a handful of Makefiles,
  for example `arch/x86/platform/pvh/Makefile`, which sets it for `head.o`,
  a built-in object, and so is not an example of safe use (see "Build
  integration"); no Makefile for purgatory, realmode or vDSO code sets it.

## Trap instructions and dead ends

**BUG and trap instruction types**

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

**Per-architecture BUG and trap encodings**

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

**Kernel BUG and WARN macros**

- `ANNOTATE_REACHABLE(1b)` on x86 and `ANNOTATE_REACHABLE(10001b)` on
  LoongArch: the label is on the trap instruction itself, not on the
  instruction after it.
- Section used: `.discard.annotate_insn`, read by `read_annotate()`.
- x86-64 `WARN()` with a format and `WARN_ONCE()` under
  `HAVE_ARCH_BUG_FORMAT_ARGS`: no trap at the call site;
  `__WARN_print_arg()` emits `static_call_mod(WARN_trap)(...)`.
- That static call for objtool: a call to a static-call trampoline;
  `annotate_call_site()` returns for `sym->static_call_tramp` before it
  consults `dead_end_function()`, so the site is never a dead end.
- `__WARN_trap()` in `arch/x86/entry/entry.S`: `ANNOTATE_REACHABLE`, then
  `ud1 (%edx), %_ASM_ARG1`, then `RET`; the `ud1` is `INSN_BUG` and the
  annotation keeps the `RET` reachable.
- Run time: `__static_call_transform()` in `arch/x86/kernel/static_call.c`
  patches such call sites to that `ud1` (`warninsn`); objtool never sees it
  at the call site.
- `ud2` plus `ARCH_WARN_REACHABLE`: what x86 `WARN_ON()`, `WARN_ON_ONCE()`
  and `__WARN()` emit through `__WARN_FLAGS()`.

**Compiler-generated trap instructions**

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

**Functions that do not return**

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

**Rust noreturn functions**

- `is_rust_noreturn()`: returns false at once unless the name starts with
  `_R`; there is no configuration or per-object guard, it runs for every
  non-local symbol passed to `__dead_end_function()`.
- Local-binding Rust symbol: never reaches `is_rust_noreturn()`; only the
  body scan in `__dead_end_function()` applies.
- Match list: longer than the `core::panicking` entries; it also covers, for
  example, `_4core6option13expect_failed`, `_4core3str16slice_error_fail` and
  three `_4core3num` radix panics. Read the function before adding a line.
- `rust_begin_unwind`: matched twice; the mangled suffix
  `_7___rustc17rust_begin_unwind` in `is_rust_noreturn()`, and the plain name
  as `NORETURN(rust_begin_unwind)` in `tools/objtool/noreturns.h`.
- `tools/objtool/noreturns.h` does hold Rust-side names: `rust_begin_unwind`
  and `rust_helper_BUG`.
- `rust_build_error`: exported under that plain name by
  `rust/build_error.rs`, and not listed in `tools/objtool/noreturns.h`.
- Adding a function: a mangled name needs a new `str_ends_with()` or
  `strstr()` line in `is_rust_noreturn()`; a plain name (`#[export_name]`,
  `#[no_mangle]`, or a C helper under `rust/helpers/`) needs `NORETURN()`.

## Objtool diagnostics

**Warnings and errors**

- `--werror`: the option is spelled in lower case; it sets `opts.werror`, see
  `check_options[]` in `tools/objtool/builtin-check.c`.
- `CONFIG_OBJTOOL_WERROR`: adds `--werror` through
  `objtool-args-$(CONFIG_OBJTOOL_WERROR)` in `scripts/Makefile.lib`.
- `scripts/Makefile.vmlinux_o`: adds `--werror` itself, also for
  `CONFIG_OBJTOOL_WERROR`, only in the `else` branch of
  `ifeq ($(delay-objtool),y)`; with `delay-objtool` it inherits
  `objtool-args-y`.
- `CONFIG_OBJTOOL_WERROR` in `lib/Kconfig.debug`: `depends on OBJTOOL &&
  !COMPILE_TEST` and has no `default`, so a config with `CONFIG_COMPILE_TEST`
  set cannot enable it.
- Warning count: the macros in `tools/objtool/include/objtool/warn.h` keep no
  count; `check()` adds up the return values of the validators in a local
  `warnings`. There is no global counter.
- `WARN()` in a function that returns 0: printed, not counted, does not fail the
  build under `--werror`; for example "file already has .ibt_endbr_seal,
  skipping" in `create_ibt_endbr_seal_sections()`.
- Warning-severity macros: `WARN()`, `WARN_FUNC()`, `WARN_INSN()`. The ELF and
  libc forms exist only as `ERROR_ELF()` and `ERROR_GLIBC()`.
- `WARN_STR`: is "error" when `opts.werror` is set, so under
  `CONFIG_OBJTOOL_WERROR` a warning line reads `error: objtool:` like a fatal
  one.
- `ERROR_INSN()`: plain `ERROR_FUNC()`; it does not test or set `sym->warned`
  and does not call `BT_INSN()`. Only `WARN_INSN()` prints once per symbol.
- `BT_INSN()`: prints when `opts.verbose || opts.backtrace`.
- After a counted warning: `do_validate_branch()` stops for that function; the
  rest of its path is not validated, the next function is.
- Warnings without `--werror`: `check()` returns `ret`, still 0, so
  `objtool_run()` goes on to `elf_write()`.
- End of `check()` with `opts.verbose`: prints "%d warning(s) upgraded to
  errors" (only with `opts.werror`) and calls `disas_warned_funcs()`; it does
  not print the command line.
- `disas_warned_funcs()`: empty stub in `tools/objtool/include/objtool/disas.h`
  when `DISAS` is not defined.
- `.orig` copy: made by `make_backup()` only with `--backup` (`opts.backup`),
  whenever `ret || warnings`, so also for warnings that are not upgraded.
- `make_backup()`: also prints the original command line itself, with the
  object replaced by `<obj>.orig -o <obj>` when `opts.output` is not set; there
  is no `print_args()` under `tools/objtool`.
- `--backup`: nothing in this tree passes it; `cmd_parse_options()` reads extra
  options from the `OBJTOOL_ARGS` environment variable.
- `.DELETE_ON_ERROR`: defined in `scripts/Kbuild.include`, which
  `scripts/Makefile.build` and `scripts/Makefile.vmlinux_o` include.

**Common warnings**

- `tools/objtool/Documentation/objtool.txt` explains 12 numbered entries. It has
  no entry for the retpoline, noinstr, DF, "return with modified stack frame",
  "return with UACCESS enabled" or "undefined stack state" messages.

| # | Documented text | Printed in | Kind | Printed text differs |
|---|---|---|---|---|
| 1 | call without frame pointer save/setup | `validate_insn()` | counted | `func+0x..`, no `()` |
| 2 | unreachable instruction | `validate_reachable_instructions()` | counted | same |
| 3 | missing __noreturn ... | `validate_reachable_instructions()` | counted | same |
| 4a | can't find starting instruction | `decode_instructions()` | fatal `ERROR()` | `error:` |
| 4b | can't decode instruction | `arch_decode_instruction()` in `tools/objtool/arch/x86/decode.c` | fatal `ERROR()` | `error:`, "at `<sec>:0x<off>`", no symbol prefix |
| 5 | unsupported instruction in callable function | `validate_insn()` | counted | `func+0x..` |
| 6 | sibling call ... modified stack frame | `validate_sibling_call()` | counted | `func+0x..` |
| 7 | stack state mismatch | `insn_cfi_match()` | counted | appends `: cfa1=...`, `reg1[..]`, `type1=` or `drap1=` |
| 8 | falls through to next function | `do_validate_branch()` | counted | same, plain `WARN()` |
| 9 | call to funcB() with UACCESS enabled | `validate_call()` | counted | `funcA+0x..: call to ...`, not `funcA() call to` |
| 10 | stack layout conflict in alternatives | `propagate_alt_cfi()` | counted | has `objtool:`; appends `: <location>` |
| 11 | unannotated intra-function call | `add_call_destinations()` | fatal `ERROR_INSN()` | `error: objtool: func+0x..:` prefix |
| 12 | not an indirect call target | nowhere | - | no code in the tree has the string |

- Entry 1: tested only with `opts.stackval`, only after `validate_call()`
  returned 0, and not for `is_special_call()` destinations.
- Entry 2: runs only when `validate_functions()` and `validate_unwind_hints()`
  together returned 0, see `if (!w)` in `check()`.
- Entries 2 and 8: suppressed when `file->ignore_unreachables` is set, which
  `--no-unreachable` does; `scripts/Makefile.lib` passes it for
  `CONFIG_GCOV_KERNEL` or `CONFIG_KCOV`.
- Entry 2 fix in the documentation: annotate with `SYM_FUNC_START` and
  `SYM_FUNC_END`, or `SYM_CODE_START` plus unwind hints. The noreturn fix
  belongs to entry 3.
- Entry 3: printed instead of entry 2 when the previous instruction is
  `dead_end` and has a call destination.
- Entry 5, `iret`: the documentation names it, but inside an `STT_FUNC` symbol
  `arch_decode_instruction()` in `tools/objtool/arch/x86/decode.c` does not make
  it `INSN_SYSRET`.
- Entry 6: the documentation says "branch to an UNDEF symbol";
  `is_sibling_call()` also covers a jump to the first instruction of another
  function in the same file, and an indirect jump that is not a jump table.
- Entry 6 fix in the documentation: unwind hints, move the destination into the
  file, or `SYM_CODE_START` with hints. It does not mention
  `STACK_FRAME_NON_STANDARD`.
- Entry 8 fix in the documentation: add the callee to the noreturn list, remove
  a wrong `unreachable()`, or look for undefined behaviour.
- Entry 8, `global_noreturns`: exists, as a static array in
  `__dead_end_function()`, filled from `tools/objtool/noreturns.h` through
  `NORETURN()`.
- Entry 9: `validate_call()` tests noinstr first; the callee name is
  `pv_ops[N]` or `{dynamic}` for an indirect call, see `call_dest_name()`.
- Entry 10: `propagate_alt_cfi()` returns -1, but `validate_insn()` returns 1,
  so it is a counted warning. It is reported at the first instruction of the
  original group.
- Entry 12: the nearest code is in `create_ibt_endbr_seal_sections()`: with
  `opts.module`, `init_module` or `cleanup_module` on `file->endbr_list` gives
  the fatal `ERROR()` "Magic init_module() function name is deprecated, use
  module_init(fn) instead".
- Macro names in the documentation: `SYM_FUNC_START`, `SYM_FUNC_END`,
  `SYM_CODE_START`, `SYM_CODE_END`; it has no older names.
- Under `--werror` every counted row above prints `error:` (see "Warnings and
  errors").

## Noinstr and uaccess

**Noinstr validation**

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

**Calls from noinstr code**

- Call through a retpoline thunk: treated as an indirect call, so accepted
  only inside a begin/end region; its reloc is against the thunk, so
  `pv_call_dest()` does not accept it.
- Tail call: `validate_sibling_call()` runs `validate_call()` and not
  `validate_return()`; with the count above 0 it is accepted, with no
  "return with instrumentation enabled" warning.
- Noreturn callee: the call itself is still checked by `validate_call()`, but
  the walk stops at `insn->dead_end`, so no `instrumentation_end()` is needed
  after it.
- `instrumentation_end()` emits: a numeric label from `__COUNTER__`, a `nop`,
  and an `ANNOTATE_INSTR_END()` entry that refers back to the label with
  `__ASM_BREF()`. It emits no reachable annotation.
- `instrumentation_begin()`: emits the same label and `nop`; only the
  annotation type differs.
- Example of a bracketed region in `kernel/entry/common.c`:
  `irqentry_nmi_enter()`. `irqentry_enter()` has no begin/end of its own in
  this tree; the regions are in the inline helpers in
  `include/linux/irq-entry-common.h`.

**Uaccess validation**

- `--uaccess`: passed for `CONFIG_HAVE_UACCESS_VALIDATION` in
  `scripts/Makefile.lib`; there is no CONFIG_X86_SMAP in this tree.
- `INSN_STAC` and `INSN_CLAC`: produced only by
  `tools/objtool/arch/x86/decode.c`.
- `validate_call()`: has three tests only (noinstr, uaccess, DF); it has no
  `__fentry__` test.
- DF: `INSN_STD` and `INSN_CLD` in `validate_insn()` are not gated by
  `opts.uaccess`, so the DF checks run in every `validate_branch()` walk.
- Inside a safe-listed function, `validate_return()` with access off: warns
  "return with UACCESS disabled from a UACCESS-safe function".
- Inside a safe-listed function, `INSN_CLAC` with `uaccess_stack` empty: warns
  "UACCESS-safe disables UACCESS".
- `uaccess_safe_builtin`: holds no `memcpy`, `memset`, `__memcpy` or
  `__memset` entry.
- Flags save and restore: tracked in `handle_insn_ops()`, not in
  `update_cfi_state()`, and only when `opts.uaccess` is set and the
  instruction has `alt_group` set.
- `alt_group`: `handle_group_alt()` sets it on the original instructions of an
  alternative as well as on the replacement.
- `pushf` or `popf` outside any alternative: updates the CFI stack state only;
  `state->uaccess` and `uaccess_stack` do not change.
- `ASM_STAC_UNSAFE` and `ASM_CLAC_UNSAFE` in `arch/x86/include/asm/smap.h`:
  carry `ANNOTATE_IGNORE_ALTERNATIVE` in the replacement, so `skip_alt_group()`
  drops it and objtool sees no change of access.

**Calls with user access enabled**

- What objtool tests: the state at each RET and call instruction, not the C
  `return` statement; a `return` written inside the region is accepted if
  access is ended before the RET.
- **Potentially unsafe usage**: a fault label that returns without calling
  `user_access_end()`.
  - Unsafe: when the region was opened directly with `user_access_begin()` or
    a read/write variant and nothing ends access between the faulting access
    and the RET; `validate_return()` warns "return with UACCESS enabled".
  - Safe: when the region is a scope such as
    `scoped_user_write_access_size()` and the label is outside it;
    `__scoped_user_access()` in `include/linux/uaccess.h` ends access through
    `__cleanup` when the scope is left, as in `filldir()` in `fs/readdir.c`.
  - Safe: when the label is inside an `__always_inline` helper and the caller
    ends access after the helper, as `strncpy_from_user()` does with
    `user_read_access_end()` after `do_strncpy_from_user()`.
- Indirect call in the region, retpoline thunk call included: always warns,
  because `func_uaccess_safe()` returns false for a NULL symbol.
- `tools/objtool/Documentation/objtool.txt`, before adding funcB to
  `uaccess_safe_builtin`: funcB "obviously does not call schedule(), and is
  marked notrace". It states no other condition.
- Other fixes the document lists first: remove the call from the region, or
  put the correct guards around the low-level access helpers.
- Enforced by objtool, not by the document: `validate_symbol()` starts a
  listed function with access on, so each call in its body must target a
  listed function or lie between `user_access_save()` and
  `user_access_restore()`, as in `kasan_report()` in `mm/kasan/report.c`.

## Stack validation and unwind hints

**Unwind hint types**

- `struct unwind_hint` in `include/linux/objtool_types.h`: has no sym_offset
  field, and `struct instruction` has no unwind_hint member; the
  per-instruction state is the bits `hint`, `save`, `restore` and the pointer
  `cfi`.
- `UNWIND_HINT_TYPE_END_OF_STACK`: becomes `ORC_TYPE_END_OF_STACK`, not
  `ORC_TYPE_UNDEFINED`; see `init_orc_entry()` in
  `tools/objtool/arch/x86/orc.c`.
- `sp_reg`, `sp_offset`, `signal`: `read_unwind_hints()` reads them only for
  `UNWIND_HINT_TYPE_END_OF_STACK`, `UNWIND_HINT_TYPE_CALL`,
  `UNWIND_HINT_TYPE_REGS` and `UNWIND_HINT_TYPE_REGS_PARTIAL`; for the other
  four types it moves to the next hint first.
- `UNWIND_HINT_TYPE_FUNC`: the instruction gets `func_cfi`, built by
  `set_func_state()` from `arch_initial_func_cfi_state()`, with type
  `UNWIND_HINT_TYPE_CALL`. The `ORC_REG_SP` and 8 that x86 `UNWIND_HINT_FUNC`
  passes are not used.
- `UNWIND_HINT_TYPE_UNDEFINED`: the instruction gets `force_undefined_cfi`;
  while `force_undefined` is set `update_cfi_state()` returns before looking
  at any stack op, until another hint replaces the state.
- CFA base `CFI_UNDEFINED` without `force_undefined`: the next stack op inside
  an `STT_FUNC` warns "undefined stack state".
- `UNWIND_HINT_TYPE_SAVE`: clears `hint` and sets `save`, so the instruction
  keeps the tracked state, `validate_unwind_hints()` does not start a walk
  there, and it does not count for the tests of `next_insn->hint`.
- `UNWIND_HINT_TYPE_RESTORE`: keeps `hint` set; `read_unwind_hints()` leaves
  `cfi` unset and `validate_insn()` fills it from the instruction with `save`.
- "UNWIND_HINT_IRET_REGS without ENDBR": only for
  `UNWIND_HINT_TYPE_REGS_PARTIAL`, not `UNWIND_HINT_TYPE_REGS`; needs `--ibt`,
  a global symbol starting at the instruction, an instruction that is not
  `INSN_ENDBR` and has no `noendbr`. It is an `ERROR_INSN()` and
  `read_unwind_hints()` returns -1.
- x86 `UNWIND_HINT_ENTRY` in `arch/x86/include/asm/unwind_hints.h`: emits
  `VALIDATE_UNRET_BEGIN` and `UNWIND_HINT_TYPE_END_OF_STACK`; no hint type is
  specific to entry.
- loongarch `UNWIND_HINT_FUNC` in `arch/loongarch/include/asm/unwind_hints.h`:
  emits `UNWIND_HINT_TYPE_CALL` with `ORC_REG_SP`, not
  `UNWIND_HINT_TYPE_FUNC`.

**Stack validation rules**

- "unsupported stack state": no such warning under `tools/objtool`; a bad
  frame at return is "return with modified stack frame" from
  `validate_return()`.
- `ASM_CALL_CONSTRAINT`: is `"+r" (current_stack_pointer)` in
  `arch/x86/include/asm/asm.h`; `current_stack_pointer` is the register
  variable declared on the line above it.
- `ASM_CALL_CONSTRAINT`: defined with no configuration test, so it is the same
  with and without frame pointers; only x86 defines it.
- Frame-pointer-only checks: the two checks behind `opts.stackval` in
  `tools/objtool/check.c`: "call without frame pointer save/setup" in
  `validate_insn()`, and setting `bp_scratch` in `update_cfi_state()`, which
  `validate_return()` reports as "BP used as a scratch register".
- `--stackval`: passed for `CONFIG_STACK_VALIDATION` in `scripts/Makefile.lib`;
  that option depends on `HAVE_STACK_VALIDATION && UNWINDER_FRAME_POINTER` in
  `lib/Kconfig.debug`. `CONFIG_FRAME_POINTER` alone does not pass it.
- "call without frame pointer save/setup": not raised when
  `is_special_call()` is true (call to a symbol with `fentry` or
  `embedded_insn`), nor outside an `STT_FUNC`.
- Saved registers at return: `has_modified_stack_frame()` compares every
  entry of `regs` with `initial_func_cfi`, in every mode; it is not a
  frame-pointer-only check.
- Every other stack check: runs in every walk, that is over all text when
  `validate_branch_enabled()` is true (`--stackval`, `--orc` or `--uaccess`),
  and over the noinstr sections with `--noinstr` alone
  (`validate_noinstr_sections()`).
- Indirect jump inside a function: the stack walk needs no annotation for it;
  `is_sibling_call()` takes an `INSN_JUMP_DYNAMIC` with no jump table as a
  sibling call, so it needs the entry stack state.
- `INSN_SYSCALL` and `INSN_SYSRET` in a function: "unsupported instruction in
  callable function" only when the next instruction has no `hint`.
- `iret` inside an `STT_FUNC`: decoded in `tools/objtool/arch/x86/decode.c` as
  a stack op that adds 40 to the stack pointer, not as `INSN_SYSRET`.
- `STACK_FRAME_NON_STANDARD_FP()` in `include/linux/objtool.h`: expands to
  `STACK_FRAME_NON_STANDARD()` only under `CONFIG_FRAME_POINTER`, and to
  nothing otherwise, so the function is still validated for ORC.

**Alternatives and the stack state**

- "stack layout conflict in alternatives": raised by `propagate_alt_cfi()`,
  which `validate_insn()` calls for each walked instruction of a group;
  `handle_group_alt()` raises no stack warning.
- What is compared: the state on entry to an instruction against what another
  variant recorded at the same byte offset from the group start; an offset
  where only one variant has an instruction start is not compared.
- Meaning of "same": `cficmp()` over every field of `struct cfi_state` except
  `hash`, which includes `stack_size`, `vals` and `signal`;
  `insn_cfi_match()` compares less.
- `skip_alt_group()`: called after `propagate_alt_cfi()` and after every
  entry of `insn->alts` was walked; when it returns true the walk of the
  group that holds the current instruction ends there.
- A variant that is not followed: only its first instruction reaches the
  shared `cfi` array; stack changes later in that variant are not checked.
- CLAC/STAC rule: when the first instruction of the first entry of
  `insn->alts` is `INSN_CLAC` or `INSN_STAC` and its group is not ignored, the
  original is not followed and the replacement is.
- CLAC/STAC rule: `skip_alt_group()` does not test the type of the original
  instruction and does not test `opts.uaccess`.
- No other condition selects one variant: besides the CLAC/STAC rule only
  `ANNOTATE_IGNORE_ALTERNATIVE` does, through the `ignore` test in
  `skip_alt_group()` (see "Annotation types"); there are no skip_orig or
  skip_alt fields in `struct special_alt`, and no test of a feature bit such
  as POPCNT or SMAP under `tools/objtool`.
- `arch_handle_alternative()` in `tools/objtool/arch/x86/special.c`: only
  makes `orig_len` equal across nested alternatives at one address.
- Jump-label and exception-table entries: both paths are followed;
  `skip_alt_group()` returns false for an instruction with no `alt_group`.
- "unsupported relocation in alternatives section": needs
  `arch_pc_relative_reloc()` true and `arch_support_alt_relocation()` false;
  the x86 `arch_support_alt_relocation()` returns true always; the loongarch
  one returns false always, but the loongarch `arch_pc_relative_reloc()`
  returns false always too.

## Model gaps

### Other mistakes models make

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
