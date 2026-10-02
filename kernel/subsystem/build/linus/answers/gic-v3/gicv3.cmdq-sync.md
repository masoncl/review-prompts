- `its_build_movi_cmd()` syncs against the collection the event is leaving
  (from `dev_event_to_col()`), not the destination it encodes.
- `its_set_affinity()` updates `col_map` only after `its_send_movi()`
  returns, so the builder still reads the old collection.
- `direct_lpi_inv()` is a redistributor write; it queues no ITS command.
