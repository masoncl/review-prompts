# USB Storage Subsystem

## Main structures

### Objects and how they relate

- `struct us_unusual_dev`: carries no `US_FL_*` flags. The flags of an entry
  are in `driver_info` of the parallel `struct usb_device_id`;
  `get_device_info()` copies `id->driver_info` into `us->fflags`.
- State bits (`US_FLIDX_*`): held in `dflags`; `struct us_data` has no field
  named flags.
- `us->srb` hand-off: protected by the host lock (`scsi_lock()` in
  `drivers/usb/storage/usb.h`), not by `us->dev_mutex`.
- `us->max_lun` is the device's LUN limit; the thread rejects a higher LUN
  with `DID_BAD_TARGET`. usb-storage writes the host's `max_lun` only in
  `usb_stor_scan_dwork()`, when `us->max_lun >= 8`.
- `us->extra` is not always set between `usb_stor_probe1()` and
  `usb_stor_probe2()`. For example `init_alauda()` sets it as the
  `initFunction` run inside `usb_stor_probe2()`, and `datafab_transport()`
  sets it on the first command.
- Host template: `usb_stor_host_template` in
  `drivers/usb/storage/scsiglue.c` is a `static const` master. Each
  sub-driver module, and `usb-storage` itself, has its own non-const copy,
  filled by `usb_stor_host_template_init()` from `module_usb_stor_driver()`.
- `uas` intfdata: the `struct Scsi_Host`, not the `struct uas_dev_info`. In
  `usb-storage` the intfdata is the `struct us_data`.
- `struct uas_dev_info` is reached through `shost->hostdata`, and through
  `sdev->hostdata` once `uas_sdev_init()` has set it.
- `uas` and `usb-storage` share more than tables. `uas` uses
  `usb_stor_adjust_quirks()` and `usb_stor_sense_invalidCDB`, both exported
  by `usb-storage`.
- `uas_usb_ids` also matches the Bulk-Only interface (`USB_PR_BULK`), so both
  drivers match the same interface. `uas_use_uas_driver()` in
  `drivers/usb/storage/uas-detect.h` is compiled into both and decides:
  `storage_probe()` declines when it returns 1, `uas_probe()` when it
  returns 0.

## Unusual device entries

**Entry macro arguments**

- Subclass codes such as `USB_SC_SCSI` and protocol codes such as
  `USB_PR_BULK`: both families are defined in `include/linux/usb/storage.h`,
  and nowhere under `drivers/usb/storage/`.
- Override codes usable in `drivers/usb/storage/unusual_devs.h`:
  `USB_SC_DEVICE`, `USB_PR_DEVICE`, and otherwise only those with a case in
  `get_protocol()` and `get_transport()` in `drivers/usb/storage/usb.c`.
- Any other resulting code: no handler is set, and `usb_stor_probe2()` returns
  `-ENXIO`. For example `USB_SC_LOCKABLE` and `USB_PR_UAS` have no case.
- Driver-private codes, for example `USB_SC_ISD200` or `USB_PR_JUMPSHOT`:
  valid only in a sub-driver header, whose probe sets the handlers itself
  between `usb_stor_probe1()` and `usb_stor_probe2()`.

**Expanding the table**

- Index into `us_unusual_dev_list[]`: the pointer difference
  `id - usb_storage_usb_ids`, computed in `storage_probe()`.
- `usb_storage_usb_ids[]`: built in `drivers/usb/storage/usual-tables.c`;
  only `us_unusual_dev_list[]` is built in `drivers/usb/storage/usb.c`. Both
  are expansions of `drivers/usb/storage/unusual_devs.h`, each under its own
  definitions of the entry macros.
- Generic `USUAL_DEV()` lines: the last lines of `unusual_devs.h`, so they
  come before the `{ }` terminator in both arrays, not after it.
- Entry macros in `unusual_devs.h`: the header may use only `UNUSUAL_DEV()`,
  `COMPLIANT_DEV()` and `USUAL_DEV()`.
- Run-time id: recognised because the `id` pointer lies outside
  `usb_storage_usb_ids[]`, not by its `driver_info`; `usb_probe_interface()`
  in `drivers/usb/core/driver.c` passes a copy on its own stack.
- `for_dynamic_ids`: `USUAL_DEV(USB_SC_SCSI, USB_PR_BULK)`, so names and
  `initFunction` are `NULL` and both overrides are explicit.
- Flags of a run-time id: `usb_store_new_id()` leaves `driver_info` 0, or
  copies it from a static entry when a reference VID and PID are written to
  `new_id`.
- Run-time id with a reference entry: gets that entry's flags, but not its
  overrides, names or init function.

**Entry matching rules**

- Revision compare: plain unsigned 16-bit in `usb_match_device()`, not BCD
  digit by digit.
- Upper bound `0x9999`: excludes a device whose `bcdDevice` is above it; the
  table uses both `0x9999` and `0xffff` as "all revisions".
- UNUSUAL_VENDOR_INTF: not in this tree; no entry macro here combines a
  vendor or product id with interface fields, so an entry cannot be limited
  to one interface of a composite device.
- Interface class: neither `storage_probe()` nor `usb_stor_probe1()` rejects
  an interface for its `bInterfaceClass`.
- Non-storage interface, entry with `USB_SC_DEVICE` or `USB_PR_DEVICE`:
  `usb_stor_probe2()` returns `-ENXIO` unless the descriptor's code has a case
  in `get_protocol()` or `get_transport()`.
- Non-storage interface, entry with both overrides explicit: no class test
  stops it; `get_pipes()` needs only a bulk-in and a bulk-out endpoint, plus
  an interrupt-in endpoint for `USB_PR_CBI`.
- Run-time id with the VID and PID of a table entry: matched first by
  `usb_probe_interface()`, so the table entry's overrides, names and init
  function are not used.
- `storage_probe()`: passes its own matched id to `uas_use_uas_driver()`, so
  it does not see `US_FL_IGNORE_UAS` set only in a later `unusual_uas.h` entry.

**Redundant override notice**

- Entries checked: any id with a nonzero `idVendor` or `idProduct`; only the
  generic `USUAL_DEV()` ids are exempt.
- Run-time ids: checked too. `for_dynamic_ids` carries explicit SCSI and
  Bulk-only codes, so a device that reports 06/50 logs "unneeded SubClass
  and Protocol entries".
- Sub-driver entries: checked too, since every sub-driver probe calls
  `usb_stor_probe1()`; the text names `unusual_devs.h` whichever header holds
  the entry.
- Level and text: `dev_notice()`; the three variants are in `msgs[]` in
  `get_device_info()`, and the message asks for a copy to be sent to
  linux-usb@vger.kernel.org and usb-storage@lists.one-eyed-alien.net.
- Suppression: `US_FL_NEED_OVERRIDE` in `us->fflags`; nothing else.
- `US_FL_IGNORE_DEVICE`: `get_device_info()` returns `-ENODEV` before the
  check, so such an entry never logs the notice.
- Each override is tested alone: one field that equals the descriptor logs
  the notice even when the other override is needed.
- Entry for a device with one wrong field: overrides that field only, as in
  `USB_SC_DEVICE, USB_PR_BULK`.

**Conventions for new entries**

- Sort order asked by both headers: VendorID, then ProductID; neither
  mentions `bcdDevice`.
- Above the entry, both headers: the submitter's email address, plus maybe a
  brief explanation of the reason; neither asks for a name or a copyright.
- With an `unusual_devs.h` patch: a copy of `/sys/kernel/debug/usb/devices`,
  taken with the device plugged in and the patch running.
- With an `unusual_uas.h` patch: lsusb -v output for the device.
- Recipient, `unusual_devs.h`: linux-usb@vger.kernel.org only; the submission
  note names no person and not the usb-storage list.
