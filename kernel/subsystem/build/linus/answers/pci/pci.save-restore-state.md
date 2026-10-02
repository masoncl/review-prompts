- `pci_bus_add_device()` in `drivers/pci/bus.c`: saves every device it adds,
  after the `pci_fixup_final` fixups and before `pm_runtime_enable()`.
- `pci_set_power_state()` and the AER and DPC recovery code: do not call
  `pci_save_state()`.
- `pci_pm_poweroff_noirq()`: does not save; only its legacy branch,
  `pci_legacy_suspend_late()`, does, when `state_saved` is clear.
- `pci_pm_suspend_noirq()` with no `pm` ops: saves without testing
  `state_saved`.
- `pci_dev_save_and_disable()`: skips the save when
  `pci_dev_config_accessible()` reads all ones; `pci_dev_restore()` still
  calls `pci_restore_state()`, which restores the older saved state.
- `pci_restore_state()`: does not test `state_saved`; it restores whatever
  `saved_config_space` and the capability save buffers hold.
- `pci_restore_state()` with no save in the same path: relied on by
  `pcibios_reset_secondary_bus()`.
- `pci_restore_state()`: clears `state_saved` as its last step and leaves the
  buffers intact, so a second restore restores the same state again.
- `pci_store_saved_state()`: returns `NULL` while `state_saved` is clear, for
  example after a restore with no save since.
- `pci_load_saved_state()` with a `NULL` state: clears the flag, returns 0,
  leaves the buffers as they were.
- `state_saved` outside PM: set by `pci_bus_add_device()` and stays set until
  a restore, `pci_load_saved_state()` or a PM callback clears it, so a set
  flag alone does not show that a driver saved state.
- Clearing before the driver callback: unconditional in
  `pci_legacy_suspend()`, in `pci_pm_freeze()` when the driver has `pm` ops
  and, with a driver bound, in `pci_pm_runtime_suspend()`;
  `pci_pm_suspend()` and `pci_pm_poweroff()` clear it only on the branch that
  calls `pm_runtime_resume()`.
- Flag set after the callback: `pci_pm_suspend_noirq()` and
  `pci_pm_runtime_suspend()` skip `pci_save_state()` and also
  `pci_prepare_to_sleep()` or `pci_finish_runtime_suspend()`.
- Flag clear after the `suspend_noirq` or `runtime_suspend` callback,
  `current_state` neither `PCI_D0` nor `PCI_UNKNOWN`:
  `pci_pm_suspend_noirq()` and `pci_pm_runtime_suspend()` skip the save too,
  and warn once if the callback changed the state.
- Flag clear in `pci_pm_poweroff_noirq()`, device with no subordinate bus:
  `pci_prepare_to_sleep()` runs with no save.
- Flag still set in `pci_pm_resume()` or `pci_pm_restore()`: taken to mean
  the noirq-phase restore did not run; they call
  `pci_restore_standard_config()`.
