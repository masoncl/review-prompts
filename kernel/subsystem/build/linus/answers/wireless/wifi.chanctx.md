- Declaration: the driver itself puts the three emulation helpers into its
  `struct ieee80211_ops`; mac80211 never installs them, and unset callbacks
  fail allocation (see Callback set validation).
- `switch_vif_chanctx`: not part of what makes a driver emulating. Left NULL,
  `ieee80211_link_reserve_chanctx()` in `net/mac80211/chan.c` returns
  `-EOPNOTSUPP` for a link that already has a context.
- `IEEE80211_HW_CHANCTX_STA_CSA`: set by `ieee80211_alloc_hw_nm()` for every
  emulating driver, whether or not `switch_vif_chanctx` is set.
- `hw->conf.chandef` on an emulating driver: the channel to tune to, not
  always the operating channel. `ieee80211_calc_hw_conf_chan()` in
  `net/mac80211/main.c` picks, in this order, `local->scan_chandef`,
  `local->tmp_channel`, the context's `def`, `local->dflt_chandef`.
- `IEEE80211_CONF_OFFCHANNEL` in `hw->conf.flags`: set whenever the chosen
  channel is not identical to the context's `def`, or there is no context.
- Emulation helpers: reach `config()` only when `local->open_count` is nonzero
  and `ieee80211_calc_hw_conf_chan()` reports a change; see
  `_ieee80211_hw_conf_chan()`.
- Software remain-on-channel: selected by `remain_on_channel` being unset, not
  by emulation; an emulating driver that sets `remain_on_channel` gets
  `drv_remain_on_channel()`, and a driver-managed one that leaves it unset
  gets `-EOPNOTSUPP` from `ieee80211_start_roc_work()`. See
  `net/mac80211/offchannel.c`.
- `hw->conf.chandef` on a driver-managed device: never written by mac80211.
  Its two writers, `ieee80211_calc_hw_conf_chan()` and
  `ieee80211_register_hw()`, are gated on `local->emulate_chanctx`.
