- Core reason: written by hand twice in `include/net/dropreason-core.h`, as an
  `FN()` line in `DEFINE_DROP_REASON` and as an entry of
  `enum skb_drop_reason` with its kernel-doc. The macro list generates only
  the names, not the enum.
- Order of the `FN()` list: need not match the enum. `drop_reasons` in
  `net/core/skbuff.c` uses designated initializers and
  `include/trace/events/skb.h` uses value/name pairs, so both key on the enum
  value.
- Enum entry without an `FN()` line: builds, and has no name. An `FN()` line
  without an enum entry does not build.
- Registration: not every subsystem registers. `SKB_DROP_REASON_SUBSYS_QDISC`
  has an entry in `enum skb_drop_reason_subsys` and no call to
  `drop_reasons_register_subsys()`; mac80211 and openvswitch do register.
- Qdisc reasons: a separate `enum qdisc_drop_reason` with its own list
  `DEFINE_QDISC_DROP_REASON` in `include/net/dropreason-qdisc.h`. Their names
  are printed by `trace_qdisc_drop()` (`include/trace/events/qdisc.h`).
- `__tcf_kfree_skb_list()` in `net/sched/sch_generic.c`: recognises a qdisc
  reason by its subsystem bits, fires `trace_qdisc_drop()` with it, and frees
  with `SKB_DROP_REASON_QDISC_DROP`.
- Unregistered or unnamed reason in `net_dm_packet_report_fill()`
  (`net/core/drop_monitor.c`): reported under the name of
  `SKB_DROP_REASON_NOT_SPECIFIED`.
- mac80211 reasons: in `net/mac80211/drop.h`, not in `include/net/mac80211.h`.
  The only mac80211 subsystem is `SKB_DROP_REASON_SUBSYS_MAC80211_UNUSABLE`;
  there is no SKB_DROP_REASON_SUBSYS_MAC80211_MONITOR.
- Values that are not drops, beyond `SKB_NOT_DROPPED_YET`, `SKB_CONSUMED` and
  `SKB_DROP_REASON_MAX`:
  - `SKB_DROP_REASON_SUBSYS_MASK`, a mask inside `enum skb_drop_reason`;
  - each subsystem's base value: `___RX_DROP_UNUSABLE`, `__OVS_DROP_REASON`,
    `__QDISC_DROP_REASON`;
  - the bounds `OVS_DROP_MAX` and `QDISC_DROP_MAX`, and `QDISC_DROP_UNSPEC`
    (0);
  - mac80211's `RX_CONTINUE` and `RX_QUEUED`, which alias `SKB_CONSUMED` and
    `SKB_NOT_DROPPED_YET`.
