- `hid_register_field()`: takes `(report, usages)` and makes one `kvzalloc()`
  holding the struct and its trailing arrays.
- `usage`, `value`, `new_value` and `usages_priorities`: each has `usages`
  entries, where `usages` is the larger of the declared usage count and
  `report_count`; that number is `field->maxusage`.
- `value` and `new_value`: not sized by `report_count`; entries from
  `report_count` up to `maxusage` exist, and the core never copies report
  data into them.
- `usage`: never has fewer than `report_count` entries.
