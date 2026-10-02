- `device_set_node()` in `led_classdev_register_ext()`: stores the pointer
  and takes no reference on the node.
- Node pointer after registration: stays in `led_cdev->dev` and is read
  later, for example by `led_get_default_pattern()` when a default trigger
  activates, by `fwnode_led_get()`, by `usbport_trig_port_observed()` and by
  `gpio_trig_activate()`.
- Trigger activation can happen at `led_trigger_register()` time, long
  after probe has returned and the iterator has put the child.
- **Unsafe usage**: saving the child pointer inside the loop without
  `fwnode_handle_get()` and passing it as `init_data->fwnode` after the
  loop; `fwnode_get_next_child_node()` has put that child by then.
  - Safe: register inside the body of
    `device_for_each_child_node_scoped()`, as `gpio_leds_create()` does; the
    iterator's reference covers the whole register call.
  - Safe: take `fwnode_handle_get()` in the loop and put it from a devm
    action that was added before the LEDs are registered, as
    `is31fl319x_parse_fw()` does with `is31_free_fwnode()`; devres releases
    in reverse order, so the put runs after the LEDs are unregistered.
- `of_node_get()` and `of_node_put()`: inlines that count nothing in
  `include/linux/of.h` without `CONFIG_OF_DYNAMIC`, so a missing or extra
  reference on an OF node shows no symptom in such a build.
