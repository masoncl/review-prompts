# ATA Subsystem

## Main structures

### Objects and how they relate

- `ap->lock`: a pointer, set to `&host->lock` in `ata_port_alloc()`, so the
  ports of one `struct ata_host` share that spinlock; the exception is
  `ahci_port_start()`, which repoints it at a per-port lock under
  `AHCI_HFLAG_MULTI_MSI`.
- `struct ata_port_operations` tables: `ata_finalize_port_ops()` rewrites the
  table in place from `ata_host_start()` and clears `inherits`; from then on a
  NULL method means absent.
- `ATA_OP_NULL`: in an initializer, forces a method to absent although a parent
  table has it.
- `struct ata_port_info`: `ata_host_alloc_pinfo()` copies the masks and flags
  but stores `pi->port_ops` as `ap->ops`, so ports built from one template
  share one ops table.
- SCSI EH entry: `ata_scsi_error()` is `.eh_strategy_handler` of
  `ata_scsi_transportt` in `drivers/ata/libata-transport.c`, which
  `ata_scsi_add_hosts()` installs as `shost->transportt`; of the EH hooks, the
  `struct scsi_host_template` macros supply only `.eh_timed_out`.
- EH thread: the SCSI EH thread of the port's `struct Scsi_Host`, so one per
  port for a host from `ata_scsi_add_hosts()`; `host->eh_mutex`, taken in
  `ata_eh_acquire()`, lets only one port of a host run EH at a time.
- libsas ports: built in `sas_ata_init()` in `drivers/scsi/libsas/sas_ata.c`
  with `ata_host_init()`, `ata_port_alloc()` and `ata_tport_add()`; there is no
  port-allocation helper with an ata_sas prefix.
- libsas objects: one `struct ata_host` and one `struct ata_port` per SATA
  device, the port marked `ATA_FLAG_SAS_HOST`; that host has `n_ports` 0 and
  no `ports[]` entries, so a walk over `host->ports[]` never reaches the port.
- libsas command EH: `sas_ata_eh()` calls `ata_scsi_cmd_error_handler()` in the
  HBA's EH thread, once per SATA device that has commands on the work list.
- libsas port EH: `sas_ata_strategy_handler()` runs
  `ata_scsi_port_error_handler()` once per SATA device through
  `async_schedule_domain()`, and the HBA's EH thread waits for them.
- `qc->tag` and `qc->hw_tag`: equal for SCSI commands; the internal qc has
  `tag` `ATA_TAG_INTERNAL` and `hw_tag` 0.
- `ap->qc_active` is indexed by `qc->tag`, `link->sactive` by `qc->hw_tag`;
  `ata_qc_get_active()` folds the internal bit onto bit 0 for drivers.
- `ap->qcmd[]`: `ATA_MAX_QUEUE + 1` entries; `ata_qc_for_each_raw()` stops
  before the internal slot.
- `ATA_MAX_DEVICES`: 2; `ata_link_max_devices()` returns 2 only when
  `ata_is_host_link()` is true and the port has `ATA_FLAG_SLAVE_POSS`,
  otherwise 1.
- PMP control link: `ap->link` itself; `sata_pmp_attach()` sets its `pmp` to
  `SATA_PMP_CTRL_PORT` and the PMP is `ap->link.device[0]`.
- `ap->pmp_link`: allocated once with `SATA_PMP_MAX_PORTS` entries in
  `sata_pmp_init_links()`, kept by `sata_pmp_detach()`, freed in
  `ata_port_free()`.
- **Potentially unsafe usage**: testing `ap->pmp_link` to see if a PMP is
  attached.
  - Unsafe: when the code needs to know whether a PMP is attached now; after a
    PMP was detached the array is still allocated and `ap->nr_pmp_links` is 0.
    `sata_pmp_attached()` tests `ap->nr_pmp_links`.
  - Safe: when the code needs to know whether the array exists, as
    `ata_port_detach()` does before it deletes the link transport objects that
    `sata_pmp_init_links()` added for all `SATA_PMP_MAX_PORTS` entries.
- `ata_for_each_link()` modes: `EDGE` gives the fan-out links only when a PMP
  is attached, else the host link, and never `ap->slave_link`; `HOST_FIRST`
  and `PMP_FIRST` give all of them. See `ata_link_next()`.
- `struct scsi_device` mapping: `ata_scsi_scan_host()` walks `EDGE`, so the PMP
  itself, `ap->link.device[0]`, gets no `dev->sdev` while it is attached.
- SCSI address: `id` is `dev->devno` on the host link; behind a PMP `channel`
  is `link->pmp` and `id` is 0. See `ata_scsi_scan_host()` and
  `__ata_scsi_find_dev()`.
- Slave link: the second device stays `ap->link.device[1]` with `dev->link`
  the host link; only `ata_dev_phys_link()` maps it to `ap->slave_link`.
- `ata_slave_link_init()`: warns if the port has `ATA_FLAG_PMP`;
  `ata_link_next()` treats slave link and PMP links as exclusive.

## Where to look

### Configuration path

