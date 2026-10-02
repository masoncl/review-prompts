# Questions: Networking Drivers (measurement set)

- guide: networking-drivers.md
- title: Networking Drivers

A wide set of questions about what a network device driver owes the core:
device lifetime, which lock and context each callback runs in, NAPI, the
transmit and receive paths, statistics and the home-made synchronization
drivers grow. It is used to measure what a model already knows before deciding
what the built guide should spend its words on. The hand-written guide it will
replace is 1,016 words and covers only statistics and ad-hoc synchronization.
Sockets, skbs and protocols belong to `networking-core`. Format:
`../../../docs/subsystem-questions.md`.

# The subsystem

## netdrv.core-files: Core files

- section: Finding your way
- relevance: 4 - the driver-facing API is spread over a dozen headers
- words: 110

Which files hold the `struct net_device_ops` and `struct ethtool_ops`
definitions, NAPI, the per-queue statistics and queue management callbacks,
the helpers for the per-device lock, the lockless transmit queue stop and wake
macros, the page pool, the XDP driver helpers, the 64-bit statistics helpers
and the software driver used for testing? A table. Start from
`include/linux/netdevice.h` and `net/core/`.

## netdrv.docs: Authoritative documentation

- section: Finding your way
- relevance: 4 - several rules for drivers are written down only there
- words: 80

Which files under `Documentation/networking/` and `Documentation/process/` are
the authority on the lock and context of each driver callback, on statistics,
on NAPI, on the transmit path, on the page pool, on feature flags and on what
the networking maintainers accept?

## netdrv.selftests: Driver selftests

- section: Finding your way
- relevance: 3 - a driver change is expected to pass them
- words: 60

Where are the selftests that exercise network drivers, which of them need real
hardware and which run against the software test driver, and what library do
they share? Start from `tools/testing/selftests/drivers/net/`.

# Device lifetime

## netdrv.alloc-register: Allocation and registration

- section: Lifetime of a net_device
- relevance: 4 - the device is live the moment it is registered
- words: 70

Which calls allocate and register a `struct net_device`, which of them expect
the caller to hold `rtnl_lock` already, and what must a driver have finished
before it registers? Start from `alloc_etherdev_mqs()` and
`register_netdev()`.

## netdrv.free-rules: Freeing a net_device

- section: Lifetime of a net_device
- relevance: 4 - double frees and leaks on the error path
- words: 80

Who frees a `struct net_device` and its private area after unregistering and
after a failed registration, and how do `needs_free_netdev` and
`priv_destructor` change that? What usage of `netdev_priv()` data around
`free_netdev()` is unsafe?

## netdrv.open-stop: Open and stop obligations

- section: Lifetime of a net_device
- relevance: 3 - what the core assumes once stop has returned
- words: 60

What must be true of the hardware and of in-flight packets once `ndo_stop`
returns, what does `netif_running()` report inside it, and when does the core
call it without the user asking?

# Locks and contexts

## netdrv.ndo-contexts: Callback contexts

- section: Which lock, which context
- relevance: 5 - sleeping in the wrong callback is the commonest driver bug
- words: 120

For `ndo_open`, `ndo_stop`, `ndo_start_xmit`, `ndo_tx_timeout`,
`ndo_get_stats64`, `ndo_set_rx_mode`, `ndo_change_mtu` and `ndo_setup_tc`,
which lock does the core hold and may the callback sleep? A table. Start from
`Documentation/networking/netdevices.rst`.

## netdrv.instance-lock: Per-device lock

- section: Which lock, which context
- relevance: 5 - decides what a driver may assume is held in every callback
- words: 90

What is the lock inside `struct net_device`, what does it protect by itself,
for which drivers does the core hold it around the driver's callbacks, and how
does a driver ask for that? How does it order against `rtnl_lock`? Start from
`netdev_need_ops_lock()` and the comment on the `lock` member in
`include/linux/netdevice.h`.

## netdrv.lock-helpers: Lock helper families

- section: Which lock, which context
- relevance: 4 - the wrong variant deadlocks or runs unlocked
- words: 80

Which helpers take the per-device lock unconditionally, which take it only for
drivers whose callbacks run under it, and which fall back to `rtnl_lock`? What
does the difference between a core function named with a `dev_` or `netdev_`
prefix and its `netif_` twin tell a driver about locking? Start from
`include/net/netdev_lock.h`.

