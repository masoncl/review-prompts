- `syscon_node_to_regmap()`: returns the entry of any node already on
  `syscon_list`, whatever its compatible; the `syscon` compatible only decides
  whether a missing entry is created.
- Entries reach the list without `syscon` in two ways:
  `of_syscon_register_regmap()` and an earlier `device_node_to_regmap()`.
- `syscon_node_to_regmap()` on creation: takes only clock index 0 with
  `of_clk_get()` and one reset with
  `of_reset_control_get_optional_exclusive()`, then deasserts the reset.
- `regmap_mmio_attach_clk()`: only prepares the clock;
  `drivers/base/regmap/regmap-mmio.c` enables and disables it around each
  register access.
- `device_node_to_regmap()`: touches no clock and no reset.
- Clock error other than `-ENOENT`, or any reset error: the lookup fails with
  that code (for example `-EPROBE_DEFER`) and no entry is added, so the next
  lookup tries again.
- First creator wins: clock and reset are handled only when the entry is
  created, so `syscon_node_to_regmap()` after `device_node_to_regmap()` on the
  same node returns the regmap with no clock attached and the reset untouched.
- `syscon_regmap_lookup_by_phandle()` with a NULL `property`: looks up `np`
  itself.
