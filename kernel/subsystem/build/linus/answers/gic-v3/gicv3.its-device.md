- `nvecs` clamp: `its_create_device()` limits `nvecs` to
  `BIT(FIELD_GET(GITS_TYPER_IDBITS, its->typer) + 1)` before it computes
  `nr_ites` and before `its_lpi_alloc()`.
- ITT size: `max(sz, ITS_ITT_ALIGN)`; no padding is added.
- ITT allocation: `itt_alloc_pool()`, not `kzalloc_node()`. Sizes of
  `PAGE_SIZE` or more come from `its_alloc_pages_node()`; smaller ones from
  the gen_pool `itt_pool`.
- `its_encode_itt()`: encodes `itt_addr >> 8`; the low 8 bits of the ITT
  address are dropped.
- `gic_flush_dcache_to_poc()` on the ITT: unconditional.
- `shared`: set only in `its_msi_prepare()`: when `its_find_device()` finds
  the device ID, or when a new device is created with
  `MSI_ALLOC_FLAGS_PROXY_DEVICE` in `info->flags`.
- `MSI_ALLOC_FLAGS_PROXY_DEVICE`: set by `its_pci_msi_prepare()` in
  `drivers/irqchip/irq-gic-its-msi-parent.c` when the last DMA alias is not
  the device itself.
- Lifetime of a shared device: never freed. `its_free_device()` is called
  only from `its_msi_teardown()` in `drivers/irqchip/irq-gic-v3-its.c`,
  which returns at once when `shared` is set, and no code clears `shared`.
