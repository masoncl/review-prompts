- `IOMEM_ERR_PTR()`: defined in `include/linux/err.h`, not in
  `include/linux/io.h`.
- `IS_ERR()`, `PTR_ERR()`, `IS_ERR_OR_NULL()`, `PTR_ERR_OR_ZERO()` and
  `ERR_CAST()`: the parameter is `__force const void *`, so in-tree code
  passes an `__iomem` pointer with no cast, for example
  `pcim_iomap_regions()` in `drivers/pci/devres.c`.
- Removing `__iomem`: in-tree code uses a `__force` cast, for example
  `arch_memremap_wb()` in `kernel/iomem.c` and `devm_iounmap()` in
  `lib/devres.c`.
- Adding `__iomem` to a plain pointer: in-tree code also does it with a plain
  cast and no `__force`, for example `memunmap()` in `kernel/iomem.c`; a missing
  `__force` on such a cast is not by itself a defect.
- `CHECKFLAGS` in the top-level `Makefile`: its only `-W` options are
  `-Wbitwise`, `-Wno-return-void` and `-Wno-unknown-attribute`, so no
  address-space warning beyond sparse's defaults is enabled.
