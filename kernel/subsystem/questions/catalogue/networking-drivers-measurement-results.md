# What the networking-drivers measurement found

Three models were asked the 54 questions in `networking-drivers-measurement.md`
with no sources, and a checker that had the sources then corrected each answer
against a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and
C; which models they were does not matter here. Readers A and C said they
assumed kernels 6.12 to 6.17 and knew the per-device lock and the per-queue
statistics; reader C needed the fewest corrections. Reader B said 6.11 to 6.13
but answered from something older, and was wrong about fundamentals. The
hand-written guide was never checked against current sources, so differences
between it and the built guide are expected and are noted near the end.

Network drivers are a subject the two current readers know well in outline:
the transmit path, BQL, the skb free variants, the transmit watchdog and the
`u64_stats_sync` rules came back almost untouched. What all three got wrong is
what moved in the last few releases, and nearly all of it is about which lock
is held around a callback.

## What all three readers got wrong

- **Ethtool callbacks and `rtnl_lock`.** All three said `rtnl_lock` is held
  around every `struct ethtool_ops` callback, and two said no opt-in exists.
  For a driver whose callbacks run under the per-device lock the core holds
  only that lock; `rtnl_lock` is added for feature-changing ioctls and for the
  commands the driver names in `op_needs_rtnl` (`ETHTOOL_OP_NEEDS_RTNL_*`,
  decided in `net/ethtool/common.h`). The same mistake leaked into each
  reader's answers on feature updates, queue counts and the change checklist.
  This one changes a verdict: a callback that calls `netdev_update_features()`
  or a phylink helper needs the bit.
- **The address filter callback.** None knew `ndo_set_rx_mode_async`, which
  runs in process context under `rtnl_lock` and the ops lock with snapshots of
  the address lists and a retry on error. `register_netdevice()` warns when an
  ops-locked driver has only `ndo_set_rx_mode`, and for such drivers the old
  callback is itself deferred to the core work item.
- **Deferred work.** All three said the core has no such service.
  `net/core/netdev_work.c` has `netdev_work_sched()`, `netdev_work_cancel()`
  and the `ndo_work` callback, run under `rtnl_lock` and `netdev_lock_ops()`,
  and cancelled at unregistration.
- **An assertion helper that does not exist.** All three named
  netdev_ops_assert_locked(). The helpers are `netdev_assert_locked_ops()` and
  `netdev_assert_locked_ops_compat()` in `include/net/netdev_lock.h`.
- **Queue counts.** All said `netif_set_real_num_tx_queues()` and its receive
  twin need `rtnl_lock`. Both assert `netdev_assert_locked_ops_compat()`: the
  per-device lock for an ops-locked driver, `rtnl_lock` for the rest.
- **What the documentation forbids in driver-private ethtool strings.** All
  three stated a wide rule (nothing that has a per-queue, page pool or standard
  ethtool home) and a rule that old duplicates are grandfathered.
  `Documentation/networking/statistics.rst` rejects only counters that match a
  member of `struct rtnl_link_stats64`, reported through ethtool or debugfs,
  and only notes the history of the rest. It asks for a constant number of
  strings because a read takes several system calls. Nothing else in the tree
  says more.
- **Standard ethtool statistics and netlink.** The readers put the pause and
  FEC counters under `ETHTOOL_MSG_STATS_GET`. That message serves the eth-phy,
  eth-mac, eth-ctrl, rmon and phy groups; pause, FEC, MAC merge, timestamping
  and link counters come back in their own get messages when
  `ETHTOOL_FLAG_STATS` is set.
- **The transmit watchdog's lock.** `dev_watchdog()` takes `tx_global_lock`
  and freezes the queues itself; it does not call `netif_tx_lock()`, and one
  reader had it running from a work item. For `TC_SETUP_BLOCK` and
  `TC_SETUP_FT` the lock is `cb_lock` or `flow_block_lock` and `rtnl_lock` may
  or may not be held.
- **Two counters read in one loop.** Every reader said they are a consistent
  pair on a 32-bit build. The header promises no consistency between counters.
- **A failed registration.** `priv_destructor` runs only on the error paths
  after `ndo_init` has succeeded, and `needs_free_netdev` never frees a device
  whose registration failed: the caller always calls `free_netdev()`.
- **A poll that returns more than its budget** gets `netdev_err_once()`, not a
  WARN, and `napi_complete_done()` also returns false when netpoll owns the
  instance or a deferral timer is armed.
- **Hardware timestamping.** Without `ndo_hwtstamp_get` and `ndo_hwtstamp_set`
  the ioctl returns `-EOPNOTSUPP`; nothing falls back to `ndo_eth_ioctl`.