## netdrv.ethtool-locking: Ethtool callback locking

- section: Which lock, which context
- relevance: 4 - a driver can no longer assume rtnl_lock in every ethtool op
- words: 70

Which locks are held around a `struct ethtool_ops` callback, does that depend
on the driver, and if a callback needs `rtnl_lock` for a helper it calls, how
does the driver get it? Name core helpers that need it.

## netdrv.rx-mode: Address filter callback

- section: Which lock, which context
- relevance: 4 - drivers that must talk to firmware cannot do it here
- words: 70

In what context does the core call the callback that programs a device's
unicast and multicast filters, and what does this tree offer a driver that has
to sleep to do that work? Start from `ndo_set_rx_mode` in
`include/linux/netdevice.h`.

## netdrv.stats-callback-context: Statistics callback context

- section: Which lock, which context
- relevance: 5 - sleeping or taking a mutex here has shipped many times
- words: 60

Which callers reach `ndo_get_stats64`, what do they hold, and may it sleep or
run while the device is being closed? What should a driver do when reading its
counters from the device can sleep?

## netdrv.ops-while-down: Callbacks on a closed device

- section: Which lock, which context
- relevance: 4 - rings freed in stop and dereferenced from ethtool or stats
- words: 60

Which driver callbacks can the core invoke while the interface is down or
between `ndo_stop` and the next `ndo_open`, and what usage of per-ring memory
in them is unsafe? What does correct code check or keep allocated, and for
which callers is a test of `netif_running()` not enough?

## netdrv.deferred-work: Deferred driver work

- section: Which lock, which context
- relevance: 2 - a new core service that replaces private work items
- words: 50

Does the core offer a driver a way to have a callback run later in process
context without the driver owning a work item, under which locks does it run,
and how is it cancelled at unregistration? Start from `net/core/netdev_work.c`.
If this tree has nothing of the kind, say so and stop.

# NAPI

## netdrv.napi-control: NAPI control calls

- section: NAPI
- relevance: 5 - a repeated or misordered call hangs or crashes
- words: 100

What do adding, enabling, disabling and deleting a NAPI instance each do, in
what state is a new instance, which of them sleep, which take a lock
themselves, and what happens if one is called twice in a row? When must a
driver use the variants whose names end in `_locked`? Start from
`napi_disable()` in `net/core/dev.c`.

## netdrv.napi-poll-contract: Poll return value

- section: NAPI
- relevance: 5 - returning the wrong count stalls or double-schedules the queue
- words: 90

What must a poll function return when it has more work and when it has
finished, what does the return value of `napi_complete_done()` mean, when may
the driver unmask its interrupt, and how is the case of finishing on exactly
the budget handled?

## netdrv.napi-budget-zero: Zero budget polls

- section: NAPI
- relevance: 4 - netpoll calls this way with interrupts off
- words: 60

When is a poll function called with a budget of zero, what may it still do,
and which APIs must it not touch in that call? How does `napi_consume_skb()`
use the budget it is given?

## netdrv.napi-after-complete: State access after completion

- section: NAPI
- relevance: 3 - a use after free that needs a concurrent stop to show
- words: 50

What does disabling a NAPI instance actually wait for, and what does that mean
for a poll function that touches its ring or private data after it has called
`napi_complete_done()`?

## netdrv.napi-scheduling: Scheduling from the interrupt handler

- section: NAPI
- relevance: 3 - the mask-then-schedule order is easy to reverse
- words: 60

How should an interrupt handler that has to mask its interrupt by hand
schedule NAPI, what is the variant for callers that know interrupts are off,
and what does that variant do when interrupts are threaded?

## netdrv.napi-queue-linking: NAPI, queue and interrupt links

- section: NAPI
- relevance: 3 - user-visible through netlink and needed for busy polling and zero copy
- words: 70

How does a driver tell the core which queues and which interrupt a NAPI
instance serves, how does it keep per-NAPI user settings across a
reconfiguration that frees the instances, and which lock do those calls need?
Start from `netif_queue_set_napi()` and `netif_napi_add_config()`.

# Transmit path

## netdrv.xmit-return: Transmit return codes

- section: Transmit
- relevance: 5 - the wrong code after freeing or queuing the skb is a double free
- words: 70

Which values may `ndo_start_xmit` return, who owns the skb after each, and what
should a driver return when it drops the packet? What does
`Documentation/networking/driver.rst` say about returning busy?

