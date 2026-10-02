- Driver without `sta_state`: `drv_sta_state()` calls `sta_add` on
  `IEEE80211_STA_AUTH` to `IEEE80211_STA_ASSOC`, and `sta_remove` on
  `IEEE80211_STA_ASSOC` to `IEEE80211_STA_AUTH`; nothing on any other step,
  including both steps that involve `IEEE80211_STA_NOTEXIST`.
- `ieee80211_alloc_hw_nm()`: rejects only `sta_state` set together with
  `sta_add` or `sta_remove`; none of the three is required.
- Missing `sta_add`: `drv_sta_add()` returns 0, so the step succeeds.
- `_sta_info_move_state()`: reports a transition to the driver only while
  `WLAN_STA_INSERTED` is set.
- Before insertion state changes are silent; `sta_info_insert_drv_state()`
  then replays every step from `IEEE80211_STA_NOTEXIST` up to the current
  state.
- Steps to and from `IEEE80211_STA_NOTEXIST`: never made by
  `sta_info_move_state()`; up comes from `sta_info_insert_drv_state()` and
  the restart replay, down from `__sta_info_destroy_part2()`, only if
  `sta->uploaded`, and from the unwind of a failed insertion.
- Failed step during insertion: `sta_info_insert_drv_state()` unwinds the
  steps already made, with `WARN_ON()` on each.
- `NL80211_IFTYPE_ADHOC`: a failed insertion step is still unwound in the
  driver, but `sta_info_insert_drv_state()` returns 0; the station stays in
  mac80211 with `sta->uploaded` false.
- `ieee80211_reconfig_stations()`: replays the upward steps from
  `IEEE80211_STA_NOTEXIST` for each uploaded station, with no downward steps
  first; a failure only hits `WARN_ON()`.
