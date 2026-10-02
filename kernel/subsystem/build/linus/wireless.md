# Wireless Subsystem Details

## Main structures

### Objects and how they relate

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

## Where to look

**Core files**

| Job | File in this tree |
|---|---|
| Simulated radio driver | `drivers/net/wireless/virtual/mac80211_hwsim_main.c`; there is no mac80211_hwsim.c. The module is still `mac80211_hwsim.o`, linked from that file and `drivers/net/wireless/virtual/mac80211_hwsim_nan.c` |
| Simulated radio driver, private state | `drivers/net/wireless/virtual/mac80211_hwsim_i.h` (`struct mac80211_hwsim_data`); `drivers/net/wireless/virtual/mac80211_hwsim.h` holds only the netlink and virtio enums, structs and macros |
| Element parser | `net/mac80211/parse.c`; the entry point is spelled `ieee802_11_parse_elems_full()` |
| Macro that splits change flags | `BSS_CHANGED_VIF_CFG_FLAGS`, defined in `net/mac80211/main.c`, not in a header; nothing outside `net/mac80211/main.c` uses it |
| Capability element layouts | one header per generation: `include/linux/ieee80211-ht.h`, `include/linux/ieee80211-vht.h`, `include/linux/ieee80211-he.h`, `include/linux/ieee80211-eht.h`, `include/linux/ieee80211-uhr.h`, `include/linux/ieee80211-s1g.h`. `include/linux/ieee80211.h` defines none of these capability structs itself; it includes the headers |

**cfg80211 and mac80211 structures**

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

## BSS change callbacks and flags

**Interface and link change callbacks**

- Wrong-kind flag in `ieee80211_vif_cfg_change_notify()` or
  `ieee80211_link_info_change_notify()`: `WARN_ON_ONCE()` only; the function
  neither masks nor returns on it, and passes the full `changed` on to the
  `drv_` wrapper.
- `drv_vif_cfg_changed()`: static inline in `net/mac80211/driver-ops.h`;
  `drv_link_info_changed()` is in `net/mac80211/driver-ops.c`.

**Flag tests in driver callbacks**

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

**Single change callback**

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

**Single notify function interface**

- `ieee80211_bss_info_change_notify()`: has `might_sleep()` only; it does not
  call `lockdep_assert_wiphy()`, and it bypasses the `drv_` wrappers that do.
- MLD interface: `WARN_ON_ONCE(ieee80211_vif_is_mld(&sdata->vif))` does not
  return; the call goes on, and the only link conf it passes is
  `&sdata->vif.bss_conf`.
- `NL80211_IFTYPE_P2P_DEVICE` or `NL80211_IFTYPE_NAN`: `WARN_ON_ONCE`, whole
  call dropped.
- `NL80211_IFTYPE_MONITOR`: `WARN_ON_ONCE` and drop when `changed` has any flag
  other than `BSS_CHANGED_TXPOWER`; the function has no `mu_mimo_owner` test.
- `BSS_CHANGED_BEACON` or `BSS_CHANGED_BEACON_ENABLED`: `WARN_ON_ONCE` and drop
  unless the type is `NL80211_IFTYPE_AP`, `NL80211_IFTYPE_ADHOC`,
  `NL80211_IFTYPE_MESH_POINT` or `NL80211_IFTYPE_OCB`.
- Interface not in the driver: the flag tested is `IEEE80211_SDATA_IN_DRIVER`,
  by `check_sdata_in_driver()`.
- **Potentially unsafe usage**: calling `ieee80211_bss_info_change_notify()` on
  an interface that can be an MLD.
  - Unsafe: when nothing before the call rules out `ieee80211_vif_is_mld()`;
    the `WARN_ON_ONCE` in the function fires and the only link conf the driver
    is handed is `&sdata->vif.bss_conf`.
  - Safe: in the non-MLD branch of an `ieee80211_vif_is_mld()` test, with
    `ieee80211_link_info_change_notify()` per link plus
    `ieee80211_vif_cfg_change_notify()` on the MLD branch, as
    `ieee80211_set_associated()` in `net/mac80211/mlme.c` does; the
    `WARN_ON_ONCE` in the function defines the requirement.

**Split macro and dropped flags**

- `BSS_CHANGED_NAN_LOCAL_SCHED`: not in `BSS_CHANGED_VIF_CFG_FLAGS`, yet
  delivered to `vif_cfg_changed`.
- Delivery of `BSS_CHANGED_NAN_LOCAL_SCHED`: by direct `drv_vif_cfg_changed()`
  calls in `net/mac80211/nan.c` and in `ieee80211_reconfig_nan()` in
  `net/mac80211/util.c`, which skip `ieee80211_vif_cfg_change_notify()` and its
  `WARN_ON_ONCE`.
- `BSS_CHANGED_NAN_LOCAL_SCHED` passed to `ieee80211_vif_cfg_change_notify()`:
  would warn; passed to `ieee80211_bss_info_change_notify()` on an
  `NL80211_IFTYPE_NAN` interface: warns and is dropped.
- `drv_link_info_changed()`: every check returns, so the whole call is dropped,
  not single flags.

| Condition in `drv_link_info_changed()` | Warns |
|---|---|
| `BSS_CHANGED_BEACON` or `BSS_CHANGED_BEACON_ENABLED` on a type other than `NL80211_IFTYPE_AP`, `NL80211_IFTYPE_ADHOC`, `NL80211_IFTYPE_MESH_POINT`, `NL80211_IFTYPE_OCB` | `WARN_ON_ONCE` |
| `NL80211_IFTYPE_P2P_DEVICE` or `NL80211_IFTYPE_NAN`, any flag | `WARN_ON_ONCE` |
| `NL80211_IFTYPE_MONITOR` with any flag other than `BSS_CHANGED_TXPOWER` and `BSS_CHANGED_MU_GROUPS` | `WARN_ON_ONCE` |
| `BSS_CHANGED_MU_GROUPS` while `sdata->vif.bss_conf.mu_mimo_owner` is false, any type | `WARN_ON_ONCE` |
| interface without `IEEE80211_SDATA_IN_DRIVER` (`check_sdata_in_driver()`) | `WARN_ONCE`, unless `local->reconfig_failure` is set |
| link for which `ieee80211_vif_link_active()` is false | silent |

- `BSS_CHANGED_MU_GROUPS` check: reads `sdata->vif.bss_conf`, not the `info`
  argument.
- `ieee80211_vif_link_active()`: on a non-MLD interface true only for link 0;
  on an MLD it tests `vif->active_links`.
- `drv_link_info_changed()`: has no test that names `NL80211_IFTYPE_AP_VLAN`,
  `NL80211_IFTYPE_NAN_DATA` or `NL80211_IFTYPE_PD`; of its checks only the
  beacon-flag one drops a call for these types.
- `ieee80211_link_info_change_notify()`: returns silently, before the wrapper,
  for `NL80211_IFTYPE_AP_VLAN`, and for `NL80211_IFTYPE_MONITOR` unless the
  hardware has `IEEE80211_HW_WANT_MONITOR_VIF`.
