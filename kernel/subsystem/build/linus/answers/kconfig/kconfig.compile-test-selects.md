- **Potentially unsafe usage**: `select BAR` in a `config FOO` with
  `depends on ARCH_FOO_VENDOR || COMPILE_TEST`, where `BAR` depends on an
  architecture or platform.
  - Unsafe: when `BAR` is defined on the architecture being configured and its
    dependencies can be below `FOO` while `COMPILE_TEST=y`; `sym_calc_value()`
    warns and forces `BAR`.
  - Safe: the select is conditional on the architecture, as `HISILICON_LPC` in
    `drivers/bus/Kconfig` does: `select INDIRECT_PIO if ARM64`, where
    `INDIRECT_PIO` in `lib/Kconfig` has `depends on ARM64`.
  - Safe: the target carries `|| COMPILE_TEST` itself, as `MTK_SMI` in
    `drivers/memory/Kconfig` does for `select MTK_SMI` in `MTK_IOMMU`.
  - Safe: the target is defined only in one architecture's Kconfig and has no
    dependencies, as `ARM_DMA_USE_IOMMU` in `arch/arm/Kconfig` is for
    `ROCKCHIP_IOMMU`; elsewhere the symbol is undefined and the select does
    nothing, so the driver must build without it.
- Target's remaining dependencies: repeated on a separate `depends on` line,
  outside the `|| COMPILE_TEST`. `ARM_SMMU` has `depends on !GENERIC_ATOMIC64`
  because `IOMMU_IO_PGTABLE_LPAE` has it beside its
  `depends on ARM || ARM64 || COMPILE_TEST`; `HISILICON_LPC` repeats
  `depends on HAS_IOPORT`.
- `ARM_SMMU`: defined in `drivers/iommu/arm/Kconfig`, with
  `select ARM_DMA_USE_IOMMU if ARM`.
- `ROCKCHIP_IOMMU`: has plain `depends on ARCH_ROCKCHIP || COMPILE_TEST`; it
  does not narrow `COMPILE_TEST`.
- Placeholder names in `Documentation/kbuild/kconfig-language.rst`: for
  example `FOO`, `BAR`, `BAZ` and `ARCH_FOO_VENDOR`; there is no ARCH_FOO.
