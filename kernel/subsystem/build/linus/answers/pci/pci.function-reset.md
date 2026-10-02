- `pci_dev_lock()`: takes `device_lock()` first, then `pci_cfg_access_lock()`.
  `pci_dev_trylock()` uses the same order.
- `pci_reset_function()`: takes `pci_dev_lock()` on `pci_upstream_bridge()`
  first, if there is one, then on the device.
- `pci_try_reset_function()`: takes `pci_dev_trylock()` on the device only,
  never on the bridge.
- `device_lock_assert()`: called in `pci_reset_function_locked()`,
  `__pci_reset_function_locked()` and `pci_dev_save_and_disable()`. It is
  `lockdep_assert_held()` on the device mutex and nothing more.
- Config access lock: not tested on the device by any of the four function
  reset entry points. `pci_reset_function_locked()` and
  `__pci_reset_function_locked()` take no lock and run with user config
  access unblocked unless the caller took `pci_cfg_access_lock()`.
- `pci_bridge_secondary_bus_reset()`: tests `block_cfg_access` of the bridge,
  prints "unlocked secondary bus reset" once, and resets anyway. Reached by
  the `bus` method through `pci_parent_bus_reset()`.
- Callers of `__pci_reset_function_locked()` that lock the bridge themselves:
  `vfio_pci_core_disable()` uses `pci_dev_trylock()` on bridge then device;
  `mlxsw_pci_reset_at_pci_disable()` uses `pci_cfg_access_lock()` on both.
- Error callbacks: every walker in `drivers/pci/pcie/err.c` holds
  `device_lock()` around the driver callback, so a reset from there uses
  `pci_reset_function_locked()`, as `ionic_pci_error_resume()` does.
  `pci_reset_function()` would take the same mutex again.
