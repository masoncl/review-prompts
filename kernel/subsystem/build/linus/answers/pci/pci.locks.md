- Functions that require a lock held by the caller:

| function | lock | checked by |
|---|---|---|
| `pci_stop_and_remove_bus_device()` | `pci_rescan_remove_lock` | `lockdep_assert_held()` |
| `pci_rescan_bus()`, `pci_rescan_bus_bridge_resize()` | `pci_rescan_remove_lock` | comment above the mutex in `drivers/pci/probe.c` only |
| `pci_walk_bus_locked()` | `pci_bus_sem` | `lockdep_assert_held()` |
| `pci_set_power_state_locked()` | `pci_bus_sem` | its own `lockdep_assert_held()` |
| `pci_enable_link_state_locked()`, `pci_disable_link_state_locked()` | `pci_bus_sem`, read | `lockdep_assert_held_read()` |
| `pci_bus_max_d3cold_delay()` | `pci_bus_sem` | `lockdep_assert_held()` |
| `pci_wait_cfg()` | `pci_lock` | `__must_hold()` annotation only |

- `pci_stop_and_remove_bus_device()`: the only assertion on
  `pci_rescan_remove_lock` in the tree.
- `pci_bus_sem`: declared in `drivers/pci/pci.h` and not exported; no code
  outside `drivers/pci` takes it. A driver holds it when the core calls it
  under the lock, for example in a `pci_walk_bus()` callback; the `_locked`
  functions are the forms that do not take it again there, as
  `vmd_pm_enable_quirk()` in `drivers/pci/controller/vmd.c` uses them.
- `pci_get_device()` does not take `pci_bus_sem`; `pci_get_slot()` does.
- `pci_lock` with `CONFIG_PCI_LOCKLESS_CONFIG`: only
  `pci_bus_read_config_byte()`, `pci_bus_write_config_byte()` and their word
  and dword siblings skip it, through `pci_lock_config()` in
  `drivers/pci/access.c`. `pci_user_read_config_dword()` and its byte, word
  and write siblings, `pci_cfg_access_lock()`, `pci_bus_set_ops()` and
  `pci_check_and_set_intx_mask()` take it unconditionally.
