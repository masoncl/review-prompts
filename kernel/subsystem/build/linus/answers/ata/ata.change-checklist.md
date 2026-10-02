- `CONFIG_SATA_HOST` and `CONFIG_PATA_TIMINGS`: have no prompt in
  `drivers/ata/Kconfig`; only a `select` turns them on, so code outside the
  core that calls into `drivers/ata/libata-sata.c` or
  `drivers/ata/libata-pata-timings.c` needs `select SATA_HOST` or
  `select PATA_TIMINGS`, as `SCSI_SAS_ATA` and `SCSI_HISI_SAS` do for
  `SATA_HOST`.
- `CONFIG_PM_SLEEP`: not used in `drivers/ata/libata-*.c` or
  `include/linux/libata.h`; the PM guards there are `CONFIG_PM`.
- **Potentially unsafe usage**: calling a function that
  `include/linux/libata.h` declares with no guard and no stub, but that is
  defined in an optional file.
  - Unsafe: from `libata-core.c`, `libata-eh.c`, `libata-scsi.c`,
    `libata-transport.c` or `libata-trace.c`, outside an `#ifdef` of the
    option; it compiles and then fails to link with the option off. For
    example `ata_tf_to_fis()`, `sata_link_debounce()`,
    `ata_qc_complete_multiple()`, `sata_async_notification()`
    (`libata-sata.c`) and `ata_timing_compute()` (`libata-pata-timings.c`).
  - Safe: from a file or region built only with the option, as
    `sata_pmp_set_lpm()` in `libata-pmp.c` calls `sata_link_scr_lpm()`
    (`SATA_PMP` depends on `SATA_HOST`), and `ata_timing_cycle2mode()` calls
    `ata_timing_find_mode()` inside `#ifdef CONFIG_ATA_ACPI` (`ATA_ACPI`
    selects `PATA_TIMINGS`).
- `sata_pmp_port_ops`, `sata_pmp_qc_defer_cmd_switch`,
  `sata_pmp_error_handler`: without `CONFIG_SATA_PMP` these are `#define`
  aliases for `sata_port_ops`, `ata_std_qc_defer` and
  `ata_std_error_handler`, so each pair must keep the same type.
- `ATA_NCQ_SHT()`, `ata_ncq_sdev_groups`, the debounce timing arrays such as
  `sata_deb_timing_normal` and the SATA attributes such as
  `dev_attr_ncq_prio_enable`: exist only under `CONFIG_SATA_HOST`, with
  no fallback.
- `include/linux/libata.h` is parsed with `CONFIG_ATA` unset: for example by
  `drivers/pnp/resource.c` and through `include/scsi/libsas.h`; that is why
  `ata_scsi_dma_need_drain` becomes `NULL` unless `IS_REACHABLE(CONFIG_ATA)`.
- Users of the libata structures outside `drivers/ata/`: all under
  `drivers/scsi/` (libsas, hisi_sas, pm8001, isci, mvsas, aic94xx) and
  `include/scsi/`; `drivers/scsi/ipr.c` does not use libata.
- `include/linux/ata.h` users with no libata: search for
  `#include <linux/ata.h>`; they include `drivers/hwmon/drivetemp.c`,
  `drivers/block/aoe/aoecmd.c` and `arch/um/drivers/ubd_kern.c`.
- libsas port: `sas_ata_init()` in `drivers/scsi/libsas/sas_ata.c` allocates
  a bare `struct ata_host` (no `ports[]` entries, `n_ports` 0), sets
  `ATA_FLAG_SAS_HOST`, and points `ap->scsi_host` at the HBA's shared
  `struct Scsi_Host`.
- **Potentially unsafe usage**: `ata_shost_to_port()` in core code.
  - Unsafe: on a path libsas reaches; that host's `hostdata` holds a
    `struct sas_ha_struct *` (`SHOST_TO_SAS_HA()` in
    `include/scsi/libsas.h`), not a `struct ata_port *`.
  - Safe: in a callback installed only by `__ATA_BASE_SHT()`, whose host
    `ata_scsi_add_hosts()` filled in; `ata_scsi_ioctl()` does this and passes
    `ap` to `ata_sas_scsi_ioctl()`, the variant libsas calls.
  - Safe: on any host allocated by `ata_scsi_add_hosts()`, which stores the
    port pointer in `hostdata`, as `ata_scsi_queuecmd()` does, and as
    `ata_scsi_error()` does, which is installed through `ata_scsi_transportt`
    and not through `__ATA_BASE_SHT()`.
