- `pci_is_managed()`: one caller in the tree, `pcim_setup_msi_release()` in
  `drivers/pci/msi/msi.c`; `drivers/pci/pci.c` makes no devres call.
- Plain calls that become managed: only those that enable MSI or MSI-X, all
  through `pci_setup_msi_context()`: `pci_alloc_irq_vectors()`,
  `pci_alloc_irq_vectors_affinity()`, `pci_enable_msi()`,
  `pci_enable_msix_range()` and its inline wrapper `pci_enable_msix_exact()`.
- Implicit MSI release: installed only by a vector allocation made after
  `pcim_enable_device()`; `is_managed` is tested at allocation time.
- Comment above `pcim_setup_msi_release()`: calls this a legacy side-effect
  that is "dangerous and confusing", with a TODO to remove it.
- Managed vector allocator: there is none with a `pcim_` prefix.
- Deprecated in `drivers/pci/devres.c`: only `pcim_iomap_table()` and
  `pcim_iomap_regions()`.
- pcim_iomap_regions_request_all and pcim_iounmap_regions: not in this tree.
- `pcim_iomap_region()` and `pcim_iomap_range()`: do not enter the mapping in
  the legacy table, so `pcim_iomap_table()` has `NULL` for that BAR; only
  `pcim_iomap()` and `pcim_iomap_regions()` fill it.
- Failure value when converting: `pcim_iomap_region()` and
  `pcim_iomap_range()` return `IOMEM_ERR_PTR()`; `pcim_iomap()` returns `NULL`;
  `pcim_iomap_regions()` returns an int.
- `pcim_iounmap()`: releases only mappings from `pcim_iomap()` and
  `pcim_iomap_range()`; given an address from `pcim_iomap_region()` or
  `pcim_iomap_regions()` it finds no match and returns without unmapping.
- `pcim_iounmap_region()`: releases only BARs mapped by `pcim_iomap_region()`
  or `pcim_iomap_regions()`.
- `pcim_release_region()` and `pcim_release_all_regions()`: static in
  `drivers/pci/devres.c`; no exported function with a `pcim_` prefix undoes
  `pcim_request_region()` or `pcim_request_all_regions()` before detach.
