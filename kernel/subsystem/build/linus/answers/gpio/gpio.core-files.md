| Job | File under `drivers/gpio/` | Easy to miss |
|---|---|---|
| Lines with several consumers | `gpiolib-shared.c` (core side, `CONFIG_GPIO_SHARED`); `gpio-shared-proxy.c` (the proxy chip, `CONFIG_GPIO_SHARED_PROXY`) | private header `gpiolib-shared.h` is shared by both; `gpio-aggregator.c` is a different job |
| Integer-based legacy calls | `gpiolib-legacy.c` | `devm_gpio_request_one()` is defined here, not in `gpiolib-devres.c`; `CONFIG_GPIOLIB_LEGACY` is `def_bool y` with no dependency, so the file is built whenever `CONFIG_GPIOLIB` is |
| Generic MMIO helper | `gpio-mmio.c` | no gpio-generic.c source: `gpio-generic.o` is only the composite object name in `drivers/gpio/Makefile`; the one exported entry point is `gpio_generic_chip_init()`, there is no bgpio_init() |
| KUnit tests | `gpiolib-kunit.c` | built by `CONFIG_GPIO_KUNIT`; there is no gpiolib-test.c |