- Recipient, `unusual_uas.h`: Hans de Goede <hdegoede@redhat.com>, with CC to
  linux-usb@vger.kernel.org.
- `COMPLIANT_DEV()`: for an entry added only to set `US_FL_CAPACITY_OK`; the
  header says such a device works correctly.
- Mode switching: the header calls in-kernel mode switching deprecated,
  forbids new entries added only for it, and points to the usb_modeswitch
  database.
- `unusual_uas.h` and the sub-driver headers: may use only `UNUSUAL_DEV()`.
  `drivers/usb/storage/uas.c` and the ignore table in
  `drivers/usb/storage/usual-tables.c` define no `COMPLIANT_DEV()` or
  `USUAL_DEV()`.

## Quirk flags, uas and usb-storage

**Flag word and quirks parameter**

- `fflags` in `struct us_data` and `flags` in `struct uas_dev_info`: both
  `u64`, not `unsigned long`.
- The `fflags` argument of `usb_stor_adjust_quirks()` and the `flags_ret`
  argument of `uas_use_uas_driver()`: both `u64 *`.
- `driver_info` in `struct usb_device_id`: `kernel_ulong_t`, which is
  `unsigned long` (`include/linux/device-id/usb.h`); narrower than the flag
  word on a 32-bit build.
- `UNUSUAL_DEV()` in `drivers/usb/storage/usual-tables.c`: casts the flags to
  `kernel_ulong_t`; the one in `drivers/usb/storage/uas.c` assigns them
  without a cast.
- `mask` in `usb_stor_adjust_quirks()`: holds exactly the 22 flags that have
  a `case` letter, `US_FL_NO_SAME` included; a matching entry can clear every
  flag it can set.
- Flags without a letter: no entry can set or clear them.
- In `uas_use_uas_driver()`: `usb_stor_adjust_quirks()` runs after the flags
  the function ORs in by code, and those flags are all in `mask`; a matching
  entry replaces them as well as the lettered table flags.

**Flag and letter definitions**

- `US_DO_ALL_FLAGS`: defined in `include/linux/usb_usual.h`; there is no
  include/linux/usb_storage.h in this tree.
- Bits 0 to 31 are all assigned; `US_FL_SENSE_AFTER_SYNC` is 0x80000000. No
  bit that fits a 32-bit `driver_info` is free.
- A flag above bit 31 in a table entry: lost on a 32-bit build, where
  `driver_info` is `unsigned long`; the `quirks` path and code that ORs into
  the `u64` flag word are not affected.
- `mask` in `usb_stor_adjust_quirks()`: a hand-written OR expression, not
  generated from `US_DO_ALL_FLAGS`; a new lettered flag has to be added to it
  by hand as well as getting a `case`.
- `show_info()` in `drivers/usb/storage/scsiglue.c`: the only expansion of
  `US_DO_ALL_FLAGS` besides the enum in `include/linux/usb_usual.h`; prints
  the new name with no edit.
- uas: gets the letter for free through the exported
  `usb_stor_adjust_quirks()`; acting on the flag still needs a test in
  `drivers/usb/storage/uas.c`.

**Flags each driver honours:** Flags both drivers test:

| Flag | uas | usb-storage |
|---|---|---|
| `US_FL_IGNORE_UAS` | `uas_use_uas_driver()` | same function, only under `CONFIG_USB_UAS` |
| `US_FL_NO_ATA_1X` | `uas_queuecommand_lck()` | `queuecommand_lck()` |
| `US_FL_MAX_SECTORS_64` | `uas_sdev_configure()` | `sdev_configure()`, any type |
| `US_FL_BROKEN_FUA` | `uas_sdev_configure()` | `sdev_configure()`, `TYPE_DISK` only |
| `US_FL_ALWAYS_SYNC` | `uas_sdev_configure()` | `sdev_configure()`, `TYPE_DISK` only |
| `US_FL_NO_READ_CAPACITY_16` | `uas_sdev_configure()` | `sdev_configure()`, `TYPE_DISK` only |
| `US_FL_FIX_CAPACITY` | `uas_sdev_configure()` | `sdev_configure()`, `TYPE_DISK` only |
| `US_FL_CAPACITY_HEURISTICS` | `uas_sdev_configure()` | `sdev_configure()`, `TYPE_DISK` only |
| `US_FL_NO_WP_DETECT` | `uas_sdev_configure()` | `sdev_configure()`, `TYPE_DISK` only |

Flags only uas tests:

| Flag | uas | usb-storage, with no flag test |
|---|---|---|
| `US_FL_NO_REPORT_LUNS` | `uas_target_alloc()` | `target_alloc()` sets `no_report_luns` for every target |
| `US_FL_NO_REPORT_OPCODES` | `uas_sdev_configure()` | `sdev_configure()` sets `no_report_opcodes` for `TYPE_DISK` only |
| `US_FL_NO_SAME` | `uas_sdev_configure()` | `sdev_configure()` sets `no_write_same` for `TYPE_DISK` only |
| `US_FL_MAX_SECTORS_240` | `uas_sdev_configure()` | not equivalent: 240 is only the template default; `sdev_configure()` raises it for tapes and for SuperSpeed or faster |

- `uas_sdev_configure()`: has no `sdev->type` test; every flag applies to
  every device type.
- `US_FL_NO_READ_DISC_INFO` and `US_FL_IGNORE_RESIDUE`: not tested by uas.
- `read_before_ms`: uas sets it for every device, usb-storage for `TYPE_DISK`
  only.
- The "uas only" and "not on uas" notes under `usb-storage.quirks=` in
  `Documentation/admin-guide/kernel-parameters.txt` do not all follow the
  code; for example `m` and `y` are marked "not on uas" and
  `uas_sdev_configure()` tests both flags.
- The remaining 19 flags are tested only by usb-storage code
  (`drivers/usb/storage/usb.c`, `drivers/usb/storage/transport.c`,
  `drivers/usb/storage/scsiglue.c`, plus `US_FL_IGNORE_RESIDUE` in
  `drivers/usb/storage/ene_ub6250.c`); none is read by neither driver.

**Choosing between uas and usb-storage**

- Nonzero result of `uas_use_uas_driver()`: `storage_probe()`, which makes the
  call only under `IS_ENABLED(CONFIG_USB_UAS)`, returns `-ENXIO` without
  checking that uas is loaded; `uas_probe()` can still fail afterwards, for
  example in `uas_switch_interface()`. At most one of the two binds, not
  exactly one.
- uas has no module parameter of its own; the usb-storage `quirks` string
  reaches it through `usb_stor_adjust_quirks()`.
- The function returns 0 in these cases, tested in this order:
  1. no altsetting passes `uas_is_interface()` (code)
  2. `uas_find_endpoints()` does not find all four pipe-usage descriptors
     (code)
  3. `US_FL_IGNORE_UAS` is set after `usb_stor_adjust_quirks()` (table,
     `quirks` letter `u`, or the coded cases below)
  4. `udev->bus->sg_tablesize == 0` (code)
  5. speed is `USB_SPEED_SUPER` or above and `hcd->can_do_streams` is 0
     (code)
- Coded cases that set flags, all before `usb_stor_adjust_quirks()`:
  - ASMedia 174c:5106 and 174c:55aa with `bMaxPower != 0`: below
    `USB_SPEED_SUPER`, or exactly 32 streams on the status pipe, sets
    `US_FL_IGNORE_UAS`; any other stream count sets `US_FL_MAX_SECTORS_240`.
  - Vendor 0x0bc2: sets `US_FL_NO_ATA_1X`; uas still binds.
  - 0bda:9210 with manufacturer "HIKSEMI" and product "MD202": sets
    `US_FL_IGNORE_UAS`.
  - No VIA device is coded in the function.