## netdrv.queue-stop-wake: Stopping and waking queues

- section: Transmit
- relevance: 5 - a lost wake-up hangs the queue until the watchdog fires
- words: 100

What race exists between a transmit routine that stops its queue when the ring
fills and a completion handler that wakes it, what usage is unsafe, and which
core helpers implement the pattern correctly? What do those helpers require of
the ring indexes and of where each side is called from? Start from
`include/net/netdev_queues.h`.

## netdrv.bql: Byte queue limits

- section: Transmit
- relevance: 4 - an unbalanced count stalls the queue for good
- words: 70

Which calls report bytes queued and bytes completed to the core, what must
balance between them, and what must a driver do when it discards a ring's
pending packets during a reset or stop? Start from `netdev_tx_sent_queue()`.

## netdrv.xmit-context: Transmit context and locking

- section: Transmit
- relevance: 4 - decides which skb free call and which lock type are legal
- words: 70

In what contexts can `ndo_start_xmit` run, what serialises two calls for the
same queue, how does a driver opt out of that serialisation and which drivers
is that meant for? Start from `HARD_TX_LOCK()` in `net/core/dev.c`.

## netdrv.skb-free-variants: Freeing skbs in a driver

- section: Transmit
- relevance: 4 - the wrong variant warns in hard interrupt context or pollutes drop tracing
- words: 80

Which calls should a driver use to free an skb in the transmit routine, in a
hard interrupt handler, in NAPI completion and on an error path, and what is
the difference between the variants that mean "dropped" and those that mean
"consumed"? Start from `dev_kfree_skb_any()`.

## netdrv.tx-timeout: Transmit watchdog

- section: Transmit
- relevance: 3 - the handler runs in a context where a reset cannot
- words: 60

What triggers `ndo_tx_timeout`, in what context and under what lock does it
run, and what do drivers that need a full reset do from it? Which field must a
driver that sets its own transmit lock-free flag keep up to date?

# Receive path and memory

## netdrv.page-pool-rules: Page pool usage

- section: Receive and buffers
- relevance: 4 - the lockless fast path rests on a rule the API cannot check
- words: 90

How many page pools should a driver create, what does setting the `napi`
member of `struct page_pool_params` promise, from which context may a driver
recycle a page directly into the pool's cache, and what must happen before a
pool is destroyed? Start from `Documentation/networking/page_pool.rst`.

## netdrv.skb-recycle: Recycling pages through skbs

- section: Receive and buffers
- relevance: 4 - forgetting it leaks DMA mappings, doing it twice corrupts the pool
- words: 60

How does an skb built on a page pool page return the page to the pool when it
is freed, what does the driver have to call for that, and what happens to the
page and its DMA mapping if it does not? Start from `skb_mark_for_recycle()`.

## netdrv.page-pool-dma-sync: Page pool DMA syncing

- section: Receive and buffers
- relevance: 2 - wrong sync ranges show only on non-coherent machines
- words: 50

Who syncs a page pool page for the CPU and who for the device, and what do the
`offset` and `max_len` parameters and `PP_FLAG_DMA_SYNC_DEV` control?

## netdrv.xdp-driver-duties: XDP in a receive path

- section: Receive and buffers
- relevance: 4 - each verdict has an obligation and redirect has a flush
- words: 90

What does a driver that runs XDP programs have to register per receive queue,
what must it do for each verdict a program returns, what must it call before
its poll function ends if any packet was redirected, and how does it advertise
which XDP features it supports? Start from `xdp_rxq_info_reg()` and
`xdp_do_flush()`.

## netdrv.queue-mgmt-ops: Queue management operations

- section: Receive and buffers
- relevance: 3 - restarting one queue must not disturb the others
- words: 80

What are the callbacks in `struct netdev_queue_mgmt_ops`, in what order does
the core call them to restart one receive queue, which of them can run on a
closed device, which lock is held, and what does providing them change about
the driver's other callbacks? Start from `netdev_rx_queue_restart()`.

# Statistics

## netdrv.u64-stats-types: 64-bit counter helpers

- section: Counters that do not tear
- relevance: 4 - the helpers behave differently on 32-bit and 64-bit builds
- words: 80

What are `struct u64_stats_sync` and `u64_stats_t`, what do the update, fetch
and read helpers compile to on a 64-bit build and on a 32-bit build, and what
do they guarantee about two counters read in one loop? Start from
`include/linux/u64_stats_sync.h`.

