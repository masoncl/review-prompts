- Empty property from `populate_properties()`: `length` 0 with a non-NULL
  `value`, so the integer and index readers, and the array readers asked for
  one or more elements, return `-EOVERFLOW`, not `-ENODATA`.
- `-ENODATA` from an integer read: only when `value` is NULL, which
  `of_find_property_value_of_size()` tests before the length.
- `of_pdt_build_one_prop()` in `drivers/of/pdt.c`: sets `length` to 0 and
  does not assign `value` when the firmware reports a property length of 0
  or less.
- Variable forms with `sz_min` 0 and nonzero `sz_max`: an empty property with
  a non-NULL `value` passes both size tests and the call returns 0 elements.
- Variable forms, property longer than a nonzero `sz_max` elements:
  `-EOVERFLOW`; nothing is truncated or copied.
- `of_property_read_string()`: tests `!prop->length` for `-ENODATA`.
- `of_property_read_string_helper()` and `of_property_match_string()`: test
  `!prop->value`; an empty property with non-NULL `value` still gives
  `-ENODATA`, from the fall-through after the loop.
- `of_property_read_string_array()` returning `-EILSEQ`:
  `of_property_read_string_helper()` has already stored the pointers to the
  strings before the unterminated one, so the output array is partly
  written.
- The integer, array and index readers, `of_property_read_string()` and
  `of_property_read_string_index()`: every error return comes before the
  first store, so the output is unchanged on failure.
