- Global lists: there is no global pci_devices list. A `struct pci_dev` is on
  `pci_bus->devices` and in the driver core's list for `pci_bus_type`;
  `pci_get_device()` searches the latter with `bus_find_device()`. The global
  list of buses is `pci_root_buses`, of root buses only.
- `struct pci_host_bridge` per domain: a domain can hold several, as under
  ACPI; each is identified by domain plus root bus number, and
  `pci_register_host_bridge()` rejects a pair for which `pci_find_bus()`
  already finds a bus, root or child.
- `pci_register_host_bridge()`: static in `drivers/pci/probe.c`. Its callers
  are `pci_scan_root_bus_bridge()`, which `pci_host_probe()` calls, and
  `pci_create_root_bus()`, which allocates the `struct pci_host_bridge`
  itself.
- `struct pci_ops` on a child bus: `pci_alloc_child_bus()` takes the host
  bridge's `child_ops` when set, else the parent bus's `ops`. The root bus
  gets the host bridge's `ops`.
- Root bus windows: held on the `pci_bus->resources` list, not in
  `pci_bus->resource[]`, which `pci_register_host_bridge()` leaves empty. The
  child bus of a transparent bridge has both once `pci_read_bridge_bases()`
  has run. `pci_bus_for_each_resource()` walks both.
- SR-IOV virtual bus (`virtfn_add_bus()` in `drivers/pci/iov.c`): besides
  `self`, `pci_bus->bridge` and every `pci_bus->resource[]` slot are NULL.
- VF created by `pci_iov_add_virtfn()`: its `resource[]` entries are children
  of the PF's `PCI_IOV_RESOURCES` entries, not of a bridge window, and its
  `dev.parent` is the PF's parent.
- Reference chain: a `struct pci_dev` holds a reference on its
  `struct pci_bus`; a bus holds one on `bus->bridge`; a `struct pci_slot`
  holds one on its bus; a VF holds one on its PF.
- Bound driver: `struct pci_dev` has its own `driver` field, set in
  `local_pci_probe()` before `probe` is called and cleared in
  `pci_device_remove()`. The core's reset, error-recovery, PM and SR-IOV
  paths read it rather than `to_pci_driver()` of `dev.driver`; the PM
  callbacks in `drivers/pci/pci-driver.c` still take `struct dev_pm_ops`
  from `dev->driver->pm`.
- `struct pci_saved_state`: a detached copy made by
  `pci_store_saved_state()` and put back into the `struct pci_dev` buffers by
  `pci_load_saved_state()`. `pci_save_state()` and `pci_restore_state()` use
  `pci_dev->saved_config_space` and the `struct pci_cap_saved_state` entries
  on `pci_dev->saved_cap_space`.
- `struct pci_slot`: also created with no hotplug driver, for example by
  `drivers/acpi/pci_slot.c`, so `slot->hotplug` may be NULL. A slot numbered
  `PCI_SLOT_ALL_DEVICES` covers every device on the bus, except with
  `per_func_slot`, which is set under `CONFIG_S390`.
- `struct pci_error_handlers`: called, for example, from
  `pcie_do_recovery()`, from the reset path (`pci_dev_save_and_disable()` and
  `pci_dev_restore()` in `drivers/pci/pci.c`), and from arch recovery code
  such as `arch/powerpc/kernel/eeh_driver.c`.
- `struct pcie_device` and `struct pcie_port_service_driver`: private to
  `drivers/pci/pcie/portdrv.h`. There are five services; the one easy to
  miss is `PCIE_PORT_SERVICE_BWCTRL`, whose state is
  `struct pcie_bwctrl_data` at `pci_dev->link_bwctrl`.
- `struct pci_pwrctrl` (`include/linux/pci-pwrctrl.h`): context of a platform
  device that powers a PCI device and shares its OF node. The host
  controller driver creates and powers these with
  `pci_pwrctrl_create_devices()` and `pci_pwrctrl_power_on_devices()`; the
  code in `drivers/pci/pwrctrl/core.c` does not rescan the bus and creates
  no device link.
- `struct pci_tsm` (`include/linux/pci-tsm.h`): per-function TEE security
  context at `pci_dev->tsm`, under `CONFIG_PCI_TSM`; `dsm_dev` names the
  function that manages it, which may be another `struct pci_dev`.
- `struct pci_ide` (`include/linux/pci-ide.h`): one Selective IDE Stream
  between an endpoint and its Root Port, under `CONFIG_PCI_IDE`;
  `host_bridge_stream` is allocated from the `struct pci_host_bridge`, and
  each partner's `stream_index` from that port's `struct pci_dev`.
