- `intel_cx0_phy_transaction_begin()`: calls `intel_psr_pause()`, takes
  `POWER_DOMAIN_DC_OFF`, and programs the message bus timer on both lanes. It
  returns a `struct ref_tracker *`.
- Both transaction helpers are static in
  `drivers/gpu/drm/i915/display/intel_cx0_phy.c`. Code in another file that
  calls `intel_cx0_read()`, `intel_cx0_write()` or `intel_cx0_rmw()` needs its
  own bracket, as `intel_lt_phy_transaction_begin()` in
  `drivers/gpu/drm/i915/display/intel_lt_phy.c` provides (no timer
  programming there).
- Bracket themselves: `intel_cx0_phy_set_signal_levels()`,
  `intel_cx0pll_enable()`, `intel_cx0pll_disable()`,
  `intel_c10pll_readout_hw_state()`, `intel_c20pll_readout_hw_state()`,
  `intel_lnl_mac_transmit_lfps()`.
- Bracketed only through a callee: `intel_cx0pll_readout_hw_state()`,
  `intel_mtl_pll_enable()`, `intel_mtl_pll_disable()`,
  `intel_cx0_pll_power_save_wa()`. The `mtl_pll_funcs` hooks in
  `drivers/gpu/drm/i915/display/intel_dpll_mgr.c` call the first three and
  add no bracket of their own.
- Expect the caller to bracket: `intel_cx0_read()`, `intel_cx0_write()`,
  `intel_cx0_rmw()`, `intel_c20_sram_read()`, `intel_c20_sram_write()`,
  `intel_readout_lane_count()`, `intel_c10_pll_program()`,
  `intel_c20_pll_program()`, `intel_cx0_program_phy_lane()`,
  `intel_c20_readout_vdr_params()`, `intel_c20_program_vdr_params()`.
- **Unsafe usage**: a message bus access without `POWER_DOMAIN_DC_OFF` held.
  - Safe: between begin and end, as `intel_c20pll_readout_hw_state()` does;
    `__intel_cx0_read()` and `__intel_cx0_write()` check it with
    `assert_dc_off()`, a `drm_WARN_ON()`. PSR pause is not asserted.
- C10 step: `intel_c10_msgbus_access_begin()` before touching C10 registers;
  the programming paths, for example `intel_c10_pll_program()` and
  `intel_cx0_program_phy_lane()`, call `intel_c10_msgbus_access_commit()`
  after their writes. There is no intel_c10_msgbus_access_end().
- The transaction helpers do not call the C10 helpers;
  `intel_c10_msgbus_access_begin()` is a separate call inside the
  transaction, as in `intel_c10pll_readout_hw_state()`.
- Both C10 helpers return at once when `intel_encoder_is_c10phy()` is false,
  so shared C10/C20 paths call them unconditionally.
- `intel_c10_msgbus_access_commit()` with `master_lane` true: also sets
  `C10_VDR_CTRL_MASTER_LANE`; only `intel_c10_pll_program()` passes true.
- Read-only C10 access: `intel_c10pll_readout_hw_state()` calls begin and no
  commit.