| # | Step | Start reading from | Context | Easy to miss |
|---|---|---|---|---|
| 1 | Request the probe | `ata_port_probe()` in `drivers/ata/libata-core.c`, from `async_port_probe()`; libsas: `sas_probe_sata()` | **Not EH.** Async worker; libsas: discovery work (`sas_discover_domain()`, `sas_revalidate_domain()`) | Sets `ATA_PFLAG_LOADING`, which decides step 10 |
| 2 | Enter EH | `ata_scsi_error()` → `ata_scsi_port_error_handler()` → `ap->ops->error_handler` → `ata_eh_recover()` | EH thread. libsas port: **normally not the EH thread itself**; inside `async_sas_ata_eh()`, scheduled with `async_schedule_domain()` by `sas_ata_strategy_handler()`, which the EH thread waits for (`async_schedule_node_domain()` runs the function in the caller when it cannot queue it) | There is no ata_do_eh; `ata_eh_recover()` is called by `ata_std_error_handler()` and, through `sata_pmp_eh_recover()`, by `sata_pmp_error_handler()`, and a driver's own handler, for example `ahci_error_handler()`, ends in one of them. Steps 3–10 run in the same task as this step |
| 3 | Reset and classify into `ehc->classes[]` | `ata_eh_reset()` | as step 2 | Methods arrive as `struct ata_reset_operations` (`ap->ops->reset`, or `ap->ops->pmp_reset` for fan-out links); `struct ata_port_operations` has no reset method members of its own |
| 4 | IDENTIFY a new device | first loop of `ata_eh_revalidate_and_attach()` → `ata_dev_read_id()` | as step 2 | A class other than ATA, ZAC, ATAPI or SEMB returns `-ENODEV`; `ata_dev_read_id()` does not classify an unknown device |
| 5 | Port multiplier instead of step 4 | `sata_pmp_attach()` | as step 2 | `ata_eh_recover()` then returns 0; `sata_pmp_eh_recover()` calls it again with `ap->ops->pmp_reset`, and fan-out devices go through steps 3–9 in that call |
| 6 | Configure | second loop of `ata_eh_revalidate_and_attach()` → `ata_dev_configure()` | as step 2 | Calls `ata_acpi_on_devcfg()` and `ap->ops->dev_config()`. `xfer_mask` here is only printed. Runs again in step 8 when `ata_dev_set_mode()` runs |
| 7 | Mark for attach | tail of the second loop: `ATA_PFLAG_SCSI_HOTPLUG` in `ap->pflags` | as step 2 | There is no ATA_DEV_ATTACH. No work is queued here for a new device; `ap->scsi_rescan_task` is scheduled in the revalidate branch, for a device that was already enabled |
| 8 | Transfer mode | `ata_eh_set_mode()` in `drivers/ata/libata-eh.c` → `ap->ops->set_mode()` or `ata_set_mode()` in `drivers/ata/libata-core.c` → `ata_dev_set_mode()` → `ata_dev_set_xfermode()` | as step 2 | There is no ata_do_set_mode. `ata_set_mode()` computes the masks with `ata_dev_xfermask()`. `ata_dev_set_mode()` calls `ata_dev_revalidate()`, which runs `ata_dev_configure()` a second time, without `ATA_EHI_PRINTINFO` |
| 9 | Link power policy | `ata_eh_link_set_lpm()`, from `ata_eh_recover()` | as step 2 | There is no ata_eh_set_lpm |
| 10 | Hand off | tail of `ata_scsi_port_error_handler()` | as step 2 | `ATA_PFLAG_LOADING` set: cleared, nothing queued. Otherwise `ap->hotplug_task` is queued on `system_dfl_long_wq` if `ATA_PFLAG_SCSI_HOTPLUG` is set and `ATA_FLAG_SAS_HOST` is not. `ATA_PFLAG_SCSI_HOTPLUG` is only tested and cleared here |
| 11 | SCSI scan | `ata_scsi_scan_host()`, from `async_port_probe()` or `ata_scsi_hotplug()`; libsas: `sas_rphy_add()` → `scsi_scan_target()`, from `sas_probe_devices()` | **Not EH.** Task of step 1, or `ap->hotplug_task` work | `ata_scsi_scan_host()` is not called for libsas ports |
| 12 | SCSI configure, attach | `ata_scsi_sdev_configure()` → `ata_scsi_dev_config()`; libsas: `sas_sdev_configure()` → `ata_sas_sdev_configure()` | **Not EH.** Scanning task of step 11 | `ata_scsi_dev_config()` sets `dev->sdev`; `ata_scsi_scan_host()` stores it again when `__scsi_add_device()` succeeds. On libsas ports only `ata_scsi_dev_config()` sets it |

## Configuring a device

**Revalidation and configure reruns**

- `ata_dev_set_mode()`: calls `ata_dev_revalidate()` with `ATA_DEV_UNKNOWN` and
  flags 0, so a transfer-mode change through `ata_set_mode()` reruns
  `ata_dev_configure()`.
- `ATA_READID_POSTRESET`: passed only by `ata_eh_revalidate_and_attach()`, when
  `ATA_EHI_DID_RESET` is set.
- `ATA_EH_REVALIDATE`: also set by `ata_eh_link_autopsy()` when the port is not
  frozen and no `AC_ERR_HSM` or `AC_ERR_TIMEOUT` was seen: for any error when a
  failed command has `ATA_QCFLAG_IO`, otherwise for an error other than
  `AC_ERR_DEV`; besides `ata_eh_reset()` and `ata_qc_complete()`.
- `ata_eh_revalidate_and_attach()`: returns `-EIO` without calling
  `ata_dev_revalidate()` when `ata_eh_link_established()` is false.
- `new_class` in `ata_dev_revalidate()`: only tested for `ATA_DEV_PMP`
  (`-ENODEV`); it is not compared with `dev->class`.
- `ata_dev_same_device()`: compares `dev->class` with the class that
  `ata_dev_read_id()` returned, by strict equality, then `ATA_ID_PROD` and
  `ATA_ID_SERNO`; the firmware revision is not compared.
- `ata_hpa_resize()` (after it unlocked the HPA) and `ata_acpi_on_devcfg()`
  (under `CONFIG_ATA_ACPI`, after a _GTF command ran): call
  `ata_dev_reread_id()` from inside `ata_dev_configure()`, so the same compare
  can fail there and `ata_dev_configure()` returns its `-ENODEV`.
- Capacity compare after configure: skipped when `dev->class` is not
  `ATA_DEV_ATA` (so not for `ATA_DEV_ZAC`), when the saved `n_sectors` was 0,
  or when `ata_id_is_locked()` is true.
- Late HPA lock (native size unchanged, size shrank, old size equalled native,
  no `ATA_QUIRK_BROKEN_HPA`): not accepted; sets `ATA_DFLAG_UNLOCK_HPA` and
  returns `-EIO` so the retry unlocks.
- `dev->quirks`: there is no dev->horkage or ata_dev_blacklisted() here;
  `ata_dev_configure()` ORs in `ata_dev_quirks()` and never assigns;
  `ata_force_quirks()` clears only the `quirk_off` bits of a `libata.force`
  entry; only `ata_dev_init()` zeroes it.
- `ATA_DFLAG_CFG_MASK`: bits 0 to 16 only; `ATA_DFLAG_DEVSLP`, `ATA_DFLAG_DA`,
  `ATA_DFLAG_NCQ_PRIO_ENABLED` and `ATA_DFLAG_CDL_ENABLED` are above it and
  survive a rerun unless a helper clears them, as the not-supported path of
  `ata_dev_config_cdl()` does for `ATA_DFLAG_CDL_ENABLED`.

**Configuration failure**

- Budget: `ehc->tries[]` is set at the start of each `ata_eh_recover()` call,
  to `ATA_EH_DEV_TRIES`, or to 1 on a link with `ATA_LFLAG_NO_RETRY`;
  `ata_eh_handle_dev_fail()` sets it back to `ATA_EH_DEV_TRIES` when it
  schedules a probe. Every `rest_fail` path in the same call that reports a
  failed device draws on it, for example set-mode, flush and LPM failures.

