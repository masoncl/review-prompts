# What the networking-core measurement found

Three models were asked the 86 questions in `networking-core-measurement.md`
with no sources, and a checker that had the sources then corrected each answer
against a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C.
Reader C is the most current, reader A is a few releases behind it, and reader B
is older again and much the weakest; which models they were does not matter
here. The hand-written guide was never checked against current sources, so
differences between it and the built guide are expected and are noted below.

## What all three readers got wrong

Readers A and C described almost every mechanism correctly. What all three
missed is what has moved recently, and a handful of facts that would change a
verdict.

- **The helper that asserts the device instance lock.** All three named
  netdev_ops_assert_locked(), which does not exist. The tree has
  `netdev_assert_locked_ops()` and `netdev_assert_locked_ops_compat()` in
  `include/net/netdev_lock.h`; `netdev_lock()` itself is in
  `include/linux/netdevice.h`. All three also gave an incomplete list of the
  notifier events that arrive with the instance lock held.
- **`NETDEV_TX_BUSY` is not always requeued.** Only the qdisc path
  (`sch_direct_xmit()`) requeues. On a device with no queue
  `__dev_queue_xmit()` frees the buffer and returns `-ENETDOWN`.
- **The transmit path's order and names.** `nf_hook_egress()` runs before
  `sch_handle_egress()`; `validate_xmit_skb()` runs before `HARD_TX_LOCK()` and
  starts with `validate_xmit_unreadable_skb()`. Readers A and C offered
  qdisc_pkt_len_init(); the tree has `qdisc_pkt_len_segs_init()`, called before
  `rcu_read_lock_bh()`.
- **`sock_queue_rcv_skb_reason()` returns an `enum skb_drop_reason`**, with
  `SKB_NOT_DROPPED_YET` for success, and takes no reason pointer. All three had
  it return an errno. Only the `sock_queue_rcv_skb()` inline maps it back, and
  it maps every filter drop to `-EPERM`.
- **The network namespace's main count** is `__ns_ref` in `struct ns_common`,
  changed through `ns_ref_inc()` and friends. All three wrote net->ns.count.
- **`getsockopt_iter` and `sockopt_t`.** `struct proto_ops` has a second
  getsockopt method that `do_sock_getsockopt()` prefers. No reader knew it;
  reader C said there was no such conversion.
- **Unreadable fragments as a failure of `pskb_may_pull()`.**
  `__pskb_pull_tail()` returns NULL when `!skb_frags_readable()`, and
  `pskb_may_pull_reason()` reports that as `SKB_DROP_REASON_NOMEM`. All three
  listed only length and allocation failure. They also disagreed with the code
  about which other helpers fail on such a buffer and how (`skb_checksum()`
  warns and returns 0; `skb_copy_bits()` returns `-EFAULT`).
- **Who may change `truesize`.** `pskb_expand_head()` changes it only when the
  buffer has no socket or the destructor is `sock_edemux`; `skb_expand_head()`
  and `tcp_trim_head()` adjust the socket's counters themselves;
  `skb_condense()` recomputes it without looking at the owner, so its callers
  run it before charging.
  No reader had all of that.
- **The socket lock's fast path.** On 64-bit `lock_sock_nested()` first tries a
  `try_cmpxchg()` on `sk_lock.combined` and may never take `slock`. For TCP,
  `release_sock()` calls the release callback only when deferred work is
  flagged (`tcp_release_cb_cond()`).
- **What `SKB_GSO_DODGY` makes the stack do** was wrong in a different way for
  each reader. Such a buffer fails `net_gso_ok()` unless the device has
  `NETIF_F_GSO_ROBUST`, so it goes to software segmentation, where
  `tcp_gso_segment()` checks the headers and may only recompute `gso_segs` and
  return NULL.
- **Drop reasons.** The enum is written out by hand and `DEFINE_DROP_REASON()`
  only builds the strings (readers A and B had it generated). The qdisc
  subsystem has its own reasons and registers nothing (readers A and C said
  every subsystem registers its names).
