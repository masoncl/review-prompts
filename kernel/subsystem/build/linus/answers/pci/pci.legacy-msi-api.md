- `pci_irq_vector()` after a legacy enable: works; it tests only
  `msi_enabled` and `msix_enabled`, then calls `msi_get_virq()`.
- `pci_irq_vector()` after `pci_enable_msix_range()`: `nr` is the MSI-X table
  index given in `entries[].entry`, not the position in the array.
- `pci_irq_get_affinity()` on a vector from a legacy enable: returns `NULL`.
- `pci_msi_vec_count()`: defined and exported in `drivers/pci/msi/msi.c`;
  `pci_msix_vec_count()` is in `drivers/pci/msi/api.c`.
- Kernel-doc "Legacy device driver API": on `pci_enable_msi()`,
  `pci_disable_msi()`, `pci_enable_msix_range()` and `pci_disable_msix()`;
  each adds that the newer pair "should, in general, be used instead".
- `pci_enable_msix_exact()`: static inline in `include/linux/pci.h` with no
  kernel-doc; no source comment calls it legacy or deprecated,
  `Documentation/PCI/msi-howto.rst` does.
- `Documentation/PCI/msi-howto.rst`, section "Legacy APIs": lists all five,
  both disable functions included, each marked `/* deprecated */`; the wording
  is "should not be used in new code".
- Multi-vector MSI: no legacy function gives it; `pci_enable_msi()` asks for
  exactly one vector.
- With `CONFIG_PCI` but without `CONFIG_PCI_MSI`: the legacy enable stubs
  return `-ENOSYS`, while the `pci_alloc_irq_vectors()` stub can still return
  1 for INTx.
