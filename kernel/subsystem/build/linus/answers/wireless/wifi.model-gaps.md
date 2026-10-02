- Models take `config`, `set_rts_threshold`, `set_frag_threshold`,
  `set_coverage_class`, `set_antenna` and `get_antenna` of
  `struct ieee80211_ops` to have their old arguments. Each takes an
  `int radio_idx`; so do `set_wiphy_params`, `set_tx_power` and `get_tx_power`
  of `struct cfg80211_ops`, and `ieee80211_hw_config()`. mac80211 passes -1
  when the call is not for one radio.
- Models take the station and key ops of `struct cfg80211_ops` to receive a
  `struct net_device *`. `add_station`, `del_station`, `change_station`,
  `get_station`, `dump_station`, `add_key` and `get_key` take a
  `struct wireless_dev *`; `set_default_key` still takes the netdev.
- Models do not know `stop` in `struct ieee80211_ops` takes `bool suspend`, or
  that the rate-control update op is `link_sta_rc_update` with a
  `struct ieee80211_link_sta *`. `struct ieee80211_ops` has no
  `sta_rc_update` member.
- Models take `ieee80211_reconfig_stations()` to restore every station.
  `ieee80211_reconfig()` does not call it for `NL80211_IFTYPE_NAN` or
  `NL80211_IFTYPE_NAN_DATA`; their stations are added back only inside
  `ieee80211_reconfig_nan()`.
- Models name SDATA_STATE_IN_DRIVER as the flag the `drv_` wrappers test. No
  such name is defined here; the flag is `IEEE80211_SDATA_IN_DRIVER`.
- Models take `cfg80211_get_bss()` to return any matching entry. It passes
  `NL80211_BSS_USE_FOR_NORMAL` to `__cfg80211_get_bss()`, which skips entries
  whose `use_for` lacks it and expired entries that are not held.
- Models list HT, VHT, HE, EHT and S1G as the headers split from
  `include/linux/ieee80211.h`. It also includes
  `include/linux/ieee80211-mesh.h`, `include/linux/ieee80211-p2p.h` and
  `include/linux/ieee80211-nan.h`.
- Models do not know UHR. `ieee80211_register_hw()` rejects UHR without EHT.
  `net/mac80211/uhr.c` holds only `ieee80211_uhr_cap_ie_to_sta_uhr_cap()`;
  the rest of the UHR handling is in other mac80211 files, for example
  `net/mac80211/mlme.c`.
- Models take `drv_set_key()` to reach the driver whenever `set_key` is set.
  It returns `-EOPNOTSUPP` without calling the driver when `fips_enabled`; see
  `net/mac80211/driver-ops.c`.
