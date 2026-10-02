- `memparse()` on overflow: returns `ULLONG_MAX`, both when the digits
  overflow (`_parse_integer_limit()` saturates) and when the suffix shift does
  (`check_shl_overflow()`); `*retptr` advances as for a valid value.
- `cpulist_parse()`: returns `-EINVAL`, `-ERANGE` or `-EOVERFLOW`; see
  `bitmap_parselist()` in `lib/bitmap-str.c`.
- `cpulist_parse()` on error: the mask was zeroed first and holds the regions
  parsed before the bad one.
- Integer `param_set_` functions built by `STANDARD_PARAM_DEF()`: return what
  the kstrto helper returns, for example `kstrtouint()`: `-EINVAL` for a parse
  error and `-ERANGE` for a value that does not fit the type.
- `-EPERM`: comes from `parse_one()` and `param_attr_store()` when
  `param_check_unsafe()` refuses, not from a `param_set_` function in
  `kernel/params.c`.
- Array parameters: `param_array()` writes each element as it parses, so on
  an error the earlier elements and `*num` are already changed.