- **Netdev conventions.** Each reader hardened what
  `Documentation/process/maintainer-netdev.rst` says: `devm_` helpers are
  acceptable but not preferred, `guard()` is discouraged only in functions over
  twenty lines, direct `__free()` is discouraged in core and drivers, and
  clean-up patches are discouraged only outside other work. The
  `SIOCDEVPRIVATE` rule is in `Documentation/networking/netdevices.rst`.

## What only some readers got wrong

Reader B, and nobody else:

- `netif_running()` is still true inside `ndo_stop`. `__dev_close_many()`
  clears `__LINK_STATE_START` before it calls the driver. This one would change
  a verdict.
- `ndo_start_xmit` runs with no core lock. It runs under the queue's
  `_xmit_lock` through `HARD_TX_LOCK()` unless `lltx` is set, and that is a bit
  in `struct net_device`; NETIF_F_LLTX is gone.
- A second `napi_disable()` is safe and none of the NAPI control calls take a
  lock. The second call sleeps for ever, `napi_enable_locked()` has a
  `BUG_ON()`, and the plain add, enable, disable and delete calls all take
  `netdev_lock()`.
- Drivers opt in to the per-device lock through netdev_lock_ops_to_holder(),
  which does not exist. The opt-in is `request_ops_lock`, or providing
  `queue_mgmt_ops` or `net_shaper_ops`.
- On a 64-bit build `u64_stats_update_begin_irqsave()` disables interrupts, a
  raw spinlock variant exists on `PREEMPT_RT`, and `u64_stats_t` wraps a plain
  `u64`. None is so: the irqsave helper returns 0, the sync object is empty,
  and the counter is a `local64_t`.
- del_timer_sync(), xdp_do_flush_map(), page_pool_return_skb_page() and a
  transmit queueing document that are not in this tree. The timer call is
  `timer_delete_sync()`.
- The per-queue statistics structures are zeroed on entry. They are filled
  with 0xff and a field left alone is not reported, so writing 0 reports a
  zero. Reader A had this wrong too.
- The lockless stop and wake macros are in `include/linux/netdevice.h`. They
  are in `include/net/netdev_queues.h`.

Readers A and B:

- Per-queue statistics callbacks run under `rtnl_lock`. For an ops-locked
  driver it is the per-device lock instead.
- Rtnetlink callers of `ndo_get_stats64` hold `rtnl_lock`. The `RTM_GETLINK`
  handler is unlocked; only RCU is guaranteed.
- `napi_enable()` does not sleep (reader A). It takes a mutex.

Readers A and C:

- The store handlers in `net/core/net-sysfs.c` as the model use of
  `rtnl_trylock()` with `restart_syscall()`. That file now goes through
  `sysfs_rtnl_lock()` and `rtnl_lock_interruptible()`; the trylock form
  survives in `net/bridge/br_sysfs_br.c` and the bonding options.
- Capability members cap_rss_ctx_supported and cap_rss_sym_xor_supported,
  which `struct ethtool_ops` no longer has.

## What the readers already knew

Readers A and C, with little or nothing to correct: the transmit return codes
and who owns the skb, the stop and wake race and the macros that solve it, BQL,
the skb free variants, the transmit watchdog, zero-budget polls, the writer and
reader rules for `u64_stats_sync` including the lockdep assertion behind
`preempt_disable_nested()`, the absence of the old fetch variants for interrupt
context, `DEV_STATS_INC()`, flags used as locks, and the timer and work
function names. All three knew that a field of a standard ethtool statistics
structure a driver does not support must be left at `ETHTOOL_STAT_NOT_SET`,
and that `ndo_get_stats64` cannot sleep.

## Where the hand-written guide is stale

- It names del_timer_sync(), which is not in the tree; the call is
  `timer_delete_sync()`, and `timer_shutdown_sync()` and `disable_work_sync()`
  also stop re-arming.
- It says writers must run with preemption disabled and leaves it there. The
  begin helper now calls `preempt_disable_nested()`, which disables preemption
  itself on `PREEMPT_RT` and asserts it through lockdep elsewhere, on 32-bit
  builds only.
- Its rule that nothing with a standard interface may appear in `ethtool -S`
  is wider than anything written in the tree (see above). That is maintainer
  practice; a built guide can only give what `statistics.rst` says and list the
  standard interfaces so that a reviewer can see when a private string has
  another home.
- Its trylock rule allows one correct form, a work item that reschedules
  itself. The tree has another, `rtnl_trylock()` followed by
  `restart_syscall()` in sysfs store handlers.