| errno | Effect in `ata_eh_handle_dev_fail()` | Attempts in total, from `ATA_EH_DEV_TRIES` |
|---|---|---|
| `-EAGAIN` | no decrement, no slow-down | not limited here |
| `-ENODEV` | decrement, `probe_mask` bit, clamp to 1, slow-down | 2 |
| `-EINVAL` | decrement, clamp to 1, slow-down | 2 |
| `-EIO` | decrement, slow-down when 1 is left | 3 |
| any other, such as `-ENOENT` | decrement only | 3 |

- `-EAGAIN`: comes from `ata_do_link_spd_quirk()` in `ata_dev_configure()`,
  which lowers `sata_spd_limit` first so that the retry makes progress.
- `-ENOENT` from `ata_dev_read_id()`: swallowed only in the new-device branch of
  `ata_eh_revalidate_and_attach()`, which thaws the port with
  `ata_eh_thaw_port()` and ignores the device; through `ata_dev_revalidate()`
  it reaches `ata_eh_handle_dev_fail()` and matches no case.
- Slow-down: runs only when tries is exactly 1 after the decrement and clamp;
  it lowers the link speed with `sata_down_spd_limit()` on the physical link,
  and calls `ata_down_xfermask_limit()` with `ATA_DNXFER_PIO` only if
  `dev->pio_mode > XFER_PIO_0`.
- `ata_dev_disable()`: does not set `ATA_DEV_NONE`; `ata_eh_dev_disable()` does
  `dev->class++`, giving for example `ATA_DEV_ATA_UNSUP`, and frees `dev->cdl`.
- `ata_eh_detach_dev()` in `ata_eh_handle_dev_fail()`: called only if the
  physical link is offline, or from `ata_eh_schedule_probe()`.
- `ata_eh_schedule_probe()`: acts only if the `probe_mask` bit is set and the
  `did_probe_mask` bit is clear, so once per slot per EH pass; it calls
  `ata_dev_init()`, which zeroes `dev->quirks`.
- New device that fails IDENTIFY or configure: `dev->class` is
  `ATA_DEV_UNKNOWN` when `ata_eh_handle_dev_fail()` runs, so
  `ata_dev_disable()` is never called; with tries at 0
  `ata_eh_revalidate_and_attach()` skips the slot and it stays
  `ATA_DEV_UNKNOWN`.
- Return value of `ata_eh_handle_dev_fail()`: ignored by `ata_eh_recover()`,
  which retries whenever any link failed, except on a frozen port with a PMP
  attached.

**Optional feature setup**

- `ata_dev_config_ncq()`: returns `int`; `ata_dev_config_lba()`, also `int`,
  passes the value on to `ata_dev_configure()`. Every other static helper in
  `drivers/ata/libata-core.c` named like `ata_dev_config_cdl()` is `void`.
- `ata_dev_config_cdl()`: `void`; it absorbs the `-ENOMEM` or `-EIO` of
  `ata_dev_init_cdl_resources()` and goes to its not-supported path.
- `ata_dev_config_cdl()` not-supported path: also taken when SET FEATURES for
  `SETFEATURES_CDL` or `SETFEATURE_SENSE_DATA_SUCC_NCQ` fails; a clear command
  duration guideline bit only warns.
- Flag clearing: only `ata_dev_config_ncq_prio()`, `ata_dev_config_cdl()`,
  `ata_dev_config_depop()` and `ata_dev_config_fua()` have a path that clears
  flags; the other helpers just return, so only bits inside
  `ATA_DFLAG_CFG_MASK` are reset for them.
- **Potentially unsafe usage**: a feature helper that returns on missing or
  invalid data without clearing a `dev->flags` bit that belongs to the
  feature.
  - Unsafe: when the bit is outside `ATA_DFLAG_CFG_MASK`; it keeps the value of
    an earlier `ata_dev_configure()` pass.
  - Safe: when the bit is inside `ATA_DFLAG_CFG_MASK`, which
    `ata_dev_configure()` clears before the helpers run, as
    `ata_dev_config_trusted()` with `ATA_DFLAG_TRUSTED`.
  - Safe: when every failure return goes through a path that clears the bit,
    as the `not_supported` label of `ata_dev_config_cdl()` does for
    `ATA_DFLAG_CDL_ENABLED`.
- `ata_dev_config_zoned()`: there is no ata_dev_config_zac() here; it sets the
  three limits to `U32_MAX` first and takes each field only if its bit 63 is
  set.
- `ata_do_link_spd_quirk()`: the name here for the link-speed step; there is no
  ata_do_link_spd_horkage().

**Checking device-reported data**

- `ata_dev_read_id()`: has no checksum, capacity or geometry check; the only
  validity test of IDENTIFY content is the type test, which returns `-EINVAL`.
- **Potentially unsafe usage**: returning a negative errno from code reached
  from `ata_dev_configure()` because device data fails a check.
  - Unsafe: when the data only serves an optional feature, or is a version or
    reserved field; the retry reads the same data, `ata_eh_handle_dev_fail()`
    clamps `-EINVAL` to one more attempt, and an attached device ends in
    `ata_dev_disable()`, while a new one is never attached.
  - Safe: when no command can be built without the data, as the ATAPI CDB
    length test in `ata_dev_configure()`; `cdb[ATAPI_CDB_LEN]` in
    `struct ata_queued_cmd` defines the upper bound.
  - Safe: when the data says it is another device, as `-ENODEV` from
    `ata_dev_reread_id()`; `ata_eh_handle_dev_fail()` then sets the
    `probe_mask` bit so the slot is probed again.
- **Potentially unsafe usage**: using a device-reported count as a loop bound
  or size.
  - Unsafe: when the count can exceed the buffer it indexes, or a buffer that a
    later consumer fills; `ata_scsiop_inq_b9()` writes `nr_cpr` descriptors
    into `ata_scsi_rbuf` with no check of its own.
  - Safe: `ata_dev_config_cpr()` rejects a count above `ATA_DEV_MAX_CPR` or
    larger than the log it read, warns, and sets `dev->cpr_log` to NULL.
  - Safe: `ata_identify_page_supported()` loops on the `u8` count at offset 8
    over entries from offset 9, which stays inside `dev->sector_buf` of
    `ATA_SECT_SIZE` bytes.
- R/W multiple count in `ata_dev_configure()`: taken only if both values are
  powers of two and the count is within the maximum; otherwise `multi_count`
  stays 0 and nothing fails.

**Log directory**

- `ata_dev_configure()`: calls `ata_clear_log_directory()` as its first step
  after the enabled test, so the first `ata_log_supported()` call of each run,
  including each revalidation, reads the directory from the device again.