- **The netdev conventions.** All three overstated
  `Documentation/process/maintainer-netdev.rst`:
  `guard()` is discouraged only in functions longer than 20 lines, `devm_` is
  acceptable, clean-ups are discouraged rather than refused, and spelling fixes
  are welcome.
- **The build-time guard on the virtio headers.** No reader could place it: it
  is two `BUILD_BUG_ON(__alignof__ ...)` lines in `xmit_skb()`. Readers A and B
  also said the hash header contains a 32-bit field and is 4-byte aligned;
  every field in the three headers is 8 or 16 bits wide, so all are 2-byte
  aligned.
- **On 32-bit the double-underscore 64-bit MIB increment still disables
  bottom halves**: `__SNMP_INC_STATS64()` is defined as `SNMP_ADD_STATS64()`.

## What readers A and B got wrong as well

- To keep a namespace found under RCU, take `get_net()`. The count may already
  be zero; in-tree code uses `maybe_get_net()`.
- `skb_orphan_frags()` always copies user pages. It does nothing when
  `SKBFL_DONT_ORPHAN` is set, which MSG_ZEROCOPY and io_uring do; only
  `skb_orphan_frags_rx()` always copies.
- Software segmentation never returns NULL, so test with `IS_ERR()`. It can;
  callers use `IS_ERR_OR_NULL()` or test both.
- A kernel socket "holds nothing on its namespace". `sk_alloc()` takes
  `net_passive_inc()` for it, so the memory stays but the namespace can be
  dismantled under it; `sk_net_refcnt_upgrade()` swaps that for a full
  reference. Reader B offered sk_change_net(), which does not exist.
- UDP and listener lookups take a reference. They take none:
  `__inet_lookup()` reports listeners as not reference counted, and only
  `__inet_lookup_established()` takes one. `sk_is_refcounted()` is
  `!sk_fullsock(sk) || !sock_flag(sk, SOCK_RCU_FREE)`, which both had backwards
  in part, and `skb_steal_sock()` takes no reference itself.
- `NF_STOLEN` always returns 0 from `nf_hook_slow()`. It returns
  `NF_DROP_GETERR()`, which is an errno when the hook used `NF_DROP_REASON()`.
  Nor does `NF_HOOK()` always consume the buffer: `br_handle_local_finish()`
  returns 1 and `br_handle_frame()` carries on with it.
- Where packet handlers are registered. `ptype_head()` picks the device's
  lists, else the namespace's `ptype_all` or `ptype_specific` when
  `af_packet_net` is set, else the global `ptype_base`; there is no global list
  of taps. Reader B had a global tap list; reader A had the namespace lists used
  whenever there is no device.
- `sk_stop_timer()` uses `timer_delete()` and `__sock_put()`; `sk_reset_timer()`
  holds the socket only if the timer was not already pending.
- What the double-underscore pointer helpers check. `__skb_put()` has only the
  linear assertion, `__skb_push()` only a `DEBUG_NET_WARN_ON_ONCE()`, and
  `__skb_pull()` a `BUG()`. Reader A gave them more checks than they have,
  reader B none.
- The buffer extension ids: both left out `SKB_EXT_CAN`, and reader B
  `SKB_EXT_PSP` and `TC_SKB_EXT` too.
- `dst_dev_put()` hands the device reference to `blackhole_netdev` with
  `netdev_ref_replace()`. Both also thought a reference on the route was enough
  to read its device.

## What only reader B got wrong

Reader B is out of date on whole mechanisms, and wrong about some fundamentals:

- A fragment is a bio_vec and `MAX_SKB_FRAGS` is 65536/PAGE_SIZE + 1. It is
  `struct skb_frag` holding a `netmem_ref`, and the limit is
  `CONFIG_MAX_SKB_FRAGS`, default 17. It invented SKBFL_NOT_READABLE for the
  `unreadable` bit.
- A shared buffer is several `struct sk_buff` pointing at one data area. That
  is a clone; shared is `users != 1` on one structure. It also had
  `skb_unshare()` clone when shared.
