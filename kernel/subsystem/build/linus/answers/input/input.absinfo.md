- `input_set_abs_params()`: sets `EV_ABS` and the `absbit` bit before it
  calls `input_alloc_absinfo()`; on allocation failure both bits stay set and
  registration then fails with `-EINVAL`.
- `input_set_capability()` with `EV_ABS`: also calls
  `input_alloc_absinfo()`, so it alone is enough to pass the registration
  check; min, max, fuzz, flat and resolution stay 0.
- Registration returns `-EINVAL` when `EV_ABS` was set in `evbit` by hand
  (`__set_bit()`) and no allocating helper was called, or when the
  allocation failed.
- The registration test looks at `EV_ABS` in `evbit`, not at `absbit`.