- `ata_dev_init()`: zeroes `dev->gp_log_dir` too; it lies between
  `ATA_DEVICE_CLEAR_BEGIN` and `ATA_DEVICE_CLEAR_END`.
- Callers: `ata_log_supported()` is static in `drivers/ata/libata-core.c` and
  every caller is reached from `ata_dev_configure()`; EH code in
  `drivers/ata/libata-sata.c` reads logs without consulting the directory.
- Cache test in `ata_read_log_directory()`: the cached version word must be
  0x0001; a device with any other version word is read again on every
  `ata_log_supported()` call.
- Wrong version word: `ata_dev_warn_once()`, return 0, the directory is used,
  no quirk is set.
- `ATA_FLAG_NO_LOG_PAGE` on the port: every directory read fails, so
  `ata_log_supported()` returns 0 for every log.

**Log support check result**

- Return type: `int`, not `bool`; for a supported log it is the 16-bit
  directory entry, the number of pages in the log.
- `ata_dev_config_cpr()`: uses the value as the number of sectors to allocate
  and read, so the count must be kept.

**Log page reads**

- ATA_QUIRK_NO_NCQ_LOG: not in this tree.

| Name | Tested in | Effect |
|---|---|---|
| `ATA_FLAG_NO_LOG_PAGE` | `ata_read_log_page()` | returns `AC_ERR_DEV`, no command, no `ata_dev_err()` message |
| `ATA_QUIRK_NO_DMA_LOG` | `ata_read_log_page()` | PIO only; the read still happens |
| `ATA_QUIRK_NO_LOG_DIR` | `ata_log_supported()` | directory not read |
| `ATA_QUIRK_NO_ID_DEV_LOG` | `ata_identify_page_supported()` | IDENTIFY DEVICE data log not read |

- `ata_eh_read_log_10h()` and `ata_eh_get_ncq_success_sense()` in
  `drivers/ata/libata-sata.c`: call `ata_read_log_page()` directly, so only the
  first two rows apply to them.

## Quirks

**Quirk flags**

- `quirks` in `struct ata_device`: `u64`.
- `enum ata_quirks`: holds bit numbers spelled like `__ATA_QUIRK_NODMA`; the
  masks, spelled like `ATA_QUIRK_NODMA`, are in the anonymous enum after it and
  use `BIT_ULL()`. No enumerator has a _BIT suffix.
- Limit: `BUILD_BUG_ON(__ATA_QUIRK_MAX > 64)` in the body of
  `ata_dev_quirks()` in `drivers/ata/libata-core.c`. There is no
  `static_assert()` for it; `include/linux/libata.h` has only a comment.
- `ata_dev_print_quirks()`: takes the mask as `unsigned int` and tests
  `1U << i`, so a flag with bit number 32 or more is cut from the mask;
  printing it needs the parameter and the test widened.
- `ata_quirk_names[]` with a hole for the new flag: the entry is NULL and the
  log shows "(null)".
- `ata_quirk_names[]` with no entry for the last enumerator: the array is
  shorter, the loop never reaches the bit, nothing is printed for it.
- `force_tbl[]`: a separate table at file scope in
  `drivers/ata/libata-core.c`, under `CONFIG_ATA_FORCE`; `ata_parse_force_one()`
  reads only this table, never `ata_quirk_names[]`.
- Keywords in `force_tbl[]` are their own strings, for example `trim_zero` there
  against `"zeroaftertrim"` in `ata_quirk_names[]`.
- A flag with no `force_tbl[]` entry works but cannot be forced; several flags
  have none, for example `ATA_QUIRK_BROKEN_HPA`.
- `ata_parse_force_one()` accepts any unique prefix of a keyword, exact match
  first; a new keyword that shares a prefix with an existing one makes that
  abbreviation fail with "ambiguous value".

**Quirk table matching**

- Entry with mask 0: still ends the walk, so `ata_dev_quirks()` returns 0;
  `{ "INTEL*SSDSC2MH*", NULL, 0 }` in `__ata_dev_quirks[]` uses this to exempt a
  model from the wider globs after it.
- Value quirk: the flag word holds only `ATA_QUIRK_MAX_SEC`; the sector count
  is in `__ata_dev_max_sec_quirks[]`, an array of
  `struct ata_dev_quirk_value`, in `drivers/ata/libata-core.c`.
- `ata_dev_get_quirk_value()`: handles only `ATA_QUIRK_MAX_SEC`, through
  `ata_dev_get_max_sec_quirk_value()`; it returns 0 for any other flag, so a
  new value quirk needs a branch there.
- Sources of the value, in order:
  1. `value` of the first `libata.force` entry for the device, if it is
     nonzero and the entry has `ATA_QUIRK_MAX_SEC` in `quirk_on`.
  2. the first entry of `__ata_dev_max_sec_quirks[]` that matches, with the
     same glob rules as `__ata_dev_quirks[]` but its own patterns.
  3. 0.
- Value 0: `ata_dev_configure()` takes the minimum with `dev->max_sectors`,
  which becomes 0; an `__ata_dev_quirks[]` entry with `ATA_QUIRK_MAX_SEC`
  therefore needs an entry in `__ata_dev_max_sec_quirks[]` that matches the
  same devices, as `"INTEL SSDSC2KG480G8"` has.
- The value is not stored in `struct ata_device`; it is looked up in each
  `ata_dev_configure()` pass.
- `force_tbl[]` keyword that takes a user value: its name ends in `=`, as
  `force_quirk_on(max_sec=, ATA_QUIRK_MAX_SEC)`; `force_quirk_val()` gives a
  keyword a fixed value.

**Quirks set at run time**

- `ata_dev_configure()`: does `dev->quirks |= ata_dev_quirks(dev)`; it never
  assigns, so a bit set earlier survives revalidation and reset unless one of
  the following clears it.
- `ata_dev_init()`: sets `dev->quirks = 0` under `ap->lock`; this explicit
  assignment clears the bits, not the `memset()` from
  `ATA_DEVICE_CLEAR_BEGIN`, which starts after `quirks`.
- `ata_dev_init()` callers: `ata_link_init()` and `ata_eh_schedule_probe()`;
  `ata_eh_detach_dev()` alone leaves `quirks` unchanged.
- `ata_force_quirks()`: clears the `quirk_off` bits of the first
  `libata.force` entry for the device at the start of every
  `ata_dev_configure()`, including bits set at run time in an earlier pass;
  code later in the same pass can set them again.