- Its example of a broken reader and writer protocol on bits (set a
  reading-statistics bit, test an open bit, clear on exit) is the handshake
  `bnxt_get_stats64()` and `__bnxt_close_nic()` use in this tree, and the
  checker offered that code as a correct example. The guide's objection, that
  the first of two concurrent readers to leave clears the bit for both, applies
  to it. The question on flags was sharpened after the measurement to ask what
  happens with two CPUs in the region at once, and the question on callbacks
  while down to ask when a test of `netif_running()` is not enough.
- Its `REPORT as bugs` paragraphs tell a reviewer what to report. The questions
  ask for unsafe usage and the correct usage that looks like it.
- It has no map of the subject and nothing on which lock a callback runs
  under, which is where every reader was out of date.

## What was left out of the build set and why

The hand-written guide is 1,016 words, so nineteen questions fit. They were
chosen by what readers got wrong and by what the old guide was for: the lock
and context of callbacks, the counters and how they are reported, and
home-made synchronization.

- Left out because readers A and C needed little or no correction: the whole
  transmit section, zero-budget polls, NAPI scheduling and access after
  completion, the 64-bit counter types and their initialisation, the `stats`
  member, persistence of counters, and the standard ethtool statistics
  callbacks.
- Left out for room although readers were wrong: freeing after a failed
  registration, the poll return value, core-allocated per-CPU statistics, the
  page pool and XDP questions, queue management callbacks, queue counts,
  feature flags, the ethtool capability members, extack, timestamping, deferred
  work, the conventions and the checklist. Several of their corrections are
  about the same lock rules the build set does ask for.
- The file table is kept, shorter, as a pointer; the documentation list is
  dropped because the table of callback contexts starts from the same file.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader A           98        29%     14     13   6.12 to 6.17
reader B          115        72%      0     53   6.11 to 6.13
reader C           79        20%     26      7   6.12 to 6.17