- Direct `drv_link_info_changed()` callers skip that pre-filter; for example
  `ieee80211_chanctx_update_npca_links()` in `net/mac80211/chan.c` sends
  `BSS_CHANGED_NPCA` this way.

**Location of changed values**

- Rows below are the ones that differ from the usual `vif->cfg` mapping; the
  other flags of `BSS_CHANGED_VIF_CFG_FLAGS` map to the like-named fields of
  `vif->cfg`.

| Flag | Field |
|---|---|
| `BSS_CHANGED_ASSOC` | `vif->cfg.assoc`, `vif->cfg.aid` |
| `BSS_CHANGED_IBSS` | `vif->cfg.ibss_joined`, `vif->cfg.ibss_creator` |
| `BSS_CHANGED_ARP_FILTER` | `vif->cfg.arp_addr_list`, `vif->cfg.arp_addr_cnt` |
| `BSS_CHANGED_MLD_VALID_LINKS` | `vif->valid_links`, `vif->dormant_links`; not in `vif->cfg` |
| `BSS_CHANGED_MLD_TTLM` | `vif->suspended_links`; `vif->neg_ttlm` when cleared |
| `BSS_CHANGED_NAN_LOCAL_SCHED` | `vif->cfg.nan_sched` |

- BSS_CHANGED_IP and BSS_CHANGED_AID: not defined in this tree.
- `BSS_CHANGED_MLD_VALID_LINKS` and `BSS_CHANGED_MLD_TTLM`: both are in
  `BSS_CHANGED_VIF_CFG_FLAGS`.
- `BSS_CHANGED_MLD_TTLM`: `ieee80211_ttlm_set_links()` in
  `net/mac80211/mlme.c` sets it when it clears a valid `vif->neg_ttlm` or when
  the new `vif->suspended_links` is non-zero;
  `ieee80211_process_ttlm_teardown()` also sends it, after clearing both
  fields.
- New negotiated mapping: `ieee80211_apply_neg_ttlm()` writes `vif->neg_ttlm`
  after `ieee80211_ttlm_set_links()` has already notified the driver.
- `BSS_CHANGED_NAN_LOCAL_SCHED`: `struct ieee80211_nan_sched_cfg` is defined in
  `include/net/mac80211.h`.

**Adding a change flag**

- Per-link flag on `NL80211_IFTYPE_NAN` or `NL80211_IFTYPE_P2P_DEVICE`:
  `drv_link_info_changed()` and `ieee80211_bss_info_change_notify()` warn and
  drop it; only `drv_vif_cfg_changed()`, called directly or through
  `ieee80211_vif_cfg_change_notify()`, reaches such an interface.
- `ieee80211_reconfig()` in `net/mac80211/util.c`: builds the set of flags
  replayed after a restart by hand, partly in its helpers
  `ieee80211_reconfig_ap_links()` and `ieee80211_reconfig_nan()`; it does not
  replay a flag that is not added there.

## Links and stations

**Per-link interface state**

- `for_each_vif_active_link()`: needs `rcu_read_lock()` or the wiphy mutex,
  either one; it reads slots with `link_conf_dereference_check()`.
  `iwl_mvm_update_smps_on_active_links()` takes `rcu_read_lock()` around it,
  `ieee80211_stop_mbssid()` runs it under the mutex.
- `for_each_valid_link()` in `include/net/cfg80211.h`: walks link IDs of a
  `valid_links` bitmap only; dereferences no RCU pointer and checks no lock.
- `link_conf[id]`: non-NULL for every valid link, inactive and dormant ones
  too; the filter on `active_links` is in the iterator, not in the array.
- `dormant_links`: valid links that cannot be activated;
  `_ieee80211_set_active_links()` returns `-EINVAL` on a running interface
  for a link outside `ieee80211_vif_usable_links()`.
- `suspended_links`: the part of `dormant_links` caused by negotiated TTLM;
  written in `ieee80211_ttlm_set_links()` and cleared in
  `ieee80211_process_ttlm_teardown()`.
- AP and AP_VLAN: `ieee80211_set_vif_links_bitmaps()` sets `active_links` to
  `valid_links` and warns on any dormant link;
  `_ieee80211_set_active_links()` returns `-EINVAL` on a running interface
  unless the type is `NL80211_IFTYPE_STATION`.
- **Potentially unsafe usage**: a driver publishing
  `struct ieee80211_bss_conf` pointers to its own RCU readers.
  - Unsafe: when a link is removed and `change_vif_links` returns with
    readers still running; `ieee80211_free_links()` calls `kfree()` on the
    link after `drv_change_vif_links()` with no grace period guaranteed in
    between, and the `synchronize_rcu()` in `ieee80211_tear_down_links()` ran
    before the callback.
  - Safe: unpublish and call `synchronize_rcu()` before returning, as
    `rtw89_ops_change_vif_links()` does.

**Station state transitions**

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

**Station teardown**

- `__sta_info_destroy()` and `__sta_info_flush()`: every downward transition
  they make runs after the grace period, in `__sta_info_destroy_part2()`;
  none runs before `synchronize_net()`.
- `drv_sta_pre_rcu_remove()`: called in `__sta_info_destroy_part1()` after
  the station has left both hashes and `local->sta_list`, so a lookup from
  inside the callback does not find it.
- `sta->uploaded` false in `__sta_info_destroy()` and `__sta_info_flush()`:
  neither `sta_pre_rcu_remove` nor the step to `IEEE80211_STA_NOTEXIST` is
  called.
- Driver with `sta_remove`: its last state callback is on
  `IEEE80211_STA_ASSOC` to `IEEE80211_STA_AUTH`, also after the grace period;
  nothing is called on the step to `IEEE80211_STA_NOTEXIST`.
- Free: `cleanup_single_sta()` calls `sta_info_free()`, which calls `kfree()`
  directly; no RCU delay follows the last transition.
- Failed insertion in `sta_info_insert_finish()`: the driver sees the unwind
  down to `IEEE80211_STA_NOTEXIST` while the station is still hashed;
  `sta_pre_rcu_remove` is not called; `synchronize_net()` runs after the
  unwind and before the free.
- **Potentially unsafe usage**: clearing a driver's RCU-published station
  pointer in the last `sta_state` or `sta_remove` call.
  - Unsafe: on the path through `__sta_info_destroy_part2()` when the pointer
    was still published until that call and the driver returns without its
    own grace period; `sta_info_free()` frees the station while driver
    readers may still dereference it.
  - Safe: clear it in `sta_pre_rcu_remove`, as `mt76_sta_pre_rcu_remove()`
    does; the `synchronize_net()` in `__sta_info_destroy()` or
    `__sta_info_flush()` follows. This covers only the removal of a station
    with `sta->uploaded` set.

**Station lookup and lifetime**

- `sta_info_get()`, `sta_info_get_bss()` and `ieee80211_find_sta()`: take and
  drop `rcu_read_lock()` internally and check nothing about the caller, so
  lockdep stays silent for a caller that holds neither RCU nor the wiphy
  mutex.
- Among the station lookups, lockdep accepts the wiphy mutex only in list
  walks, for example `sta_info_get_by_idx()` and `__iterate_stations()` in
  `net/mac80211/util.c`.
