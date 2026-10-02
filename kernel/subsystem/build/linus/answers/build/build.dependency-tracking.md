- Per-option file: `include/config/FOO` for `CONFIG_FOO`; the name is copied
  as written, same case, flat, no `.h` suffix. See `use_config()` in
  `scripts/basic/fixdep.c` and `conf_touch_dep()` in
  `scripts/kconfig/confdata.c`.
- `is_ignored_file()`: drops only `include/generated/autoconf.h`;
  `include/linux/kconfig.h` stays in `deps_<target>` and is scanned.
- `_MODULE` suffix: stripped by `parse_config_file()`, so `CONFIG_FOO_MODULE`
  records `include/config/FOO`.
- Token pasting: `CONFIG_##name` records nothing, because the name after
  `CONFIG_` is empty; an object that reaches an option only that way is not
  rebuilt when the option changes.
- `conf_touch_deps()`: touches the file when the value differs from the old
  `include/config/auto.conf`, when an option with no old value is now set,
  and when an option with an old value has no new one.
- Header rule without `FORCE`: `$(call cmd,...)` with real prerequisites only
  is also valid, as the `.asn1.h` rule in `scripts/Makefile.build`; it reruns
  on timestamps only, and a header that `make clean` must remove then goes in
  `clean-files`, as `crc32table.h` in `lib/crc/Makefile`.
- Header name in the depfile: `parse_dep_file()` copies it verbatim into
  `deps_<target>` and emits `$(deps_<target>):` with no recipe; fixdep puts
  no requirement on how the explicit dependency is spelled.
