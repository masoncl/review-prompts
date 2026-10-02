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
