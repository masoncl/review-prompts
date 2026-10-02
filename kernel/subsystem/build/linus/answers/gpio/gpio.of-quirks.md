- `of_find_gpio_rename()` entry: keyed by the `con_id` the driver asks for,
  plus `compatible` when not NULL; `legacy_id` is the property then parsed.
- `legacy_id` NULL in an `of_find_gpio_rename()` entry: the property is named
  exactly `con_id`, with no suffix.
- `of_gpio_try_fixup_polarity()` entry: `propname` is compared with
  `strcmp()` against the property name actually parsed.
- Renamed property: the polarity entry carries the legacy name, for example
  `"gpios-reset"` for `"himax,hx8357"`; a tree that uses `reset-gpios` gets no
  override from that entry.
- Suffix in a polarity entry: `reset-gpio` and `reset-gpios` are different
  keys; an entry covers only the one it spells.
- `of_gpio_set_polarity_by_property()`: when the boolean property is absent
  it forces `OF_GPIO_ACTIVE_LOW`, whatever the specifier says; it fits only a
  binding where that property is the sole source of polarity.
- `enable-active-high`: handled by entries of
  `of_gpio_set_polarity_by_property()`, not inline.
- Inline in `of_gpio_flags_quirks()`: `gpio-open-drain` for
  `"reg-fixed-voltage"`, `spi-cs-high` for `cs-gpios`, and
  `snps,reset-active-low`; each is guarded by `IS_ENABLED()` in a C `if`, not
  by `#if`.
- `of_find_gpio_quirks`: holds `of_find_gpio_rename()`,
  `of_find_trigger_gpio()` and, only under
  `IS_ENABLED(CONFIG_SND_SOC_MT2701_CS42448)`, `of_find_mt2701_gpio()`; there
  is no of_find_usb_gpio().
- `of_find_trigger_gpio()`: always in the array; it returns `-ENOENT` itself
  without `CONFIG_LEDS_TRIGGER_GPIO`.
