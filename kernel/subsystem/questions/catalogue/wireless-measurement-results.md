# What the wireless measurement found

Three models were asked the 35 questions in `wireless-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader A said it assumed kernels 6.12 to
6.17, reader B 6.10 to 6.12 and reader C 6.12 to 6.19. Readers A and C know the
multi-link rework, the single wiphy mutex and the split change callbacks.
Reader B knows that the split exists but describes the locking of several
releases earlier, believes the single change callback has been removed, and
invents names. Two of the questions (`wifi.misplaced-flag-handling` and
`wifi.mlo-requirements`) were added after the first run and asked in a second
one. The hand-written guide was never checked against current sources, so
differences between it and the built guide are expected and are noted near the
end.

The hand-written guide is about one thing, which mac80211 callback receives
which `BSS_CHANGED_*` flag, so five of the questions are about that and thirty
sample the rest of the stack: cfg80211, nl80211, mac80211's driver interface,
locking, stations, the data path.

## What all three readers got wrong

- **The split macro is not the whole story.** All three said every flag that
  reaches the interface-wide callback is in `BSS_CHANGED_VIF_CFG_FLAGS`, one of
  them "by construction". `BSS_CHANGED_NAN_LOCAL_SCHED` is not in the macro.
  `net/mac80211/nan.c` and `ieee80211_reconfig_nan()` in `net/mac80211/util.c`
  hand it straight to `drv_vif_cfg_changed()`, its value is in
  `vif->cfg.nan_sched`, and hwsim, iwlwifi and mt7925 test for it in their
  interface-wide callbacks. `ieee80211_vif_cfg_change_notify()` would warn on
  it.
- **Which interface types get which flags.** `drv_link_info_changed()` drops,
  with a warning, the two beacon flags on anything but AP, IBSS, mesh and OCB
  interfaces, everything on P2P device and NAN interfaces, and everything but
  `BSS_CHANGED_TXPOWER` and `BSS_CHANGED_MU_GROUPS` on a monitor interface; it
  drops `BSS_CHANGED_MU_GROUPS` unless `mu_mimo_owner` is set; and it returns
  silently for a link that is not active. Every reader had the monitor rule
  wrong.
- **The simulated driver moved.** All three named mac80211_hwsim.c, one of
  them in a directory it left some time ago. It is
  `drivers/net/wireless/virtual/mac80211_hwsim_main.c`, beside
  `mac80211_hwsim_nan.c` and `mac80211_hwsim_i.h`.
- **The link bitmaps.** `dormant_links` are valid links disabled by an
  advertised TID-to-link mapping or suspended by a negotiated one, and
  `suspended_links` is the second kind, a subset of the first. Readers gave one
  cause or the other. `for_each_vif_active_link()` takes no lock: it uses
  `link_conf_dereference_check()`, so the caller holds RCU or the wiphy mutex.
  On an interface that is not multi-link `link_conf[0]` points at
  `vif->bss_conf`.
- **What mac80211 demands of a multi-link driver.** Readers A and C listed
  `IEEE80211_HW_CONNECTION_MONITOR` as required and a DEAUTH_NEED_MGD_TX_PREP
  flag as forbidden. The block in `ieee80211_register_hw()` does not check the
  first, and the second is not defined anywhere in the tree. Reader B said the
  link-change callbacks are required; only `link_info_changed` is. All three
  left out the two per-band checks (no `IEEE80211_HT_CAP_DELAY_BA`, no
  per-band `vendor_elems`).
- **Transmit queue scheduling.** All three bracketed a scheduling round with a
  start and an end call. `ieee80211_txq_schedule_end()` is an empty inline
  marked deprecated; only `ieee80211_txq_schedule_start()` matters. Reader B
  also said `wake_tx_queue` is optional; `ieee80211_alloc_hw_nm()` returns
  `NULL` without it.
- **Key link ids.** All three said `link_id` in `struct ieee80211_key_conf`
  is -1 on an interface that is not multi-link. Only pairwise keys get -1; a
  group key gets the link's id, which is 0 there. A failed disable is logged
  and the key is treated as removed; a failed set is never followed by a
  disable, so the pointer must not be kept.
- **Station teardown.** `__sta_info_destroy_part1()` unlinks the station and
  calls `sta_pre_rcu_remove`, `synchronize_net()` runs, and
  `__sta_info_destroy_part2()` steps the state down to not-existing and frees
  the station at once, with no grace period after the last callback. One
  reader had a grace period after it and another had none before it. The older
  callbacks `sta_add` and `sta_remove` are emulated on the authenticated to
  associated step, not on creation. A lookup is safe under RCU or the wiphy mutex, since both halves of
  the destroy assert the mutex.
- **Restart.** `ieee80211_restart_hw()` only stops the queues, sets
  `in_reconfig` and queues `ieee80211_restart_work()`, which takes the RTNL and
  then the wiphy mutex. In `ieee80211_reconfig()` channel contexts come back
  before `ieee80211_hw_config()`, stations of interfaces that are not APs
  before `drv_conf_tx()`, stations of APs only after beaconing starts, and keys
  last. Only a failing `drv_start()` or `drv_add_interface()` reaches
  `ieee80211_handle_reconfig_failure()`; everything else just warns.
- **Iterators.** None listed `for_each_interface()`,
  `for_each_active_interface()` and `for_each_station()`, which need the wiphy
  mutex. `ieee80211_iterate_interfaces()` takes `iflist_mtx`, not the wiphy
  mutex, and without the active flag it includes interfaces that are not in the
  driver.
- **Callbacks outside the mutex.** `get_et_sset_count` and `get_et_strings`
  are documented as called without the wiphy mutex; nobody listed them. The
  atomic set also includes `get_key_seq`, `sta_rate_tbl_update`,
  `event_callback`, `release_buffered_frames`, `allow_buffered_frames` and
  `ipv6_addr_change`.
- **The transmit control block.** `rate_driver_data` as well as `driver_data`
  overlays `control.vif`, `control.hw_key` and `control.flags`;
  `ieee80211_tx_info_clear_status()` keeps each rate's index and flags and
  zeroes the rest of `status`; only drivers call it.
- **BSS entries.** The list of functions that return a referenced entry was
  incomplete every time (`__cfg80211_get_bss()` takes the reference; the
  others are wrappers). A reference does not keep the elements alive: they are
  replaced and freed with `kfree_rcu()`, while the entry itself is freed with
  a plain `kfree()`.
- **Feature advertising.** `wiphy->features` has every bit used or reserved;
  `enum wiphy_flags` still has room and some of its bits are reported through
  attributes of their own.

## What only some readers got wrong

- **The single change callback** (readers A and B). Reader B said
  `bss_info_changed` no longer exists. It is still in `struct ieee80211_ops`,
  most drivers still use it, `drv_vif_cfg_changed()` and
  `drv_link_info_changed()` fall back to it when the split callback is `NULL`,
  and `ieee80211_bss_info_change_notify()` calls it with every flag. Reader A
  did not know whether it may be combined with the split pair:
  `ieee80211_alloc_hw_nm()` refuses `link_info_changed` together with
  `bss_info_changed`, and either split callback without the other.
- **Where the split is defined** (reader B). The macro is in
  `net/mac80211/main.c`, not the driver header, and the notify functions pass
  the flags on unmasked after warning.
- **Callback set validation** (readers A and B). Required without condition:
  `tx`, `start`, `stop`, `config`, `add_interface`, `remove_interface`,
  `configure_filter`, `wake_tx_queue`. A driver without channel contexts must
  point the add, remove and change callbacks at the `ieee80211_emulate_`
  helpers and leave assign and unassign unset; leaving them all `NULL`, which
  reader B described, is rejected.
- **Locks** (reader B). Reader B named three mutexes in
  `struct ieee80211_local` for stations, keys and channel contexts. None
  exists; `iflist_mtx` is the only other sleeping lock, and everything else is
  under the wiphy mutex, read with `wiphy_dereference()` or
  `sdata_dereference()`.
- **Wiphy work** (readers A and B). `struct wiphy_work` has no embedded work
  item. Cancel and flush both need the mutex held and assert it; cancel does
  not wait, flush runs the item. Reader B had flush taking the mutex itself.
  Work runs on `system_dfl_wq` and is skipped while the device is suspended.
  Reader B left out `wiphy_hrtimer_work`.
- **The RTNL** (readers A and B). `nl80211_pre_doit()` always takes the RTNL
  and drops it again unless the command has `NL80211_FLAG_NEED_RTNL`. Both
  said cfg80211 operations usually run with it.
- **nl80211 command flags** (reader B, and reader A in part). `internal_flags`
  holds an index made by `IFLAGS()` into `nl80211_internal_flags[]`, not a
  bitmask. A new combination needs a `SELECTOR()` line in
  `INTERNAL_FLAG_SELECTORS`; without one the reference to
  `__missing_selector()` fails the link. Most commands are in
  `nl80211_small_ops`. Strict validation starts at `NL80211_ATTR_HE_OBSS_PD`.
- **Names reader B made up or carried over.** ieee80211_tx_status() (it is
  `ieee80211_tx_status_skb()` now), ieee80211_parse_elems(), a regdb.h beside
  `net/wireless/reg.c`, drv_bss_info_changed(), a struct rdev_ops,
  drv_verify_area_lock_held(), a tx_frags callback, a BSS_CHANGED_FLAGS list in
  the trace header. It also put element parsing in `net/mac80211/util.c`
  (`net/mac80211/parse.c`) and the capability structures in
  `include/linux/ieee80211.h` (they are in `include/linux/ieee80211-ht.h`,
  `-vht.h`, `-he.h`, `-eht.h`, `-s1g.h` and `-uhr.h`; reader A was unsure
  whether that split had happened).
- **Hardware flags** (reader B). Adding one means adding a line to
  `hw_flag_names[]` in `net/mac80211/debugfs.c`; a `BUILD_BUG_ON()` checks it.
- **Link activation** (readers A and B). `can_activate_links` is optional. The
  new link's channel context is assigned right after the old one is
  unassigned, before the first `change_sta_links`, and `link_info_changed` for
  the new link comes before the last `change_vif_links`.

## What the readers already knew

Readers A and C: the two callbacks and which flags are interface-wide, the
field each of those flags reports (all but the NAN one), that a driver which
tests a flag in the wrong callback gets no warning and never runs that code,
the object model, how hardware flags are declared and named, what adding a
change flag involves, and roughly which file holds what. Reader C also had the
callback validation in `ieee80211_alloc_hw_nm()` right, the single change
callback, the wiphy mutex and the station states. All three knew that the
`WARN_ON_ONCE()` in the two notify functions polices mac80211's own callers
and not drivers.

## Where the hand-written guide is stale

Its names all exist. What it says about them is partly wrong and mostly
incomplete.

- Its opening and its second quick check say that misrouting a flag between
  the callbacks "triggers `WARN_ON_ONCE` at runtime". The warnings are in
  `ieee80211_vif_cfg_change_notify()` and `ieee80211_link_info_change_notify()`
  and fire on what mac80211's own code passes in. A driver that handles a flag
  in the wrong callback gets no warning; the flag never arrives there and the
  code is dead. The warning does not stop the call either.
- "Any flag in that macro is VIF-global, everything else is link-specific" is
  not true of `BSS_CHANGED_NAN_LOCAL_SCHED`, which is outside the macro, is
  delivered to the interface-wide callback, and reports `vif->cfg.nan_sched`.
- Its table of link-specific flags has 13 of them and reads as a list. The
  enum has 28 that are not interface-wide, `BSS_CHANGED_NPCA` being the
  newest.
- On the fallback it does not say that `ieee80211_alloc_hw_nm()` refuses one
  split callback without the other and `link_info_changed` together with
  `bss_info_changed`, or that `ieee80211_register_hw()` refuses a driver that
  sets `WIPHY_FLAG_SUPPORTS_MLO` without `link_info_changed`.
- It does not mention the third notify function,
  `ieee80211_bss_info_change_notify()`, which takes both kinds of flag, warns
  on a multi-link interface, and is what a driver with the single callback is
  mostly called through.
- It says nothing of the interface types for which flags are dropped, of the
  silent return for an inactive link, or of `check_sdata_in_driver()`.
- For `BSS_CHANGED_MLD_TTLM` it gives no field. They are `vif->neg_ttlm` and,
  set beside it, `vif->dormant_links` and `vif->suspended_links`.
- It covers nothing else in the stack: locking, link state, stations, nl80211.
- Its quick checks tell a reviewer what to flag. The build set asks what the
  code does.

## What was left out of the build set and why

The build set has 11 of the 35 questions and asks for 530 words, which with
titles and headings comes to about 650: inside the twenty percent allowed
around the 600 words a guide this short is sized to, and no answer has fewer
than 40. It first had the same 11 at 20 to 40 words each, 320 in all, sized to
the 402 words of the hand-written guide, and many of the bullets came out as
fragments that meant nothing without the question ("Split: defined in
`net/mac80211/main.c`", "Failure: `WARN_ON()`, NULL"). The same 11 are kept
with room to say what each fact is about: 40 to 50 words for most, 55 for the
table of fields and 60 for the list of registration checks. Nothing came back
from the measurement set, because eleven questions at that floor already fill
the size, and a twelfth would push the guide towards its upper limit. The set
keeps the hand-written guide's emphasis on the change callbacks. Left out:

- `wifi.misplaced-flag-handling`: the mistake the old guide exists for. All
  three readers already describe it correctly, so its words went elsewhere.
  The answers on the callbacks and on the macro's coverage say where the
  warnings are and what they test. It is the first to bring back if the guide
  is allowed to grow.
- The object model, the documentation and tests, hardware flags, protocol
  headers: readers A and C answer them. The core files question is narrowed
  in the build set to the files that moved or that a reader looked for in the
  wrong place.
- cfg80211 operation context, mac80211 callback context, the receive and
  status entry points, iterators: every reader got details wrong, and they
  matter to driver patches, but each asks for a list that needs 80 words or
  more and 600 words do not stretch to them. The wiphy mutex and wiphy work
  questions are kept because the oldest reader's picture of the locking is of
  a different kernel.
- Channel contexts, link activation, station states and lookup, the transmit
  control block, transmit queues, keys, restart: all partly wrong for all
  readers, all confined to one area each. They stay in the measurement set for
  a larger wireless guide.
- nl80211 commands and attributes, feature flags, BSS references, element
  parsing: the same. Element parsing is the one with security weight, and the
  readers' errors in it were about helper names and what the parser copies,
  not about the length checks.
- Operation wrappers and the change checklist: the adding-a-flag question is
  kept as the one most likely to be hit by a patch to this code.

Two kept questions differ from their measurement text. The core files
question asks only for the files named above. The question on the two
callbacks gained a sentence saying what to do on a tree that has only one.

Three questions were reworded in both files when the build set was resized,
and the numbers below are for the earlier wordings.
`wifi.change-flag-coverage` and `wifi.mlo-requirements` now ask for flag and
interface type names in full, because one builder had written MONITOR,
TXPOWER and HAS_RATE_CONTROL without the prefixes that make them names in the
tree. `wifi.new-change-flag` asked which in-tree driver should be updated
with a new flag, which took for granted that one should; it now asks whether
any has to be, and both builders answer that none does.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count. The last two rows were asked in a second run and are included in
the totals.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader A           78        31%      8     13   6.12 to 6.17
reader B          119        73%      0     34   6.10 to 6.12
reader C           84        26%     10      8   6.12 to 6.19

question                         reader A      reader B      reader C   verdict
wifi.core-files                   0% ( 0)      20% ( 5)       1% ( 2)   middling
wifi.object-model                 0% ( 0)      62% ( 6)       1% ( 1)   weak: reader B
wifi.protocol-headers            33% ( 1)      78% ( 2)       1% ( 1)   weak: reader B
wifi.docs-tests                   9% ( 1)      76% ( 2)      45% ( 2)   weak: reader B, reader C
wifi.wiphy-mutex                 31% ( 3)      75% ( 5)       7% ( 2)   weak: reader B
wifi.wiphy-work                  55% ( 2)      77% ( 3)      25% ( 3)   weak: reader A, reader B
wifi.cfg80211-ops-context        49% ( 3)      75% ( 2)      26% ( 3)   weak: reader A, reader B
wifi.mac80211-ops-context        43% ( 4)      87% ( 3)      32% ( 3)   weak: reader A, reader B
wifi.rx-tx-status-context        41% ( 2)      78% ( 3)      30% ( 1)   weak: reader A, reader B
wifi.iterators                   32% ( 4)      50% ( 3)      39% ( 3)   weak: reader B
wifi.ops-validation              41% ( 3)      79% ( 2)       0% ( 0)   weak: reader A, reader B
wifi.hw-flags                     0% ( 0)      87% ( 1)       2% ( 1)   weak: reader B
wifi.chanctx                     25% ( 2)      71% ( 2)      22% ( 1)   weak: reader B
wifi.change-callbacks             0% ( 0)      72% ( 3)      11% ( 3)   weak: reader B
wifi.change-flag-data            13% ( 1)      62% ( 2)       6% ( 1)   weak: reader B
wifi.change-flag-coverage        47% ( 3)      94% ( 2)      49% ( 2)   all weak
wifi.legacy-change-callback      46% ( 2)      89% ( 3)       9% ( 0)   weak: reader A, reader B
wifi.link-state                  37% ( 4)      77% ( 4)      30% ( 3)   weak: reader B
wifi.link-activation             32% ( 2)      82% ( 4)      29% ( 2)   weak: reader B
wifi.sta-state                   34% ( 3)      65% ( 4)       9% ( 2)   weak: reader B
wifi.sta-lookup                  42% ( 2)      58% ( 1)      56% ( 2)   all weak
wifi.tx-info                     11% ( 1)      84% ( 3)      54% ( 5)   weak: reader B, reader C
wifi.txq                         50% ( 3)      82% ( 4)      49% ( 3)   all weak
wifi.keys                        26% ( 3)      78% ( 3)      42% ( 5)   weak: reader B, reader C
wifi.hw-restart                  57% ( 4)      79% ( 5)      33% ( 3)   weak: reader A, reader B
wifi.nl80211-command             55% ( 3)      87% ( 6)      39% ( 2)   weak: reader A, reader B
wifi.nl80211-attrs               33% ( 1)      75% ( 2)      37% ( 3)   weak: reader B
wifi.feature-flags               44% ( 1)      75% ( 2)      49% ( 2)   all weak
wifi.bss-refs                    52% ( 3)      66% ( 3)      30% ( 4)   weak: reader A, reader B
wifi.element-parsing             25% ( 3)      53% ( 6)      17% ( 3)   weak: reader B
wifi.op-wrappers                 34% ( 3)      72% ( 7)      44% ( 5)   weak: reader B, reader C
wifi.new-change-flag             11% ( 2)      94% ( 3)      17% ( 2)   weak: reader B
wifi.change-checklist            17% ( 2)      54% ( 3)      33% ( 3)   weak: reader B
wifi.misplaced-flag-handling     28% ( 2)      77% ( 4)      37% ( 3)   weak: reader B
wifi.mlo-requirements            27% ( 5)      86% ( 6)      23% ( 3)   weak: reader B
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `wifi.sta-lookup`, `wifi.tx-info`, `wifi.hw-restart`, `wifi.nl80211-command`, `wifi.bss-refs`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `wifi.cfg80211-ops-context`, `wifi.mac80211-ops-context`, `wifi.rx-tx-status-context`, `wifi.chanctx`, `wifi.sta-state`, `wifi.nl80211-attrs`, `wifi.element-parsing`, `wifi.change-checklist`.
Put back because a guide has to say what each main structure is before anything else: `wifi.object-model`.

## Questions reorganised

By subject now, 27 questions as before, each a hazard, a contract or orientation. Subjects: BSS
change callbacks and flags; links and stations; driver registration and restart; locking and
callback context; data path; elements and scan results; nl80211. Nothing merged or dropped.
Narrowed: `wifi.change-checklist` from seven things a change must keep working to the wrapper,
tracepoint, simulated driver and kerneldoc of a changed callback; `wifi.chanctx` and
`wifi.sta-state` lost their lists of callbacks and states. `wifi.mac80211-ops-context` now also
asks which iterators need the wiphy mutex, and `wifi.change-callbacks` what a driver that tests a
flag in the wrong callback sees.
