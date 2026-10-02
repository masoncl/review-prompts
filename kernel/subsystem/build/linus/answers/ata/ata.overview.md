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
