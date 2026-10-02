- Every check below is `WARN_ON()` followed by `return -EINVAL`, in
  `ieee80211_register_hw()` in `net/mac80211/main.c`.
- Checked, complete list:

| Item | Must be |
|---|---|
| `local->emulate_chanctx` | false |
| `link_info_changed` op | set |
| `IEEE80211_HW_HAS_RATE_CONTROL` | set |
| `IEEE80211_HW_AMPDU_AGGREGATION` | set |
| `IEEE80211_HW_MFP_CAPABLE` | set |
| `IEEE80211_HW_AP_LINK_PS` | set |
| `IEEE80211_HW_HOST_BROADCAST_PS_BUFFERING` | clear |
| `IEEE80211_HW_NEED_DTIM_BEFORE_ASSOC` | clear |
| `IEEE80211_HW_TIMING_BEACON_ONLY` | clear |
| `IEEE80211_HW_SUPPORTS_DYNAMIC_PS` | set, only if `IEEE80211_HW_SUPPORTS_PS` is set |
| `IEEE80211_HW_PS_NULLFUNC_STACK` | clear, only if `IEEE80211_HW_SUPPORTS_PS` is set |
| `IEEE80211_HT_CAP_DELAY_BA` in `ht_cap.cap` of any band with `ht_supported` | clear |
| `vendor_elems.len` of any band's iftype data | 0 |

- The last two rows are tested later, inside the per-band loop, not in the
  `WIPHY_FLAG_SUPPORTS_MLO` block.
- Not tested: `IEEE80211_HW_CONNECTION_MONITOR`,
  `IEEE80211_HW_AMPDU_KEYBORDER_SUPPORT`,
  `IEEE80211_HW_SINGLE_SCAN_ON_ALL_BANDS`, `change_vif_links`,
  `change_sta_links`, and `interface_modes`.
- IEEE80211_HW_DEAUTH_NEED_MGD_TX_PREP: no such flag in this tree.
