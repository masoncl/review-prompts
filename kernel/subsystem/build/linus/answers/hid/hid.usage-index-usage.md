- `hid_set_field()` value check: no clamping and no comparison of the value
  with `logical_minimum` or `logical_maximum`.
- `hid_set_field()` on a field with `logical_minimum < 0`: returns -1 after
  `hid_err()` when the value does not fit in `report_size` bits; on other
  fields any value is stored.
- Array field (no `HID_MAIN_ITEM_VARIABLE`): the `usage[]` index is
  `value - field->logical_minimum` and must be below `field->maxusage`.
- `hid_array_value_is_valid()`: makes that check for the core but is static
  in `drivers/hid/hid-core.c`; a driver has to write the test itself.
