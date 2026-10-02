- Order in `pcie_do_recovery()`: `error_detected()` walk, then the
  `mmio_enabled()` walk if the status is `PCI_ERS_RESULT_CAN_RECOVER`, then
  `reset_subordinates()`, then the `slot_reset()` walk, then `resume()`.
- `reset_subordinates()`: called when the state is `pci_channel_io_frozen` or
  the status is `PCI_ERS_RESULT_NEED_RESET`. A non-fatal error whose merged
  vote is `PCI_ERS_RESULT_NEED_RESET` gets a real reset.
- Frozen channel with status `PCI_ERS_RESULT_CAN_RECOVER`: `mmio_enabled()`
  runs before the reset, while `error_state` is still
  `pci_channel_io_frozen`.
- `slot_reset()` walk: runs only when the status is
  `PCI_ERS_RESULT_NEED_RESET`. A frozen recovery whose status is
  `PCI_ERS_RESULT_RECOVERED` after `mmio_enabled()` is reset and goes
  straight to `resume()`.
- Callers and states: `AER_NONFATAL` passes `pci_channel_io_normal`.
  `AER_FATAL`, DPC, EDR and, with `CONFIG_PCIEAER`,
  `pci_host_handle_link_down()` pass `pci_channel_io_frozen`.
- Reset callbacks: `aer_root_reset()`, `dpc_reset_link()` and
  `pci_host_reset_root_port()` in
  `drivers/pci/controller/pci-host-common.c`.
- `aer_root_reset()`: uses `pcie_reset_flr()` for an RCEC or RCiEP, otherwise
  `pci_bus_error_reset()`, which resets the slots when the bus has slots and
  every one of them can be reset, and does a secondary bus reset otherwise.
- Recovery scope: the device itself for `PCI_EXP_TYPE_ROOT_PORT`,
  `PCI_EXP_TYPE_DOWNSTREAM`, `PCI_EXP_TYPE_RC_EC` and `PCI_EXP_TYPE_RC_END`;
  otherwise `pci_upstream_bridge()`.
- `merge_result()` by current status:

| Current status | New vote that changes it |
|---|---|
| any, tested first | `PCI_ERS_RESULT_NO_AER_DRIVER` replaces it; `PCI_ERS_RESULT_NONE` never does |
| `PCI_ERS_RESULT_CAN_RECOVER`, `PCI_ERS_RESULT_RECOVERED` | any other vote replaces it |
| `PCI_ERS_RESULT_DISCONNECT` | besides the first row, only `PCI_ERS_RESULT_NEED_RESET` |
| `PCI_ERS_RESULT_NEED_RESET`, `PCI_ERS_RESULT_NO_AER_DRIVER` | nothing besides the first row |

- `PCI_ERS_RESULT_DISCONNECT` loses to `PCI_ERS_RESULT_NEED_RESET` in either
  order of voting.
- Disconnected device in `report_error_detected()`: votes
  `PCI_ERS_RESULT_DISCONNECT` and its callback is not called; the test comes
  before `pci_dev_set_io_state()`.
- `PCI_ERS_RESULT_NONE` from `report_error_detected()`: when
  `pci_dev_set_io_state()` fails, or for a bridge with no `error_detected()`.
- Non-bridge with no `error_detected()`: votes `PCI_ERS_RESULT_NO_AER_DRIVER`
  for both channel states. Bridge means `hdr_type` is
  `PCI_HEADER_TYPE_BRIDGE`.
- `report_slot_reset()` and `report_resume()`: set `error_state` to
  `pci_channel_io_normal` before they call the driver.
- On failure, `report_perm_failure_detected()` runs for each device: it calls
  `error_detected()` with `pci_channel_io_perm_failure` and sends
  `pci_uevent_ers()` with `PCI_ERS_RESULT_DISCONNECT`.
- `report_perm_failure_detected()`: does not write `error_state`. The devices
  are not disconnected for `pci_dev_is_disconnected()`, and config accesses
  still reach the hardware.
- `error_state` after failure: `pci_channel_io_frozen` if a fatal recovery
  failed before the `slot_reset()` walk, `pci_channel_io_normal` after it.
- Return value on failure: the merged status as it stands, for example
  `PCI_ERS_RESULT_NO_AER_DRIVER`. It is not rewritten to
  `PCI_ERS_RESULT_DISCONNECT`.