- `ieee80211_find_sta_by_ifaddr()` and `ieee80211_find_sta_by_link_addrs()`:
  take no `rcu_read_lock()` themselves and walk the rhashtable, so the caller
  needs `rcu_read_lock()` even under the wiphy mutex, as
  `sta_info_insert_check()` does.
- `ieee80211_find_sta()` and `ieee80211_find_sta_by_ifaddr()`: return NULL
  for a station whose `sta->uploaded` is false, although mac80211 has it.
- ath9k TX completion: the `ieee80211_find_sta_by_ifaddr()` call is in
  `ath_tx_process_buffer()`, which passes the result to
  `ath_tx_complete_aggr()`.

## Driver registration and restart

**Callback set validation**

- `config`: required, in the same `WARN_ON()` as the other seven callbacks.
- Channel context callbacks all NULL: rejected. Only two shapes pass:

| Shape | `add_chanctx`, `remove_chanctx`, `change_chanctx` | `assign_vif_chanctx`, `unassign_vif_chanctx` |
|---|---|---|
| emulation | exactly the three `ieee80211_emulate_add_chanctx()`, `ieee80211_emulate_remove_chanctx()`, `ieee80211_emulate_change_chanctx()` | both NULL |
| driver-managed | all non-NULL, none of them an emulation helper | both non-NULL |

- `switch_vif_chanctx`: not looked at by `ieee80211_alloc_hw_nm()` in either
  shape.
- `ampdu_action`: tested by neither `ieee80211_alloc_hw_nm()` nor
  `ieee80211_register_hw()`; `net/mac80211/agg-tx.c` tests it at run time.

**Channel contexts**

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

**Radio of a channel context**

- `ieee80211_find_available_radio()` in `net/mac80211/chan.c` picks the radio;
  it returns the first index, in ascending order, that passes all its tests.
- `radio_mask`: the easy part to miss. A radio is skipped unless its bit is
  set in the `sdata->wdev.radio_mask` of the interface that asks for the
  context.
- `radio_idx` of -1: not proof of a wiphy without radios.
  `ieee80211_alloc_chanctx()` is the only writer, and
  `ieee80211_replace_chanctx()` calls it with a literal -1.
- Readers of `radio_idx` in mac80211 test it for `>= 0` before using it as an
  index or bit number, for example `ieee80211_replace_chanctx()` and
  `__ieee80211_get_radio_mask()` in `net/mac80211/util.c`.

**Multi-link driver requirements**

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

**Hardware restart**

- `ieee80211_restart_hw()`: flushes nothing and cancels nothing. Flushing
  `local->workqueue` and `ieee80211_scan_cancel()` happen in
  `ieee80211_restart_work()` in `net/mac80211/main.c`.
- `ieee80211_restart_work()` before `ieee80211_reconfig()`: also flushes all
  wiphy work, cancels `csa_connection_drop_work` and drops the connection of a
  station with `csa_active`, flushes `dec_tailroom_needed_wk` and the ROC
  work, and calls `synchronize_net()`.
- `ieee80211_reconfig()` order, for a restart:
  1. `drv_start()`.
  2. `drv_set_frag_threshold()`, `drv_set_rts_threshold()` (once per radio
     when `n_radio` is nonzero), `drv_set_coverage_class()`.
  3. `drv_add_interface()`: the virtual monitor vif (only with
     `IEEE80211_HW_WANT_MONITOR_VIF`), then each running interface.
  4. `drv_add_chanctx()` for each context not in state
     `IEEE80211_CHANCTX_REPLACES_OTHER`.
  5. `ieee80211_hw_config()`, then `ieee80211_configure_filter()`.
  6. Per running interface: `drv_change_vif_links()` (MLD only), chanctx
     assignment per active link, `drv_join_ibss()`, stations (not for
     `NL80211_IFTYPE_AP`, `NL80211_IFTYPE_AP_VLAN`,
     `NL80211_IFTYPE_MONITOR`, `NL80211_IFTYPE_NAN` and
     `NL80211_IFTYPE_NAN_DATA` interfaces), `drv_conf_tx()` (not for
     `NL80211_IFTYPE_AP_VLAN`, `NL80211_IFTYPE_MONITOR`,
     `NL80211_IFTYPE_NAN` and `NL80211_IFTYPE_NAN_DATA` interfaces), then by
     type: the vif and link change notifications; for `NL80211_IFTYPE_AP`
     `drv_start_ap()` before the notification that carries the beacon flags;
     for `NL80211_IFTYPE_NAN` `ieee80211_reconfig_nan()`.
  7. `ieee80211_recalc_ps()`.
  8. Stations of `NL80211_IFTYPE_AP` and `NL80211_IFTYPE_AP_VLAN`
     interfaces.
  9. Keys, with `ieee80211_reenable_keys()`.
  10. Remaining MLD links, with `ieee80211_set_active_links()`.
  11. Scheduled scan restart.
  12. BA sessions torn down with `ieee80211_sta_tear_down_BA_sessions()`;
      they are not restored.
  13. `drv_reconfig_complete()`.
  14. `local->in_reconfig` cleared, `ieee80211_reconfig_roc()` called,
      interface work requeued.
  15. Queues woken.
  16. `ieee80211_sta_restart()` for station interfaces.
- Step 3 skips: `NL80211_IFTYPE_AP_VLAN`, `NL80211_IFTYPE_NAN_DATA` (added
  later by `ieee80211_reconfig_nan()`), and monitor interfaces unless
  `IEEE80211_HW_NO_VIRTUAL_MONITOR` is set.
- Channel of an emulating driver: restored in step 4, not step 5.
  `ieee80211_hw_config()` warns on `IEEE80211_CONF_CHANGE_CHANNEL`;
  `local->in_reconfig` forces that flag in `ieee80211_calc_hw_conf_chan()`.
- `reconfig_complete` op on a restart: runs while `local->in_reconfig` is
  still true and the queues are still stopped.
- `local->open_count` of 0: `ieee80211_reconfig()` jumps to `wake_up`;
  neither `drv_start()` nor `drv_reconfig_complete()` is called.

**Reconfiguration locks and failures**

- Failures that end the reconfiguration: `drv_start()`, and
  `drv_add_interface()` in the loop over `local->interfaces`. Both call
  `ieee80211_handle_reconfig_failure()` and return the error.
- `drv_resume()` returning negative (reached only with `local->wowlan`, under
  `CONFIG_PM`): also ends the reconfiguration and returns the error, without
  `ieee80211_handle_reconfig_failure()`.
- A fatal return skips `drv_reconfig_complete()`; the `reconfig_complete` op
  is not called.
- Queues on a `drv_start()` failure: woken by `ieee80211_reconfig()` itself,
  before `ieee80211_handle_reconfig_failure()`, which does not clear
  `IEEE80211_QUEUE_STOP_REASON_SUSPEND`.
- Other callback failures do not end the reconfiguration:

