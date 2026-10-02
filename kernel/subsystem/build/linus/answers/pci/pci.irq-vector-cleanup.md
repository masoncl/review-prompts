- `Documentation/PCI/msi-howto.rst`: on a `pcim_enable_device()` device the
  driver "shouldn't call" `pci_free_irq_vectors()`.
- Kernel-doc of `pci_free_irq_vectors()`: "Do not call this function" on such
  a device, it "can lead to double-free issues".
- **Potentially unsafe usage**: `pci_free_irq_vectors()` on a
  `pcim_enable_device()` device.
  - Unsafe: while a handler from `devm_request_irq()` is still installed on a
    vector, as in remove or a probe error path; devres frees that handler only
    after remove or the failed probe returns.
  - Safe: when no handler is installed on any vector, as `ahci_init_irq()` in
    `drivers/ata/ahci.c` does before it allocates again; the later
    `pcim_msi_release()` frees only what is enabled then, since
    `pci_disable_msix()` and `pci_disable_msi()` return early when
    `msix_enabled` and `msi_enabled` are clear.
  - Safe: no explicit call, with `devm_request_irq()` after the allocation, as
    `switchtec_init_isr()` in `drivers/pci/switch/switchtec.c` does;
    `pcim_msi_release()` is registered at the first allocation, so it runs
    after the handlers are released.
- Handler still installed when vectors are freed: nothing in
  `drivers/pci/msi/` or `kernel/irq/msi.c` checks for it; there is no
  `BUG_ON()` for it there.
- With `CONFIG_SPARSE_IRQ`, on the irq domain path: `free_desc()` in
  `kernel/irq/irqdesc.c` deletes the descriptor; with `CONFIG_PROC_FS`,
  `remove_proc_entry()` warns "removing non-empty directory"; a later
  `free_irq()` finds no descriptor and returns `NULL` without freeing the
  action.
- After an INTx result: `pci_free_irq_vectors()` does nothing; the
  `pci_intx(dev, 1)` done by the allocation is not undone.