- Flags the function adds in code reach uas only: `storage_probe()` passes
  `NULL` for `flags_ret`, and `get_device_info()` builds `us->fflags` from
  `id->driver_info` plus `quirks`.
- `drivers/usb/storage/unusual_uas.h` is included in two places:
  - `drivers/usb/storage/uas.c`, inside `uas_usb_ids[]`.
  - `drivers/usb/storage/unusual_devs.h`, under
    `#if IS_ENABLED(CONFIG_USB_UAS)`, after the last `UNUSUAL_DEV()` entry and
    before the `USUAL_DEV()` entries.
- `drivers/usb/storage/unusual_uas.h` is not included in
  `drivers/usb/storage/uas-detect.h`, nor directly in
  `drivers/usb/storage/usb.c`.
- `usb_match_id()` returns the first match: a device that matches an entry in
  both files gets the `drivers/usb/storage/unusual_devs.h` flags in
  `storage_probe()` and the `drivers/usb/storage/unusual_uas.h` flags in
  `uas_probe()`.
- An entry in `drivers/usb/storage/unusual_devs.h` outside
  `drivers/usb/storage/unusual_uas.h` is not in `uas_usb_ids[]`;
  `uas_probe()` matches such a device through a generic interface entry with
  `driver_info` 0, so the two calls of the function can return different
  results.

**Per-device SCSI settings**

- No `sdev` field is forced for every device type. The unconditional
  settings sit in the `TYPE_DISK` branch; the else branch for a non-disk
  device sets only `use_10_for_ms`, plus `no_read_disc_info` with
  `US_FL_NO_READ_DISC_INFO`.
- `use_10_for_ms` for a disk: set only when the subclass is neither
  `USB_SC_SCSI` nor `USB_SC_CYP_ATACB`.
- `last_sector_bug`: unconditional for disks. `us->use_last_sector_hacks` is
  the one skipped by `US_FL_FIX_CAPACITY`, `US_FL_CAPACITY_OK`,
  `US_FL_SCM_MULT_TARG` or a non-Bulk protocol.
- `try_rc_10_first`: set for disks unless `US_FL_NEEDS_CAP16`.
- `skip_ms_page_3f`: set only for a disk with `US_FL_NO_WP_DETECT` or
  `US_FL_ALWAYS_SYNC`.
- `US_FL_NOT_LOCKABLE`: tested outside the type branch, for any device type.
- Not done in `sdev_configure()`: it does not write `scsi_level`,
  `use_10_for_rw` or the DMA alignment. `.dma_alignment = 511` is in the
  template; `pdt_1f_for_no_lun` is set in `target_alloc()` for `USB_SC_UFI`.
- `lim->max_hw_sectors` normally arrives holding the template's 240, then
  the first matching case applies:
  1. `US_FL_MAX_SECTORS_64` or `US_FL_MAX_SECTORS_MIN`: `min()` of the
     current value and 64, or `PAGE_SIZE >> 9` with `US_FL_MAX_SECTORS_MIN`.
  2. `TYPE_TAPE`: 0x7FFFFF.
  3. speed `USB_SPEED_SUPER` or above: 2048.
  4. otherwise unchanged.
- After that, for every device: clamped to `dma_max_mapping_size()` of
  `us->pusb_dev->bus->sysdev`, in sectors.
- The comment in `sdev_configure()` about `sdev_init()`: it covers the whole
  `TYPE_DISK`/else block. The reason given is that `sdev_init()` is called
  before the device type is known; it adds that these settings therefore
  cannot be overridden through scsi devinfo.

**Host template**

- `.target_alloc`: set to `target_alloc()`, which takes
  `struct scsi_target *`; it is the only per-target callback.
- `.cmd_per_lun`, `.dma_boundary`, `.no_write_same`: not set in
  `usb_stor_host_template`; `uas_host_template` is the one with
  `.dma_boundary`.
- Fixed for every device: `can_queue = 1`, `dma_alignment = 511`,
  `emulated`, `skip_settle_delay`.
- Template values that are only starting points:
  - `sg_tablesize`: `usb_stor_probe1()` overwrites `host->sg_tablesize` for
    every host with `usb_stor_sg_tablesize()`.
  - `this_id`: `usb_stor_probe2()` sets it to 7 with `US_FL_SCM_MULT_TARG`.
  - `max_sectors`: see "Per-device SCSI settings".
- `usb_stor_host_template_init()`: sets `name`, `proc_name` and `module`
  after the struct copy; `name` and `proc_name` get the same string.
- `module_usb_stor_driver()` in `drivers/usb/storage/usb.h`: the only caller
  of `usb_stor_host_template_init()`; `drivers/usb/storage/usb.c` and every
  ums sub-driver use it, and it runs in module init, not in probe.

## The command path and its locks

**Queuecommand and the control thread**

- `usb_stor_control_thread()` in `drivers/usb/storage/usb.c`: completes the
  command with `scsi_done_direct()`, not `scsi_done()`.
- Order at the end of a command: `us->srb = NULL` under the host lock,
  `scsi_unlock()`, `mutex_unlock(&us->dev_mutex)`, then `scsi_done_direct()`;
  neither lock is held at the call.
- `queuecommand_lck()` in `drivers/usb/storage/scsiglue.c`: its two early
  completions (`US_FLIDX_DISCONNECTING`, and `US_FL_NO_ATA_1X` with `ATA_12` or
  `ATA_16`) call `scsi_done()` in the context that called the queue callback,
  with the host lock held by `DEF_SCSI_QCMD()`.
- On wake-up the thread tests `US_FLIDX_TIMED_OUT`, not `US_FLIDX_ABORTING`,
  under the host lock; if set it sets `DID_ABORT << 16` and skips the protocol
  handler.
- End of command, two independent tests under the host lock:
  - `srb->result == DID_ABORT << 16`: `scsi_done_direct()` is skipped.
  - `US_FLIDX_TIMED_OUT` set: `complete(&us->notify)`, then
    `US_FLIDX_ABORTING` and `US_FLIDX_TIMED_OUT` are cleared.
  - A command that finished with another result before the abort was noticed
    gets both `complete(&us->notify)` and `scsi_done_direct()`.
- `usb_stor_host_template`: sets `.can_queue = 1` and does not set
  `.cmd_per_lun`; the one-command limit is `can_queue` plus the
  `us->srb != NULL` test in `queuecommand_lck()`.

**us_data lifetime and flag words**

- `fflags`: `u64`; `dflags`: `unsigned long`, bits 0 to 8 defined in
  `drivers/usb/storage/usb.h`.
- `fflags` is written after probe with plain non-atomic `|=` and `&=`: see
  `sdev_configure()`, `usb_stor_invoke_transport()` and
  `usb_stor_Bulk_transport()`.
- `release_everything()`: drops the only `struct Scsi_Host` reference that
  usb-storage holds; nothing under `drivers/usb/storage/` calls
  `scsi_host_get()`.
- `dissociate_dev()`: takes or drops no `struct usb_device` reference; nothing
  under `drivers/usb/storage/` calls `usb_get_dev()` or `usb_get_intf()`.
- After `release_everything()` the freed pointers (`current_urb`, `extra`,
  `cr`, `iobuf`) keep their old values; only the interface data is set to
  NULL, so a NULL test on a field does not detect teardown.
- A `struct Scsi_Host` reference keeps the `struct us_data` memory; it does
  not keep `us->extra`, `us->iobuf`, `us->cr` or `us->current_urb`.
