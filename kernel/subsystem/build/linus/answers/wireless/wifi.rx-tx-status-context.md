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
