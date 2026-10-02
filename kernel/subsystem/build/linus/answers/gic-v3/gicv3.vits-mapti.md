- Collection: need not exist or be mapped; a missing one is created unmapped
  by `vgic_its_alloc_collection()`.
- Collection ID of a missing collection: must pass `vgic_its_check_id()`
  against `its->baser_coll_table`, else `E_ITS_MAPC_COLLECTION_OOR`.
- Event ID: `vgic_its_check_event_id()` also requires the ITT slot of the
  event to be in a visible memslot, not only the range.
- LPI number: rejected when `lpi_nr < GIC_LPI_OFFSET` or
  `lpi_nr >= max_lpis_propbaser(kvm->arch.vgic.propbaser)`; there is no other
  case.
- Unwind: a collection created by this command is freed with
  `vgic_its_free_collection()` when `vgic_its_alloc_ite()` or
  `vgic_add_lpi()` fails; a collection that already existed is kept.