question                           reader A      reader B      reader C   verdict
netdrv.core-files                   4% ( 1)      71% ( 4)       1% ( 1)   weak: reader B
netdrv.docs                        16% ( 1)      17% ( 1)       0% ( 2)   middling
netdrv.selftests                   14% ( 0)      85% ( 2)      23% ( 2)   weak: reader B
netdrv.alloc-register               0% ( 0)      59% ( 3)      15% ( 2)   weak: reader B
netdrv.free-rules                  25% ( 3)      70% ( 3)      17% ( 3)   weak: reader B
netdrv.open-stop                   12% ( 1)      75% ( 3)      22% ( 2)   weak: reader B
netdrv.ndo-contexts                25% ( 7)      55% ( 8)      20% ( 3)   weak: reader B
netdrv.instance-lock               30% ( 1)      81% ( 2)      10% ( 1)   weak: reader B
netdrv.lock-helpers                27% ( 1)      84% ( 2)      15% ( 2)   weak: reader B
netdrv.ethtool-locking             59% ( 2)      84% ( 2)      64% ( 2)   all weak
netdrv.rx-mode                     67% ( 1)      89% ( 1)      72% ( 1)   all weak
netdrv.stats-callback-context      19% ( 1)      78% ( 1)       0% ( 0)   weak: reader B
netdrv.ops-while-down              20% ( 1)      62% ( 1)      35% ( 1)   weak: reader B
netdrv.deferred-work               93% ( 1)      98% ( 1)      91% ( 1)   all weak
netdrv.napi-control                40% ( 6)      74% ( 5)      11% ( 1)   weak: reader A, reader B
netdrv.napi-poll-contract          32% ( 3)      66% ( 1)      39% ( 3)   weak: reader B
netdrv.napi-budget-zero            17% ( 2)      67% ( 1)      26% ( 1)   weak: reader B
netdrv.napi-after-complete          9% ( 1)      51% ( 1)       2% ( 1)   weak: reader B
netdrv.napi-scheduling             14% ( 2)      57% ( 1)       0% ( 0)   weak: reader B
netdrv.napi-queue-linking          43% ( 2)      80% ( 1)      33% ( 1)   weak: reader A, reader B
netdrv.xmit-return                 28% ( 1)      65% ( 3)       0% ( 0)   weak: reader B
netdrv.queue-stop-wake             45% ( 3)      74% ( 1)       0% ( 0)   weak: reader A, reader B
netdrv.bql                         10% ( 1)      62% ( 1)       0% ( 0)   weak: reader B
netdrv.xmit-context                16% ( 2)      64% ( 1)       0% ( 0)   weak: reader B
netdrv.skb-free-variants            5% ( 0)      74% ( 1)       0% ( 0)   weak: reader B
netdrv.tx-timeout                   8% ( 0)      69% ( 1)       0% ( 0)   weak: reader B
netdrv.page-pool-rules             31% ( 1)      77% ( 3)      28% ( 3)   weak: reader B
netdrv.skb-recycle                 17% ( 1)      75% ( 2)      35% ( 2)   weak: reader B
netdrv.page-pool-dma-sync          34% ( 1)      78% ( 2)       8% ( 1)   weak: reader B
netdrv.xdp-driver-duties           10% ( 1)      71% ( 1)      11% ( 1)   weak: reader B
netdrv.queue-mgmt-ops              33% ( 3)      66% ( 3)      27% ( 2)   weak: reader B
netdrv.u64-stats-types             15% ( 1)      68% ( 4)      20% ( 3)   weak: reader B
netdrv.u64-stats-writers           15% ( 2)      86% ( 2)       0% ( 0)   weak: reader B
netdrv.u64-stats-irq               33% ( 1)      68% ( 2)       4% ( 1)   weak: reader B
netdrv.u64-stats-readers           18% ( 1)      74% ( 1)       0% ( 0)   weak: reader B
netdrv.u64-stats-init              21% ( 1)      80% ( 2)      32% ( 2)   weak: reader B
netdrv.core-pcpu-stats             17% ( 2)      82% ( 5)      20% ( 4)   weak: reader B
netdrv.dev-stats-field             22% ( 1)      72% ( 1)      29% ( 2)   weak: reader B
netdrv.stats-interfaces            17% ( 3)      40% ( 1)      15% ( 2)   weak: reader B
netdrv.ethtool-private-stats       72% ( 2)      79% ( 1)      55% ( 1)   all weak
netdrv.ethtool-std-stats           27% ( 2)      68% ( 1)      26% ( 1)   weak: reader B
netdrv.queue-stats                 54% ( 4)      88% ( 1)      14% ( 1)   weak: reader A, reader B
netdrv.stats-persistence           46% ( 1)      79% ( 1)      38% ( 1)   weak: reader A, reader B
netdrv.flag-synchronization         8% ( 1)      90% ( 4)       7% ( 1)   weak: reader B
netdrv.trylock-usage                8% ( 1)      74% ( 1)       3% ( 1)   weak: reader B
netdrv.timer-work-teardown         27% ( 3)      75% ( 2)       4% ( 1)   weak: reader B
netdrv.reset-task                  31% ( 2)      86% ( 0)      14% ( 1)   weak: reader B
netdrv.features                    27% ( 4)      62% ( 4)      18% ( 3)   weak: reader B
netdrv.queue-count                 30% ( 2)      77% ( 2)      16% ( 1)   weak: reader B
netdrv.ethtool-ops-validation      37% ( 3)      75% ( 3)      41% ( 1)   weak: reader B, reader C
netdrv.extack-errors               52% ( 1)      79% ( 1)      43% ( 1)   all weak
netdrv.hwtstamp                    59% ( 2)      77% ( 1)      49% ( 1)   all weak
netdrv.netdev-conventions          81% ( 3)      86% ( 4)      35% ( 3)   weak: reader A, reader B
netdrv.change-checklist            57% ( 4)      54% ( 8)      23% ( 8)   weak: reader A, reader B
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `netdrv.change-checklist`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `netdrv.alloc-register`, `netdrv.free-rules`, `netdrv.napi-poll-contract`, `netdrv.napi-budget-zero`, `netdrv.xmit-return`, `netdrv.queue-stop-wake`, `netdrv.bql`, `netdrv.xmit-context`, `netdrv.skb-free-variants`, `netdrv.page-pool-rules`, `netdrv.skb-recycle`, `netdrv.xdp-driver-duties`, `netdrv.u64-stats-types`, `netdrv.core-pcpu-stats`, `netdrv.dev-stats-field`, `netdrv.ethtool-std-stats`.

## Questions reorganised

By subject now, 38 questions as before, each a hazard, a contract or orientation. Subjects: locks
and callback context; device lifetime and teardown; NAPI; transmit; receive buffers and XDP;
counters that do not tear; reporting statistics; home-made synchronization.
Merged: what the statistics structures hold on entry, asked twice in `netdrv.queue-stats` and
`netdrv.ethtool-std-stats`, is one question, `netdrv.stats-unset-fields`; `netdrv.queue-stats`
keeps the base callback, the lock and the queue count. Nothing dropped whole. Narrowed:
`netdrv.change-checklist` from six concurrent paths to the transmit watchdog and netpoll, the rest
being asked in the callback-context questions; `netdrv.rx-mode` now also asks for the deferred work.
