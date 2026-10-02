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
