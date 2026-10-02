- PCI_IRQ_LEGACY: not defined in this tree; the INTx flag is `PCI_IRQ_INTX`
  in `include/linux/pci.h`.
- `pci_irq_type()` in `include/linux/pci.h`: returns `PCI_IRQ_MSIX`,
  `PCI_IRQ_MSI` or `PCI_IRQ_INTX` for the type that was granted; with
  `CONFIG_PCI` but without `CONFIG_PCI_MSI` it returns `PCI_IRQ_INTX`.
- `max_vecs < min_vecs`: `-ERANGE` from `__pci_enable_msix_range()` and
  `__pci_enable_msi_range()` in `drivers/pci/msi/msi.c`, not `-EINVAL`; not
  checked at all when only `PCI_IRQ_INTX` is set.
- `affd` passed without `PCI_IRQ_AFFINITY`: `WARN_ON()`, `affd` is dropped and
  the allocation proceeds; no error is returned.
- Failure value: the errno of the last of MSI-X and MSI that was tried, since
  each helper overwrites `nvecs`; the MSI-X errno is lost when `PCI_IRQ_MSI`
  is also set; `-ENOSPC` when neither flag is set.
- `-ENOSPC` is not the only "cannot satisfy" result: a device without the
  capability gives `-EINVAL` from `pci_msix_vec_count()` or
  `pci_msi_vec_count()`.
- `pci_msi_supported()` failing (for example MSI off globally, `dev->no_msi`,
  `PCI_BUS_FLAGS_NO_MSI` on the device's bus or a bus above it) or a device
  not in `PCI_D0`: `-EINVAL`.
- `-ENOTSUPP`: when `pci_msi_domain_supports()` is false; `-ENODEV`: when
  `pci_setup_msix_device_domain()` or `pci_setup_msi_device_domain()` fails.
- `PCI_IRQ_VIRTUAL`: MSI-X only; the count is not capped at the table size, so
  the return value can exceed `pci_msix_vec_count()`; the extra vectors are
  `is_virtual` and are not programmed into the device; for example
  `switchtec_init_isr()` in `drivers/pci/switch/switchtec.c`.
- With `CONFIG_PCI` but without `CONFIG_PCI_MSI`: the inline stub in
  `include/linux/pci.h` returns 1 on the same INTx condition as
  `pci_alloc_irq_vectors_affinity()` (`PCI_IRQ_INTX` set, `min_vecs` 1,
  `dev->irq` non-zero) but does not call `pci_intx()`; otherwise `-ENOSPC`.
