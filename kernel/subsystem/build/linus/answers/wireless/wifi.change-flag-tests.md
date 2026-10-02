- Flag tested in `vif_cfg_changed`: delivered if it is in
  `BSS_CHANGED_VIF_CFG_FLAGS`, or if mac80211 passes it to
  `drv_vif_cfg_changed()` directly, as it does for
  `BSS_CHANGED_NAN_LOCAL_SCHED` (see "Split macro and dropped flags").
- `drv_vif_cfg_changed()` and `drv_link_info_changed()`: do not mask `changed`;
  the only masking with `BSS_CHANGED_VIF_CFG_FLAGS` is in
  `ieee80211_bss_info_change_notify()`.
- Missing split op: the wrapper does not warn; the fallback to
  `bss_info_changed` is under "Single change callback".
- `check_sdata_in_driver()`: tests `IEEE80211_SDATA_IN_DRIVER` in
  `sdata->flags`, not `SDATA_STATE_RUNNING`; its `WARN_ONCE` is suppressed when
  `local->reconfig_failure` is set, the call is dropped either way.
- `ieee80211_bss_info_change_notify()`: calls `vif_cfg_changed` and
  `link_info_changed` directly, not through the wrappers, so the
  `lockdep_assert_wiphy()`, `BSS_CHANGED_MU_GROUPS` and
  `ieee80211_vif_link_active()` checks of `drv_link_info_changed()` do not
  apply on that path.
- Flag tested in `link_info_changed`: when delivered through
  `drv_link_info_changed()` it must also pass the type and link checks listed
  under "Split macro and dropped flags".
