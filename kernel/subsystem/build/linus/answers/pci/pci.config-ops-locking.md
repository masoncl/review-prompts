- `pci_user_read_config_dword()`, `pci_user_write_config_dword()` and their
  byte and word siblings: hold `pci_lock` across the callback in every
  configuration; they use `raw_spin_lock_irq()` directly, not
  `pci_lock_config()`.
- `pci_check_and_set_intx_mask()` in `drivers/pci/irq.c`: calls
  `bus->ops->read` and `bus->ops->write` directly under
  `raw_spin_lock_irqsave(&pci_lock)`, in every configuration, for a
  read-modify-write of `PCI_COMMAND`.
- With `CONFIG_PCI_LOCKLESS_CONFIG`: the two paths above enter the callback
  with `pci_lock` held and `pci_bus_read_config_dword()` and its siblings
  enter it without, so `pci_lock` excludes nothing between them.
- `CONFIG_PCI_LOCKLESS_CONFIG`: has no prompt; `arch/x86/Kconfig` and
  `CONFIG_UML_PCI` select it. A driver in `drivers/pci/controller` that
  builds on x86 runs lockless; `vmd_pci_read()` and `vmd_pci_write()`
  serialise with their own raw spinlock `cfg_lock`.
- `raw_pci_read()` and `raw_pci_write()` on arm64, riscv and loongarch: call
  the bus's `ops->read` and `ops->write` without taking `pci_lock`, from
  `acpi_os_read_pci_configuration()` and `acpi_os_write_pci_configuration()`
  in `drivers/acpi/osl.c`. On these architectures a callback can run
  concurrently with a `pci_lock` holder although
  `CONFIG_PCI_LOCKLESS_CONFIG` is off.
- There are no config accessors with a noirq suffix in
  `drivers/pci/access.c`.
- Output on failure: the callback need not set it on the accessor paths;
  `PCI_OP_READ()` and `PCI_USER_READ_CONFIG()` pass a local `u32` and store
  `PCI_SET_ERROR_RESPONSE()` on any non-zero return.
- `pci_generic_config_read()` and `pci_generic_config_read32()`: return
  `PCIBIOS_DEVICE_NOT_FOUND` when `map_bus` returns NULL and do not write
  `*val`.
- Direct callers: get no fixup; `raw_pci_read()` in
  `arch/arm64/kernel/pci.c` hands the callback the caller's own pointer, so
  the caller gets whatever the callback left there.
