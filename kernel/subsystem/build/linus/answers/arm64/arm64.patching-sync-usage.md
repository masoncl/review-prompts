- Instruction class: no function in `arch/arm64/kernel/patching.c` checks
  which instructions are swapped; there is no aarch64_insn_hotpatch_safe()
  here.
- `aarch64_insn_patch_text_nosync()`: tests only 4-byte alignment
  (`-EINVAL`) and accepts any 32-bit value; the caller chooses between it
  and `aarch64_insn_patch_text()`.
- **Potentially unsafe usage**: `aarch64_insn_patch_text_nosync()` with
  nothing after it that resynchronises the other CPUs.
  - Unsafe: when the caller then relies on no CPU still running the old
    instruction; the only `isb` is the one in `caches_clean_inval_pou()`, on
    the calling CPU, and another CPU may keep executing what it already
    fetched.
  - Safe: followed by `kick_all_cpus_sync()`, as
    `arch_jump_label_transform_apply()` does; `flush_icache_range()` in
    `arch/arm64/include/asm/cacheflush.h` defines the same IPI as the
    resynchronisation step.
  - Safe: the text written cannot be reached until a later exception, as in
    `arch_prepare_ss_slot()`, which fills the slot before
    `arch_arm_kprobe()` writes the BRK; the slot is entered only from
    `setup_singlestep()` in the BRK handler.
  - Safe: `aarch64_insn_patch_text()`, where every other CPU does `isb()`
    in `aarch64_insn_patch_text_cb()` before it leaves.
- Jump label: arm64 defines `HAVE_JUMP_LABEL_BATCH` and has no definition of
  `arch_jump_label_transform()`.
- `arch_jump_label_transform_queue()`: queues nothing; it patches at once
  with `aarch64_insn_patch_text_nosync()`, ignores the result and returns
  `true`.
- `arch_jump_label_transform_apply()`: not a no-op; it is the one
  `kick_all_cpus_sync()` per `__jump_label_update()` in
  `kernel/jump_label.c`.
- `__apply_alternatives()`: calls no routine from `arch/arm64/mm/cache.S`,
  since that code is itself patched; it uses `clean_dcache_range_nopatch()`
  per entry, then one `dsb(ish)`, `icache_inval_all_pou()`, `isb()`.
- `apply_alternatives_module()`: no `stop_machine()` and no cache
  maintenance; `__apply_alternatives()` skips both the clean and the I-cache
  invalidate when `is_module`.
- Module alternatives: the maintenance is `flush_module_icache()` in
  `kernel/module/main.c`, which runs after `post_relocation()` has called
  `module_finalize()`.
