- `pci_device_add()` in `drivers/pci/probe.c` makes the device visible to
  lookups in two steps: the `bus->devices` insertion serves `pci_get_slot()`
  and `pci_walk_bus()`; the later `device_add()` serves `pci_get_device()`
  and `for_each_pci_dev`, which go through `bus_find_device()`.
- `pci_bus_add_device()` in `drivers/pci/bus.c` does not call `device_add()`.
- Binding gate: bit `PCI_DEV_ALLOW_BINDING` in `priv_flags`. `pci_bus_match()`
  returns 0 while `pci_dev_binding_disallowed()` is true. There is no
  match_driver field in this tree.
- `pci_dev_allow_binding()`: called only from `pci_bus_add_device()`, and only
  if the device has no OF node or `of_device_is_available()` is true. A
  device with an unavailable node is still marked added, and
  `pci_bus_match()` keeps returning 0 for it.
- Attach call: `device_initial_probe()`, not `device_attach()`. It does
  nothing when the bus `drivers_autoprobe` is off, and it allows async probe,
  so a probe can still be running after `pci_bus_add_device()` returns.
- Order in `pci_bus_add_device()`: `pcibios_bus_add_device()` runs before
  `pci_fixup_device(pci_fixup_final, dev)`; `pci_save_state()` and
  `pm_runtime_enable()` run before the gate opens. It makes no pwrctrl call.
- Code that must precede any probe: in `pci_device_add()`, or in
  `pci_bus_add_device()` before `pci_dev_allow_binding()`.
- `pci_fixup_enable` is not a pre-probe pass: its only call site is
  `do_pci_enable_device()` in `drivers/pci/pci.c`.
- sysfs files: attribute groups (`pci_dev_groups`, `pci_dev_attr_groups` in
  `drivers/pci/pci-sysfs.c`) created by `device_add()`, so userspace can reach
  them before final fixups. `pci_bus_add_device()` creates none of them and
  `pci_stop_dev()` removes none; `device_del()` removes them. There is no
  pci_create_sysfs_dev_files() here.
- Added state: bit `PCI_DEV_ADDED` in `priv_flags`, through
  `pci_dev_assign_added()`, `pci_dev_is_added()` and
  `pci_dev_test_and_clear_added()` in `drivers/pci/pci.h`. `struct pci_dev`
  has no added member; in `include/linux/pci.h`, `is_added` is a member of
  `struct pci_bus` only.
- Removed state: bit `PCI_DEV_REMOVED`, set by
  `pci_dev_test_and_set_removed()`. Its only user is `pci_destroy_dev()`,
  which returns early on a second call. There is no read-only helper for it.
- `PCI_DEV_ADDED` during a synchronous probe started by
  `pci_bus_add_device()`: still clear, because `pci_dev_assign_added()` runs
  after `device_initial_probe()`.
- `PCI_DEV_ADDED` during remove from `pci_stop_dev()`: already clear, because
  the bit is cleared before `device_release_driver()`.
- `pci_destroy_dev()`: `device_del()` runs before the `bus->devices` removal,
  so for a moment `pci_get_slot()` finds a device that `pci_get_device()`
  does not.
- `pci_release_dev()`: drops the `pci_bus_get()` reference taken in
  `pci_alloc_dev()`, so `dev->bus` stays valid while a device reference is
  held. It does not free a driver override string.
