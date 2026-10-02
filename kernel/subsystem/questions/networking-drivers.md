# Questions: Networking Drivers

- guide: networking-drivers.md
- title: Networking Drivers

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name.
`catalogue/networking-drivers-measurement.md` is the wider set the readers were measured on and
`catalogue/networking-drivers-measurement-results.md` says what they got wrong. No number says how
long an answer or the guide should be. Format: `../../docs/subsystem-questions.md`.

# Main structures

## netdrv.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## netdrv.core-files: Core files

- section: Finding your way
- relevance: 4 - the driver-facing API is spread over a dozen headers

A table and nothing else, job to file: the `struct net_device_ops` and `struct ethtool_ops`
definitions; NAPI; the per-queue statistics and queue management callbacks; the helpers for the
per-device lock; the lockless transmit queue stop and wake macros; the page pool; the XDP driver
helpers; the 64-bit statistics helpers; the core's deferred work for drivers; the software
driver used for testing. Where a reader is likely to look in a file that does not hold it in
this tree, say so in the row. Start from `include/linux/netdevice.h` and `net/core/`.

# Locks and callback context

## netdrv.instance-lock: Per-device lock

- section: Locks and callback context
- relevance: 5 - decides what a driver may assume is held in every callback

What does the lock inside `struct net_device` protect by itself, for which drivers does the core
hold it around the driver's callbacks and how does a driver come to be one of them, and how does
it order against `rtnl_lock`? Start from `netdev_need_ops_lock()` and the comment on the `lock`
member in `include/linux/netdevice.h`.

## netdrv.lock-helpers: Lock helper families

- section: Locks and callback context
- relevance: 4 - the wrong variant deadlocks or runs unlocked

Which helpers take the per-device lock unconditionally, which take it only for drivers whose
callbacks run under it, and which fall back to `rtnl_lock`, the assertion helpers included? What
does the difference between a core function such as `dev_open()` and its twin `netif_open()` tell
a driver about locking, and which lock do `netif_set_real_num_tx_queues()` and
`netif_set_real_num_rx_queues()` expect? Start from `include/net/netdev_lock.h`.

## netdrv.ndo-contexts: Callback contexts

- section: Locks and callback context
- relevance: 5 - sleeping in the wrong callback is the commonest driver bug

For `ndo_open`, `ndo_stop`, `ndo_start_xmit`, `ndo_tx_timeout`, `ndo_get_stats64`,
`ndo_set_rx_mode`, `ndo_change_mtu` and `ndo_setup_tc`, which lock does the core hold and may
the callback sleep? A table, with what differs for a driver whose callbacks run under the
per-device lock. Start from `Documentation/networking/netdevices.rst`.

## netdrv.ethtool-locking: Ethtool callback locking

- section: Locks and callback context
- relevance: 4 - a driver can no longer assume rtnl_lock in every ethtool op

Which locks does the core hold around a `struct ethtool_ops` callback, and does that depend on the
driver? How does a driver whose callback needs `rtnl_lock` get it?

## netdrv.rx-mode: Address filter callback

- section: Locks and callback context
- relevance: 4 - drivers that must talk to firmware cannot do it here

In what context does the core call `ndo_set_rx_mode`, and may the callback sleep? What does the
core provide for a driver that has to sleep to program its filters, and what does
`register_netdevice()` check about a driver's address filter callbacks? Start from
`ndo_set_rx_mode` in `include/linux/netdevice.h`.

## netdrv.deferred-work: Deferred work for drivers

- section: Locks and callback context
- relevance: 4 - work that a driver defers by itself runs without the locks its other callbacks rely on

What does the core provide for a driver that has deferred work to run under the core's locks, and
which locks does that work run under? Start from `netdev_work_sched()`.

## netdrv.stats-callback-context: Statistics callback context

- section: Locks and callback context
- relevance: 5 - sleeping or taking a mutex here has shipped many times

What do the callers that reach `ndo_get_stats64` through `dev_get_stats()` hold that a driver can
rely on? May the callback sleep, and can it run while the device is being closed?

## netdrv.stats-sleeping-reads: Sleeping counter reads

- section: Locks and callback context
- relevance: 5 - a driver that must sleep to read its counters needs a way that does not sleep in the callback

What does `Documentation/networking/statistics.rst` say a driver should do when reading its
counters from the device can sleep? Start from the notes for driver authors in
`Documentation/networking/statistics.rst`.