| Call | On failure |
|---|---|
| `drv_add_chanctx()`, `drv_join_ibss()`, `drv_sta_state()` in `ieee80211_reconfig_stations()` | `WARN_ON()`, continue |
| `ieee80211_reconfig_nan()` | `WARN_ON()`, continue; the rest of the NAN restore is skipped |
| `drv_assign_vif_chanctx()`, `drv_change_vif_links()`, `drv_conf_tx()`, `drv_start_ap()`, `ieee80211_hw_config()` | return value dropped, no warning |
| key upload in `ieee80211_reenable_keys()` | return value dropped; `ieee80211_key_enable_hw_accel()` logs with `sdata_err()` unless the error is `-ENOSPC` or `-EOPNOTSUPP` |
| scheduled scan restart | scan reported stopped with `cfg80211_sched_scan_stopped_locked()` |

- `ieee80211_reconfig_disconnect()`: never called by `ieee80211_reconfig()` on
  a failure. Only a driver reaches it, through
  `ieee80211_hw_restart_disconnect()` or `ieee80211_resume_disconnect()`.
- The flag set that way is acted on at the very end, by
  `ieee80211_sta_restart()` in `net/mac80211/mlme.c`.

## Locking and callback context

**The wiphy mutex**

- `iflist_mtx`: the only other sleeping lock in `struct ieee80211_local`; it
  is the only `struct mutex` declared in `net/mac80211/ieee80211_i.h`.
- key_mtx, sta_mtx and chanctx_mtx: exist nowhere in this tree; keys,
  stations and channel contexts are under the wiphy mutex.
- `struct ieee80211_local` has no member named `sta_lock`; the spinlock next
  to the station list is `tim_lock`.
- Comments in `net/mac80211/ieee80211_i.h` that say "RTNL and local->mtx"
  are stale; `struct ieee80211_local` has no `mtx` member.
- `iflist_mtx` nests inside the wiphy mutex: order is RTNL, wiphy mutex,
  `iflist_mtx`; see `ieee80211_if_add()` in `net/mac80211/iface.c`.
- `iflist_mtx` covers writes to `local->interfaces`, and the writes to
  `local->monitor_sdata` in `net/mac80211/iface.c`; `__iterate_interfaces()`
  in `net/mac80211/util.c` accepts `iflist_mtx` or the wiphy mutex for
  reading.
- Scoped locking: `DEFINE_GUARD(wiphy, ...)` in `include/net/cfg80211.h`;
  code writes `guard(wiphy)(wiphy)` or `scoped_guard(wiphy, wiphy)`, so a
  search for `wiphy_lock()` alone misses lock sites, for example
  `cfg80211_wiphy_work()` and `cfg80211_netdev_notifier_call()`.

**Wiphy mutex assertions**

- `rcu_dereference_wiphy()`: `rcu_dereference_check()` on `wiphy->mtx`, for
  code reached both under `rcu_read_lock()` and under the mutex; defined in
  `include/net/cfg80211.h`.
- `rcu_dereference_wiphy()` kerneldoc says "or RTNL"; the macro tests only
  `wiphy->mtx`, so holding the RTNL alone trips the check.
- mac80211 forms: `sdata_dereference()` in `net/mac80211/ieee80211_i.h`;
  `link_conf_dereference_protected()`, `link_conf_dereference_check()`,
  `link_sta_dereference_protected()`, `link_sta_dereference_check()` in
  `include/net/mac80211.h`, usable from drivers.
- `lockdep_sta_mutex_held()`: an inline that returns `true` without
  `CONFIG_LOCKDEP`; with it, tests the wiphy mutex of the station's `local`.
- `rcu_dereference_protected_tid_tx()` in `net/mac80211/sta_info.h`: accepts
  `sta->lock` or the wiphy mutex.
- net/wireless often writes the assertion as
  `lockdep_assert_held(&rdev->wiphy.mtx)` instead of
  `lockdep_assert_wiphy()`; both mean the same.

**Wiphy work items**

- `struct wiphy_hrtimer_work`: same five operations as
  `struct wiphy_delayed_work`, named `wiphy_hrtimer_work_init()`,
  `wiphy_hrtimer_work_queue()`, `wiphy_hrtimer_work_cancel()`,
  `wiphy_hrtimer_work_flush()`, `wiphy_hrtimer_work_pending()`;
  `CLOCK_BOOTTIME`, relative `ktime_t` delay, 1 ms slack.
- Worker: `cfg80211_wiphy_work()` runs on `system_dfl_wq`.
- While `rdev->suspended` is set the worker returns without running
  anything; items stay queued until `wiphy_resume()` in
  `net/wireless/sysfs.c` queues the worker again.
- `wiphy_delayed_work_queue()` on an armed item: `mod_timer()` moves the
  deadline to the new value, so repeated queueing postpones the handler.
- Flush never drops the wiphy mutex; `cfg80211_process_wiphy_works()` calls
  the handlers inline in the caller.
- `wiphy_delayed_work_flush()` and `wiphy_hrtimer_work_flush()`: delete the
  timer first, then run the handler only if the item is already on the work
  list; with the timer still armed the handler does not run and the item is
  left idle.
- Flush from inside a handler does not deadlock: the running item is taken
  off the list before `func` is called, so flushing itself does nothing.
- `cfg80211_process_wiphy_works()`: after 100 handlers in one call without
  reaching the target it WARNs and empties the list, dropping what is still
  queued.
- Mutex assertion: `wiphy_work_cancel()`, `wiphy_delayed_work_cancel()`,
  `wiphy_hrtimer_work_cancel()`, `wiphy_delayed_work_flush()` and
  `wiphy_hrtimer_work_flush()` assert it on entry; `wiphy_work_flush()`
  asserts it only through `cfg80211_process_wiphy_works()`, reached when
  `work` is NULL or the item is on the list.
- **Unsafe usage**: calling a wiphy work cancel or flush function without
  the wiphy mutex.
  - Safe: under the mutex, as `_cfg80211_unregister_wdev()` does before
    `wiphy_work_cancel()`; the cancel functions assert it.
  - Safe: from inside a wiphy work handler, which `cfg80211_wiphy_work()`
    calls with the mutex held.
- **Unsafe usage**: freeing an object that embeds a wiphy work item while
  the item is queued or its timer is armed.
  - Safe: cancel under the wiphy mutex before the free, as
    `ieee80211_link_stop()` does for `csa.finalize_work` before
    `ieee80211_free_links()` frees the link; `cfg80211_wiphy_work()` calls
    `wk->func` and the timer callbacks read `dwork->wiphy`, and
    `cfg80211_dev_free()` WARNs if the list is not empty.

**cfg80211 operation context**

- `nl80211_pre_doit()`: calls `rtnl_lock()` unconditionally, looks up the
  device, takes the wiphy mutex, then calls `rtnl_unlock()` unless
  `NL80211_FLAG_NEED_RTNL` is set.
- Wiphy mutex in `nl80211_pre_doit()`: taken whenever an rdev was looked up
  (`NL80211_FLAG_NEED_WIPHY`, `NL80211_FLAG_NEED_NETDEV` or
  `NL80211_FLAG_NEED_WDEV`) and `NL80211_FLAG_NO_WIPHY_MTX` is clear.
