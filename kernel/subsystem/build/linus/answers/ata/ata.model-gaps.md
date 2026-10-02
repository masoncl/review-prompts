- Models take `ata_port_freeze()`, `ata_port_abort()` and
  `ata_port_schedule_eh()` to always schedule EH. `ata_std_sched_eh()` returns
  early while `ATA_PFLAG_INITIALIZING` is set, which is from
  `ata_port_alloc()` until `ata_port_probe()`.
- Models take `ata_dev_configure()` to touch only per-device state.
  `ata_dev_config_lpm()` can set `ATA_QUIRK_NOLPM` and force
  `ap->target_lpm_policy` to `ATA_LPM_MAX_POWER`.
- Models take revalidation in `ata_eh_revalidate_and_attach()` to start at
  IDENTIFY. When `link->lpm_policy` is above `ATA_LPM_MAX_POWER` it first
  calls `ata_eh_link_set_lpm()` with `ATA_LPM_MAX_POWER`.
- Models take EH entry to be copy-and-clear only.
  `ata_scsi_port_error_handler()` runs `ata_eh_handle_port_resume()` before the
  copy; without `CONFIG_PM` that is an empty stub. `ata_eh_recover()` serves
  `ATA_EH_SET_ACTIVE` with `ata_dev_power_set_active()`.
- Models do not know that a port can lack `freeze` and `thaw`. `sas_sata_ops`
  in `drivers/scsi/libsas/sas_ata.c` has neither; `__ata_port_freeze()` and
  `ata_eh_thaw_port()` test the pointer before the call.
- Models take `ata_msleep()` to always drop EH ownership while it sleeps. It
  calls `ata_eh_release()` and `ata_eh_acquire()` only when `ap` is not NULL
  and `ap->host->eh_owner == current`.
- Models take `ata_log_supported()` to return a bool. Its failures return 0,
  not an errno.
- Models take every quirk to be printable. `ata_dev_print_quirks()` returns
  without printing once `ATA_EHI_DID_PRINT_QUIRKS` is set in `ehc->i.flags` of
  the link.
- Models take `ata_eh_reset()` to take the link and four callbacks. Its
  parameters are the port, the link, `classify` and one
  `struct ata_reset_operations` pointer.
- Models name ata_do_eh(). There is none; `ata_std_error_handler()` calls
  `ata_eh_autopsy()`, `ata_eh_report()`, `ata_eh_recover()` and
  `ata_eh_finish()` itself.
