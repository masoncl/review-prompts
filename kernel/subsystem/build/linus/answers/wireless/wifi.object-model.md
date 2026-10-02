| Link slot | Non-MLD | MLD |
|---|---|---|
| Interface: `sdata->link[]`, `vif->link_conf[]` | slot 0 points at `sdata->deflink` and `vif->bss_conf`, with `vif->valid_links` 0 | every valid link, link 0 included, is a separately allocated `struct link_container` (`net/mac80211/link.c`); no slot points at `sdata->deflink` or `vif->bss_conf` |
| Station: `link[]` in `struct sta_info` and in `struct ieee80211_sta` | slot 0 points at `deflink` | the first link is `deflink`, installed at the slot of the link id given to `__sta_info_alloc()`; later links are `struct sta_link_alloc` from `ieee80211_sta_allocate_link()` |

- cfg80211 side of an interface link: an unnamed struct, element of
  `wdev->links[]` in `struct wireless_dev`; it holds the link address, AP or
  client state and CAC state, and neither embeds nor points at a
  `struct ieee80211_bss_conf`.
- `struct ieee80211_bss_conf` to `struct ieee80211_link_data`: no
  `container_of()`; `link->conf` is a pointer. Go `bss_conf->vif`,
  `vif_to_sdata()`, then `sdata->link[bss_conf->link_id]`.
- `wdev_to_ieee80211_vif()`: returns NULL unless the interface is running and
  has `IEEE80211_SDATA_IN_DRIVER` set; see `net/mac80211/util.c`.
- `IEEE80211_DEV_TO_SUB_IF()`: is `netdev_priv()`, so it needs a netdev.
  `NL80211_IFTYPE_P2P_DEVICE` and `NL80211_IFTYPE_NAN` interfaces have
  `sdata->dev` NULL; reach those with `IEEE80211_WDEV_TO_SUB_IF()`.
