- `devicename`: in `Documentation/leds/leds-class.rst`, a unique identifier
  created by the kernel, such as phyN or inputN, not the hardware, product or
  vendor; vendor and product names are called deprecated.
- Sections that do not apply are left blank; the examples include
  `":kbd_backlight"` and `"input5::kbd_backlight"`.
- Keyboard with one brightness/colour setting: one (multicolor) LED class
  device, function part `kbd_backlight`, name must end with
  `:kbd_backlight`; the text sets no rule on the devicename or colour part.
- Keyboard with several zones: one LED class device per zone, named
  `<devicename>:<color>:kbd_zoned_backlight-<zone_name>`.
- `<devicename>`: must be the same for all zones of one keyboard.
- `<zone_name>`: descriptive of the part of the keyboard the zone covers and
  fit to show to a user; reuse values of similar keyboards, such as right,
  middle, left, corners, wasd, main, cursor, numpad.
- Exception: one big zone plus small extra areas; the big zone uses
  `kbd_backlight`, the small ones the zoned form.
- Per-key addressable backlights: must not use LED class devices.
- `include/dt-bindings/leds/common.h`: has `LED_FUNCTION_KBD_BACKLIGHT`; it
  has no define for the zoned function, and no code in this tree uses the
  zoned string.
