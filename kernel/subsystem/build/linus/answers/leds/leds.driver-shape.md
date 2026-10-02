- Iteration: both `gpio_leds_create()` and `led_pwm_create_fwnode()` use
  `device_for_each_child_node_scoped()`; neither calls
  `fwnode_handle_put()`, and early `return` inside the loop is correct.
- No child nodes: `gpio_leds_create()` returns `-ENODEV`, `led_pwm_probe()`
  returns `-EINVAL`.
- `led_pwm_create_fwnode()`: returns `-EINVAL` for a child with neither
  `label` nor an OF node.
- `led_pwm_add()`: sets `cdev.name` to that label or node name and also
  passes `init_data` with the node, so the sysfs name comes from
  `led_compose_name()` and can differ from `cdev.name`.
- `led_pwm_add()` with `LEDS_DEFSTATE_KEEP`: reads `pwm_get_state()`; a
  period of 0 turns the state into `LEDS_DEFSTATE_OFF` and uses
  `pwm_init_state()`.
- `create_gpio_led()` after registering: calls
  `devm_pinctrl_get_select_default()` on the LED class device, which works
  through the node the core set; an error other than `-ENODEV` fails probe.
- `platform_set_drvdata()`: both drivers call it after all LEDs are
  registered; the callbacks reach their data with `container_of()`.
