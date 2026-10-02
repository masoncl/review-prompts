- Hardware control fields in `of_phy_led()`: set only when the PHY driver has
  all three of `led_hw_is_supported`, `led_hw_control_set` and
  `led_hw_control_get`.
- `hw_control_get_device` in `of_phy_led()`: set to
  `phy_led_hw_control_get_device()` unconditionally under
  `CONFIG_LEDS_TRIGGERS`; `struct phy_driver` has no op behind it.
- Brightness in `of_phy_led()`: phylib fills `brightness_set_blocking`, never
  `brightness_set`.
- `of_phy_leds()` is not reached for a genphy driver: `phy_probe()` tests
  `IS_ENABLED(CONFIG_PHYLIB_LEDS) && !phy_driver_is_genphy(phydev)`.
- `of_phy_leds()` registers nothing and returns 0 without `CONFIG_OF_MDIO`, or
  when the driver has none of `led_brightness_set`, `led_blink_set`,
  `led_hw_control_set`.
- Qualcomm PHYs: the LED ops are in `drivers/net/phy/qcom/qca807x.c` and
  `drivers/net/phy/qcom/qca808x.c`; `drivers/net/phy/qcom/at803x.c` sets none.
- Providers outside phylib fill `struct led_classdev` themselves; search for
  assignments to `hw_control_trigger` to list them (DSA:
  `drivers/net/dsa/qca/qca8k-leds.c`, `drivers/net/dsa/mv88e6xxx/leds.c`;
  MAC: `drivers/net/ethernet/realtek/r8169_leds.c`,
  `drivers/net/ethernet/intel/igc/igc_leds.c`).
- `drivers/net/ethernet/realtek/r8169_leds.c`: registers LEDs with
  `hw_control_trigger` and the four `hw_control_` callbacks, and no
  brightness callback at all.
- `drivers/leds/leds-cros_ec.c`: sets `hw_control_trigger` to its private
  trigger name and sets none of the callbacks; its hardware mode is entered by
  the trigger's own `activate`, through `trigger_type`
  (`struct led_hw_trigger_type`), as in `drivers/leds/leds-turris-omnia.c`.
- Consumer: `drivers/leds/trigger/ledtrig-netdev.c` is the only code that
  reads `hw_control_trigger` or calls the four callbacks.
