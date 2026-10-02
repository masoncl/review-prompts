- Step: `gpa` advances by the callback's return value times `esz`, not by one
  entry; `id` advances by the same return value.
- Return values of `scan_its_table()`: `< 0` read or callback error; 0 the
  callback found the last element; 1 the next step would leave the table.
- First read: happens before any bound test, so `size` must cover at least
  one entry.
- `next_offset * esz`: a 32-bit multiply, widened afterwards; it is bounded
  because the offsets come from a 14-bit DTE field or a 16-bit ITE field.
- Bound: in bytes, not IDs; `vgic_its_restore_dte()` does not test
  `id + offset`, and an offset past the table ends the scan with 1.
- ID after a step: tested by `vgic_its_restore_dte()` with
  `vgic_its_check_id()`, or by `vgic_its_restore_ite()` with
  `vgic_its_check_event_id()`, only when the new entry is valid;
  `handle_l1_dte()` does not test it.