- `it821x_dev_config()` in `drivers/ata/pata_it821x.c`: clears
  `ATA_QUIRK_DIAGNOSTIC`, which `ata_sff_dev_classify()` may have set during
  reset; `ata_dev_configure()` tests that bit after the `dev_config` hook.
- Which error sets a bit: the tree has no common rule.
  - `ata_read_log_page()`: sets `ATA_QUIRK_NO_DMA_LOG` on any nonzero
    `err_mask` from the DMA read, also when the port is frozen.
  - `ata_dev_config_ncq()`: sets `ATA_QUIRK_BROKEN_FPDMA_AA` only when
    `err_mask` is not `AC_ERR_DEV`, then returns `-EIO`.
  - `ata_hpa_resize()`: sets `ATA_QUIRK_BROKEN_HPA` on `-EACCES`, and on any
    error from `ata_read_native_max_address()` when HPA is not to be unlocked.
- Logging: `ata_dev_print_quirks()` prints only the mask of the matched table
  entry, so a bit set at run time never shows in the "applying quirks" line.
- `ata_read_log_page()`: has no message for setting the bit; `ata_dev_err()`
  runs only if the read finally fails. `ata_hpa_resize()` warns when it sets
  its bit.
- `ATA_QUIRK_NO_LOG_DIR`: not set at run time; it comes only from
  `__ata_dev_quirks[]` and `force_tbl[]`. `ata_identify_page_supported()` sets
  `ATA_QUIRK_NO_ID_DEV_LOG` when `ata_log_supported()` returns 0.
- **Unsafe usage**: setting a quirk bit after a failed command without testing
  that bit before the command is issued.
  - Safe: test the bit first and skip the command, as `ata_hpa_resize()` does
    with `ATA_QUIRK_BROKEN_HPA`; the bit is still set on the next pass because
    `ata_dev_configure()` ORs.
  - Safe: set the bit and fail the pass, as `ata_dev_config_ncq()` does;
    `ata_eh_handle_dev_fail()` requests a reset for `-EIO` without calling
    `ata_dev_init()` while tries remain, and the retry skips the command
    because of the test before it.

## Issuing and completing commands

**Command path**

- `__ata_scsi_queuecmd()`: its first test returns `SCSI_MLQUEUE_DEVICE_BUSY`
  when `ata_port_eh_scheduled()` is true, before any CDB check.
- ata_qc_new_init(): not in this tree; `ata_scsi_qc_new()` in
  `drivers/ata/libata-scsi.c` picks and initialises the slot itself.
- `ata_scsi_qc_new()` fails in two cases only: the port is frozen, or on an
  `ATA_FLAG_SAS_HOST` port `cmd->budget_token >= ATA_MAX_QUEUE`.
- `ata_scsi_qc_new()` failure: completes the command with `DID_OK` and
  `SAM_STAT_TASK_SET_FULL` through `scsi_done()`; `ata_scsi_translate()` then
  returns 0, so no `SCSI_MLQUEUE_*` value reaches SCSI.
- Tag: `ata_scsi_qc_new()` takes `scsi_cmd_to_rq(cmd)->tag`; on
  `ATA_FLAG_SAS_HOST` ports it takes `cmd->budget_token`, not the block tag.
- Bad CDB length in `__ata_scsi_queuecmd()`: `DID_ERROR << 16` with no sense
  data.
- Opcode with no xlat function: goes to `ata_scsi_simulate()`, whose default
  case sets ILLEGAL REQUEST sense; this is not a failure of translation.
- libsas: `sas_queuecommand()` takes `ap->lock` with `spin_lock_irq()` around
  `ata_sas_queuecmd()`, which is `__must_hold(ap->lock)` and locks nothing.
- `ATA_QCFLAG_ACTIVE` and `ap->qc_active`: set in `ata_qc_issue()`, not in
  `ata_scsi_qc_new()`; a qc that was set up but not issued is not active.
- `ata_qc_issue()` failure: returns void; it ORs the error into
  `qc->err_mask` and calls `ata_qc_complete()`, and `ata_scsi_qc_issue()` still
  returns 0.
- Adapter offline (`ata_adapter_is_online()` false): `ata_scsi_find_dev()`
  returns NULL, giving `DID_BAD_TARGET`; `ata_qc_issue()` tests it again and
  fails the qc with `AC_ERR_HOST_BUS`.
- `ATA_DFLAG_SLEEPING` in `ata_qc_issue()`: the command is not issued; the
  link gets `ATA_EH_RESET` and `ata_link_abort()`, so the command goes to EH.

**Deferring a command**

| `qc_defer` returns | `ata_scsi_qc_issue()` does |
|---|---|
| 0 | `ata_qc_issue()`, returns 0 |
| `ATA_DEFER_LINK`, NCQ command | `ata_qc_free()`, returns `SCSI_MLQUEUE_DEVICE_BUSY` |
| `ATA_DEFER_LINK`, non-NCQ command | stores the qc in `link->deferred_qc`, returns 0 |
| `ATA_DEFER_LINK_EXCL` | `ata_qc_free()`, returns `SCSI_MLQUEUE_DEVICE_BUSY`; never held |
| `ATA_DEFER_PORT` | `ata_qc_free()`, returns `SCSI_MLQUEUE_HOST_BUSY`; never held |
| anything else | `WARN_ON_ONCE()`, `ata_qc_free()`, returns `SCSI_MLQUEUE_HOST_BUSY` |

- No `qc_defer` callback: the command is issued at once and never held.
- `deferred_qc` and `deferred_qc_work`: members of `struct ata_link`, one held
  command per link; there is no such field in `struct ata_port`.
- `link->deferred_qc` set: every new command for that link is freed and
  returned with `SCSI_MLQUEUE_DEVICE_BUSY` before `qc_defer` is called.
- Held qc: SCSI counts it as issued, yet it has no `ATA_QCFLAG_ACTIVE`, so
  `ata_qc_from_tag()` returns NULL for it and `ata_scsi_cmd_error_handler()`
  does not find it.
- Trigger: `ata_scsi_schedule_deferred_qc()` runs at the end of
  `ata_scsi_qc_complete()` and `atapi_qc_complete()`, for the link of the
  command that completed; it queues the work on `system_highpri_wq` only when
  `qc_defer` returns 0 for the held qc.
- Sender: `ata_scsi_deferred_qc_work()` takes `ap->lock` itself and calls
  `ata_qc_issue()`, so `qc_issue` here runs in a work item, under `ap->lock`
  taken by the work function and not by `ata_scsi_queuecmd()`.
- `ata_scsi_deferred_qc_work()`: calls `qc_defer` again inside
  `WARN_ON_ONCE()` and issues the qc whatever it returns; a held qc is passed
  to `qc_defer` once when queued, once per completion on its link, and once
  in the work.