# Device lifetime and teardown

## netdrv.alloc-register: Allocation and registration

- section: Device lifetime and teardown
- relevance: 4 - the device is live the moment it is registered

Which of the calls that register and unregister a `struct net_device` expect the caller to hold
`rtnl_lock` already and which take it themselves, and what must a driver have finished before it
registers? Start from `alloc_etherdev_mqs()` and `register_netdev()`.

## netdrv.free-rules: Freeing a net_device

- section: Device lifetime and teardown
- relevance: 4 - double frees and leaks on the error path

Who frees a `struct net_device` and its private area after unregistering and after a failed
registration, and how do `needs_free_netdev` and `priv_destructor` change that in each case? What
are the requirements for using `netdev_priv()` data around `free_netdev()` in order to assure safe
usage?

## netdrv.timer-work-teardown: Stopping timers and work

- section: Device lifetime and teardown
- relevance: 4 - the function names changed and the old ones are gone

Which functions in `include/linux/timer.h` and `include/linux/workqueue.h` stop a timer or a work
item and wait for a running instance, and which of them also prevent it from being queued again?
When must a driver call them relative to freeing its rings and unregistering the device? Start
from `include/linux/timer.h` and `include/linux/workqueue.h`.

## netdrv.change-checklist: Watchdog and netpoll against teardown

- section: Device lifetime and teardown
- relevance: 4 - the paths a test on an idle link does not reach

When a driver's stop, reset or ring reconfiguration path frees or replaces its rings, what does
the core guarantee about the transmit watchdog and about netpoll running against it, which lock
does each of those take, and what is left to the driver?

## netdrv.ops-while-down: Callbacks on a closed device

- section: Device lifetime and teardown
- relevance: 4 - rings freed in stop and dereferenced from ethtool or stats

Which kinds of driver callback can the core invoke while the interface is down or between
`ndo_stop` and the next `ndo_open`? What are the requirements for such a callback that reads
per-ring memory, in order to assure safe usage? What does `netif_running()` return inside
`ndo_stop`?

## netdrv.reset-task: Reset work against close

- section: Device lifetime and teardown
- relevance: 4 - a deadlock between rtnl_lock and cancel_work_sync recurs in drivers

A driver's reset work item takes `rtnl_lock`, and its `ndo_stop` has to stop that work. What are
the requirements for the reset work and for the close path in order to assure that the two do not
deadlock? Name one in-tree driver that meets them.

# NAPI

## netdrv.napi-control: NAPI control calls

- section: NAPI
- relevance: 5 - a repeated or misordered call hangs or crashes

In what state does `netif_napi_add()` leave a new NAPI instance, and which of `napi_enable()`,
`napi_disable()` and `netif_napi_del()` sleep or take a lock themselves? When must a driver use a
variant such as `napi_enable_locked()`? Start from `napi_disable()` in `net/core/dev.c`.

## netdrv.napi-repeated-calls: Repeated enable or disable

- section: NAPI
- relevance: 5 - a second call in a row hangs or crashes, and an error path is where it happens

What happens when `napi_enable()` or `napi_disable()` is called twice in a row for the same
instance? Start from `napi_disable()` in `net/core/dev.c`.

## netdrv.napi-poll-contract: Poll return value

- section: NAPI
- relevance: 5 - returning the wrong count stalls or double-schedules the queue

What must a poll function return when it has more work, when it has finished, and when it has done
exactly the budget? What does a false return from `napi_complete_done()` mean, and when may the
driver unmask its interrupt?

## netdrv.napi-budget-zero: Zero budget polls

- section: NAPI
- relevance: 4 - netpoll calls this way with interrupts off

When is a poll function called with a budget of zero, and what are the requirements for what it
does in that call in order to assure safe usage? How does `napi_consume_skb()` use the budget it
is given?

# Transmit

## netdrv.xmit-context: Transmit context and locking

- section: Transmit
- relevance: 4 - decides which skb free call and which lock type are legal

In what contexts can `ndo_start_xmit` run, and what serialises two calls for the same queue? Start
from `HARD_TX_LOCK()` in `net/core/dev.c`.

## netdrv.xmit-lock-opt-out: Lockless transmit opt-out

- section: Transmit
- relevance: 4 - a driver that opts out must serialise its transmit routine itself

