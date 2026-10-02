- `GPIOD_FLAGS_BIT_NONEXCLUSIVE`: still honoured, and still passed by many
  in-tree drivers, mostly under `drivers/regulator/`.
  - The only message is a `dev_info()` in `gpiod_find_and_request()` on each
    second request. Nothing rejects or warns about a new user.
  - On a line marked `GPIOD_FLAG_SHARED` the flag has no effect: each consumer
    gets its own proxy descriptor, so `gpiod_request()` does not return
    `-EBUSY`.
  - `drivers/regulator/fixed.c` passes the flag unconditionally and is correct
    in both configurations; `regulator_ena_gpio_request()` skips its search of
    `regulator_ena_gpio_list` for an entry with the same descriptor when
    `gpiod_is_shared()` is true.
- Configuration: `GPIO_SHARED` in `drivers/gpio/Kconfig` is `def_bool y` and
  `depends on HAVE_SHARED_GPIOS || COMPILE_TEST`. It has no prompt.
  - Only `ARCH_QCOM` in `arch/arm64/Kconfig.platforms` selects
    `HAVE_SHARED_GPIOS`.
  - `GPIO_SHARED_PROXY` is a separate tristate with `default m`.
- Scan: `gpio_shared_init()` is a `postcore_initcall()` and scans devicetree
  only. `gpio_shared_of_traverse()` takes only:
  - properties named by suffix (`-gpios`, `-gpio`, `gpios`, `gpio`); a legacy
    name of `of_find_gpio_rename()` without such a suffix is not scanned
  - specifiers with exactly two cells, whose target node has
    `gpio-controller`
  - nodes that are available, are not a `gpio-hog` and are not named
    `__symbols__`
- `gpiochip_setup_shared()`, at chip registration, for each line with more
  than one reference:
  - sets `GPIOD_FLAG_SHARED` on the real descriptor
  - requests the real line itself with label "shared", so any direct request
    of that line gets `-EBUSY`
  - creates one auxiliary device per reference, not one per line
- Lookup: `gpio_shared_add_proxy_lookup()` adds a board table whose `key` is
  the proxy chip's label. Until `drivers/gpio/gpio-shared-proxy.c` has bound
  and registered that chip, the consumer gets `-EPROBE_DEFER`.
- `gpio_shared_add_proxy_lookup()`: matches the consumer by fwnode pointer and
  by `con_id`. With no match it does `WARN_ON(1)` and returns `-ENOENT`.
- Proxy chip: `gpio_shared_proxy_probe()` sets `can_sleep` to true whatever the
  real chip is.
  - `gpiod_cansleep()` is true for every shared line.
  - A consumer must use the `_cansleep` value calls, from process context.
- Output value: a vote against `def_val`, not "high wins". See
  `gpio_shared_proxy_set_unlocked()`.
  - `def_val` is the value of the last `direction_output` made while the line
    had one user.
  - The real line is at the other value while at least one consumer asks for
    it, and returns to `def_val` when the last such vote is withdrawn.
  - `gpio_shared_proxy_free()` withdraws the vote of a consumer that releases
    the line.
- Direction with more than one user: `-EPERM` if the request differs from the
  real line's direction. With one user it is applied.
- Configuration with more than one user: `gpio_shared_proxy_set_config()`
  applies a differing value and logs a `dev_dbg()`. It does not refuse.
- `gpiod_get_value_cansleep()` on a proxy: reads the real line, not the
  consumer's own vote.
- `gpiod_is_shared()`: tests `GPIOD_FLAG_SHARED_PROXY`, which is set on the
  proxy's descriptor. `GPIOD_FLAG_SHARED` is on the real line, which consumers
  never hold.
- reset-gpio: the first `reset-gpios` reference to a line adds one placeholder
  reference in `gpio_shared_setup_reset_proxy()`; later ones add none.
  - `gpio_shared_dev_is_reset_gpio()` matches it to the reset-gpio device
    later, and is a stub that returns false without `CONFIG_RESET_GPIO`.
  - `gpio_shared_entry_is_really_shared()`: a line with two references, one of
    them the placeholder, is not shared.
- **Unsafe usage**: requesting a line marked `GPIOD_FLAG_SHARED` with no
  consumer device.
  - Unsafe: when the getter has no `struct device`, as with
    `fwnode_gpiod_get_index()`, which passes a NULL consumer;
    `gpio_shared_add_proxy_lookup()` passes it to `dev_name()`.
  - Safe: `devm_fwnode_gpiod_get_index()`, or `gpiod_get_index()` with a
    non-NULL `dev`; both pass the device as the consumer.