- EH: `ata_eh_set_pending()` calls `ata_scsi_requeue_deferred_qc()` unless
  `ATA_PFLAG_EH_PENDING` is already set; each held command on the port is
  finished with `DID_REQUEUE`.
- SCSI timeout: `.eh_timed_out` is `ata_scsi_eh_timed_out()` in
  `__ATA_BASE_SHT()`; a held command that timed out is finished with
  `DID_TIME_OUT` and `SCSI_EH_DONE` is returned, other held commands get
  `DID_REQUEUE`, and EH is scheduled on the port if any command was held.
- libsas: `sas_eh_timed_out()` does the same through
  `ata_scsi_retry_deferred_qc()`.
- **Unsafe usage**: a `qc_defer` callback that returns `ATA_DEFER_LINK` on a
  path that reads or sets `ap->excl_link`.
  - Safe: return `ATA_DEFER_LINK_EXCL` in its place, as `sil24_qc_defer()` and
    `sata_pmp_qc_defer_cmd_switch()` do with the result of
    `ata_std_qc_defer()`; the `ATA_DEFER_LINK_EXCL` case in
    `ata_scsi_qc_issue()` keeps such a qc out of `link->deferred_qc`.
  - Safe: return only 0 or `ATA_DEFER_PORT`, as `mv_qc_defer()` does.
  - Safe: `ATA_DEFER_LINK` from a path that never touches `ap->excl_link`, as
    `ahci_pmp_qc_defer()` returns the result of `ata_std_qc_defer()` when no
    PMP is attached or FBS is enabled, and calls
    `sata_pmp_qc_defer_cmd_switch()` otherwise.

**Command completion**

- ATA_QCFLAG_FAILED: not in this tree; the flag is `ATA_QCFLAG_EH`.
- `ata_qc_complete()`: sets `ATA_QCFLAG_EH` when `err_mask` is non-zero, then
  chooses the EH path by testing `ATA_QCFLAG_EH`, not `err_mask`;
  `ata_do_link_abort()` sets the flag and calls `ata_qc_complete()` without
  touching `err_mask`.
- Internal command (`ata_tag_internal()`): always `fill_result_tf()` then
  `__ata_qc_complete()`, with or without an error; `ata_qc_schedule_eh()` is
  never called for it.
- Failed non-internal command: `ata_qc_complete()` does not call
  `__ata_qc_complete()`; the qc keeps `ATA_QCFLAG_ACTIVE` and its tag until EH
  finishes it in `__ata_eh_qc_complete()`.
- `fill_result_tf()`: returns without calling `qc_fill_rtf` when
  `ATA_QCFLAG_RTF_FILLED` is already set; `ahci_qc_ncq_fill_rtf()` in
  `drivers/ata/libahci.c` sets it for successful NCQ commands.
- `ata_qc_for_each()` and `ata_qc_for_each_with_internal()`: built on
  `ata_qc_from_tag()`, so they yield NULL for a qc that EH owns;
  `ata_qc_for_each_raw()` uses `__ata_qc_from_tag()` and yields every slot
  below `ATA_MAX_QUEUE`.

**Internal commands**

- EH ownership: not asserted; `ata_exec_internal()` calls `ata_eh_release()`
  and `ata_eh_acquire()` around the wait only when
  `ap->host->eh_owner == current`.
- Probe: there is no ata_bus_probe() here; `ata_port_probe()` schedules EH, so
  probing issues its internal commands from EH.
- `dma_dir != DMA_NONE` with a NULL `buf`: `WARN_ON()` and `AC_ERR_INVALID`,
  before any lock is taken; a non-NULL `buf` with `DMA_NONE` is not checked
  and is ignored.
- `timeout` of 0: the module parameter `ata_probe_timeout` (seconds) is used
  when it is non-zero; only otherwise `ata_internal_cmd_timeout()`.
- Returned mask when the qc has `ATA_QCFLAG_EH`: `AC_ERR_DEV` is added if the
  result status has `ATA_ERR` or `ATA_DF`; an empty mask becomes
  `AC_ERR_OTHER`; `AC_ERR_OTHER` is cleared when any other bit is set.
- **Potentially unsafe usage**: calling `ata_exec_internal()` while commands
  are outstanding on the port.
  - Unsafe: when the normal path can still issue or complete commands;
    `ata_exec_internal()` sets `link->active_tag` to `ATA_TAG_POISON`, zeroes
    `link->sactive`, `ap->qc_active` and `ap->nr_active_links`, drops
    `ap->lock` to wait, and writes the saved values back afterwards.
  - Safe: from EH, as `ata_eh_read_log_10h()` does through
    `ata_read_log_page()`; the outstanding qcs have `ATA_QCFLAG_EH`, and
    `__ata_scsi_queuecmd()` refuses new commands while
    `ata_port_eh_scheduled()` is true.

**Frozen ports and timeouts**

- Timeout with the qc still active: `ata_port_freeze()` reaches
  `ata_do_link_abort()`, which sets `ATA_QCFLAG_EH` and calls
  `ata_qc_complete()`; the qc goes through `__ata_qc_complete()`, so it is
  unmapped and inactive before `post_internal_cmd` runs.
- After that timeout: the port is frozen and `ATA_PFLAG_EH_PENDING` is set;
  `ata_exec_internal()` does no reset and no thaw.
- `AC_ERR_SYSTEM`: returned for a frozen port before any command is issued,
  and also set by the `sys_err` path of `ata_qc_issue()`, which does not
  freeze the port; test `ata_port_is_frozen()` to learn whether the port is
  frozen, as `ata_read_log_page()` does before it retries.

**Data buffers**

- `sector_buf`: a member of `struct ata_device`, reached as
  `dev->sector_buf`; `struct ata_port` has no such member.
- ap->ncq_sense_buf: not in this tree; the two-sector buffer is
  `ncq_sense_log_buf` in `struct ata_cdl`, reached through `dev->cdl`, used by
  `ata_eh_get_ncq_success_sense()`.
- `ata_log_supported()`: reads the log directory into `dev->gp_log_dir` and
  caches it there; it does not touch `dev->sector_buf`.
- Memory type is defined by `sg_set_buf()` in `include/linux/scatterlist.h`:
  it calls `virt_to_page()` on `buf`, and under `CONFIG_DEBUG_SG` it does
  `BUG_ON(!virt_addr_valid(buf))`; this holds for PIO commands too.
- Lifetime: `buf` is needed only until `ata_exec_internal()` returns, on a
  timeout as well; `__ata_qc_complete()` unmaps it before the return.
