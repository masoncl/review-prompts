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
