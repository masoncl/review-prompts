- `pci_dev_is_disconnected()`: defined in `include/linux/pci.h`, so drivers may
  call it, as `nvme_timeout()` does. `pci_dev_set_disconnected()` and
  `pci_dev_set_io_state()` are private to the core, in `drivers/pci/pci.h`.
- `pci_dev_set_disconnected()` callers: hotplug and resume code, for example
  `pciehp_unconfigure_device()` and `pci_pm_bridge_power_up_actions()`.
  Nothing under `drivers/pci/pcie/` calls it: AER, DPC and EDR do not mark
  devices disconnected.
- `pciehp_unconfigure_device()` with `presence` false: reached for a Link Down
  event as well as a presence change; `pciehp_handle_presence_or_link_change()`
  passes `SURPRISE_REMOVAL` for both. A disconnected device may still be in
  the slot.
- `pci_dev_set_io_state()`: never leaves `pci_channel_io_perm_failure`; in
  that state a request for `pci_channel_io_frozen` or `pci_channel_io_normal`
  returns false.
- `pci_dev_set_disconnected()`: also calls `pci_doe_disconnected()`, which
  under `CONFIG_PCI_DOE` cancels the DOE mailbox tasks of the device.
- A clear flag does not prove presence: the flag is set by software, for
  example in `pciehp_unconfigure_device()`, which runs after the hardware
  event.
- `pcie_capability_read_word()` and `pcie_capability_read_dword()` on a
  disconnected device, for an implemented register: return
  `PCIBIOS_DEVICE_NOT_FOUND` with the value set to 0, not all ones.
- Config accesses with no disconnected test: `pci_bus_read_config_dword()`,
  `pci_user_read_config_dword()` and their byte, word and write siblings in
  `drivers/pci/access.c`; they call `bus->ops` directly.
- `__pci_read_msi_msg()`: has no disconnected test of its own; for MSI-X it
  reads the table with `readl()`. For a disconnected device
  `__pci_write_msi_msg()` and `pci_msix_shutdown()` skip the hardware.
- **Potentially unsafe usage**: `PCI_POSSIBLE_ERROR()` on a value from
  `pcie_capability_read_word()` as the only "device gone" test.
  - Unsafe: when the return value is not tested and nothing else bounds what
    the code does with the 0 read for a disconnected device, for example a
    wait with no timeout until a bit is set.
  - Safe: also test the return value, as `pciehp_check_link_active()` does;
    `pcie_capability_read_word()` defines the zeroing.
  - Safe: in a loop with a timeout, as `pcie_poll_cmd()` in
    `drivers/pci/hotplug/pciehp_hpc.c`.
  - Safe: where a value of 0 ends the work, as `pcie_pme_irq()` in
    `drivers/pci/pcie/pme.c` returns `IRQ_NONE` when `PCI_EXP_RTSTA_PME` is
    clear.
