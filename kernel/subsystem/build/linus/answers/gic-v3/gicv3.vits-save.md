- Device whose ID fails `vgic_its_check_id()`: skipped by
  `vgic_its_save_device_tables()`; the save does not fail.
- `compute_next_devid_offset()`: skips such devices, so the next offset of an
  earlier DTE points at the next device that is saved.
- Event with `ite->collection` NULL: `vgic_its_save_ite()` writes an all-zero
  ITE, which restore reads as invalid.
- `compute_next_eventid_offset()`: skips ITEs with a NULL collection.
- Event whose collection exists with `COLLECTION_NOT_MAPPED`: saved normally
  with its ICID.
- `vgic_its_save_cte()`: sets the valid bit for every collection on the list,
  and stores `COLLECTION_NOT_MAPPED` as the target of an unmapped one.
- Saving fails with `-EACCES` in `vgic_its_save_itt()` for an ITE with
  `ite->irq->hw` set when `kvm_vgic_global_state.has_gicv4_1` is false.