- `kfree_skb()` is safe with interrupts disabled. `dev_kfree_skb_any_reason()`
  exists because it is not.
- `CHECKSUM_NONE` on transmit means "fill it in", and `CHECKSUM_PARTIAL` on
  receive asks the stack to compute. Both are the wrong way round.
- A socket counts drops with a bare atomic increment. `sk_drops_add()` picks
  the per-NUMA `sk_drop_counters` when the socket has them.
- A route is counted by an atomic __refcnt and moves to loopback_dev on device
  removal. It is `rcuref_t __rcuref`, and `blackhole_netdev`.
- `ip_route_input_noref()` returns a route pointer. It returns a drop reason
  and attaches the route to the buffer.
- NETIF_F_LLTX. It is the `lltx` bit in `struct net_device`.
- It did not know how a driver opts in to the instance lock and invented
  NETDEV_ONE_LOCK. It gave `_locked` suffixes for the locked variants; the tree
  pairs `dev_open()` with `netif_open()`.
- dev->refcnt; `dev_hold()` as an older raw call; `dev_get_by_index()` as the
  current held lookup (it is marked deprecated for `netdev_get_by_index()`).
- An exit_batch_rtnl callback. It is `exit_rtnl(net, dev_kill_list)`.
- `bind` and `connect` take `struct sockaddr *`. They take
  `struct sockaddr_unsized *`.
- `props.family` is the inner family of an xfrm state. It is the outer one.
- sk_state_load(), __napi_alloc_skb(), dev_kfree_skb_list_any(),
  netif_receive_generic_xdp(), GRO_DROP and include/net/datagram.h, none of
  which exist. It said there are no KUnit tests; there are two in `net/core/`.

## What only reader C got wrong

- `skb_pull()`, `skb_trim()` and control-block writes are unsafe on a clone.
  A clone has its own `struct sk_buff`; those are unsafe only when shared.
- __dev_get_by_flags() as an RTNL lookup. It is `netdev_get_by_flags_rcu()`,
  which returns a held device.
- A failed `register_netdevice()` has always run `priv_destructor`. Only after
  `ndo_init()` succeeded.
- `dst_dev()` never returns NULL. Metadata routes start with no device.
- It used __udp4_lib_rcv(), which is now `udp_rcv()`.

## What the readers already knew

Readers A and C needed nothing of substance on buffer geometry, validating
lengths before pull and put, re-reading header pointers after
`pskb_may_pull()`, the rule against writing to a shared or cloned buffer, what
`skb_share_check()` and `skb_unshare()` do to the input, clone versus copy,
control-block lifetime, queue locking, the two socket structures, `sock_release()`
against `release_sock()`, the dst noref rule and `ip_route_input()`, and what
keeps `skb->dev` valid. Those are most of the hand-written guide. All three had
the entry points. Reader B had the ideas behind most of these but rarely the
details.

## Where the hand-written guide is stale

`networking-core.md` names nothing that is missing from the tree, and its
descriptions of `skb_put()`, `skb_push()`, `skb_pull()`, `skb_unshare()`,
`sock_hold()`, `ip_route_input()` and the MIB macros still match the code. Its
problem is what it leaves out and a few absolutes:

- "In all cases the caller of `NF_HOOK()` loses ownership." An `okfn` can return
  with the buffer still owned by the caller's caller
  (`br_handle_local_finish()`), and a caller of `nf_hook()` owns the buffer when
  it returns 1. `NF_DROP` is freed by `kfree_skb_reason()`, which is now an
  inline over `sk_skb_reason_drop()`.
- `sock_put()` "calls `sk_free()` when it reaches zero" stops one step short:
  `sk_free()` only drops the bias on `sk_wmem_alloc`, and the socket is freed
  when that second count drains, from `sock_wfree()` if packets are in flight.
- "Check `skb_shared()` / `skb_cloned()` before modifying" does not say how.
  `pskb_expand_head()` has `BUG_ON(skb_shared(skb))`, so a shared buffer needs
  `skb_share_check()` first, and `skb_ensure_writable()`, `skb_cow()` or
  `skb_cow_head()` after it. The guide never mentions `skb_header_cloned()`.