- `NL80211_FLAG_NO_WIPHY_MTX`: the handler takes the mutex itself before it
  calls the op, for example `nl80211_new_interface()`.
- `nl80211_del_interface()`: unlocks the wiphy mutex around `dev_close()`
  and relocks before `del_virtual_intf` is called.
- `rdev_` wrappers in `net/wireless/rdev-ops.h`: none asserts the wiphy
  mutex.
- `cfg80211_register_netdevice()` asserts the RTNL as well as the wiphy
  mutex, so it is usable only from ops documented to hold the RTNL
  (`add_virtual_intf`, `del_virtual_intf`, `change_virtual_intf`) or from
  code that took both locks itself.
- What decides the variant is whether the caller holds the wiphy mutex, not
  whether it is inside an op; `brcmf_net_attach()` picks by a `locked`
  argument.
- **Potentially unsafe usage**: `register_netdevice()` or
  `unregister_netdevice()` with the wiphy mutex held.
  - Unsafe: when the netdev has `ieee80211_ptr` set;
    `cfg80211_netdev_notifier_call()` takes the wiphy mutex on
    `NETDEV_REGISTER` when `wdev->registered` is false, and on
    `NETDEV_UNREGISTER` when it is true and `wdev->registering` is false;
    the caller deadlocks on its own mutex.
  - Safe: `cfg80211_register_netdevice()` and
    `cfg80211_unregister_netdevice()` with RTNL and wiphy mutex held, as
    `ieee80211_if_add()` does; the first sets `wdev->registered` and
    `wdev->registering`, the second clears `wdev->registered`, so the
    notifier skips the wdev. For unregistering, the netdev must already be
    closed: the notifier takes the mutex unconditionally on
    `NETDEV_GOING_DOWN` and `NETDEV_DOWN`.
  - Safe: a netdev with no `ieee80211_ptr`, as the monitor netdev that
    `wilc_wfi_init_mon_interface()` registers; the notifier returns at once
    when `dev->ieee80211_ptr` is NULL.
  - Safe: the plain functions with the wiphy mutex not held, as
    `brcmf_net_attach()` does with `register_netdev()`; the notifier then
    takes the mutex.

**mac80211 callback context**

- Kerneldoc above `struct ieee80211_ops`: states "must be atomic" or "can
  sleep" for many callbacks, but not all; for example `wake_tx_queue`,
  `get_txpower` and `net_setup_tc` state nothing.
- The kerneldoc has no general rule about the wiphy mutex; it names the
  mutex for two callbacks only, `get_et_sset_count` and `get_et_strings`,
  both "not held".
- The wrapper is where the context shows: a `drv_` wrapper that starts with
  `might_sleep()` and `lockdep_assert_wiphy()` is a sleeping callback under
  the mutex.
- `drv_configure_filter()`, `drv_get_tsf()` and `drv_sta_pre_rcu_remove()`:
  all sleep and assert the wiphy mutex.
- Wrappers that sleep without asserting the mutex: for example
  `drv_net_setup_tc()`, `drv_can_neg_ttlm()` and `drv_vif_add_debugfs()`
  call `might_sleep()` only.
- `drv_tx()`: calls the driver with no check and no tracepoint.
- `check_sdata_in_driver()` result is ignored by some wrappers, for example
  `drv_start_nan()`; they warn and call the driver anyway.
- There is no sdata_assert_lock here; wrappers use `lockdep_assert_wiphy()`.
- `for_each_interface()`, `for_each_active_interface()`,
  `for_each_station()` in `include/net/mac80211.h`: require the wiphy
  mutex; the assertion is in `__ieee80211_iterate_interfaces()` and
  `__ieee80211_iterate_stations()`, which
  `ieee80211_iterate_active_interfaces_mtx()` and
  `ieee80211_iterate_stations_mtx()` also use.
- **Potentially unsafe usage**: `ieee80211_iterate_interfaces()` or
  `ieee80211_iterate_active_interfaces()` from driver code.
  - Unsafe: in a callback that mac80211 makes with `iflist_mtx` held;
    `ieee80211_del_virtual_monitor()` holds it across
    `ieee80211_link_release_channel()` and `drv_remove_interface()`, so the
    iterator deadlocks on `iflist_mtx`.
  - Safe: from a context that holds no mac80211 lock, as the plain work
    handler `rt2x00lib_intf_scheduled()` does.
  - Safe: under the wiphy mutex use
    `ieee80211_iterate_active_interfaces_mtx()` or
    `for_each_active_interface()`; `__ieee80211_iterate_interfaces()` takes
    no lock.

**Changing a driver callback**

- Signature mismatch in a built driver: a build error, not a warning;
  `scripts/Makefile.warn` sets `-Werror=incompatible-pointer-types`
  unconditionally.
- cfg80211 op checks live in two places: `wiphy_new_nm()` checks op pairs
  with `WARN_ON()` and continues; `wiphy_register()` checks ops against
  advertised features and interface modes and returns `-EINVAL`.
- mac80211 op checks: `ieee80211_alloc_hw_nm()` in `net/mac80211/main.c`
  returns `NULL` on a missing mandatory or inconsistent op;
  `ieee80211_register_hw()` has further checks against hw flags.
- All of these checks fire at runtime; none fails the build.
- Direct calls: in net/wireless every call through `rdev->ops` is in
  `net/wireless/rdev-ops.h`; in mac80211 some calls bypass the `drv_`
  wrappers, in `net/mac80211/cfg.c` (for example `testmode_cmd`,
  `set_sar_specs`) and in `ieee80211_bss_info_change_notify()` in
  `net/mac80211/main.c`; search for `local->ops->`.
- `mac80211_config_ops` in `net/mac80211/cfg.c`: one table shared by every
  mac80211 driver, so a cfg80211 test of `rdev->ops->x`, such as the
  `CMD()` macro in `net/wireless/nl80211.c`, is true for all of them; the
  mac80211 implementation has to return `-EOPNOTSUPP` itself when the
  driver lacks the `struct ieee80211_ops` callback.

## Data path

**Receive and status entry points**

- `ieee80211_rx_ni()` and `ieee80211_tx_status_ni()`: the process-context
  variants; inlines in `include/net/mac80211.h` that wrap `ieee80211_rx()` and
  `ieee80211_tx_status_skb()` in `local_bh_disable()`/`local_bh_enable()`.
- `ieee80211_tx_status_noskb()`: inline over `ieee80211_tx_status_ext()` with
  `skb` NULL; same context as `ieee80211_tx_status_ext()`.
- `ieee80211_rx_napi()`: `napi` may be NULL, and delivery is then
  `netif_receive_skb_list()`; `ieee80211_rx_list()` has no napi argument.
- `ieee80211_rx_list()`: the caller holds `rcu_read_lock()` as well as BH
  disabled; `ieee80211_rx_napi()` takes `rcu_read_lock()` itself.
- `ieee80211_tx_status_ext()`: takes no `rcu_read_lock()` to cover
  `status->sta`; `ieee80211_tx_status_skb()` holds it around its sta lookup
  and the call.
