- `CONFIG_UAPI_HEADER_TEST`: `usr/include/Makefile` compiles the exported
  headers with `-std=c90`, and with `-std=c++98` for C++, but headers under
  `include/uapi` expand `__ALIGN_KERNEL()` and `__ALIGN_KERNEL_MASK()` only
  inside other macro definitions, for example `XT_ALIGN()` and
  `NL_MMAP_MSG_ALIGN()`, so the test parses no expansion of them.
- Direct UAPI users of `__ALIGN_KERNEL()`: `XT_ALIGN()` in
  `include/uapi/linux/netfilter/x_tables.h` and `NL_MMAP_MSG_ALIGN()` in
  `include/uapi/linux/netlink.h`; `XT_TARGET_INIT()` puts `XT_ALIGN()` in a
  struct initializer.
- `__ALIGN_KERNEL_MASK()` in assembly: `LOAD_PHYSICAL_ADDR` in
  `arch/x86/include/asm/page_types.h` expands it and
  `arch/x86/boot/header.S` uses that value, so the mask form must stay plain
  arithmetic with no cast and no `__typeof__`.
- vDSO: the kernel wrappers are in `include/vdso/align.h`, which
  `include/vdso/datapage.h` includes, so an expansion must also compile in
  vDSO code.
