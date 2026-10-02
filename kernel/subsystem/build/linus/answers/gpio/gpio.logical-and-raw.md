- Descriptor flag names: `GPIOD_FLAG_ACTIVE_LOW`, `GPIOD_FLAG_OPEN_DRAIN` and
  `GPIOD_FLAG_OPEN_SOURCE` in `drivers/gpio/gpiolib.h`; there is no
  FLAG_ACTIVE_LOW.
- Open drain in `gpiod_set_value_nocheck()`: acts on the value after
  inversion; physical 1 switches the line to input, physical 0 drives it low.
- Open source in `gpiod_set_value_nocheck()`: the mirror image; physical 0
  switches the line to input, physical 1 drives it high.
- `gpiod_set_value_nocheck()`: tests only the flag bit, so it emulates by
  switching direction even where `gpiod_direction_output_nonotify()` had set
  open drain in hardware with `gpio_set_config()`.
- `gpio_direction_input()`: calls `gpiod_direction_input()`; there is no raw
  input call, and input direction carries no polarity.