- `status->sta` passed to `ieee80211_tx_status_ext()`: the caller keeps it
  valid across the call, as `mt76_tx_status_unlock()` does with
  `rcu_read_lock()`.
- Context checks in the RX and status entry points: the only one is
  `WARN_ON_ONCE(softirq_count() == 0)` in `ieee80211_rx_list()`;
  `net/mac80211/status.c` has no context assertion.
- Status from hardirq: `rate_control_tx_status()` takes
  `sta->rate_ctrl_lock` with `spin_lock_bh()`.
- `ieee80211_tx_status_irqsafe()` is lossy: once both queues together exceed
  `IEEE80211_IRQSAFE_QUEUE_LIMIT`, frames without
  `IEEE80211_TX_CTL_REQ_TX_STATUS` are freed with `ieee80211_free_txskb()` and
  never reach rate control. `ieee80211_rx_irqsafe()` frames are not dropped by
  this limit.
- Dispatch on `skb->pkt_type`: in `ieee80211_handle_queued_frames()` in
  `net/mac80211/main.c`; `ieee80211_tasklet_handler()` only calls it, and so
  does `ieee80211_stop_device()` under `local_bh_disable()`.
- `ieee80211_handle_queued_frames()`: takes from `local->skb_queue_unreliable`
  only when `local->skb_queue` is empty, so unrequested status is handled after
  all queued RX.
- No-mixing and serialisation rules: stated in kerneldoc and comments only; no
  entry point records or tests which variant a hw has used.
- RX locking inside mac80211: `ieee80211_rx_handlers()` runs the handler chain
  under `local->rx_path_lock`, and reordering holds
  `tid_agg_rx->reorder_lock`.
- Outside those locks, for example: `ieee80211_rx_h_check_dup()` writes
  `rx->sta->last_seq_ctrl[]`, and `ieee80211_rx_8023()` writes the station RX
  statistics; unserialised RX calls race on these.
- `IEEE80211_HW_USES_RSS`: RX calls for one hw run in parallel by design, for
  example `iwl_mld_pass_packet_to_mac80211()`, which takes the RX queue and
  its napi.
- With `IEEE80211_HW_USES_RSS`: `ieee80211_rx_8023()` and
  `ieee80211_invoke_fast_rx()` use `pcpu_rx_stats`.
- `ieee80211_invoke_fast_rx()`: refuses a frame without
  `RX_FLAG_DUP_VALIDATED`, with or without `IEEE80211_HW_USES_RSS`; the frame
  then goes through `ieee80211_invoke_rx_handlers()`, where
  `ieee80211_rx_h_check_dup()` runs before `local->rx_path_lock` is taken.
- RX before status: `ieee80211_handle_filtered_frame()` tests
  `WLAN_STA_PS_STA`, which `sta_ps_start()` in `net/mac80211/rx.c` sets; a
  status handled before the RX frame that put the station to sleep is retried
  once through `ieee80211_add_pending_skb()` instead of being held in
  `sta->tx_filtered[]`.
- Serialising direct RX against direct status is the driver's job: for example
  `mt76_rx_complete()` and `mt76_tx_status_unlock()` both hold `dev->rx_lock`
  around the mac80211 call.

**Transmit control block**

- Head: `struct ieee80211_tx_info` has no `ack_frame_id` member; `status_data`
  with `status_data_idr` does that job.
- `status_data_idr` set: `status_data` is the id in
  `local->ack_status_frames`. Clear: `status_data` is a type and subdata from
  `enum ieee80211_status_data` in `net/mac80211/ieee80211_i.h`.
- `tx_time_mc`: head bit, read together with `tx_time_est` for airtime
  accounting at status time.
- Head at status or free time: `ieee80211_report_used_skb()` reads `flags`,
  `status_data_idr`, `status_data`, `tx_time_est` and `tx_time_mc`;
  `ieee80211_free_txskb()` reaches it too, so the head must survive in a frame
  that is dropped.
- `status`: has no `is_valid_ack_signal` member; validity of
  `status.ack_signal` is `IEEE80211_TX_STATUS_ACK_SIGNAL_VALID` in
  `status.flags`.
- `status.link_valid` and `status.link_id`: set by the driver for MLO;
  `ieee80211_report_ack_skb()` reads them.
- `rate_driver_data`: not inside `control`; it is in an anonymous struct of the
  union, after `driver_rates` and `pad`, and is the driver's area.
- `rate_driver_data` starts at the offset of `control.vif`: it preserves the
  rates, `control.rts_cts_rate_idx` and the RTS/CTS bits, not `control.vif` or
  `control.hw_key`.
- `status.status_driver_data`: the last 16 bytes; overlays neither
  `control.rates` nor `control.vif`, but does overlay `control.flags` and
  `control.enqueue_time` (and `control.hw_key` on 64-bit). A driver can keep
  data there while the frame is queued once it has read those, as
  `mt76_tx_skb_cb()` users do.
- `status.ack_signal`: lies on `control.rts_cts_rate_idx` and the RTS/CTS bits.
- `status.ampdu_ack_len` through `status.link_id`: lie on the bytes of
  `control.vif` (and of `control.hw_key` on 32-bit).
- `net/mac80211/status.c` does not read `info->control`: it finds the interface
  with `ieee80211_sdata_from_skb()`, and `ieee80211_handle_filtered_frame()`
  zeroes `control` and sets `control.vif` again before it requeues a frame.
- `ieee80211_tx_info_clear_status()`: does not touch `info->flags`, so
  `IEEE80211_TX_STAT_ACK` and the other status bits stay as they were;
  `rtw_tx_report_tx_status()` clears `IEEE80211_TX_STAT_ACK` by hand.
- `ieee80211_tx_info_clear_status()`: zeroes to the end of `status`,
  `status_driver_data` included.
- Through the union that same range is `control.rts_cts_rate_idx` and the
  RTS/CTS bits, `control.vif`, `control.hw_key`, `control.flags`,
  `control.enqueue_time`, all of `rate_driver_data`, and `driver_data` past its
  first 12 bytes.
- **Potentially unsafe usage**: reporting status without
  `ieee80211_tx_info_clear_status()`.
  - Unsafe: when the bytes after `status.rates` still hold control or driver
    data; `ieee80211_tx_status_ext()` reads `status.flags` and
    `status.tx_time`, and `ieee80211_report_ack_skb()` reads
    `status.link_valid`, from what was a pointer.
  - Safe: zero all of `info->status` and set `status.rates[0].idx` to -1, as
    `wmi_process_mgmt_tx_comp()` in `drivers/net/wireless/ath/ath11k/wmi.c`
    does; `ieee80211_tx_get_rates()` stops at a negative `idx`.
- **Unsafe usage**: reading per-frame driver data after
  `ieee80211_tx_info_clear_status()`.
  - Unsafe: when the data is in `rate_driver_data`, `status_driver_data` or
    `driver_data` past its first 12 bytes and was not copied out first; it
    reads back as zero.
  - Safe: fetch it before the clear, as `zd_mac_tx_to_dev()` does with
    `info->rate_driver_data[0]`; the `memset_after()` in
    `ieee80211_tx_info_clear_status()` defines what is lost.

