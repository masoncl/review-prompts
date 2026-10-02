- Per-link pairs are joined by pointer, not embedding: `struct ieee80211_link_data`
  reaches `struct ieee80211_bss_conf` through its `conf` member, and
  `struct link_sta_info` reaches `struct ieee80211_link_sta` through `pub`.
- No `container_of()` leads from `struct ieee80211_bss_conf` or
  `struct ieee80211_link_sta` back to the private struct; go through the
  `link_id` and the `link[]` array of the sdata or `struct sta_info`.
- Extra links are allocated as a pair: `struct link_container` in
  `net/mac80211/link.c`, `struct sta_link_alloc` in `net/mac80211/sta_info.c`.
- Driver private areas in mac80211: `priv` on `struct ieee80211_hw`, and
  `drv_priv` on `struct ieee80211_vif`, `struct ieee80211_sta`,
  `struct ieee80211_txq` and `struct ieee80211_chanctx_conf`;
  `struct ieee80211_bss_conf` and `struct ieee80211_link_sta` have none.
- `valid_links` in `struct ieee80211_sta`: 0 for a non-MLO station;
  `__sta_info_alloc()` sets it, to `BIT(link_id)`, only when it is given a
  link id of 0 or more.
- Link set is recorded in both layers: `valid_links` and `links[]` in
  `struct wireless_dev`, and `vif.valid_links` and `link[]` in the sdata.
- Stations: `struct ieee80211_sub_if_data` has no list of its stations; all are
  on the device-wide `sta_list` of `struct ieee80211_local` and are filtered by
  `sta->sdata`.
- Station lookup uses two tables in `struct ieee80211_local`: `sta_hash` keyed
  by `sta->addr` (the MLD address) and `link_sta_hash` keyed by the link
  address.
- Both station tables are `struct rhltable`, so one address can match several
  entries on different interfaces; see `sta_info_get()` in
  `net/mac80211/sta_info.c`.
- `emulate_chanctx` in `struct ieee80211_local`: records whether the driver
  supplied the emulation helpers or its own chanctx ops;
  `ieee80211_alloc_hw_nm()` sets it.
- `struct ieee80211_chanctx` keeps no list or count of users;
  `ieee80211_chanctx_refcount()` in `net/mac80211/chan.c` recomputes it by
  walking the running interfaces on `local->interfaces`.
- Chanctx users are of three kinds: a link assigned to it
  (`bss_conf->chanctx_conf`), a link that reserved it (`reserved_chanctx`),
  and a `struct ieee80211_nan_channel` of the NAN interface.
- `struct ieee80211_chan_req`: what a user asks of a chanctx, the operating
  chandef plus the AP's; a link's own channel is `bss_conf->chanreq.oper`, and
  `struct ieee80211_bss_conf` has no chandef member.
- `struct wiphy_radio`: one radio of a multi-radio wiphy (`radio`,
  `n_radio` in `struct wiphy`); a chanctx belongs to at most one radio
  (`conf.radio_idx`, -1 for none) and `radio_mask` in `struct wireless_dev`
  limits which radios an interface may use.
- AP_VLAN sdata: never passed to `drv_add_interface()`, yet it has its own
  links, taken from the parent AP's `vif.valid_links`
  (`ieee80211_apvlan_link_setup()`).
- AP_VLAN links of an MLD AP: each `struct ieee80211_bss_conf` starts as a
  copy of the AP's link conf; see `ieee80211_link_init()` in
  `net/mac80211/link.c`.
- AP_VLAN chanctx pointer: copied from the AP's link by
  `ieee80211_link_vlan_copy_chanctx()`; the chanctx user walk skips AP_VLAN.
- Monitor interfaces and the driver:

  | Case | What the driver sees |
  |---|---|
  | `MONITOR_FLAG_ACTIVE` set, or `IEEE80211_HW_NO_VIRTUAL_MONITOR` | the monitor sdata itself |
  | neither, `IEEE80211_HW_WANT_MONITOR_VIF` set | only the virtual monitor, `local->monitor_sdata`, which exists only while no non-monitor interface is running |
  | none of the three | no monitor vif |

- `local->monitor_sdata`: an sdata with no netdev that is never put on
  `local->interfaces`; see `ieee80211_add_virtual_monitor()` in
  `net/mac80211/iface.c`.
- Netdev-less interface types in cfg80211 are `NL80211_IFTYPE_P2P_DEVICE`,
  `NL80211_IFTYPE_NAN` and `NL80211_IFTYPE_PD`; mac80211 implements no
  `start_pd` op, and `ieee80211_if_add()` builds a netdev-less sdata only for
  the first two.
- NAN uses two interface types: `NL80211_IFTYPE_NAN` is the netdev-less
  management interface, `NL80211_IFTYPE_NAN_DATA` is a netdev whose
  `u.nan_data.nmi` points at the management sdata.
- NAN local schedule: `struct ieee80211_nan_sched_cfg` in `vif.cfg.nan_sched`
  of the management interface, holding up to `IEEE80211_NAN_MAX_CHANNELS`
  `struct ieee80211_nan_channel`.
- NAN stations come in two kinds: one on the management interface that owns
  the peer schedule (`nan_sched` in `struct ieee80211_sta`, a
  `struct ieee80211_nan_peer_sched`), and ones on data interfaces whose `nmi`
  member points at it.
- Removing a station on the NAN management interface also destroys every
  data-interface station whose `nmi` points at it; see `__sta_info_destroy_part1()`
  in `net/mac80211/sta_info.c`.
- Keys: every `struct ieee80211_key` of an interface is on `sdata->key_list`;
  `ieee80211_key_replace()` in `net/mac80211/key.c` also puts it in one slot:

  | Key | Slot |
  |---|---|
  | pairwise, with a station | `ptk[]` in `struct sta_info` |
  | group, with a station | `gtk[]` in `struct link_sta_info` |
  | WEP or pairwise, no station | `keys[]` in `struct ieee80211_sub_if_data` |
  | group, no station | `gtk[]` in `struct ieee80211_link_data` |

- `struct ieee80211_txq` per station: `IEEE80211_NUM_TIDS + 1` entries; the
  last is for management frames and exists only if the driver sets
  `IEEE80211_HW_STA_MMPDU_TXQ` (station interfaces) or
  `IEEE80211_HW_BUFF_MMPDU_TXQ` (others).
- `struct ieee80211_txq` per vif: `txq` for multicast data and `txq_mgmt`,
  which only a NAN interface gets; an interface created as AP_VLAN, P2P
  device or non-active monitor gets no vif TXQ, and a later type change adds
  none (`ieee80211_if_add()`).
- A reference on a BSS entry also counts on its `hidden_beacon_bss` and
  `transmitted_bss`; see `bss_ref_get()` in `net/wireless/scan.c`.
