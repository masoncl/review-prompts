- Models have the table and the deciding bit right; see
  `include/linux/gfp_types.h` and `gfpflags_allow_blocking()` in
  `include/linux/gfp.h`.
- `GFP_TRANSHUGE_LIGHT`: a composite with neither reclaim bit (it is built
  with `& ~__GFP_RECLAIM`), so it neither sleeps nor wakes kswapd;
  `GFP_TRANSHUGE` adds back only `__GFP_DIRECT_RECLAIM`.
