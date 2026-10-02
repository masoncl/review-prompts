| Function | Rejects | Does not test |
|---|---|---|
| `vgic_its_restore_dte()` | `num_eventid_bits > VITS_TYPER_IDBITS`, then `vgic_its_check_id()` failure; both `-EINVAL` | an existing device with that ID; the ITT address |
| `vgic_its_restore_ite()` | non-zero `lpi_id < VGIC_MIN_LPI`; `event_id + offset` out of range; missing collection; `vgic_its_check_event_id()` failure; all `-EINVAL` | `find_ite()`; the upper LPI bound of `max_lpis_propbaser()` |

- Collection in `vgic_its_restore_ite()`: must exist; it may be unmapped, and
  then `vgic_add_lpi()` gets a NULL vCPU.
- ITT address: tested only indirectly, by the read in `scan_its_table()` and
  by `vgic_its_check_event_id()` for each valid ITE.
- `vgic_its_free_device_list()` on a failed device restore: frees every
  device on `its->device_list`, not only those this restore created.