- **Potentially unsafe usage**: a timer, work item, private URB or input
  device set up by a sub-driver that reaches `us` or `us->extra`.
  - Unsafe: when it can still run or be queued after
    `us->extra_destructor()` returns; `usb_stor_release_resources()` then
    frees `us->extra` and `release_everything()` drops the host reference.
  - Safe: stopped synchronously inside the destructor, as
    `realtek_cr_destructor()` does with `timer_shutdown_sync()` under
    `CONFIG_REALTEK_AUTOPM` and `onetouch_release_input()` does with
    `usb_kill_urb()` and `input_unregister_device()`.

**Locks and what they cover**

- `struct us_data` has one lock member, `dev_mutex`, and no spinlock member of
  its own.
- `usb_stor_reset_resume()`: does not take `dev_mutex`; it only calls
  `usb_stor_report_bus_reset()`.
- `usb_stor_probe1()` and `usb_stor_probe2()`: do not take `dev_mutex`;
  `usb_stor_scan_dwork()` does, around `usb_stor_Bulk_max_lun()`.
- `usb_stor_disconnect()`: never takes `dev_mutex`; `kthread_stop()` in
  `usb_stor_release_resources()` is what waits for a running command before
  the URB and buffers are freed.
- Sub-drivers take `dev_mutex` too; search `drivers/usb/storage/` for
  `dev_mutex`.
- `dflags` bits and the host lock:

| Bit | Set in | Cleared in | Host lock at every site |
|---|---|---|---|
| `US_FLIDX_URB_ACTIVE` | `usb_stor_msg_common()` | same; `usb_stor_stop_transport()` | no; only the `usb_stor_stop_transport()` site, through its caller |
| `US_FLIDX_SG_ACTIVE` | `usb_stor_bulk_transfer_sglist()` | same; `usb_stor_stop_transport()` | no; as above |
| `US_FLIDX_ABORTING` | `command_abort_matching()` | `usb_stor_control_thread()`; `Handle_Errors`; `isd200_invoke_transport()` | no; the first three sites hold it, `isd200_invoke_transport()` does not |
| `US_FLIDX_DISCONNECTING` | `quiesce_and_remove_host()`, twice | never | no; the first set (device `USB_STATE_NOTATTACHED`) is unlocked |
| `US_FLIDX_RESETTING` | `Handle_Errors` | end of `usb_stor_invoke_transport()` | no; set locked, cleared unlocked |
| `US_FLIDX_TIMED_OUT` | `command_abort_matching()` | `usb_stor_control_thread()` | yes |
| `US_FLIDX_SCAN_PENDING` | `usb_stor_probe2()` | `usb_stor_scan_dwork()` | no |
| `US_FLIDX_REDO_READ10` | `usb_stor_probe2()`; `usb_stor_invoke_transport()` | `usb_stor_invoke_transport()` | no |
| `US_FLIDX_READ10_WORKED` | `usb_stor_invoke_transport()` | `usb_stor_invoke_transport()` | no |

- US_FLIDX_DONT_SCAN is not defined in this tree.
- `last_sector_hacks()`: touches no `dflags` bit.
- `command_abort_matching()` tests `US_FLIDX_RESETTING` and sets
  `US_FLIDX_ABORTING`, and `Handle_Errors` sets `US_FLIDX_RESETTING` and
  clears `US_FLIDX_ABORTING`, each inside one host-lock section; that pairing
  is what the host lock gives these bits.

**Submitting URBs for a command**

- `usb_stor_stop_transport()`: has one caller, `command_abort_matching()`,
  reached from `command_abort()` and `device_reset()`; it is skipped when
  `US_FLIDX_RESETTING` is set.
- `usb_stor_msg_common()` and `usb_stor_bulk_transfer_sglist()`: test only
  `US_FLIDX_ABORTING`, never `US_FLIDX_DISCONNECTING`.
- The comment block above `usb_stor_blocking_completion()` in
  `drivers/usb/storage/transport.c` describes a disconnect cancel and a
  `US_FLIDX_DISCONNECTING` test in the submit path; the code has neither.
- `US_FLIDX_DISCONNECTING` is tested in `queuecommand_lck()`,
  `usb_stor_reset_common()` and `usb_stor_port_reset()` only.
- `usb_stor_bulk_transfer_sglist()` with `US_FLIDX_ABORTING` set: returns
  `USB_STOR_XFER_ERROR` with `*act_len = 0`, not an errno, and has no timeout
  (`usb_sg_wait()`).
- `usb_stor_msg_common()` and `usb_stor_bulk_transfer_sglist()` are static;
  sub-drivers reach them through the exported helpers in
  `drivers/usb/storage/transport.c`, for example
  `usb_stor_bulk_transfer_buf()`, `usb_stor_bulk_srb()` and
  `usb_stor_control_msg()`.
- Sub-driver code that runs its own protocol through those helpers: for
  example `rts51x_bulk_transport()` in `drivers/usb/storage/realtek_cr.c` and
  `ene_send_scsi_cmd()` in `drivers/usb/storage/ene_ub6250.c`.
- `drivers/usb/storage/uas.c`: does not use `struct us_data` or these helpers.
- **Potentially unsafe usage**: `usb_bulk_msg()`, `usb_control_msg()` or a
  private URB in a usb-storage sub-driver.
  - Unsafe: on a path reached from `us->transport()` or `us->proto_handler()`;
    `usb_stor_stop_transport()` cancels only `us->current_urb` and
    `us->current_sg`, so `command_abort_matching()` stays in
    `wait_for_completion(&us->notify)` until that I/O ends or times out by
    itself.
  - Safe: in an `initFunction`, which `usb_stor_acquire_resources()` calls
    before `kthread_run()`, as `sierra_ms_init()` does with
    `usb_control_msg()`.
  - Safe: a URB that serves no SCSI command and is killed in the
    `extra_destructor`, as the interrupt URB in
    `drivers/usb/storage/onetouch.c`.
- **Potentially unsafe usage**: calling the helpers outside the control thread.
  - Unsafe: without `us->dev_mutex` once `usb_stor_probe2()` has started the
    control thread; the helpers use `us->current_urb`, `us->current_sg` or
    `us->cr`, which a command that may be running uses too.
  - Safe: with `us->dev_mutex` held, which `usb_stor_control_thread()` holds
    while it runs a command, as `usb_stor_scan_dwork()` and `device_reset()`
    do.
  - Safe: in an `initFunction`, which `usb_stor_acquire_resources()` calls
    before `kthread_run()` and before `scsi_add_host()`, as
    `usb_stor_euscsi_init()` does.

**iobuf and DMA-safe buffers**

- `us->iobuf`: allocated with `usb_alloc_coherent()` in `associate_dev()`, not
  `kmalloc()`; the DMA address is in `us->iobuf_dma`.
- `usb_stor_msg_common()`: sets `URB_NO_TRANSFER_DMA_MAP` only when
  `transfer_buffer == us->iobuf` (pointer equality); a pointer into the middle
  of `us->iobuf` is mapped by `usb_hcd_map_urb_for_dma()` like any other
  buffer.
- `usb_stor_msg_common()`: assigns `transfer_dma = us->iobuf_dma` for every
  transfer; only the flag is conditional.
- `usb_stor_CB_transport()`: copies `srb->cmnd` into `us->iobuf` with
  `memcpy()` and sends `us->iobuf`; it does not pass `srb->cmnd`.
- Stack command blocks in sub-drivers: for example `rts51x_read_mem()` keeps
  `cmnd[12]` on the stack and `rts51x_bulk_transport()` copies it into
  `bcb->CDB` inside `us->iobuf`.
