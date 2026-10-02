- Module alias: `led_trigger_set_default()` requests `"ledtrig:%s"`, with a
  colon.
- `led_trigger_write()`: requests no module itself; a load happens only
  through the word default.
- Modules with a `MODULE_ALIAS()` of that form: few; search the tree for
  `"ledtrig:`. For example `drivers/leds/trigger/ledtrig-default-on.c` has
  one and `drivers/leds/trigger/ledtrig-timer.c` does not.
- Lock order in `led_trigger_set_default()`: `triggers_list_lock` (read),
  then `trigger_lock` (write).
- `default_trigger` equal to "none": `led_trigger_set_default()` calls
  `led_trigger_remove()` and returns before it takes `triggers_list_lock`.
- Failed attach: `led_match_default_trigger()` returns true whatever
  `led_trigger_set()` returned, so no module is requested, the error is
  dropped, and `led_classdev_register_ext()` still succeeds.
- Trigger registered but not `trigger_relevant()` for the LED: counts as not
  found, and the module load is requested.
- Without `CONFIG_MODULES`: `request_module_nowait()` is a stub that returns
  `-ENOSYS`; the LED waits for `led_trigger_register()`.
