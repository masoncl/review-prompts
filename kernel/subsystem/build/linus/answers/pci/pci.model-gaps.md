- Models take pci_remove_sysfs_dev_files to remove the sysfs files of a
  device. It is defined nowhere in this tree.
- Models take `pci_device_remove()` to set `current_state` to `PCI_UNKNOWN`.
  `pci_pm_set_unknown_state()` in `drivers/pci/pci-driver.c` does that write,
  for a device in `PCI_D0`; it is defined under `CONFIG_PM_SLEEP` and called
  from `pci_legacy_suspend_late()`, `pci_pm_suspend_noirq()` and
  `pci_pm_freeze_noirq()`.
- Models take `driver_override` to be a string in `struct pci_dev`. It is a
  member of `struct device`; `pci_bus_type` sets `.driver_override = true`,
  and the code under `drivers/pci/` reads it only through
  `device_match_driver_override()` and `device_has_driver_override()`.
- Models take `pci_resize_resource()` to have three arguments and to leave
  the release of the BARs to the caller. It takes a fourth argument
  `exclude_bars`, releases the device's resources in the same bridge window
  itself through `pci_do_resource_release_and_resize()`, and restores them
  on failure.
- Models take a secondary bus reset always to toggle
  `PCI_BRIDGE_CTL_BUS_RESET`. For a port on a root bus whose host bridge sets
  `reset_root_port`, the `__weak` `pcibios_reset_secondary_bus()` in
  `drivers/pci/pci.c` calls that hook instead, and calls
  `pci_restore_state()` on the port when it succeeds.
- Models take the PCI core never to call `pcie_set_target_speed()`.
  `pci_device_add()` in `drivers/pci/probe.c` reaches it through
  `pcie_failed_link_retrain()`, with `CONFIG_PCI_QUIRKS` and
  `CONFIG_PCIEPORTBUS`.
- Models name pci_pwrctrl_register as the call a pwrctrl driver makes. A
  driver under `drivers/pci/pwrctrl/` calls `pci_pwrctrl_init()` and
  `devm_pci_pwrctrl_device_set_ready()`.