- **Unsafe usage**: passing a buffer on the stack to
  `usb_stor_bulk_transfer_buf()`, `usb_stor_ctrl_transfer()` or
  `usb_stor_control_msg()`.
  - Unsafe: on a host controller that maps with DMA (`hcd_uses_dma()`, no
    `localmem_pool`), `usb_hcd_map_urb_for_dma()` in
    `drivers/usb/core/hcd.c` hits `WARN_ONCE()` and fails the submit with
    `-EAGAIN`; the first two helpers then return `USB_STOR_XFER_ERROR`, the
    third returns `-EAGAIN`.
  - Safe: build the bytes in `us->iobuf`, as `sddr09_request_sense()` does for
    its command.
  - Safe: a `kmalloc()` buffer, as `rts51x_read_mem()` uses for its data.

**Transfer and transport result codes**

- `usb_stor_ctrl_transfer()`: returns `USB_STOR_XFER_*`, not an errno;
  `usb_stor_control_msg()` is the control helper that returns the length or a
  negative errno.
- `usb_stor_invoke_transport()`, first test after `us->transport()` returns:
  `US_FLIDX_TIMED_OUT` (not `US_FLIDX_ABORTING`); if set the result is
  `DID_ABORT << 16` and it goes to `Handle_Errors`, whatever was returned.
- Reaction to each transport value:

| Value | `usb_stor_invoke_transport()` |
|---|---|
| `USB_STOR_TRANSPORT_GOOD` | `SAM_STAT_GOOD`; auto-sense only when the protocol is `USB_PR_CB` or `USB_PR_DPCM_USB` and the direction is not `DMA_FROM_DEVICE`, or with `US_FL_SENSE_AFTER_SYNC` on `SYNCHRONIZE_CACHE` |
| `USB_STOR_TRANSPORT_FAILED` | REQUEST SENSE through `us->transport()`; when that returns `USB_STOR_TRANSPORT_GOOD`, `SAM_STAT_CHECK_CONDITION`, or `DID_ERROR << 16` when the sense is empty and the command is not `ATA_12` or `ATA_16` |
| `USB_STOR_TRANSPORT_NO_SENSE` | `SAM_STAT_CHECK_CONDITION`, `last_sector_hacks()`, return; the transport has already filled `srb->sense_buffer` |
| `USB_STOR_TRANSPORT_ERROR` | `DID_ERROR << 16`, `Handle_Errors` |
| any other value | no default case: it matches none of the tests, so `srb->result` is set to `SAM_STAT_GOOD` and the value triggers no auto-sense and no reset |

- The two families overlap in value: `USB_STOR_XFER_SHORT` equals
  `USB_STOR_TRANSPORT_FAILED`, `USB_STOR_XFER_STALLED` equals
  `USB_STOR_TRANSPORT_NO_SENSE`, `USB_STOR_XFER_LONG` equals
  `USB_STOR_TRANSPORT_ERROR`.
- **Unsafe usage**: returning a `USB_STOR_XFER_*` value other than
  `USB_STOR_XFER_GOOD`, or a negative errno, from `us->transport()`.
  - Unsafe: `USB_STOR_XFER_ERROR` (4) and any errno match none of the tests in
    `usb_stor_invoke_transport()` and leave `SAM_STAT_GOOD`; values 1 to 3 are
    taken as the transport code with the same number.
  - Safe: map the transfer result first, as `usb_stor_Bulk_transport()` and
    `usb_stor_CB_transport()` do.
- `us->transport_reset()` result: `device_reset()` treats only a negative value
  as failure; `Handle_Errors` ignores it.
- `interpret_urb_result()`: has no case for `-ENOENT` (what `usb_kill_urb()`
  leaves); it falls to the default and gives `USB_STOR_XFER_ERROR`.

## Sense, Bulk-only and recovery

**Automatic sense requests**

- `need_auto_sense` in `usb_stor_invoke_transport()` is set by exactly three
  tests:
  - the transport returned `USB_STOR_TRANSPORT_FAILED`;
  - `us->protocol` is `USB_PR_CB` or `USB_PR_DPCM_USB` and
    `srb->sc_data_direction != DMA_FROM_DEVICE`, even when the transport
    returned `USB_STOR_TRANSPORT_GOOD`;
  - `US_FL_SENSE_AFTER_SYNC` is set and `srb->cmnd[0] == SYNCHRONIZE_CACHE`.
- `srb->cmnd[0] == REQUEST_SENSE`: no test of it gates auto-sense; a failed
  REQUEST SENSE is auto-sensed like any other command.
- Nonzero residue on a command not expected to be short: debug message only,
  no auto-sense. `isd200_invoke_transport()` in
  `drivers/usb/storage/isd200.c` is the one that auto-senses on it.
- `USB_STOR_TRANSPORT_GOOD` on `ATA_12` or `ATA_16` with
  `!(srb->cmnd[2] & 0x20)`: sets `US_FL_SANE_SENSE` (unless it or
  `US_FL_BAD_SENSE` is set); this test does not set `need_auto_sense`.
- `USB_STOR_TRANSPORT_NO_SENSE` from the command itself: result
  `SAM_STAT_CHECK_CONDITION`, no auto-sense, no reset.
- Sense length: `US_SENSE_SIZE` (18), or `~0` with `US_FL_SANE_SENSE`, which
  `scsi_eh_prep_cmnd()` clamps to `SCSI_SENSE_BUFFERSIZE` (96). There is no
  32-byte request.
- Sense longer than 18 bytes (`sense_buffer[7] > US_SENSE_SIZE - 8`) with
  `(sense_buffer[0] & 0x7C) == 0x70`: no second REQUEST SENSE; sets
  `US_FL_SANE_SENSE` for later commands and truncates byte 7 to 10.
- `US_FL_SANE_SENSE` is also set by `sdev_configure()` in
  `drivers/usb/storage/scsiglue.c`, for `TYPE_DISK` with
  `scsi_level > SCSI_SPC_2`, unless `US_FL_BAD_SENSE`.
- Large sense request that returns `USB_STOR_TRANSPORT_FAILED`: clears
  `US_FL_SANE_SENSE`, sets `US_FL_BAD_SENSE`, retries once with 18 bytes. An
  abort during a large sense request makes the same flag change.
- `US_FL_BAD_SENSE`: blocks both tests in `usb_stor_invoke_transport()` that
  set `US_FL_SANE_SENSE`.
- Sense fetch aborted (`US_FLIDX_TIMED_OUT`): `DID_ABORT << 16`, then reset.
- Any other sense fetch that is not `USB_STOR_TRANSPORT_GOOD`,
  `USB_STOR_TRANSPORT_NO_SENSE` included: `DID_ERROR << 16`, then reset.
- `US_FL_SCM_MULT_TARG` on that path: returns with `DID_ERROR << 16`, no
  reset, and without calling `last_sector_hacks()`.
- Empty sense (key, ASC, ASCQ zero and filemark/ILI bits clear), no retry of
  the sense command:

| Case | Result |
|---|---|
| command returned `USB_STOR_TRANSPORT_GOOD` | `SAM_STAT_GOOD`, `sense_buffer[0] = 0` |
| `ATA_12` or `ATA_16` | `SAM_STAT_CHECK_CONDITION`, sense untouched |
| otherwise | `DID_ERROR << 16`, sense key forced to `HARDWARE_ERROR` |

- `DID_IMM_RETRY << 16`: only for `READ_10` with `US_FL_INITIAL_READ10`.
  `usb_stor_probe2()` pre-sets `US_FLIDX_REDO_READ10`, so the first
  `READ_10` to reach that test is retried whatever its result; later ones
  when a `READ_10` fails after one succeeded.
- Underflow to `DID_ERROR << 16`: applies when result is `SAM_STAT_GOOD` or
  `srb->sense_buffer[2] == 0`, so also to a `SAM_STAT_CHECK_CONDITION` whose
  byte 2 is zero.

**Bulk-only CSW tolerances**

- CSW `Signature`: a value other than `US_BULK_CS_SIGN` is not rejected. The
  first one seen is stored in `us->bcs_signature`; a later CSW that differs
  returns `USB_STOR_TRANSPORT_ERROR`.
