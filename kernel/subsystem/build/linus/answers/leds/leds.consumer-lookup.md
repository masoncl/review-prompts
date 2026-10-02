- `provider`: compared with the class device name, not with
  `led_cdev->name`; registration does not rewrite `led_cdev->name` when it
  appends a suffix.
- Name collision: the LED that already holds the plain name is the one
  `class_find_device_by_name()` finds, so `led_get()` returns that other LED
  and does not defer.
- Entry use: `led_get()` reads the entry only under `leds_lookup_lock` and
  keeps no pointer to it; the returned LED does not depend on the entry.
- **Potentially unsafe usage**: a `struct led_lookup_data`, or a string it
  points to, in memory that is not static.
  - Unsafe: when the memory, or a string it points to, is released while the
    entry is still on `leds_lookup_list`; every later `led_get()` that
    reaches the table walks it.
  - Safe: an entry embedded in driver data and removed before that data is
    freed, as `skl_int3472_unregister_leds()` does for entries added by
    `skl_int3472_register_led()`.
  - Safe: an entry added just before the get and removed just after, as
    `yogabook_probe()` does around `devm_led_get()`.
- **Unsafe usage**: adding an entry with a NULL `dev_id` or `con_id`, or
  calling `led_get()` with a NULL `con_id`; `led_get()` passes them to
  `strcmp()` untested.
  - Safe: fill every string before `led_add_lookup()`, as `yogabook_probe()`
    sets `dev_id` from `dev_name()` first.
- **Unsafe usage**: `led_remove_lookup()` on an entry that is not on the
  list, either never added or already removed; it tests only for a NULL
  pointer before `list_del()`.
  - Safe: remove only what was added, as `skl_int3472_unregister_leds()`
    loops over the `n_leds` entries that `skl_int3472_register_led()` added.