- The control-block rule is absolute. `unix_destruct_scm()` reads `UNIXCB()`
  from a destructor, correctly, because the buffer never leaves AF_UNIX. The
  field is `char cb[48] __aligned(8)`.
- The packet type table stops at 5. `PACKET_USER` (6) and `PACKET_KERNEL` (7)
  exist and the field is three bits.
- The xfrm section calls `skb_dst(skb)->ops->family` the most reliable source.
  In-tree code just as often switches on `skb->protocol`
  (`xfrm_inner_extract_output()`) or picks the inner mode with
  `xfrm_ip2inner_mode()`.
- "Hold `rcu_read_lock()` during routing table lookups" is not what callers of
  `ip_route_input_noref()` do: it takes the lock itself, and the caller needs a
  read section to use the unreferenced route afterwards.
- It has nothing on unreadable fragments, drop reasons, which functions free a
  buffer when they fail, request and timewait sockets, kernel sockets and
  namespaces, the device instance lock, or the fact that a reference on a route
  does not pin its device.
- It was never onboarded to the drift checker.

## What was left out of the build set

The hand-written guide is 1,807 words, so the build set is 41 of the 86
questions with small budgets. Because reader B is weak nearly everywhere, the
cut was made by importance and by what readers A and C miss, not by dropping
what every reader knows. It keeps the hand-written guide's subjects (moving the
data pointers, shared and cloned buffers, linear headers, socket references,
hook ownership, handoff, routes under RCU, MIB counters, the control block,
header alignment, xfrm families) and adds the helper families every reader had
under old names. Left out, by reason:

- Readers A and C answer them: buffer geometry, validating lengths,
  dereferencing headers, shared against cloned, clone and copy, queues and
  lists, the control block's layout, the two socket structures,
  `sock_release()` against `release_sock()`, the device pointer on a buffer,
  device references and teardown, the entry points.
- Real but too narrow for a guide loaded on every networking patch: the shared
  info block, truesize, allocation variants, headroom, reading without pulling,
  trimming and padding, checksums across a pull, payload-only references,
  fragments owned elsewhere, extensions, scrubbing, checksum state, packet
  type, socket callbacks, lockless fields, memory accounting, drop counters,
  address arguments, the cached route on a socket, the receive path stages,
  transmit locking, RTNL, notifiers, per-device statistics, per-namespace
  operations, finding the namespace, writing a hook function, the debug
  assertions, documentation and tests.
- Covered by a neighbouring answer: queueing to a socket (the table of
  ownership on failure), the xfrm family fields (the usage question).

A first build without the question on the context the MIB macros need had one
builder say that either preemption or bottom halves being off is enough for the
double-underscore macros. The macros only assert the first; a softirq on the
same CPU updating the same counter needs the second. The usage question was
added so that the guide says it outright.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A: 151 corrections, 24% rewritten on average
reader B: 235 corrections, 74% rewritten on average
reader C: 161 corrections, 18% rewritten on average

