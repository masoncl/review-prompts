- `devm_pci_alloc_host_bridge()`: sets `bridge->dev.parent` itself, then calls
  `devm_of_pci_bridge_init()` in `drivers/pci/of.c`.
- `devm_of_pci_bridge_init()` with an OF node: sets `swizzle_irq` and
  `map_irq`, then runs the static `pci_parse_request_of_pci_ranges()`; a
  driver cannot and need not call that itself.
- `pci_parse_request_of_pci_ranges()`: parses "bus-range", "ranges" and
  "dma-ranges", requests the windows with `devm_request_pci_bus_resources()`
  and remaps I/O windows with `devm_pci_remap_iospace()`.
- `devm_of_pci_bridge_init()` without an OF node: returns 0 and fills nothing;
  `bridge->windows` stays empty and `map_irq` stays NULL.
- Bus window on DT: always present; a missing "bus-range" becomes [0-0xff] in
  `devm_of_pci_get_host_bridge_resources()`.
- `bridge->busnr`: overwritten by `pci_scan_root_bus_bridge()` from the start
  of the first `IORESOURCE_BUS` window; a driver's own value survives only
  when no such window exists.
- No bus window: `pci_scan_root_bus_bridge()` logs with `dev_info()`, uses
  `bridge->busnr` to 0xff, and shrinks the end to the highest bus found
  after the scan.
- `bridge->ops`: must be non-NULL; `pci_register_host_bridge()` dereferences
  `bus->ops->add_bus` with no test.
- `pci_rescan_remove_lock`: taken twice in `pci_host_probe()`, around
  `pci_scan_root_bus_bridge()` and around `pci_bus_add_devices()`;
  `pci_scan_root_bus_bridge()` does not take it itself.
- Unlocked steps: `pci_bus_claim_resources()`,
  `pci_assign_unassigned_root_bus_resources()`,
  `pcie_bus_configure_settings()` and the runtime PM calls.
- Runtime PM state: `pci_host_probe()` tests nothing and discards the return
  values of `pm_runtime_set_active()` and `devm_pm_runtime_enable()`.
- **Potentially unsafe usage**: calling `pci_host_probe()` while the
  controller device is not both runtime-PM enabled and `RPM_ACTIVE`.
  - Unsafe: when the driver enables runtime PM on the controller afterwards
    while it is `RPM_SUSPENDED`; `pm_runtime_enable()` warns "Enabling runtime
    PM for inactive device with active children".
  - Unsafe: when runtime PM is enabled but the controller is not
    `RPM_ACTIVE`; `__pm_runtime_set_status()` returns `-EBUSY` and
    `bridge->dev` is enabled while suspended.
  - Safe: when the driver never enables runtime PM on the controller, as
    `pci_host_common_init()` does; the `-EBUSY` test in
    `__pm_runtime_set_status()` needs the parent's `power.disable_depth` to
    be 0, and the warning is only in `pm_runtime_enable()` of the
    controller.
  - Safe: `pm_runtime_enable()` then a successful `pm_runtime_get_sync()`
    first, as `rcar_pcie_probe()` does.
- `pci_host_probe()` failure: only `pci_register_host_bridge()` can fail it,
  before any device is scanned; once registration succeeds it returns 0.
- **Unsafe usage**: passing `bridge->bus` to `pci_stop_root_bus()` or
  `pci_remove_root_bus()` after `pci_host_probe()` returned an error;
  `pci_register_host_bridge()` frees the bus and leaves `bridge->bus`
  pointing at it, or NULL when `pci_alloc_bus()` failed.
  - Safe: on that error undo only the driver's own setup, as
    `dw_pcie_host_init()` does.
  - Safe: stop/remove after `pci_host_probe()` returned 0 and a later probe
    step failed, as `qcom_pcie_probe()` does through
    `dw_pcie_host_deinit()`.
- Bridge lifetime: the root bus holds its own reference on `bridge->dev`,
  taken in `pci_register_host_bridge()` and dropped in
  `release_pcibus_dev()`; the devres `put_device()` alone does not free the
  bridge or its private area while the bus exists.
- Bus left registered at unbind: what devres frees is the controller's other
  managed objects, including the `struct resource` objects behind
  `bridge->windows`, which `devm_of_pci_get_host_bridge_resources()`
  allocates on the controller device.
- `devm_pm_runtime_enable(&bridge->dev)`: is devres of `bridge->dev`, not of
  the controller; `device_del()` in `pci_remove_root_bus()` releases it.
