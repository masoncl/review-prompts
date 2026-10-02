- `bss_info_changed`: exists in `struct ieee80211_ops`;
  `ieee80211_bss_info_change_notify()` exists in `net/mac80211/main.c`.
- mac80211 calls `bss_info_changed` from three places:
  - `ieee80211_bss_info_change_notify()`: once, with the unsplit `changed`;
  - `drv_vif_cfg_changed()`: when `vif_cfg_changed` is NULL, with
    `&sdata->vif.bss_conf`;
  - `drv_link_info_changed()`: when `link_info_changed` is NULL, with the
    link's conf.
- `ieee80211_alloc_hw_nm()` in `net/mac80211/main.c`: `WARN_ON` and returns
  NULL when exactly one of `vif_cfg_changed` and `link_info_changed` is set, or
  when `link_info_changed` and `bss_info_changed` are both set.
- Driver with none of the three ops: accepted by `ieee80211_alloc_hw_nm()`;
  it gets no change notification.
