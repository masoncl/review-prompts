- `HARDWARE MONITORING` in `MAINTAINERS`: has a content pattern,
  `K: (devm_)?hwmon_device_(un)?register(|_with_groups|_with_info)`; this is
  what sends out-of-directory patches to the hwmon list.
- `F:` lines of that entry: cover only docs, bindings, `drivers/hwmon/`,
  `include/linux/hwmon*.h` and `include/trace/events/hwmon*.h`; no file under
  `drivers/acpi/` or any other subsystem is listed.
- Other entries with `L: linux-hwmon@vger.kernel.org`: none covers an
  out-of-directory file that registers a hwmon device; the only paths outside
  `Documentation/` and `drivers/hwmon/` are `include/linux/f75375s.h`,
  `include/dt-bindings/thermal/lm90.h` and `drivers/gpio/gpio-ltc4283.c`.
- `K:` matching in `scripts/get_maintainer.pl`: unanchored, so
  `hwmon_device_register_for_thermal()` and `hwmon_device_unregister()` both
  match.
- `K:` on a patch: tested against the lines before the first `---`/`+++`
  file line (commit message included) and, after it, only against lines that
  start with `+` or `-`; a name that appears only in context lines does not
  match.
- `K:` with `get_maintainer.pl -f <file>`: not applied unless
  `--keywords-in-file` is given; the default is off.
- Finding the callers: search the tree for the `K:` regex; all callers outside
  `drivers/hwmon/` are under `drivers/`, except those under
  `sound/soc/codecs/`.
- No register call exists under `drivers/net/ethernet/wangxun/`,
  `drivers/mfd/`, `drivers/infiniband/` or `drivers/iio/`.
- `drivers/w1/w1.c`: a bus core that registers the hwmon device for slave
  drivers that supply `chip_info`; the slave file has no register call, so a
  patch to it does not match `K:`.