## Elements and scan results

**Parsing elements**

- **Potentially unsafe usage**: passing a length computed by subtraction to
  `for_each_element()` or `cfg80211_find_elem()`.
  - Unsafe: when nothing earlier checked that the frame is at least as long as
    its fixed part. `for_each_element()` trusts `_datalen`, and a negative
    `int len` of `cfg80211_find_elem()` becomes a large `unsigned int` in
    `cfg80211_find_elem_match()`, so the walk runs past the buffer.
  - Safe: after a length check, as `cfg80211_inform_bss_frame_data()` does
    with `len < min_hdr_len` before it computes `ielen`.
- **Potentially unsafe usage**: copying `elem->datalen` (or `elems->ssid_len`)
  bytes into a fixed-size buffer.
  - Unsafe: when the length was not bounded; it is the raw length byte, up to
    255, for example an SSID longer than `IEEE80211_MAX_SSID_LEN`.
  - Safe: bound it first, as `__cfg80211_connect_result()` does with `min()`
    and `ieee80211_mgd_assoc()` does by rejecting
    `datalen > sizeof(assoc_data->ssid)`.
- `for_each_element_completed()`: returns false after any `break` out of the
  loop, not only for a malformed tail.
- Extension elements: `data[0]` is the extension ID, so size helpers such as
  `ieee80211_he_capa_size_ok()` take `data + 1` and `datalen - 1`; a
  `sizeof()` test on `datalen` needs `+ 1`, unless a test of `datalen`
  against `ieee80211_he_oper_size()` follows, which counts the extension ID
  byte, as in `cfg80211_get_ies_channel_number()`.
- Size helpers such as `ieee80211_he_capa_size_ok()` and
  `ieee80211_mle_size_ok()`: defined in the split headers
  `include/linux/ieee80211-he.h`, `include/linux/ieee80211-eht.h`,
  `include/linux/ieee80211-uhr.h` and `include/linux/ieee80211-mesh.h`.
- `cfg80211_find_vendor_elem()`: a non-NULL result has `datalen >= 4`, also
  when `oui_type` is negative.
- Fragmented elements: `for_each_element()` yields each `WLAN_EID_FRAGMENT`
  as its own element; `cfg80211_defragment_element()` joins them.
- There is no ieee802_11_parse_elems_crc() here; the only wrapper is
  `ieee802_11_parse_elems()` in `net/mac80211/ieee80211_i.h`. CRC input is
  `filter` and `crc` in `struct ieee80211_elems_parse_params`, the result is
  `elems->crc`.
- `ieee802_11_parse_elems_full()` returns NULL also when
  `params->link_id >= 0` and `params->bss` are both set, after a `WARN_ON()`.
- `link_id` in the params: must be -1 when no per-link parse is wanted. A
  zeroed field asks for the per-STA profile of link 0.
- `params->mode`: elements of a newer generation than the mode are not stored,
  and no error bit is set. A zeroed `mode` is `IEEE80211_CONN_MODE_S1G`.
- S1G members (`s1g_capab`, `s1g_oper`, `s1g_bcn_compat`, `aid_resp`): stored
  only when `mode` is exactly `IEEE80211_CONN_MODE_S1G`, so never through
  `ieee802_11_parse_elems()`, which passes `IEEE80211_CONN_MODE_HIGHEST`.
- `elems->parse_error`: a `u8` bitmask of
  `enum ieee80211_elems_parse_error`.
- `parse_error == 0` does not mean every element was well formed:
  `ieee80211_parse_extension_element()` drops a wrong-sized extension element
  without setting `IEEE80211_PARSE_ERR_BAD_ELEM_SIZE`.
- Duplicates: for the IDs in the first `switch` of
  `_ieee802_11_parse_elems_full()` the first good occurrence wins and
  `IEEE80211_PARSE_ERR_DUP_ELEM` is set. For other IDs, including extension
  elements, a later occurrence overwrites the pointer. Exceptions:
  `WLAN_EID_EXT_TID_TO_LINK_MAPPING` is appended to `ttlm[]`, and with
  `params->bss` NULL `elems->ml_basic` is the first basic multi-link element,
  found by `ieee80211_prep_mle_link_parse()`.

**BSS entry references**

- `__cfg80211_get_bss()` and the inline `cfg80211_get_ibss()`: also return a
  referenced entry, or NULL.
- Functions that consume the caller's reference on every path, so the caller
  must not put again: `cfg80211_connect_done()` and `cfg80211_roamed()`, for
  each `links[].bss` passed in.
- `cfg80211_rx_assoc_resp()` and `cfg80211_assoc_failure()`: consume the
  reference and the hold that `cfg80211_mlme_assoc()` took when the `assoc`
  op succeeded; on a successful association
  `__cfg80211_connect_result()` keeps both for `current_bss`.
- `cfg80211_unlink_bss()`: drops the scan list's own reference through
  `__cfg80211_unlink_bss()`, not the caller's. It also unlinks every entry on
  the `nontrans_list` of the entry.
- A reference keeps the memory, not the place in the list. `hold` in
  `struct cfg80211_internal_bss`, not `refcount`, stops
  `__cfg80211_bss_expire()` and `cfg80211_bss_expire_oldest()`; see
  `cfg80211_hold_bss()` in `net/wireless/core.h`.
- An unlinked entry has `list_empty()` true on its `list`;
  `cfg80211_update_link_bss()` in `net/wireless/sme.c` handles that case.
- `ieee80211_bss_get_elem()` in `net/wireless/util.c`: takes no lock itself.
  It calls `rcu_dereference(bss->ies)`, so the caller holds `rcu_read_lock()`
  across the call and every use of the result.
- **Unsafe usage**: reading `ies`, `beacon_ies` or `proberesp_ies` of an
  entry under `wiphy->mtx` alone, for example with `wiphy_dereference()`.
  `cfg80211_update_known_bss()` replaces them and calls `kfree_rcu()` under
  `rdev->bss_lock` only, and mac80211 reaches it from `ieee80211_scan_rx()` in
  the RX path.
  - Safe: `rcu_read_lock()`, `rcu_dereference()`, copy out, unlock, as
    `ieee80211_mgd_assoc()` does for the SSID.
  - Safe: inside `net/wireless/scan.c` with `rdev->bss_lock` held and
    `rcu_access_pointer()`, as `is_bss()` does when called from
    `__cfg80211_get_bss()`.
- `beacon_ies` and `proberesp_ies`: either can be NULL. `ies` is non-NULL on
  an inserted entry; `__cfg80211_bss_update()` rejects a NULL one.
- `cfg80211_bss_iter()`: calls the callback under
  `spin_lock_bh(&rdev->bss_lock)`. The callback must not sleep and must not
  call `cfg80211_ref_bss()`, `cfg80211_put_bss()` or the get and inform
  functions, which take the same lock.
- A `cfg80211_bss_iter()` callback still takes `rcu_read_lock()` before
  `rcu_dereference(bss->ies)`, as
  `iwl_mvm_check_he_obss_narrow_bw_ru_iter()` does.
