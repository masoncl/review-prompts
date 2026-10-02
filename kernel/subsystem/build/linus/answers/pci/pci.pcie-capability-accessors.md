- Failed read of an implemented register: output is reset to 0, not all
  ones; the return is the unconverted result of `pci_read_config_word()` or
  `pci_read_config_dword()`.
- Misaligned `pos`: `PCIBIOS_BAD_REGISTER_NUMBER` with output 0, not
  `-EINVAL`.
- `PCI_EXP_SLTSTA` on a port with no slot: `pcie_capability_read_word()`
  gives `PCI_EXP_SLTSTA_PDS` when `pcie_downstream_port()` is true, 0
  otherwise.
- `pcie_capability_read_dword()` has the same `PCI_EXP_SLTSTA` test, but it
  cannot fire: `PCI_EXP_SLTSTA` fails `pos & 3` and returns
  `PCIBIOS_BAD_REGISTER_NUMBER` first.
- `pos` not listed in the switch of `pcie_capability_reg_implemented()`:
  treated as unimplemented on every device, for example `PCI_EXP_SLTCTL2`;
  reads give 0 with return 0, writes are dropped with return 0.
- `pcie_capability_clear_and_set_word()` in `include/linux/pci.h`: locks for
  `PCI_EXP_LNKCTL`, `PCI_EXP_LNKCTL2` and `PCI_EXP_RTCTL`; no other `pos`.
- The lock: `pcie_cap_lock` in `struct pci_dev`, taken with
  `spin_lock_irqsave()` in `pcie_capability_clear_and_set_word_locked()`; it
  is not `pci_lock`.
- `pcie_capability_clear_and_set_dword()`: does not take `pcie_cap_lock` for
  any register.
- **Unsafe usage**: open-coded read-modify-write of `PCI_EXP_LNKCTL2` with
  `pcie_capability_read_word()` then `pcie_capability_write_word()` while
  another context can update it; the write helper does not take
  `pcie_cap_lock`.
  - Safe: `pcie_capability_clear_and_set_word()`, as
    `drivers/pci/pcie/bwctrl.c` does for `PCI_EXP_LNKCTL2_TLS`.