## netdrv.u64-stats-writers: Writer requirements

- section: Counters that do not tear
- relevance: 5 - a violation hangs readers forever, and only on 32-bit
- words: 90

What must be true of the code between `u64_stats_update_begin()` and
`u64_stats_update_end()` with respect to other writers and to preemption, what
usage is unsafe, and what that looks similar is correct? What does the begin
helper itself check or do about preemption, including on `PREEMPT_RT`?

## netdrv.u64-stats-irq: Writers and interrupt context

- section: Counters that do not tear
- relevance: 4 - the deadlock needs an interrupt at the wrong instruction
- words: 60

When must a writer use `u64_stats_update_begin_irqsave()`, what does that
variant do on each word size, and is there a separate reader variant for
interrupt or bottom-half context in this tree?

## netdrv.u64-stats-readers: Reader loops

- section: Counters that do not tear
- relevance: 4 - a retry runs the loop body again
- words: 70

What may the body of a loop between `u64_stats_fetch_begin()` and
`u64_stats_fetch_retry()` do and not do, what usage gives wrong totals only
under contention, and what does a correct loop that sums per-CPU counters look
like? Name in-tree code that shows it.

## netdrv.u64-stats-init: Initialising the sync object

- section: Counters that do not tear
- relevance: 3 - the missing call shows up as a lockdep splat on 32-bit only
- words: 60

When is `u64_stats_init()` required, what goes wrong without it, and which
allocation helpers for per-CPU statistics call it for the driver? Start from
`netdev_alloc_pcpu_stats()`.

## netdrv.core-pcpu-stats: Core-allocated per-CPU statistics

- section: Where counters live
- relevance: 4 - drivers still hand-roll what the core now allocates and reports
- words: 90

What does setting `pcpu_stat_type` on a `struct net_device` make the core do,
what are the kinds and their structures, which helpers update them, and in
what order does `dev_get_stats()` choose between the driver's callbacks, these
and `dev->stats`? What does the core add on top of whatever the driver
reports?

## netdrv.dev-stats-field: The stats member of net_device

- section: Where counters live
- relevance: 4 - plain increments from several CPUs lose counts and trip KCSAN
- words: 70

What usage of the `stats` member of `struct net_device` is unsafe when several
CPUs can update it, which macros exist for that case and what do they cost, and
which drop counters does the core keep for the driver so that it should not
count them itself? Start from `DEV_STATS_INC()` and
`dev_core_stats_rx_dropped_inc()`.

## netdrv.stats-interfaces: Statistics interfaces

- section: Reporting counters
- relevance: 5 - each kind of counter has one right home
- words: 110

Which interfaces does a driver have for reporting counters (the link
statistics, per-queue statistics, the standard ethtool groups, page pool
statistics, driver-private strings), which callback or structure feeds each,
and how does user space read it? A table. Start from
`Documentation/networking/statistics.rst`.

## netdrv.ethtool-private-stats: Driver-private ethtool statistics

- section: Reporting counters
- relevance: 5 - maintainers reject duplicates of standard counters
- words: 80

What may a driver expose through `get_ethtool_stats` and `get_strings`, which
counters are not accepted there, where is that written down, and how are
counters that were exposed that way before a standard interface existed
treated? What does the documentation ask of the number of strings over time?

## netdrv.ethtool-std-stats: Standard ethtool statistics callbacks

- section: Reporting counters
- relevance: 4 - zeroing the structure reports counters the device does not have
- words: 80

Which `struct ethtool_ops` callbacks report standards-defined hardware
counters, what value do the fields of the structures they fill hold on entry,
and what must a driver do with a field it does not support? Are these counters
meant to be kept by software or by the device?

## netdrv.queue-stats: Per-queue statistics

- section: Reporting counters
- relevance: 4 - the contract on unset fields and on totals is unusual
- words: 90

What are the callbacks in `struct netdev_stat_ops`, are the structures they
fill zeroed on entry, what must a driver do with a counter it does not keep,
what is the base callback for, and which lock is held? What should happen to
per-queue counters when the number of queues changes?

## netdrv.stats-persistence: Counters across down and up

- section: Reporting counters
- relevance: 3 - counters kept in rings vanish when the rings are freed
- words: 40

What does the kernel documentation require of interface statistics when the
interface is brought down and up again or its rings are reallocated, and how do
drivers that keep counters in ring structures meet that?