- There is no Olympus signature constant in this tree.
- `US_FL_IGNORE_RESIDUE` affects only the residue; `US_FL_BULK32` only the
  CBW length. Neither relaxes the signature check.
- `Tag` mismatch: accepted when `US_FL_BULK_IGNORE_TAG` is set.
- Check order: `Tag` and `Status` first, then `Signature`. A signature is
  learnt only from a CSW that passed the first two.
- `us->bcs_signature`: never cleared, so it survives resets.
- `usb_stor_Bulk_transport()` does no reset itself; see "Recovery after a
  transport error".
- Tolerances and the reason the code gives:

| Deviation | What the code does | Reason given |
|---|---|---|
| odd CSW signature | learns the first one | broken devices report odd signatures |
| zero-length CSW | reads the CSW once more | devices append needless zero-length packets to data |
| data phase skipped, no ZLP | 13-byte short IN treated as the CSW | device went straight to status |
| babble (`USB_STOR_XFER_LONG`) | still reads CSW; fake sense `usb_stor_sense_invalidCDB` if `Status` is `US_BULK_STAT_OK` | spec requires the CSW; retry is pointless |
| bogus residue | sets `US_FL_IGNORE_RESIDUE` | heuristic on full 36-byte `INQUIRY` or 8-byte `READ_CAPACITY` |

- Skipped data phase: the 13 bytes are tested against `US_BULK_CS_SIGN`, not
  against `us->bcs_signature`.
- Skipped data phase: the first `US_BULK_CS_WRAP_LEN` bytes of the command's
  transfer buffer are zeroed so CSW bytes do not leak to the caller; resid is
  set to the full length; the `Tag`, `Status` and `Signature` checks then run
  as usual.

**Recovery after a transport error**

- Order at `Handle_Errors`: `usb_stor_port_reset()` first.
  `us->transport_reset()`, the class-specific reset, runs only if the port
  reset returned < 0.
- Before either reset: `US_FLIDX_RESETTING` is set and `US_FLIDX_ABORTING`
  cleared under the host lock. With `US_FLIDX_ABORTING` set,
  `usb_stor_msg_common()` returns `-EIO` and the class reset could send
  nothing.
- `us->dev_mutex`: released by `usb_stor_invoke_transport()` around
  `usb_stor_port_reset()` only, and retaken after.
  `usb_stor_port_reset()` itself never touches it.
- Reason: `usb_reset_device()` calls `usb_stor_pre_reset()`, which takes
  `us->dev_mutex`; `usb_stor_post_reset()` releases it.
- `us->transport_reset()`: runs with `us->dev_mutex` held.
- Reset outcome: the return value of `us->transport_reset()` is discarded,
  and neither reset changes `srb->result`.
- `usb_stor_port_reset()` returns an error without resetting when:
  - `us->pusb_dev->quirks & USB_QUIRK_RESET`: `-EPERM`, before any lock is
    tried;
  - `usb_lock_device_for_reset()` fails: device state
    `USB_STATE_NOTATTACHED` or `USB_STATE_SUSPENDED`, interface condition
    `USB_INTERFACE_UNBINDING` or `USB_INTERFACE_UNBOUND`, or the device lock
    not obtained within one second of polling (`-EBUSY`);
  - `US_FLIDX_DISCONNECTING` is set once the lock is held: `-EIO`.
- `usb_stor_port_reset()` makes no test for `USB_STATE_CONFIGURED`.
- A negative return from `usb_reset_device()` itself also leads to the class
  reset.

**SCSI error handlers**

- `command_abort_matching()` with `srb_match` set and `us->srb != srb_match`:
  returns `FAILED`. With `us->srb == NULL`: returns `SUCCESS`.
- `US_FLIDX_TIMED_OUT`: always set once a command matches.
- `US_FLIDX_ABORTING`: set by `command_abort_matching()`, not tested by it.
  It is set, and `usb_stor_stop_transport()` called, only when
  `US_FLIDX_RESETTING` is clear, so an abort cannot cancel the URBs of a
  reset in progress.
- Wait: `wait_for_completion(&us->notify)`, uninterruptible, no timeout. Not
  `us->cmnd_ready`, not `us->dev_mutex`.
- `device_reset()`: calls `command_abort_matching(us, NULL)` first and
  discards its return value, then `us->transport_reset()` under
  `us->dev_mutex`. It does not call `usb_stor_report_device_reset()`.
- `bus_reset()`: calls only `usb_stor_port_reset()`; aborts nothing and takes
  no `us->dev_mutex` itself. `usb_stor_report_bus_reset()` is called from
  `usb_stor_post_reset()` in `drivers/usb/storage/usb.c`.

## Probe, disconnect and sub-drivers

**Probe in two halves**

- `get_transport()` and `get_protocol()`: run at the end of
  `usb_stor_probe1()`, so `usb_stor_probe2()` does not overwrite the handlers
  the caller sets in between.
- `us->transport` and `us->proto_handler`: must be non-NULL on entry to
  `usb_stor_probe2()`, else `-ENXIO`.
- `initFunction`: runs inside `usb_stor_probe2()`, from
  `usb_stor_acquire_resources()`, not between the halves.
  - It runs after `get_pipes()` and the `us->current_urb` allocation, and
    before `kthread_run()`.
  - It may replace the handlers after the NULL check, as
    `usbat_set_transport()` does, and `realtek_cr_autosuspend_setup()` under
    `CONFIG_REALTEK_AUTOPM`.
- Between the halves `us->current_urb` is NULL and the pipe fields are unset,
  so the transfer helpers in `drivers/usb/storage/transport.c` cannot be used
  there.
- `us->max_lun` set between the halves is overwritten:
  - by `usb_stor_probe2()` when `US_FL_SCM_MULT_TARG` or `US_FL_SINGLE_LUN` is
    set;
  - by `usb_stor_scan_dwork()` when `us->protocol` is `USB_PR_BULK` and
    neither flag is set.
- `usb_stor_probe2()` order: control thread, then
  `usb_autopm_get_interface_no_resume()`, then `scsi_add_host()`.
- `scsi_scan_host()`: not called by `usb_stor_probe2()`; it runs later from
  `usb_stor_scan_dwork()`, which probe2 only queues.
- `usb_stor_probe1()` failure: calls `release_everything()` on every failure
  after `scsi_host_alloc()` succeeded.
- `*pus`: written right after `scsi_host_alloc()` succeeds, so after any later
  failure of `usb_stor_probe1()` it is non-NULL and dangling; when
  `scsi_host_alloc()` itself fails it is not written.
- **Unsafe usage**: returning an error between the halves without calling
  `usb_stor_probe2()`.
  - Unsafe: `release_everything()` is static in `drivers/usb/storage/usb.c`
    and nothing exported undoes `usb_stor_probe1()` alone, so the host,
    `us->cr`, `us->iobuf` and any `us->extra` leak.
  - Safe: do the fallible setup in `initFunction`, where a failure reaches
    `release_everything()` through probe2, as `rio_karma_init()` does.
- **Potentially unsafe usage**: calling `usb_stor_disconnect()` from a probe
  routine.
  - Unsafe: after either half returned non-zero; the interface data is NULL,
    so `usb_stor_disconnect()` dereferences NULL.
  - Safe: after `usb_stor_probe2()` returned 0 and a later step failed, as
    `ene_ub6250_probe()` does; nothing has been released yet.

**Disconnect order**

- `US_FLIDX_DISCONNECTING`: a bit in `us->dflags`; there is no
  US_FLAG_DISCONNECTING here.
