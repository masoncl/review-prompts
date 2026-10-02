- Range checks come first: `type > HID_FEATURE_REPORT` or
  `id >= HID_MAX_IDS` returns NULL before any lookup.
- Lookup: does not call `hid_get_report()` and ignores
  `report_enum->numbered`; a non-zero id indexes `report_id_hash[id]`
  directly, id 0 uses `list_first_entry_or_null()` on `report_list`.
