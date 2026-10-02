- `__uaccess_mask_ptr()`: one `bic` that clears bit 55; no compare with
  `TASK_SIZE_MAX`, no conditional select, no speculation barrier, and the tag
  byte is kept.
- `__access_ok()` in `include/asm-generic/access_ok.h`: range test only;
  callers apply the mask after `access_ok()`, search `uaccess_mask_ptr`.
- `get_user` is defined as `__get_user`, and `put_user` as `__put_user`; both
  forms run `might_fault()`, `access_ok()` and the mask.
- `__raw_get_user(x, ptr, label)`: on a fault jumps to `label` and leaves `x`
  unassigned; `__get_user_error()` does the zeroing and sets `-EFAULT`.
- `__get_mem_asm()` with `CONFIG_CC_HAS_ASM_GOTO_OUTPUT`: for a user access
  the extable entry is `_ASM_EXTABLE_UACCESS()`, which names `wzr` for both
  registers, so the fixup only branches.
- **Potentially unsafe usage**: running anything but the access instructions
  between `uaccess_ttbr0_enable()` and `uaccess_ttbr0_disable()`.
  - Unsafe: when a caller expression or call inside the window reaches the
    scheduler directly; `check_and_switch_context()` in
    `arch/arm64/mm/context.c` skips `cpu_switch_mm()` when
    `system_uses_ttbr0_pan()`, so nothing reopens the window when the task
    runs again.
  - Safe: a fault, interrupt or preemption taken as an exception inside the
    window; `__swpan_entry_el1` in `arch/arm64/kernel/entry.S` closes TTBR0
    and records the state in `PSR_PAN_BIT` of the saved pstate, and
    `__swpan_exit_el1` reopens it.
  - Safe: evaluating `x` and `ptr` into temporaries before the enable, as
    `__raw_get_user()` and `__raw_put_user()` do.
- `uaccess_ttbr0_disable()`: tests only `system_uses_ttbr0_pan()` and keeps no
  nesting count; an accessor with its own window, such as
  `raw_copy_from_user()`, leaves an enclosing `user_access_begin()` window
  closed when it returns.
- `user_access_begin()`: `access_ok()` plus `uaccess_ttbr0_enable()`; it never
  changes PSTATE.PAN, so on hardware PAN it opens nothing.
- `__uaccess_ttbr0_enable()`: one `isb()`, after both the TTBR1_EL1 and the
  TTBR0_EL1 write.
- Futex ops with `ARM64_HAS_LSUI` (`CONFIG_ARM64_LSUI`): `__lsui_llsc_body()`
  in `arch/arm64/include/asm/lsui.h` picks the LSUI variants, which use only
  `uaccess_ttbr0_enable()`; the LL/SC variants use
  `uaccess_enable_privileged()`.
- `uaccess_enable_privileged()`: calls `mte_enable_tco()` first, which with
  `CONFIG_KASAN_HW_TAGS` and `ARM64_MTE` sets PSTATE.TCO (tag checks off);
  `uaccess_disable_privileged()` clears it.
- `mte_enable_tco()`: emits no instruction without `CONFIG_KASAN_HW_TAGS`;
  with it, a `nop` unless the CPU has `ARM64_MTE`.
- `uaccess_enable_privileged()` with software PAN: returns after
  `uaccess_ttbr0_enable()` and never reaches `__uaccess_disable_hw_pan()`.