question                        reader A      reader B      reader C
net.core-files                   1% ( 1)      87% ( 5)       5% ( 2)
net.entry-points                 3% ( 1)       0% ( 0)      10% ( 3)
net.docs-tests                   8% ( 1)      67% ( 2)      19% ( 1)
net.conventions                 67% ( 5)      86% ( 4)      49% ( 2)
net.debug-asserts               48% ( 2)      76% ( 1)      22% ( 1)
net.skb-geometry                 0% ( 0)      60% ( 1)       0% ( 0)
net.skb-shared-info             21% ( 1)      79% ( 3)       6% ( 1)
net.skb-frags                    2% ( 1)      73% ( 2)       4% ( 1)
net.skb-unreadable              36% ( 4)      87% ( 2)      24% ( 3)
net.skb-truesize                65% ( 3)      85% ( 4)      57% ( 2)
net.skb-alloc                   55% ( 2)      50% ( 3)      15% ( 2)
net.skb-headroom                36% ( 3)      79% ( 4)      27% ( 2)
net.skb-put-push-pull           18% ( 1)      57% ( 4)       0% ( 1)
net.skb-length-usage             0% ( 0)      74% ( 2)       1% ( 1)
net.skb-may-pull                23% ( 1)      73% ( 2)       5% ( 1)
net.skb-pointer-reload          22% ( 2)      83% ( 3)      28% ( 3)
net.skb-linearize-usage          0% ( 0)      55% ( 1)       0% ( 0)
net.skb-header-pointer          28% ( 1)      47% ( 1)       8% ( 1)
net.skb-trim-pad                39% ( 1)      71% ( 3)      18% ( 2)
net.skb-rcsum                   19% ( 1)      73% ( 2)      35% ( 3)
net.skb-shared-vs-cloned        10% ( 1)      82% ( 2)       0% ( 0)
net.skb-dataref-halves          27% ( 1)      78% ( 1)      22% ( 3)
net.skb-private-copy            16% ( 1)      76% ( 1)       0% ( 0)
net.skb-write-helpers           11% ( 1)      85% ( 1)      24% ( 3)
net.skb-write-usage              0% ( 0)      70% ( 6)      15% ( 1)
net.skb-clone-copy              12% ( 2)      73% ( 2)       0% ( 0)
net.skb-shared-frags            43% ( 2)      77% ( 4)      46% ( 4)
net.skb-free-functions          27% ( 3)      70% ( 4)       4% ( 1)
net.skb-drop-reasons            23% ( 2)      86% ( 2)      21% ( 4)
net.skb-handoff-usage           24% ( 3)      85% ( 3)      11% ( 2)
net.skb-error-ownership          8% ( 3)      40% ( 2)      11% ( 2)
net.skb-owner                   19% ( 3)      76% ( 3)      23% ( 3)
net.skb-queues-lists             4% ( 0)      75% ( 2)      11% ( 1)
net.skb-cb                      17% ( 1)      65% ( 3)       0% ( 0)
net.skb-cb-usage                 0% ( 0)      85% ( 2)       9% ( 1)
net.skb-extensions              25% ( 2)      66% ( 2)      35% ( 4)
net.skb-scrub                   51% ( 2)      73% ( 4)      23% ( 1)
net.skb-checksum-state           4% ( 1)      69% ( 4)      21% ( 3)
net.skb-gso                     32% ( 3)      66% ( 2)      40% ( 2)
net.skb-pkt-type                33% ( 1)      68% ( 1)      51% ( 2)
net.sock-vs-socket               6% ( 1)      34% ( 1)       0% ( 0)
net.sock-release-vs-unlock       6% ( 1)      83% ( 1)      11% ( 1)
net.sock-kernel-sockets         50% ( 1)      65% ( 1)       8% ( 2)
net.sock-refcount               19% ( 1)      87% ( 1)      30% ( 2)
net.sock-lookup-refs            57% ( 4)      85% ( 4)      10% ( 2)
net.sock-refcount-usage         35% ( 2)      70% ( 1)       5% ( 1)
net.sock-minisocks              27% ( 3)      80% ( 1)      21% ( 2)
net.sock-lock                   50% ( 3)      67% ( 3)      40% ( 4)
net.sock-bh-usage               35% ( 2)      78% ( 3)      42% ( 1)
net.sock-callbacks              18% ( 2)      38% ( 2)      19% ( 2)
net.sock-lockless-fields         2% ( 1)      79% ( 3)      27% ( 4)
net.sock-mem-accounting         39% ( 2)      75% ( 4)      41% ( 6)
net.sock-rcv-queue              48% ( 3)      67% ( 3)      53% ( 5)
net.sock-drops                  48% ( 1)      77% ( 1)      53% ( 1)
net.sock-sockopt                38% ( 1)      66% ( 1)      27% ( 2)
net.sock-sockaddr               22% ( 1)      81% ( 1)       0% ( 0)
net.sock-dst-cache              30% ( 1)      71% ( 3)       4% ( 1)
net.dev-rx-entry                34% ( 3)      68% ( 4)      32% ( 2)
net.dev-rx-path                 24% ( 2)      74% ( 5)      11% ( 3)
net.dev-ptype-delivery          46% ( 2)      80% ( 2)       0% ( 0)
net.dev-tx-path                 59% ( 3)      71% ( 3)      22% ( 4)
net.dev-xmit-return             40% ( 2)      75% ( 3)      11% ( 2)
net.dev-tx-lock                 29% ( 1)      79% ( 2)      27% ( 2)
net.dev-refs                     6% ( 1)      79% ( 4)      11% ( 2)
net.dev-lifetime                19% ( 2)      86% ( 4)       9% ( 1)
net.dev-skb-dev                 11% ( 1)      89% ( 2)       0% ( 0)
net.dev-rtnl                    26% ( 1)      75% ( 2)      12% ( 1)
net.dev-instance-lock           25% ( 4)      85% ( 4)      30% ( 4)
net.dev-locked-variants         14% ( 2)      86% ( 1)      44% ( 3)
net.dev-notifiers               41% ( 3)      87% ( 3)      34% ( 2)
net.dev-sw-stats                11% ( 2)      83% ( 5)       6% ( 2)
net.snmp-stats                  10% ( 2)      90% ( 5)      18% ( 2)
net.snmp-usage                  15% ( 1)      73% ( 3)      19% ( 1)
net.netns-refs                  11% ( 1)      70% ( 4)      34% ( 4)
net.netns-pernet                16% ( 3)      82% ( 5)       7% ( 2)
net.netns-lookup                43% ( 3)      89% ( 4)      39% ( 3)
net.dst-refcount                12% ( 2)      81% ( 4)       2% ( 1)
net.dst-noref                   13% ( 2)      75% ( 4)      10% ( 2)
net.dst-noref-usage             25% ( 1)      84% ( 2)       0% ( 0)
net.dst-dev                     29% ( 2)      85% ( 2)      17% ( 2)
net.nf-hook-ownership           12% ( 3)      80% ( 7)       0% ( 0)
net.nf-hook-usage               11% ( 2)      83% ( 4)       6% ( 1)
net.nf-hook-fn                  19% ( 1)      76% ( 5)      25% ( 3)
net.xfrm-family                 25% ( 2)      88% ( 3)      13% ( 1)
net.xfrm-family-usage           35% ( 1)      79% ( 2)      31% ( 2)
net.uapi-hdr-alignment          55% ( 3)      90% ( 3)      44% ( 4)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `net.sock-mem-accounting`, `net.sock-rcv-queue`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `net.skb-geometry`, `net.skb-shared-info`, `net.skb-headroom`, `net.skb-length-usage`, `net.skb-linearize-usage`, `net.skb-shared-vs-cloned`, `net.skb-clone-copy`, `net.skb-owner`, `net.skb-cb`, `net.skb-checksum-state`, `net.sock-release-vs-unlock`, `net.sock-lockless-fields`, `net.dev-rx-path`, `net.dev-refs`, `net.dev-lifetime`, `net.dev-skb-dev`, `net.dev-rtnl`, `net.netns-pernet`.

## Questions reorganised

By subject now, 59 questions from 63, each a hazard, a contract or orientation. Subjects: buffer
layout; moving the data pointers; sharing and writing; per-buffer state; ownership and freeing;
receive and transmit paths; socket references and kinds; socket lock, accounting and options;
routes; devices and their locks; network namespaces; protocol headers and counters.
Merged: `net.skb-cb` and `net.skb-cb-usage` into `net.skb-cb-lifetime`; `net.dst-noref` and
`net.dst-noref-usage` into `net.dst-noref-lifetime`; `net.snmp-stats` and `net.snmp-usage` into
`net.snmp-counters`. Dropped: `net.skb-shared-info`, an inventory of members; what clones share is
asked in `net.skb-shared-vs-cloned`. `net.sock-mem-accounting` now also asks who may change `truesize`.