- `qc->private_data` of an internal command: `sas_ata_task_abort()` reads it
  as the `struct completion *` that `ata_exec_internal()` stores.
- `include/trace/events/libata.h`: has no `CONFIG_` guard and is built in
  every config (`libata-trace.o` is in `libata-y`), SFF and BMDMA events
  included; a field read in `TP_fast_assign()` must exist in every config, as
  `hsm_task_state` does outside the `CONFIG_ATA_SFF` block.
- Trace flags: `include/trace/events/libata.h` has no `__print_flags()`
  table; the flags with the `ATA_QCFLAG_`, `ATA_TFLAG_`, `ATA_EH_` and
  `AC_ERR_` prefixes are decoded by functions such as
  `libata_trace_parse_qc_flags()` in `drivers/ata/libata-trace.c`.
- Trace decoder strings: are literals, so a flag rename breaks the build
  there but leaves the printed text unchanged; the four flag decoders print
  the raw hex value first, so an undecoded bit is still visible.
- Trace value names: `show_opcode_name()`, `show_protocol_name()`,
  `show_class_name()`, `show_error_name()` and `show_sff_hsm_state_name()`
  stringify the macro name, so renaming a constant listed there, such as
  `ATA_CMD_READ_LONG_ONCE`, `ATA_PROT_NCQ`, `ATA_DEV_ZAC` or `HSM_ST_LAST`,
  changes the trace output text.
- `TRACE_DEFINE_ENUM()`: not used in `include/trace/events/libata.h`.
- Device flags (`dev->flags`, for example `ATA_DFLAG_DEVSLP`): no tracepoint
  prints them.
- Tracepoints called from LLD modules: need
  `EXPORT_TRACEPOINT_SYMBOL_GPL()` in `drivers/ata/libata-core.c`; a renamed
  event must be renamed there too.
- Transport sysfs file names: `ata_dev_attr()`, `ata_dev_simple_attr()` and
  `ata_link_linkspeed_attr()` in `drivers/ata/libata-transport.c` use the
  struct field name as the file name, so renaming `class`, `pio_mode`,
  `dma_mode`, `xfer_mode`, `spdn_cnt`, `hw_sata_spd_limit`, `sata_spd_limit`
  or `sata_spd` renames the file; `ata_port_simple_attr()` takes the name
  separately.
- `ata_class_names[]`: also read by exported `ata_port_classify()`, which
  logs "found unknown device" for a class with no entry.
- ABI text: transport files are in `Documentation/ABI/testing/sysfs-ata`;
  the SCSI host and device attributes are in
  `Documentation/ABI/testing/sysfs-class-scsi_host` and
  `Documentation/ABI/testing/sysfs-block-device`.
- `libata.force` keywords: come from the first argument of the macros such
  as `force_quirk_on()` in `force_tbl[]` (`force_quirk_onoff()` and
  `force_lflag_onoff()` also make a second keyword with "no" in front), not
  from the flag name; renaming a constant such as `ATA_QUIRK_NONCQ` or
  `ATA_LFLAG_NO_HRST` leaves the keywords unchanged.
- `struct ata_force_param`: holds `lflags_on` and `lflags_off` as `u16`, so
  a forceable link flag above bit 15 needs the fields widened.
- `ata_quirk_names[]`: indexed by the bit numbers of `enum ata_quirks`, such
  as `__ATA_QUIRK_NODMA`; nothing at build time checks that a new quirk has
  an entry (the only check is `BUILD_BUG_ON(__ATA_QUIRK_MAX > 64)`).
- "horkage": no identifier in this tree has it in its name; the one
  occurrence is a stale comment in `drivers/scsi/isci/request.c`; quirks are
  bits such as `ATA_QUIRK_NOTRIM` in `dev->quirks`.