How does a driver opt out of the core's serialisation of `ndo_start_xmit`, and which drivers is
opting out meant for? Start from `HARD_TX_LOCK()` in `net/core/dev.c`.

## netdrv.xmit-return: Transmit return codes

- section: Transmit
- relevance: 5 - the wrong code after freeing or queuing the skb is a double free

Who owns the skb after each value that `ndo_start_xmit` may return, and which value must a driver
return after it drops the packet? What does `Documentation/networking/driver.rst` say about
returning `NETDEV_TX_BUSY`?

## netdrv.skb-free-variants: Freeing skbs in a driver

- section: Transmit
- relevance: 4 - the wrong variant warns in hard interrupt context or pollutes drop tracing

Which calls should a driver use to free an skb in the transmit routine, in a hard interrupt
handler, in NAPI completion and on an error path, and what is the difference between the
variants that mean "dropped" and those that mean "consumed"? Start from `dev_kfree_skb_any()`.

## netdrv.bql: Byte queue limits

- section: Transmit
- relevance: 4 - an unbalanced count stalls the queue for good

What must balance between the calls that report bytes queued and bytes completed to the core,
and what must a driver do when it discards a ring's pending packets during a reset or stop?
Start from `netdev_tx_sent_queue()`.

## netdrv.queue-stop-wake: Stopping and waking queues

- section: Transmit
- relevance: 5 - a lost wake-up hangs the queue until the watchdog fires

Which race between a transmit routine that stops its queue when the ring fills and a completion
handler that wakes it do the macros in `include/net/netdev_queues.h` close? What do those macros
require of the ring indexes and of where each side is called from? Start from
`include/net/netdev_queues.h`.

# Receive buffers and XDP

## netdrv.page-pool-rules: Page pool usage

- section: Receive buffers and XDP
- relevance: 4 - the lockless fast path rests on a rule the API cannot check

What does setting the `napi` member of `struct page_pool_params` promise, from which context may
a driver recycle a page directly into the pool's cache, and what must happen before a pool is
destroyed? Start from `Documentation/networking/page_pool.rst`.

## netdrv.skb-recycle: Recycling pages through skbs

- section: Receive buffers and XDP
- relevance: 4 - forgetting it leaks DMA mappings, doing it twice corrupts the pool

How does an skb built on a page pool page return the page to the pool when it is freed, what
does the driver have to call for that, and what happens to the page and its DMA mapping if it
does not? Start from `skb_mark_for_recycle()`.

## netdrv.xdp-driver-duties: XDP in a receive path

- section: Receive buffers and XDP
- relevance: 4 - each verdict has an obligation and redirect has a flush

What must a driver that runs XDP programs do with the buffer for each verdict a program returns,
what must it call before its poll function ends if any packet was redirected, and what does it
have to register per receive queue first? Start from `xdp_rxq_info_reg()` and `xdp_do_flush()`.

# u64_stats counters

## netdrv.u64-stats-types: 64-bit counter helpers

- section: u64_stats counters
- relevance: 4 - the helpers behave differently on 32-bit and 64-bit builds

What do `struct u64_stats_sync` and `u64_stats_t` turn into on a 64-bit build and on a 32-bit
build, what do the update, fetch and read helpers compile to on each, and what do they
guarantee about two counters read in one loop? Start from `include/linux/u64_stats_sync.h`.

## netdrv.u64-stats-irq: Writers and interrupt context

- section: u64_stats counters
- relevance: 4 - the deadlock needs an interrupt at the wrong instruction

When must a writer use `u64_stats_update_begin_irqsave()`, what does that variant do on each
word size, and is there a separate reader variant for interrupt or bottom-half context in this
tree?

## netdrv.u64-stats-writers: Writer exclusion and preemption

- section: u64_stats counters
- relevance: 5 - a violation hangs readers forever, and only on 32-bit

What are the requirements for the code between `u64_stats_update_begin()` and
`u64_stats_update_end()`, with respect to other writers and to preemption, in order to assure safe
usage? What does `u64_stats_update_begin()` itself check or do about preemption, including on
`PREEMPT_RT`?

## netdrv.u64-stats-readers: Reader loops

- section: u64_stats counters
- relevance: 4 - a retry runs the loop body again