- `quiesce_and_remove_host()` sets the bit under `scsi_lock()`, after
  `scsi_remove_host()` returns.
  - It sets it earlier only when `us->pusb_dev->state` is
    `USB_STATE_NOTATTACHED`.
  - On an unbind with the device present, commands can still run through the
    control thread and the sub-driver during `scsi_remove_host()`.
- `quiesce_and_remove_host()`: does not take `us->dev_mutex` itself, does not
  call `usb_stor_stop_transport()`, and completes no command.
- `scsi_remove_host()`: called unconditionally by
  `quiesce_and_remove_host()`.
- `wake_up(&us->delay_wait)`: wakes only a waiter in
  `usb_stor_reset_common()`; it does not complete `us->cmnd_ready`.
- `usb_stor_release_resources()` order: `complete(&us->cmnd_ready)`,
  `kthread_stop()`, `us->extra_destructor`, `kfree(us->extra)`,
  `usb_free_urb(us->current_urb)`.
- Sub-driver destructor: runs after `kthread_stop()` has returned, and before
  `dissociate_dev()` and `scsi_host_put()`.
- `dissociate_dev()`: frees `us->cr` and `us->iobuf` and clears the interface
  data; it does not free the URB.
- Exit signal: `usb_stor_release_resources()` does not write `us->srb`; the
  thread leaves its command loop because it finds `us->srb` NULL after the
  completion.
- Waiting for the control thread to exit: `kthread_stop()`;
  `struct us_data` has no completion for thread exit.
- Probe-failure path: `release_everything()` runs with
  `US_FLIDX_DISCONNECTING` clear; `us->srb` is NULL because the host was never
  added successfully.

**Sub-driver private data**

- `kfree(us->extra)`: done by `usb_stor_release_resources()` on every path,
  with or without a destructor.
  - `init_usbat()` in `drivers/usb/storage/shuttle_usbat.c` sets `us->extra`
    and no destructor.
- Destructor: frees only what the data points to, never the data itself.
- `us->extra_destructor`: called whenever it is non-NULL; `us->extra` is not
  tested.
  - After `init_realtek_cr()` fails through `INIT_FAIL` it is called with
    NULL, and `realtek_cr_destructor()` returns early.
  - After `rio_karma_init()` fails with `-EIO` it is called with fully
    allocated data.
- **Unsafe usage**: an init function that frees the data on its error path
  and leaves `us->extra` pointing at it.
  - Unsafe: `usb_stor_probe2()` then calls `release_everything()`, which runs
    any destructor on freed memory and frees the data again.
  - Safe: free before `us->extra` is assigned, as `isd200_init_info()` does.
  - Safe: free and set `us->extra` to NULL, with a destructor that accepts
    NULL, as `init_realtek_cr()` does.
  - Safe: free nothing and return the error, as `init_usbat()` does.
- There is no del_timer_sync() in this tree; `include/linux/timer.h` has
  `timer_delete_sync()` and `timer_shutdown_sync()`.
- Self re-arming timer: allowed; `rts51x_suspend_timer_fn()` re-arms itself,
  and `mod_timer()` does nothing once `timer_shutdown_sync()` has run.
- `timer_setup()` in `init_realtek_cr()`: comes right after `us->extra` is
  assigned and before any step that can fail, so the destructor never sees a
  non-NULL pointer with an uninitialised timer.
- `rts51x_suspend_timer_fn()`: takes neither `us->dev_mutex` nor the host
  lock and does not test `US_FLIDX_DISCONNECTING`; it reaches `us` through
  `chip->us`, which is valid until `scsi_host_put()`.
- Work items: no sub-driver in `drivers/usb/storage/` keeps one in
  `us->extra`; the core stops its own `us->scan_dwork` with
  `cancel_delayed_work_sync()` in `quiesce_and_remove_host()`.

**Sub-driver tables and registration**

- `.driver_info`: holds the entry's flags, which `get_device_info()` copies
  to `us->fflags`; it is not the index.
- Index: the pointer difference `id - karma_usb_ids`, with no range check in
  `karma_probe()`; `karma_driver` sets `.no_dynamic_id = 1`, so no id from
  outside the table arrives.
- `karma_usb_ids[]` and `karma_unusual_dev_list[]`: both `static const`.
- Main driver exclusion: `ignore_ids[]` in
  `drivers/usb/storage/usual-tables.c`, tested by `usb_usual_ignore_device()`
  in `storage_probe()` before `usb_stor_probe1()`; on a match
  `storage_probe()` returns `-ENXIO`, whatever `unusual_devs.h` says for the
  device; there is no USB_US_TYPE_NONE.
  - The list of `unusual_*.h` includes there is written by hand; a new
    sub-driver header must be added to it.
  - The match is on the device's vendor, product and `bcdDevice` range only,
    so every interface of the device is refused.
  - The guard in `unusual_karma.h` is a compile-time test, so the main driver
    refuses the device whenever the option is `y` or `m`, even if `ums-karma`
    is not loaded.
- `NO_SDDR09` in `unusual_devs.h`: the one place where the main table itself
  changes with a sub-driver option; when `CONFIG_USB_STORAGE_SDDR09` is off
  it adds entries for devices that `unusual_sddr09.h` claims when the option
  is on.
- `karma_host_template`: declared by the source as a non-const
  `static struct scsi_host_template`, with no initialiser.
  - `module_usb_stor_driver()` does not define it; it fills it with
    `usb_stor_host_template_init()` and then calls `usb_register()`.
- `MODULE_DEVICE_TABLE(usb, karma_usb_ids)`: needed for autoloading.
- Symbol namespace: the core uses plain `EXPORT_SYMBOL_GPL()`; the namespace
  comes from `DEFAULT_SYMBOL_NAMESPACE` in `drivers/usb/storage/Makefile`.
- `CONFIG_USB_STORAGE_KARMA`: has no `depends on` line; the entry sits inside
  the `if USB_STORAGE` block of `drivers/usb/storage/Kconfig`.

## UAS

**UAS command bookkeeping**

- Tag table: `devinfo->cmnd[]` in `struct uas_dev_info`, slot index
  `uas_tag - 1`; there is no uas_find_uas_cmnd() here, and
  `struct uas_cmd_info` has no list member. `uas_stat_cmplt()` indexes the
  array with the tag from the IU.
- `devinfo->shutdown`: not covered by `devinfo->lock`; `uas_shutdown()`
  writes it and `uas_pre_reset()` / `uas_post_reset()` read it unlocked.
- `uas_submit_urbs()`: takes `cmnd` and `devinfo` only, no gfp argument;
  every allocation and submit in it uses `GFP_ATOMIC`.
- `uas_submit_urbs()` return: 0, `-ENOMEM` for a failed allocation, or the
  `usb_submit_urb()` error; never a `SCSI_MLQUEUE_DEVICE_BUSY` style value.
- `uas_submit_urbs()` on failure: leaves the state bit of the failed step
  set, for example `ALLOC_DATA_IN_URB` or `SUBMIT_CMD_URB`, so a retry
  resumes at that step.
- `uas_cmd_cmplt()`: takes no lock and touches no command state; it only
  logs a nonzero `urb->status` and frees the URB.
- `COMMAND_INFLIGHT`: set when the cmd URB is submitted, cleared by
  `uas_stat_cmplt()` on `IU_ID_STATUS` or `IU_ID_RESPONSE` and by
  `uas_zap_pending()`; it means "status not yet received", not "cmd URB not
  yet completed".
- `uas_try_complete()`: `COMMAND_ABORTED` blocks completion as well as the
  three in-flight bits.
