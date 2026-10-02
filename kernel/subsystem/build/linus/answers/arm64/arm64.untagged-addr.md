- `untagged_addr()` and `__untagged_addr()`: both are macros in
  `arch/arm64/include/asm/memory.h`.
- `untagged_addr()` on a value with bit 55 set: returned unchanged, so a
  kernel pointer keeps its KASAN tag, whatever the top byte is.
- `__tag_reset()`: is `__untagged_addr()` only under `CONFIG_KASAN_SW_TAGS` or
  `CONFIG_KASAN_HW_TAGS`; otherwise it expands to `(addr)` and changes nothing.
- `__tag_reset()` on a kernel pointer, with either option on: sets the top byte
  to 0xff; this is what `kasan_reset_tag()` and `virt_addr_valid()` use.
- `access_ok()`: untags only if `CONFIG_ARM64_TAGGED_ADDR_ABI` is on and the
  caller has `PF_KTHREAD` or `TIF_TAGGED_ADDR`; otherwise a tagged pointer
  fails the range check.
- `__access_ok()`: the generic one in `include/asm-generic/access_ok.h`; it
  does not untag.
- `mm_untag_mask()`: arm64 defines it in
  `arch/arm64/include/asm/mmu_context.h`; it returns `-1UL >> 8` for every mm,
  whatever the task setting.
- `mm_untag_mask()` on arm64 takes no user address and untags nothing; it is
  only reported, as `untag_mask` in `fs/proc/array.c`.
