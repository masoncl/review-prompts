- `HARD_TX_LOCK()`: defined in `include/linux/netdevice.h`; it takes
  `txq->_xmit_lock` only when `dev->lltx` is clear.
- Callers of the transmit routine: search for `HARD_TX_LOCK` and
  `netdev_start_xmit`; besides the qdisc path, `__dev_queue_xmit()` and
  netpoll there are, for example, `__dev_direct_xmit()`, `generic_xdp_tx()`,
  `xfrm_dev_resume()` and pktgen.
- netpoll, direct path: `__netpoll_send_skb()` retries `HARD_TX_TRYLOCK()` for
  up to one tick, polling the device between tries.
- netpoll, deferred path: on failure the skb goes to `npinfo->txq`, and
  `queue_process()` (a work item) sends it with `HARD_TX_LOCK()` inside
  `local_irq_save()`.
- Qdisc exclusion: there is no __QDISC_STATE_RUNNING here; `qdisc_run_begin()`
  in `include/net/sch_generic.h` uses the `running` field of `struct Qdisc`,
  or `spin_trylock()` on `seqlock` for a `TCQ_F_NOLOCK` qdisc.
- Same-CPU recursion check: `netif_tx_owned()`; on the transmit path it is
  called only in the branch of `__dev_queue_xmit()` for a qdisc with no
  `enqueue`.
- `netif_tx_owned()` under `CONFIG_PREEMPT_RT`: compares `rt_mutex_owner()` of
  `_xmit_lock` with `current`, not `xmit_lock_owner` with the CPU.
- `netif_tx_lock()` in `net/sched/sch_generic.c`: holds only
  `dev->tx_global_lock` on return; `netif_freeze_queues()` takes and drops
  each `_xmit_lock` just to set `__QUEUE_STATE_FROZEN`.
