- Call site: not always `setup_arch()`; for example powerpc calls
  `parse_early_param()` from `early_init_devtree()` in
  `arch/powerpc/kernel/prom.c`.
- `parse_early_options()`: runs the early handlers on any string and is not
  covered by the `done` flag; `sh_early_platform_driver_register_all()` in
  `arch/sh/drivers/platform_early.c` calls it directly.
- Static keys: generic code orders `jump_label_init()` before
  `parse_early_param()` only in `start_kernel()`; an architecture that parses
  earlier has that order only if it calls `jump_label_init()` itself.
- Architectures that parse without calling `jump_label_init()` first: for
  example arm and mips; search `arch/` for both names to see the rest.
- memblock: not guaranteed; for example `parse_early_param()` runs before
  `e820__memblock_setup()` on x86 and before `arm_memblock_init()` on arm.
- **Potentially unsafe usage**: calling `static_branch_enable()` or
  `static_branch_disable()` from an `early_param()` handler.
  - Unsafe: when the handler can be built for an architecture that calls
    `parse_early_param()` without `jump_label_init()` before it;
    `STATIC_KEY_CHECK_USE()` in `include/linux/jump_label.h` warns.
  - Safe: when the handler is built only where `jump_label_init()` comes
    first, as `early_randomize_kstack_offset()` in `init/main.c`, which
    depends on `HAVE_ARCH_RANDOMIZE_KSTACK_OFFSET`.
  - Safe: store the value and flip the key later, as `early_init_on_alloc()`
    with `mem_debugging_and_hardening_init()` in `mm/mm_init.c`.
