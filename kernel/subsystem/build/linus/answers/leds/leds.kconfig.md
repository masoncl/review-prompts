- `CONFIG_LEDS_TRIGGERS`: a `menuconfig` in `drivers/leds/trigger/Kconfig`,
  sourced from `drivers/leds/Kconfig` inside `if NEW_LEDS`.
- `led-triggers.o`: its own object in `drivers/leds/Makefile`, not part of
  `led-class.o`; always built in, also when `LEDS_CLASS=m`.
- `led-triggers.o` and `led-core.o`: reference no symbol of
  `drivers/leds/led-class.c`, so both link built in while the class is a module.
- Optional LED: no Kconfig file in this tree uses `LEDS_CLASS || !LEDS_CLASS` or
  `LEDS_CLASS || LEDS_CLASS=n`, for the class, multicolor or flash symbols.
- Optional LED, forms this tree uses, for example: a bool sub-option with
  `depends on LEDS_CLASS=y || LEDS_CLASS=<TRISTATE>` (`PHYLIB_LEDS`,
  `MAC80211_LEDS`), or `depends on !(R8169=y && LEDS_CLASS=m)` (`R8169_LEDS`).
- `select LEDS_CLASS_MULTICOLOR` from outside: goes with `select NEW_LEDS` and
  `select LEDS_CLASS`, as `HID_MSI` in `drivers/hid/Kconfig` does.
- **Potentially unsafe usage**: a bool option with plain
  `depends on LEDS_CLASS`.
  - Unsafe: when its code calls a function of `drivers/leds/led-class.c`, for
    example `led_classdev_register_ext()`, and can be built in; Kconfig allows
    the bool at `y` with `LEDS_CLASS=m`, and the link fails.
  - Safe: when its code calls only `drivers/leds/led-triggers.c` and
    `drivers/leds/led-core.c` functions, as `BT_LEDS` with
    `net/bluetooth/leds.c` does; with `select LEDS_TRIGGERS` both objects are
    built in.
  - Safe: `depends on LEDS_CLASS=y`, as `PCI_NPEM` in `drivers/pci/Kconfig`.
  - Safe: `depends on LEDS_CLASS=y || LEDS_CLASS=<TRISTATE>`, where the tristate
    is the module the code is linked into, as `NET_DSA_QCA8K_LEDS_SUPPORT`.
