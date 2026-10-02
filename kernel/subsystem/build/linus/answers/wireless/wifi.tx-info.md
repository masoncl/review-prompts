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
