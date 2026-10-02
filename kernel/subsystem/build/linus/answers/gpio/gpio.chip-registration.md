- `gc->parent` NULL: accepted without a warning.
- `gc->label` NULL: `gdev->label` becomes `"unknown"`.
- `gdev->owner`: `gc->parent->driver->owner` when the parent is bound, else
  `gc->owner`, else `THIS_MODULE` of gpiolib; `gc->owner` is ignored when the
  parent has a driver.
- `gpiochip_get_ngpios()`: when `gc->ngpio` is 0, reads `"ngpios"` with
  `fwnode_property_read_u32()` from `gpiochip_choose_fwnode()`, so
  `gc->fwnode` wins over the parent's node, and writes the result to
  `gc->ngpio`.
- `gpiochip_get_ngpios()` read error other than `-ENODATA`: returned as it
  is, without the zero-lines message.
- `gc->names` and `"gpio-line-names"`: both are applied; each non-empty
  property string overrides the `gc->names` entry.
- `gpiochip_set_desc_names()`: stores the `gc->names[i]` pointers without
  copying, and warns only about a name already used on another chip.
- Hogs: `of_gpiochip_add()` applies none and the tree has no
  machine_gpiochip_add(); `gpiochip_hog_lines()` runs after
  `acpi_gpiochip_add()` for each child fwnode with `"gpio-hog"`, except an
  OF node already marked `OF_POPULATED`.
- Failing hog: `gpiochip_hog_lines()` returns the error and registration
  fails; a hog node with no state property only warns.
- `of_gpiochip_add()`: there is no of_gpio_simple_xlate(); the default is
  `of_gpio_twocell_xlate()`, or `of_gpio_threecell_xlate()` when
  `of_gpio_n_cells` is 3, which needs `of_node_instance_match` or fails with
  `-EINVAL`.
- First driver callback called: `init_valid_mask()`; the `get_direction()`
  loop comes after it and skips lines the mask excludes.
- `gpio_device_find()`: skips a device until `device_is_registered()` is
  true, so fwnode, OF, ACPI and label lookups cannot find the chip before
  `gpiochip_setup_dev()`, the last step.
- Reachable before `gpiochip_setup_dev()`, from list insertion on:
  `gpio_to_desc()` by number, `gpio_name_to_desc()` by line name, and
  `gc->dbg_show()` through debugfs in `gpiolib_seq_show()`; none of them
  tests `device_is_registered()`.
- Hogs and ACPI event interrupts (`acpi_gpiochip_request_interrupts()`):
  request lines and call the chip before a lookup through
  `gpio_device_find()` can.