- **Unsafe usage**: passing a buffer outside the kernel linear map (a stack
  array under `CONFIG_VMAP_STACK`, `vmalloc()` memory) as `buf`.
  - Safe: `dev->sector_buf` with `sectors` of 1, as
    `ata_identify_page_supported()` does; `struct ata_device` lives inside the
    port or PMP link allocation, made with `kzalloc_obj()` in
    `ata_port_alloc()` and `kzalloc_objs()` in `sata_pmp_init_links()`, so it
    passes the `virt_addr_valid()` test in `sg_set_buf()`.
  - Safe: an own `kzalloc()` buffer of the transfer length, freed after the
    call on failure too, as `ata_dev_config_cpr()` and
    `zpodd_get_mech_type()` do.
  - Safe: a buffer inside a `kzalloc_obj()` structure, as
    `ata_dev_init_cdl_resources()` does with `cdl->desc_log_buf`.

**Error masks and errnos**

- Return types: `ata_exec_internal()`, `ata_read_log_page()` and
  `ata_dev_set_feature()` are declared `unsigned int` and return a mask;
  `ata_dev_read_id()`, `ata_dev_reread_id()`, `ata_dev_configure()` and
  `ata_dev_revalidate()` are declared `int` and return an errno; see the
  definitions in `drivers/ata/libata-core.c`.
- `ata_dev_read_id()`: never returns `-EAGAIN`; its values are 0, `-ENODEV`
  (unsupported class), `-ENOENT`, `-EIO` and `-EINVAL`.
- `ata_dev_read_id()` returns `-ENOENT` in three cases: `AC_ERR_NODEV_HINT`
  set; both IDENTIFY flavours failed with `err_mask == AC_ERR_DEV` and
  `ATA_ABORTED`; an ATA device on an `ATA_HOST_IGNORE_ATA` host.
- `ata_dev_read_id()` on a SEMB-signature device whose IDENTIFY fails: returns
  0 and sets `*p_class` to `ATA_DEV_SEMB_UNSUP`; a caller must look at the
  class as well as the return value.
- `ata_dev_configure()`: returns `-EAGAIN` from `ata_do_link_spd_quirk()`;
  returns 0 when the device is not enabled and when it disables the device
  itself (`ATA_QUIRK_DISABLE`, ATAPI not allowed).
- **Potentially unsafe usage**: returning an `AC_ERR_*` mask from a function
  declared `int`.
  - Unsafe: when a caller tests the result with `< 0`, or passes it on to
    `ata_eh_handle_dev_fail()`, whose `switch` matches negative errnos only.
  - Safe: when no caller reads the result, as with `eject_tray()` in
    `drivers/ata/libata-zpodd.c`, whose only caller `zpodd_post_poweron()`
    discards it.

## Error handling and locks

**Entering error handling**

- `ata_port_abort()` and `ata_port_freeze()` with at least one command aborted:
  do not call `ata_port_schedule_eh()` or `scsi_schedule_eh()`; each
  non-internal command enters EH through `ata_qc_complete()`,
  `ata_qc_schedule_eh()` and `blk_abort_request()`.
- `ata_do_link_abort()`: calls `ata_port_schedule_eh()` only when it aborted
  nothing.
- Aborted internal command (`ATA_TAG_INTERNAL`): `ata_qc_complete()` finishes
  it through `__ata_qc_complete()` and never reaches `ata_qc_schedule_eh()`;
  only `ATA_PFLAG_EH_PENDING`, set by `ata_eh_set_pending()` from
  `ata_do_link_abort()`, remains.
- `ata_std_sched_eh()` while `ATA_PFLAG_INITIALIZING` is set: returns without
  setting `ATA_PFLAG_EH_PENDING` and without `scsi_schedule_eh()`.
- `ata_scsi_error()`: calls `ata_scsi_port_error_handler()` only when a command
  timed out or `ata_port_eh_scheduled()` is true; otherwise it only flushes
  `ap->eh_done_q`.
- `eh_info` and `eh_context`: fields of `struct ata_link`, not of
  `struct ata_port`; the entry loop handles every link of the port.
- `link->eh_context`: zeroed whole by `memset()` before `eh_info` is copied
  into `eh_context.i`, on every pass including a repeat.
- `ATA_PFLAG_RESUMING` at entry: each enabled device gets `ATA_DFLAG_RESUMING`
  and `ATA_EH_SET_ACTIVE` in `ehc->i.dev_action[]`.
- Probing: `ata_scsi_port_error_handler()` does not wait for it;
  `ATA_PFLAG_LOADING` is only cleared in its final clean-up.

**Ownership release during sleeps**

- `ata_exec_internal()` in `drivers/ata/libata-core.c`: releases ownership
  around its completion wait when `eh_owner == current`, so every internal
  command issued from EH lets another port's EH run.
- `msleep()` in EH context: keeps ownership; `ata_msleep()` gives it up when
  its `ap` is not NULL.
- **Unsafe usage**: `ata_msleep()` or `ata_exec_internal()` in the middle of a
  sequence on a resource shared by the ports of one host.
  - Unsafe: when another port's EH can touch the same resource; it runs as
    soon as `ata_eh_release()` unlocks `eh_mutex`.
  - Safe: sleep with `msleep()` so ownership is kept, as `ahci_start_port()`
    in `drivers/ata/libahci.c` does while the host-wide EM transmit bit is
    busy.
- `drivers/ata/Makefile` sets `CONTEXT_ANALYSIS := y`; `ata_eh_acquire()` is
  declared `__acquires(&ap->host->eh_mutex)` and `ata_eh_release()`
  `__releases()` of the same.
- Conditional release under that analysis: `ata_msleep()` is marked
  `__context_unsafe()`; `ata_exec_internal()` balances its calls with
  `__acquire()` and `__release()`.

**Driver error handler**

- `error_handler` must be non-NULL after `ata_finalize_port_ops()`:
  `ata_scsi_port_error_handler()` is its only caller and has no NULL test.
- The entry copy and clear of `eh_info` runs before the call, whether or not
  the handler is then called.
- The handler is skipped, and `ata_eh_finish()` called instead, when
  `ATA_PFLAG_UNLOADING` or `ATA_PFLAG_SUSPENDED` is set, or when
  `ata_adapter_is_online()` is false (PCI channel offline).
- `ata_eh_unload()` runs before `ata_eh_finish()` only when
  `ATA_PFLAG_UNLOADING` is set and `ATA_PFLAG_UNLOADED` is not.
