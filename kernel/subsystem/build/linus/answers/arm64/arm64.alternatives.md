- Replacement location: `.subsection 1` of the section that holds the
  original; arm64 does not use an `.altinstr_replacement` section.
- `get_alt_insn()` rewrites: immediate branches (`aarch64_insn_is_branch_imm()`)
  whose target is outside the replacement, and `adrp`.
- `get_alt_insn()` hits `BUG()` for the rest of
  `aarch64_insn_uses_literal()`: `adr`, `ldr` literal, `ldrsw` literal and
  `prfm` literal. The `BUG()` fires only at patch time on a system that has
  the cap.
- Rewritten branch range: not checked; `aarch64_insn_encode_immediate()` masks
  the new offset, so a short-range branch that no longer reaches is encoded
  wrong silently.
- Length mismatch: caught at assembly by the `.org` directives, and by
  `BUG_ON()` in `__apply_alternatives()`; the "<= orig_len" comment on
  `alt_len` in `struct alt_instr` does not hold.
- `ALTERNATIVE_CB()` entry: `alt_len` must be 0 (`BUG_ON()`), and `alt_offset`
  holds the callback.
- Callback in a module's alternatives: must satisfy `core_kernel_text()`,
  else `apply_alternatives_module()` returns `-ENOEXEC` and the load fails.
- `__init` callback: fails that test once `system_state` reaches
  `SYSTEM_FREEING_INITMEM`, so a module loaded after that cannot use it.
- `noinstr` on a callback: not enforced; in-tree callbacks are a mix, for
  example `kvm_update_va_mask()` is `__init`, `kvm_patch_vector_branch()` is
  plain, `alt_cb_patch_nops()` is `noinstr`.
- Callback used by nVHE hyp code: needs a `KVM_NVHE_ALIAS()` line in
  `arch/arm64/kernel/image-vars.h`.
- Callback used from a module: must be exported, as `alt_cb_patch_nops()` is.
- vDSO: `alternative_has_cap_likely()` uses plain `ALTERNATIVE()` under
  `BUILD_VDSO` instead of the callback.
- `updptr` for the kernel image: `lm_alias()` of `origptr`; for a module it
  equals `origptr`.
