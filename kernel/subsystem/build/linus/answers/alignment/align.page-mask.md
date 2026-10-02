- `PAGE_MASK` has two definitions in `include/vdso/page.h`, selected by
  `#if !defined(CONFIG_64BIT)`:

| Kernel | Definition | Type |
|---|---|---|
| `CONFIG_64BIT` not set | `(~((1 << CONFIG_PAGE_SHIFT) - 1))` | int, negative |
| `CONFIG_64BIT` set | `(~(PAGE_SIZE - 1))` | unsigned long |

- `CONFIG_PHYS_ADDR_T_64BIT` is not tested in `include/vdso/page.h`; every
  32-bit kernel gets the int form, with or without wide physical addresses.
- `value & PAGE_MASK` on a 32-bit kernel: keeps bits 32 to 63 of a `u64`,
  `phys_addr_t`, `dma_addr_t` or `loff_t`, because the int is sign-extended to
  the wider type.
- `(u64)PAGE_MASK` on a 32-bit kernel: also sign-extends, the high 32 bits are
  ones.
- There is no PHYS_PAGE_MASK in this tree; x86 has `PHYSICAL_PAGE_MASK` in
  `arch/x86/include/asm/page_types.h`, which casts `PAGE_MASK` to
  `signed long` and ANDs it with `__PHYSICAL_MASK`.
- **Potentially unsafe usage**: masking with a hand-written
  `~(PAGE_SIZE - 1)`.
  - Unsafe: when the value is wider than unsigned long, such as a `u64`, a
    `loff_t`, or a `phys_addr_t` under `CONFIG_PHYS_ADDR_T_64BIT`, on a kernel
    without `CONFIG_64BIT`; `PAGE_SIZE` is `_AC(1,UL) << CONFIG_PAGE_SHIFT`,
    so the mask is a 32-bit unsigned long, is zero-extended, and clears bits
    32 to 63.
  - Safe: when the value is unsigned long or narrower, as
    `pt_topa_prev_entry()` in `arch/x86/events/intel/pt.c` does after casting
    a pointer to unsigned long.
  - Safe: in code built only with `CONFIG_64BIT`, where unsigned long is 64
    bits, as `handle_pfmf()` in `arch/s390/kvm/s390/priv.c`.
  - Safe: `PAGE_MASK` itself applied to the wide value, as `__early_ioremap()`
    in `mm/early_ioremap.c` does with `phys_addr &= PAGE_MASK` on a
    `resource_size_t`.
- **Potentially unsafe usage**: converting `PAGE_MASK` to unsigned long, or
  another unsigned 32-bit type, before it meets the value: stored in an
  unsigned long variable, passed as an unsigned long parameter, or combined
  first with an unsigned long operand.
  - Unsafe: when the result then masks a value wider than unsigned long on a
    kernel without `CONFIG_64BIT`; the sign extension is lost and bits 32 to
    63 are cleared.
  - Safe: when the value masked is unsigned long or narrower, as in
    `PFN_ALIGN()` in `include/linux/pfn.h`, whose argument is cast to
    unsigned long first.
  - Safe: a cast straight to the wide type or to a signed type, as
    `(loff_t)PAGE_MASK` in `bl_write_pagelist()` in
    `fs/nfs/blocklayout/blocklayout.c`, or `(signed long)PAGE_MASK` in
    `PHYSICAL_PAGE_MASK`.