- `uas_queuecommand_lck()` when `devinfo->resetting` is set or
  `uas_submit_urbs()` returns an error, all returning 0 unless noted:

  | Condition | Action | Slot stored |
  |---|---|---|
  | `devinfo->resetting` | `DID_ERROR`, `scsi_done()` | no |
  | `-ENODEV`, no in-flight bit set | `DID_NO_CONNECT`, `scsi_done()` | no |
  | `-ENODEV`, an in-flight bit set | nothing; no `scsi_done()`, no `uas_add_work()` | yes |
  | other error, `SUBMIT_STATUS_URB` still set | returns `SCSI_MLQUEUE_DEVICE_BUSY` | no |
  | other error, `SUBMIT_STATUS_URB` clear | `uas_add_work()` | yes |

- `SUBMIT_STATUS_URB` still set after `uas_submit_urbs()` fails in
  `uas_queuecommand_lck()`: only when `uas_submit_sense_urb()` failed; there
  a data or cmd URB allocation or submit failure other than `-ENODEV` always
  goes to `uas_add_work()`, never to `SCSI_MLQUEUE_DEVICE_BUSY`.
- `uas_do_work()` on a failed retry: requeues `devinfo->work`; it sets no
  result and completes no command.
- `uas_add_work()`: uses `queue_work()` on the file-local `workqueue` in
  `drivers/usb/storage/uas.c`, not `schedule_work()`;
  `uas_wait_for_pending_cmnds()` flushes that work with `flush_work()`.
- **Potentially unsafe usage**: calling `scsi_done()` on a uas command
  outside `uas_try_complete()`.
  - Unsafe: when the command is in `devinfo->cmnd[]` or one of its in-flight
    bits is set; `uas_stat_cmplt()` finds it through the slot and
    `uas_data_cmplt()` takes it from `urb->context`.
  - Safe: in `uas_queuecommand_lck()` before the command is stored in
    `devinfo->cmnd[]` and before any of its URBs is submitted, as the
    `devinfo->resetting` branch does.
  - Safe: clear the in-flight bit under `devinfo->lock`, then call
    `uas_try_complete()`, which tests the bits; `uas_data_cmplt()` does this.

**UAS error handling and reset**

- Handlers installed in `uas_host_template`: `.eh_abort_handler =
  uas_eh_abort_handler` and `.eh_host_reset_handler =
  uas_eh_host_reset_handler`; there is no uas_eh_device_reset_handler() here.
- `.eh_device_reset_handler`, `.eh_target_reset_handler`,
  `.eh_bus_reset_handler`: not set by uas; `scsi_try_bus_device_reset()`,
  `scsi_try_target_reset()` and `scsi_try_bus_reset()` in
  `drivers/scsi/scsi_error.c` return `FAILED` for a NULL handler, so the only
  reset step of SCSI EH that reaches uas is the host reset.
- Per-device template hooks: `.sdev_init = uas_sdev_init` and
  `.sdev_configure = uas_sdev_configure`; the template has no slave_alloc
  member.
- `uas_eh_abort_handler()`: acts on the one command passed in; it kills only
  that command's in-flight data URBs with `usb_kill_urb()`, touches no
  anchor, and has no warning for an already set `COMMAND_ABORTED`; there is
  no uas_abort_work here.
- `uas_eh_host_reset_handler()`: after `usb_lock_device_for_reset()` it sets
  `devinfo->resetting`, kills the `cmd_urbs`, `sense_urbs` and `data_urbs`
  anchors, calls `uas_zap_pending()` with `DID_RESET`, calls
  `usb_reset_device()`, clears `resetting`, then `usb_unlock_device()`.
- `usb_reset_device()` in `drivers/usb/core/hub.c`: calls `uas_pre_reset()`
  before and `uas_post_reset()` after the port reset, so on the host reset
  path both run inside `uas_eh_host_reset_handler()` with `resetting` set and
  the table already zapped.
- `uas_pre_reset()`: does not set `resetting` and kills no URB; it blocks the
  host and waits in `uas_wait_for_pending_cmnds()`; it returns 0 or 1, never
  a negative errno.
- `uas_pre_reset()` returning 1: `usb_reset_device()` calls
  `usb_forced_unbind_intf()` before the port reset and does not call
  `uas_post_reset()` for that interface.
- `uas_post_reset()`: does not clear `resetting`, does not call
  `uas_zap_pending()` and submits no URB itself.
- `uas_post_reset()` returning 1: sets `needs_binding`;
  `usb_unbind_and_rebind_marked_interfaces()` is called only when the port
  reset returned 0.
- Completion while `devinfo->resetting`: `uas_stat_cmplt()` returns without
  clearing `COMMAND_INFLIGHT`; `uas_data_cmplt()` clears its in-flight bit
  and URB pointer first, then returns without `uas_try_complete()`.
- `uas_zap_pending()`: walks `devinfo->cmnd[]` only, so a command whose slot
  `uas_eh_abort_handler()` cleared is not completed by it.
- `uas_disconnect()`: kills the three anchors between
  `cancel_work_sync(&devinfo->work)` and `uas_zap_pending()` with
  `DID_NO_CONNECT`, and calls `cancel_work_sync(&devinfo->scan_work)` before
  `scsi_remove_host()`.
- `uas_shutdown()`: returns at once unless `system_state == SYSTEM_RESTART`;
  only then does it set `devinfo->shutdown`, free the streams and reset.
- **Unsafe usage**: calling `uas_zap_pending()` while a data URB of a
  command in `devinfo->cmnd[]` is still in flight.
  - Unsafe: `uas_try_complete()` returns `-EBUSY` on the data in-flight bit,
    the `WARN_ON()` in `uas_zap_pending()` fires and the command stays in
    its slot.
  - Safe: set `devinfo->resetting`, then kill the `data_urbs` anchor first,
    as `uas_disconnect()` does; `uas_data_cmplt()` clears the in-flight bit
    even while `resetting`.
- **Unsafe usage**: calling `usb_kill_urb()` or `usb_kill_anchored_urbs()`
  while holding `devinfo->lock`.
  - Unsafe: `usb_kill_urb()` has `might_sleep()` and waits for the
    completion handler, and `uas_data_cmplt()` takes `devinfo->lock`.
  - Safe: take `usb_get_urb()` references under the lock, drop the lock,
    then `usb_kill_urb()` and `usb_put_urb()`, as `uas_eh_abort_handler()`
    does.

## Model gaps

### Other mistakes models make

- Models take DMA alignment to come from blk_queue_update_dma_alignment().
  That function is not in this tree; `usb_stor_host_template` sets
  `.dma_alignment = 511`.
- Models do not know that `uas_queuecommand_lck()` first returns
  `SCSI_MLQUEUE_DEVICE_BUSY` when `host_self_blocked` is set.
- Models do not know that `delay_use` is held in milliseconds:
  `usb_stor_probe2()` passes it to `msecs_to_jiffies()`, and
  `delay_use_set()` scales a bare number by 1000 and takes an "ms" suffix
  as is.
- Models do not know the `CONFIG_HIGHMEM` test in `usb_stor_probe1()`: with
  `CONFIG_HIGHMEM` enabled, a host controller without DMA or with
  `localmem_pool` gets `-EINVAL` through label `release`.
- Models do not know the LUN limit in `usb_stor_Bulk_max_lun()`: it returns 0
  for a byte above `US_BULK_MAX_LUN_LIMIT`.
- Models take queue callbacks to return int. `queuecommand_lck()` and
  `uas_queuecommand_lck()` return `enum scsi_qc_status`, with a literal 0 for
  success; see `DEF_SCSI_QCMD()` in `include/scsi/scsi_host.h`.
- Models do not know `kmalloc_obj()` and `kzalloc_obj()` from
  `include/linux/slab.h`; `associate_dev()` and, for example, `init_alauda()`
  allocate with them.
- Models name slave_alloc and slave_configure as template hooks.
  `struct scsi_host_template` has neither here; `usb_stor_host_template` sets
  `.sdev_init` and `.sdev_configure`.
