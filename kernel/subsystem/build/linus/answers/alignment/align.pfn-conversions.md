- `PFN_UP()` result type: the type of `x + PAGE_SIZE`, so unsigned long for an
  argument narrower than unsigned long, and `u64` for a `u64` argument on a
  32-bit kernel.
- `PFN_DOWN()` result type: the integer-promoted type of `x`.
- There is no pfn_t type in this tree; `include/linux/pfn.h` defines only
  five function-like macros.