- `inform_bss` op in `struct cfg80211_ops`: `rdev_inform_bss()` calls it
  inside the `bss_lock` section of `cfg80211_inform_single_bss_data()`, so the
  same limits apply as for a `cfg80211_bss_iter()` callback. mac80211's
  `ieee80211_inform_bss()` is the only implementation outside the kunit test
  `net/wireless/tests/scan.c`.

## nl80211

**Adding an nl80211 command**

- `nl80211_ops` (`struct genl_ops`): holds two commands,
  `NL80211_CMD_GET_WIPHY` and `NL80211_CMD_GET_STATION`, both with `.done`;
  every other command is in `nl80211_small_ops` (`struct genl_small_ops`).
- `.internal_flags`: a `u8` index of `enum nl80211_internal_flags_selector`
  into `nl80211_internal_flags[]`, not the flag bitmask;
  `NL80211_FLAG_MLO_UNSUPPORTED` is 0x100.
- `IFLAGS()`: matches the OR of the flags against each `SELECTOR()` value by
  equality, so a combination must match one line exactly.
- New combination: add one `SELECTOR()` line to `INTERNAL_FLAG_SELECTORS()` in
  `net/wireless/nl80211.c`; the enum and `nl80211_internal_flags[]` are
  generated from it, and `nl80211_pre_doit()` needs no change.
- Missing `SELECTOR()` line: the entry's static initializer becomes a call to
  `__missing_selector()`, which is declared but defined nowhere, so the build
  fails.
- Entry with no `.internal_flags`: no lookup, both `info->user_ptr[]` NULL, no
  wiphy mutex; the handler looks up and locks itself, as `nl80211_set_wiphy()`
  does.
- `info->user_ptr[1]`: `struct net_device *` with `NL80211_FLAG_NEED_NETDEV`,
  `struct wireless_dev *` with `NL80211_FLAG_NEED_WDEV`, NULL with
  `NL80211_FLAG_NEED_WIPHY`.
- P2P device and NAN: no flag variants; `NL80211_FLAG_CHECK_NETDEV_UP` calls
  `wdev_running()`, which tests `wdev->is_running` when there is no netdev.
- `NL80211_FLAG_MLO_VALID_LINK_ID`: on an MLD `NL80211_ATTR_MLO_LINK_ID` must
  be present and in `wdev->valid_links`; on a non-MLD its presence gives
  `-EINVAL`.
- `nl80211_pre_doit()` failure: `genl_family_rcv_msg_doit()` skips the handler
  and `nl80211_post_doit()`, so `nl80211_pre_doit()` must undo its own locks
  and reference on every error path.
- `.dumpit`: `genl_family_rcv_msg_dumpit()` calls neither hook, so
  `.internal_flags` covers `.doit` only; see `nl80211_prepare_wdev_dump()`.
- **Unsafe usage**: a `NL80211_FLAG_NEED_WDEV` handler frees a wdev that has
  no netdev and leaves `info->user_ptr[1]` set.
  - Unsafe: `nl80211_post_doit()` reads `wdev->netdev` from the freed wdev.
  - Safe: set `info->user_ptr[1] = NULL` before the free, as
    `nl80211_del_interface()` does.

**Adding an nl80211 attribute**

- Missing policy entry: an attribute sent by userspace is rejected by
  `validate_nla()` with `-EINVAL` ("Unsupported attribute") before a `.doit`
  handler runs; it is never accepted unvalidated, since every new number is
  above the strict start.
- Attributes only sent by the kernel: need no entry (for example
  `NL80211_ATTR_WIPHY_RADIOS`, `NL80211_ATTR_TX_HW_TIMESTAMP`); some carry
  `{ .type = NLA_REJECT }`, as `NL80211_ATTR_RECONNECT_REQUESTED` does.
- `NL80211_ATTR_MLO_LINK_ID` policy:
  `NLA_POLICY_RANGE(NLA_U8, 0, IEEE80211_MLD_MAX_NUM_LINKS - 1)`; it bounds the
  index into `wdev->links[]`, not whether the link exists.
- `nl80211_link_id()`: returns 0 when the attribute is absent, for handlers
  that index `wdev->links[]`, for example `nl80211_color_change()`.
- `nl80211_link_id_or_invalid()`: returns -1 when the attribute is absent, for
  handlers where the link id is optional.
- Per-link ids inside `NL80211_ATTR_MLO_LINKS`: `nl80211_process_links()`
  parses each link with no policy; the bound comes from the entry
  `NLA_POLICY_NESTED_ARRAY(nl80211_policy)`.
- **Potentially unsafe usage**: using the link id in an op without
  `NL80211_FLAG_MLO_VALID_LINK_ID`.
  - Unsafe: when the handler treats the link as existing and nothing has
    tested `wdev->valid_links`; on an MLD `nl80211_link_id()` returns 0 for an
    absent attribute.
  - Safe: the handler tests `wdev->valid_links & BIT(link_id)` itself and
    rejects an id on a non-MLD, as `nl80211_del_station()` does.
  - Safe: the handler calls `nl80211_validate_key_link_id()` before the op, as
    `nl80211_new_key()` does; it makes the same `wdev->valid_links` tests for
    a group key and rejects any link id for a pairwise key.

**Strict attribute validation**

- Start: `nl80211_policy[0]` is
  `{ .strict_start_type = NL80211_ATTR_HE_OBSS_PD }`; there is no separate
  constant for it.
- `.strict_start_type`: `validate_nla()` in `lib/nlattr.c` adds
  `NL_VALIDATE_STRICT` per attribute, for each one numbered at or above it.
- Unknown attribute numbers and trailing bytes: tested in
  `__nla_validate_parse()` with the op's own flags, so an op with
  `GENL_DONT_VALIDATE_STRICT` still skips attributes above `NL80211_ATTR_MAX`.
- Ops with no `.validate`: parsed with `NL_VALIDATE_STRICT` for every
  attribute, including those numbered below `NL80211_ATTR_HE_OBSS_PD`.
- Commands at or above `.resv_start_op` (`NL80211_CMD_REMOVE_LINK_STA + 1`):
  must leave `.validate` zero; otherwise `genl_validate_ops()` hits a
  `WARN_ON()` and `genl_register_family()` returns `-EINVAL`.
- Nested policies: `validate_nla()` passes its strict flags into
  `nested_policy`, so everything inside a strict attribute is strict.
- Nested `.strict_start_type`: no policy under `net/wireless/` other than
  `nl80211_policy` sets it.
- `NL80211_ATTR_MLO_LINKS`: its nested policy is `nl80211_policy` itself, so
  old attributes inside it are strict too.
- Plain `{ .type = NLA_NESTED }` entry: accepted above the strict start (for
  example `NL80211_ATTR_MBSSID_ELEMS`); the contents are unvalidated until the
  handler parses them.
- Handler parse of a nested set: `nla_parse_nested()` is strict,
  `nla_parse_nested_deprecated()` is liberal.
- `NLA_FLAG`: not in `nla_attr_len[]`; a payload is rejected at any
  validation level.

## Model gaps

### Other mistakes models make

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
