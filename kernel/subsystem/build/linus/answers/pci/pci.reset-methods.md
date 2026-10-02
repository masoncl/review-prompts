- Order in `pci_reset_fn_methods[]`: device_specific → acpi → flr → af_flr →
  pm → bus → cxl_bus. The `acpi` entry is `pci_dev_acpi_reset()`, which
  evaluates `_RST`.
- `__pci_reset_function_locked()`: does not probe. It calls each entry of
  `dev->reset_methods[]` with `PCI_RESET_DO_RESET`. `dev->reset_methods[]` is
  filled only by `pci_init_reset_methods()` and `reset_method_store()`, which
  probe.
- `pci_dev_wait()`: returns `-ENOTTY` on timeout and for a disconnected
  device. A method that reset the device and then timed out, such as
  `pcie_flr()`, makes the walk go on to the next method.
- `pci_bridge_wait_for_secondary_bus()`: also returns `-ENOTTY` on failure,
  so after a failed `bus` reset the walk goes on, to `cxl_bus` if that is the
  next entry of `dev->reset_methods[]`.
- Errors that stop the walk: any other code. For example the error from
  `pci_dev_reset_iommu_prepare()`, which each method calls before it resets,
  and `-EINVAL` from `pci_pm_reset()` when the device is not in `PCI_D0`.
- `pci_init_reset_methods()`: stops probing at the first probe result that is
  neither 0 nor `-ENOTTY`; later methods are left out of
  `dev->reset_methods[]`.
- `reset_done()`: called whether or not the reset succeeded;
  `pci_dev_restore()` runs unconditionally in `pci_reset_function()`,
  `pci_reset_function_locked()` and `pci_try_reset_function()`.
- `pci_dev_save_and_disable()`: calls `reset_prepare()` and
  `pci_set_power_state()`, then returns without `pci_save_state()` or the
  `PCI_COMMAND` write if `pci_dev_config_accessible()` reads all ones.