- An ops table with no `.inherits` chain to `ata_base_port_ops` must set
  `error_handler`, `sched_eh` and `end_eh` itself; all three are called
  without a NULL test. For example `ata_dummy_port_ops` and `sas_sata_ops` in
  `drivers/scsi/libsas/sas_ata.c`.
- `ata_sff_port_ops` sets `ata_sff_error_handler()`, and `ata_bmdma_port_ops`
  sets `ata_bmdma_error_handler()`; each ends in the next one down to
  `ata_std_error_handler()`.
- The `error_handler` member is declared
  `__must_hold(&ap->host->eh_mutex)` in `include/linux/libata.h`; handlers
  carry the same annotation, for example `ata_sff_error_handler()`.

**Reporting from interrupt handlers**

- Error tied to a known active command: goes in `qc->err_mask`, not
  `ehi->err_mask`; `ahci_error_intr()` does this for `PORT_IRQ_TF_ERR`.
- Frozen port: `ata_eh_link_autopsy()` adds `ATA_EH_RESET` whenever the port is
  frozen, unless `ATA_EHI_NO_AUTOPSY` is set; so a port left frozen by
  `ata_port_freeze()` gets `ATA_EH_RESET` even if the handler requested none.
- Aborted but not frozen port: the abort itself adds no reset; one comes from
  `ehi->action`, from `AC_ERR_HSM` or `AC_ERR_TIMEOUT` in the error masks, or
  from the analysis in `ata_eh_link_autopsy()`, for example
  `ata_eh_analyze_serror()` or `ata_eh_speed_down()`.
- `ahci_error_intr()` without FBS: the link is the first one for which
  `ata_link_active()` is true, else `ap->link`.
- `ata_link_abort()` branch in `ahci_error_intr()`: reached only when no
  `PORT_IRQ_FREEZE` bit is set. `PORT_IRQ_IF_ERR` is one of those bits, so an
  FBS device error reported with it freezes the port, unless
  `AHCI_HFLAG_IGN_IRQ_IF_ERR` masked the bit.

**Reset callbacks**

- The four callbacks are members of `struct ata_reset_operations` in
  `include/linux/libata.h`; `struct ata_port_operations` has no flat
  `prereset` or `hardreset` member, and drivers write `.reset.hardreset`.
- `struct ata_port_operations` embeds it as `reset` and `pmp_reset`;
  `ata_std_error_handler()` passes `&ap->ops->reset`, and
  `sata_pmp_eh_recover()` passes `pmp_reset` for the fan-out links.
- `ata_eh_freeze_port()` before the reset: unconditional, also on an already
  frozen port, but only when `ata_is_host_link()` is true.
- PMP fan-out link: `ata_eh_reset()` calls neither `ata_eh_freeze_port()` nor
  `ata_eh_thaw_port()`.
- After `postreset`: only `eh_info.serror` of the link and slave is zeroed;
  `ATA_PFLAG_EH_PENDING` is not cleared and there is no second thaw.
- `-ENOENT` is special only from `prereset`: reset skipped, classes set to
  `ATA_DEV_NONE`, result 0, with no freeze, thaw or `postreset` call.
- `-ENOENT` with a slave link: skips the reset only when both `prereset`
  calls return `-ENOENT`.
- `-ENOENT` from `softreset` or `hardreset`: an ordinary failure, taken to the
  `fail` label.
- Other non-zero value from `prereset`: `ata_eh_reset()` returns it at once,
  with no retry.
- `-EAGAIN` from the first reset method, hard or soft: not a failure.
- `-EAGAIN` from `hardreset`: asks for a follow-up softreset; see "Choice of
  reset method".
- `-EAGAIN` from the follow-up softreset: a failure, like any non-zero value.
- `sata_link_hardreset()` returns `-EAGAIN` when the link is not offline,
  `sata_pmp_supported()` is true and the link is the host link, with or
  without `check_ready`.

**Choice of reset method**

- Hardreset is used first; softreset is first only when no hardreset remains.
- The flag that drops hardreset is `ATA_LFLAG_NO_HRST`; there is no
  ATA_LFLAG_NO_HARDRESET in this tree.
- `ATA_EH_HARDRESET` or `ATA_EH_SOFTRESET` requested in `ehc->i.action` does
  not steer the choice; both bits are cleared before the method is picked, and
  `ata_eh_reset()` then sets the bit of the method it picked.
- The first method is picked before `prereset`, and not picked again after
  it.
- After `prereset` the only test of `ehc->i.action` is whether both
  `ATA_EH_RESET` bits are now clear, which skips the reset.
- Follow-up softreset after a hardreset: when `ata_eh_followup_srst_needed()`
  is true, that is `-EAGAIN` from hardreset, or `sata_pmp_supported()` on the
  host link; the device class is not tested.
- `ata_eh_followup_srst_needed()` is false when `ATA_LFLAG_NO_SRST` is set or
  `ata_link_offline()` is true, even after `-EAGAIN`.
- A failed reset does not switch method: the retry sets the method back to
  hardreset whenever a hardreset callback remains.

**Locks and flag words**

- `flags` has no lock: it is written at host setup and from EH callbacks
  without `ap->lock`, for example by `sil24_pmp_attach()`.
- `pflags` is protected by `ap->lock`; writes before the port is visible are
  unlocked, for example in `ata_port_alloc()`.
- `pflags` reads are often unlocked, for example the `ATA_PFLAG_UNLOADING`
  test in `ata_scsi_port_error_handler()`.
- **Potentially unsafe usage**: writing `ap->pflags` without `ap->lock`.
  - Unsafe: once interrupts or EH can run for the port;
    `__ata_port_freeze()` and `ata_eh_set_pending()` do plain read-modify-write
    of `pflags` under `ap->lock`.
  - Safe: before the port is visible to anything else, as `ata_port_alloc()`
    does.
- `end_eh`: called with `ap->lock` held and EH ownership still held.
- `post_internal_cmd`: called from `ata_exec_internal()` with `ap->lock`
  dropped; EH ownership is held only if the caller owned it.
- `freeze`: the libata core calls it through `__ata_port_freeze()` under
  `ap->lock`; the shutdown paths `ata_pci_shutdown_one()` and
  `ahci_platform_shutdown()` call it with no libata lock.
- `lost_interrupt`: under `ap->lock` in `ata_scsi_cmd_error_handler()`, before
  EH ownership is taken.
- `port_suspend` and `port_resume`: EH ownership, no `ap->lock`.
- Lock requirements are annotated in this tree, for example
  `__must_hold(ap->lock)` on `ata_scsi_translate()`.

## Other users and builds

**Outside callers and Kconfig guards**

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

## Model gaps

### Other mistakes models make

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
