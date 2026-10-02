These are conventions that the maintainers of the LED subsystem ask of new
code. Existing code may differ. A kernel tree cannot supply all of them, so
they are kept by hand and inserted as they are.

- The subject of a commit has the form "leds: <driver>: <Capitalized
  description>", for example "leds: qwerty: Add support for Qwerty LED".
- Always capitalize the description after the subsystem prefix. The MFD and
  Backlight subsystems ask for the same.
- Choose clear names for data structures. Name the structure that holds a
  driver's private data after the device, for example struct qwerty_led, and
  name the variable that holds an instance `ddata`. Avoid generic names such
  as `info` or `priv`.
- Prefer `devm_led_classdev_register()` or `devm_led_classdev_register_ext()`
  to the unmanaged `led_classdev_register()`.
- Prefer `devm_led_trigger_register()` to `led_trigger_register()` where
  possible.
- In a new device tree binding, prefer the `color` and `function` properties
  to `label`. Use `label` only in a legacy driver or for backwards
  compatibility.
- Do not print a message when an operation succeeds, such as "LED registered
  successfully" or "Probe success". Log only errors and warnings.
- Always use `dev_err_probe()` to report a probe failure, such as a missing
  regulator or GPIO.