# Synchronization in drivers

## netdrv.flag-synchronization: Flags and atomics as locks

- section: Home-made synchronization
- relevance: 5 - invisible to lockdep and nearly always racy
- words: 110

What usage of an atomic counter, a boolean or a bit in a state word to keep
two driver paths (statistics readers, reset work, the close path) from
touching the same data is unsafe, why do lockdep and the memory model not
cover it, and what that looks similar is correct? If a bit is set on entry to
a region and cleared on exit, what happens when two CPUs are in the region at
once? Name in-tree uses of state bits that are correct, and say what makes them
so. Start from `__LINK_STATE_START` and `NAPI_STATE_SCHED`.

## netdrv.trylock-usage: Trylock patterns

- section: Home-made synchronization
- relevance: 3 - a retry loop around trylock hides a lock ordering problem
- words: 70

What usage of `mutex_trylock()`, `spin_trylock()` or `rtnl_trylock()` in a
driver is unsafe, and what that looks similar is correct? Name in-tree code
that shows the correct form.

## netdrv.timer-work-teardown: Stopping timers and work

- section: Home-made synchronization
- relevance: 4 - the function names changed and the old ones are gone
- words: 80

Which functions does this tree provide to stop a timer or a work item and wait
for a running instance, which of them also prevent it from being queued again,
and in which order relative to freeing rings and unregistering should a driver
call them? Start from `include/linux/timer.h` and `include/linux/workqueue.h`.

## netdrv.reset-task: Reset work against close

- section: Home-made synchronization
- relevance: 4 - a deadlock between rtnl_lock and cancel_work_sync recurs in drivers
- words: 80

A driver's reset work item takes `rtnl_lock` and its `ndo_stop` cancels that
work and waits. What usage here deadlocks, and how do in-tree drivers structure
the reset work and the close path so that it does not? Name one.

# Configuration interfaces

## netdrv.features: Feature flags

- section: Configuration
- relevance: 3 - the sets look alike and only one is user-toggled
- words: 80

What is the difference between the `features`, `hw_features`,
`vlan_features` and `hw_enc_features` sets, what do `ndo_fix_features` and
`ndo_set_features` each do, and what must a driver call, under which lock,
when something changes what it can offer? Start from
`Documentation/networking/netdev-features.rst`.

## netdrv.queue-count: Changing queue counts

- section: Configuration
- relevance: 3 - the locking requirement differs before and after registration
- words: 60

Which calls tell the core how many transmit and receive queues are in use,
which locks must be held when the device is registered, and what can fail?
Start from `netif_set_real_num_queues()`.

## netdrv.ethtool-ops-validation: Ethtool capability fields

- section: Configuration
- relevance: 3 - the core rejects requests for what the driver did not declare
- words: 70

Which members of `struct ethtool_ops` declare what a driver supports so that
the core can reject other requests before calling it, and what happens at
registration if coalescing callbacks are set without the matching declaration?
Start from `supported_coalesce_params`.

## netdrv.extack-errors: Error reporting

- section: Configuration
- relevance: 2 - a documented preference reviewers enforce
- words: 40

How should a driver report a configuration error when the callback is given a
netlink extended ack, and what does the documentation say about also logging
it?

## netdrv.hwtstamp: Hardware timestamping configuration

- section: Configuration
- relevance: 2 - the ioctl path is no longer how new drivers do it
- words: 50

Through which callbacks does a driver get and set its hardware timestamping
configuration in this tree, and is the ioctl path still available to new
drivers? Start from `ndo_hwtstamp_set`.

# Process

## netdrv.netdev-conventions: Netdev conventions

- section: Process
- relevance: 3 - preferences that are enforced on every driver patch
- words: 80

What do the networking maintainers ask for on local variable order, on
device-managed allocation and the scope-based cleanup helpers, on clean-up
patches, and on `SIOCDEVPRIVATE` in new drivers? Where is each written down?

# Changing a driver

## netdrv.change-checklist: Driver change checklist

- section: What a change must preserve
- relevance: 4 - the paths a test on an idle link does not reach
- words: 90

When a driver's open, stop, reset or ring reconfiguration path changes, which
concurrent paths must keep working against it: statistics readers, ethtool
callbacks, the transmit watchdog, netpoll, suspend and resume, XDP program
swap? For each, what does the core guarantee and what is left to the driver?