What are the requirements for the body of a loop between `u64_stats_fetch_begin()` and
`u64_stats_fetch_retry()` in order to assure safe usage? Name in-tree code that sums per-CPU
counters and meets them.

# Reporting statistics

## netdrv.stats-interfaces: Statistics interfaces

- section: Reporting statistics
- relevance: 5 - each kind of counter has one right home

A table of the interfaces a driver chooses between for reporting counters (the link statistics,
per-queue statistics, the standard ethtool groups, page pool statistics, driver-private
strings): which callback or structure feeds each, and how user space reads it, including which
netlink message carries which standard group. Start from
`Documentation/networking/statistics.rst`.

## netdrv.core-pcpu-stats: Core-allocated per-CPU statistics

- section: Reporting statistics
- relevance: 4 - drivers still hand-roll what the core now allocates and reports

What does setting `pcpu_stat_type` on a `struct net_device` make the core do for the driver, and
in what order does `dev_get_stats()` choose between the driver's callbacks, these and
`dev->stats`? What does the core add on top of whatever the driver reports?

## netdrv.queue-stats: Per-queue statistics

- section: Reporting statistics
- relevance: 4 - the contract on totals and on the lock is unusual

For the callbacks in `struct netdev_stat_ops`, what is the base callback for, which lock is held
when they run and does that depend on the driver, and what should happen to per-queue counters
when the number of queues changes?

## netdrv.stats-unset-fields: Unsupported counter fields

- section: Reporting statistics
- relevance: 4 - zeroing the structure reports counters the device does not have

What do the fields hold on entry to the callbacks of `struct netdev_stat_ops` and to the `struct
ethtool_ops` callbacks that report standards-defined hardware counters, and what must a driver do
with a field it does not support? Are the standards-defined counters meant to be kept by software
or by the device?

## netdrv.ethtool-private-stats: Driver-private ethtool statistics

- section: Reporting statistics
- relevance: 5 - maintainers reject duplicates of standard counters

What does the documentation say may not be reported through `get_ethtool_stats` and `get_strings`,
and how does it treat counters that were reported that way before a standard interface existed?
What does it ask of the number of strings over time, and why? Start from the notes for driver
authors in `Documentation/networking/statistics.rst`.

## netdrv.dev-stats-field: The stats member of net_device

- section: Reporting statistics
- relevance: 4 - plain increments from several CPUs lose counts and trip KCSAN

What are the requirements for updating the `stats` member of `struct net_device` when several CPUs
can update it, in order to assure safe usage, and what do the macros for that case cost? Which
drop counters does the core keep for the driver, so that the driver should not count them itself?
Start from `DEV_STATS_INC()` and `DEV_CORE_STATS_INC()`.

# State bits, atomics and trylock

## netdrv.flag-synchronization: Flags and atomics as locks

- section: State bits, atomics and trylock
- relevance: 5 - invisible to lockdep and nearly always racy

What are the requirements for using a flag or a counter in place of a lock to keep two driver
paths from touching the same data, in order to assure safe usage? What makes the core's uses of
`__LINK_STATE_START` and `NAPI_STATE_SCHED` correct? Start from `__LINK_STATE_START` and
`NAPI_STATE_SCHED`.

## netdrv.trylock-usage: Trylock patterns

- section: State bits, atomics and trylock
- relevance: 3 - a retry loop around trylock hides a lock ordering problem

What are the requirements for calling a trylock function such as `spin_trylock()` or
`rtnl_trylock()` in a driver, in order to assure safe usage? Name in-tree code that shows it.

# Model gaps

## netdrv.model-gaps: Other mistakes models make

- drafts: all
- relevance: 5 - a model that is told how it is wrong can correct for it

Going by what each reader said from memory for every question in this guide, which is given
below, what do models believe about this code that is wrong in this tree? One bullet per mistake:
the belief, put plainly as a model would hold it, then what is true here and where to see it.
Cover names that are gone and what does the job now, numbers and limits that have changed,
behaviour that has changed, rules the readers state more broadly than the code supports, and what
is new that none of them knew. Most consequential first: a belief that would make a reviewer
approve a bug or reject correct code comes before a file that moved. Leave out what the readers
had right, and a slip only one of them made that the others show is not a belief. One or two lines to
a bullet: the belief and the truth. Every section of this guide already corrects what models
get wrong about its subject, and what a section covers is taken out of this list afterwards, so what
matters most here is what no question above asks about.
