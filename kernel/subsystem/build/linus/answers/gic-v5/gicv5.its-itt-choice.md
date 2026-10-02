- Two-level support bit: `GICV5_ITS_IDR1_ITT_LEVELS` in `GICV5_ITS_IDR1`;
  `GICV5_ITS_IDR2` only supplies the maximum, `GICV5_ITS_IDR2_EVENTID_BITS`.
- Two-level is chosen when that bit is set and `event_id_bits` is at least the
  L2 bits; with the bit set, `gicv5_its_l2sz_two_level()` returns false only
  for `l2_bits > id_bits`.
- `event_id_bits` equal to the L2 bits: `gicv5_its_create_itt_two_level()`
  returns `-EINVAL` (its test is `>=`); there is no fallback to
  `gicv5_its_create_itt_linear()`.
- **Unsafe usage**: making the index of the `out_free` loop in
  `gicv5_its_create_itt_two_level()` unsigned.
  - Unsafe: `i >= 0` is always true for an unsigned index, and a failure at
    slot 0 starts the loop at `i - 1`, so `l2ptrs` is indexed out of bounds.
  - Safe: `int i` counting down from `i - 1` while `i >= 0`, as the function
    does; `i` is the only signed index there, `num_ents` and the loop in
    `gicv5_its_free_itt_two_level()` are `unsigned int`.
- **Unsafe usage**: calling `gicv5_its_free_itt()` after
  `gicv5_its_create_itt_two_level()` failed.
  - Unsafe: `its_dev->itt_cfg.l2.l2ptrs`, `l1itt`, `num_l1_ents` and
    `l2itt = true` are set before the allocation loop and not cleared in
    `out_free`, so the tables would be freed twice.
  - Safe: return the error without freeing, as `gicv5_its_device_register()`
    does; `gicv5_its_alloc_device()` then jumps to `out_dev_free`, past
    `gicv5_its_device_unregister()`.
