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
