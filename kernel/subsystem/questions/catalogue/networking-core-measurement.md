# Questions: Networking core (measurement set)

- guide: networking-core.md
- title: Networking Core: SKB, Sockets, and Packet Flow

A wide set of questions about the networking core: socket buffers, sockets,
the device receive and transmit paths, device and namespace lifetime, route
cache entries and the netfilter hook entry points. It is used to measure what a
model already knows before deciding what the built guide should spend its words
on. The hand-written guide it will replace is 1,807 words. Drivers and netlink
have their own guides. Format: `../../../docs/subsystem-questions.md`.

# The subsystem

## net.core-files: Core files

- section: Finding your way
- relevance: 4 - helpers have moved between files and headers
- words: 120

Which files hold the socket buffer implementation and its header, software
segmentation and receive offload, the device receive and transmit paths, the
helpers that take the device instance lock, generic socket code and the socket
system calls, datagram helpers, route cache entries, network namespaces, drop
reasons, the netfilter hook core and the protocol MIB macros? A table. Start
from `net/core/` and `include/net/`.

## net.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 100

For each job (allocate a buffer in a driver's receive path, hand a received
buffer to the stack, transmit a buffer through a device's queue, drop a buffer
with a reason, queue a buffer on a socket's receive queue, create a socket from
kernel code, drop the last reference to a socket), which function do you start
reading from? A table.

## net.docs-tests: Documentation and tests

- section: Finding your way
- relevance: 3 - several rules live only in the documentation
- words: 90

Which files under `Documentation/networking/` and `Documentation/process/` are
the authority on buffer geometry and sharing, on device lifetime and locking,
on checksum and segmentation offloads and on the netdev patch process, and
where are the unit tests and selftests for the networking core?

## net.conventions: Netdev conventions

- section: Finding your way
- relevance: 3 - reviewers enforce them and they differ from the rest of the kernel
- words: 90

Which conventions do the networking maintainers ask for that differ from the
rest of the kernel (order of local variable declarations, scope-based cleanup
and guard helpers, device-managed allocation, stand-alone clean-up patches,
exports meant only for the core), and where is each written down? Start from
`Documentation/process/maintainer-netdev.rst`.

## net.debug-asserts: Debug assertions

- section: Finding your way
- relevance: 3 - new checks in hot paths are expected to use them
- words: 60

Which assertion macros and dump helpers does the networking core provide for
conditions too costly to check in production, which configuration option
enables them, and what do they compile to when it is off? Start from
`include/net/net_debug.h`.

# The socket buffer

## net.skb-geometry: Buffer geometry

- section: Buffer layout
- relevance: 5 - nothing else about buffers makes sense without it
- words: 100

How is a packet's data laid out across the linear area, the page fragments and
the fragment list, and what do `len`, `data_len`, `head`, `data`, `tail` and
`end` each describe? How is `skb_headlen()` derived from them?

## net.skb-shared-info: Shared info block

- section: Buffer layout
- relevance: 4 - what clones share and what survives to the destructor
- words: 90

Where does `struct skb_shared_info` live, which of its fields are cleared when
a buffer is allocated, which fields overlay each other in a union, and what, if
anything, does the structure promise about `destructor_arg`?

## net.skb-frags: Page fragments

- section: Buffer layout
- relevance: 4 - the fragment type has changed and old accessors can return NULL
- words: 100

What does a `skb_frag_t` hold in this tree, which accessors read it, what do
the page and address accessors return when the fragment is not ordinary kernel
memory, and what bounds the number of fragments? Start from `skb_frag_page()`
and `skb_frag_netmem()`.

## net.skb-unreadable: Unreadable payload

- section: Buffer layout
- relevance: 4 - touching such data from the CPU is a crash or a leak
- words: 90

When is a buffer's paged data not readable by the CPU, how is that marked on
the buffer, and which core operations refuse or fail on such a buffer? Start
from `skb_frags_readable()`. If this tree has no such notion, say so and stop.

## net.skb-truesize: Truesize

- section: Buffer layout
- relevance: 3 - wrong values break socket memory accounting silently
- words: 80

What does `truesize` account for, which code may change it after a buffer has
been charged to a socket, and what breaks if it changes behind the socket's
back? Start from `skb_set_owner_r()` and `skb_try_coalesce()`.

## net.skb-alloc: Allocation variants

- section: Buffer layout
- relevance: 3 - the right allocator depends on context
- words: 100

Which allocation functions serve a process-context sender, a driver outside
NAPI, a driver inside NAPI poll, and a driver wrapping memory it already owns,
and which slab caches and per-CPU caches sit behind them? Start from
`__alloc_skb()` and `napi_alloc_skb()`.

## net.skb-headroom: Headroom

- section: Buffer layout
- relevance: 4 - pushing a header without room is a panic
- words: 90

How much headroom do the receive allocators reserve, how does a sender learn
how much a device needs, and what must code do before pushing a header when it
cannot know that the room is there and private? Start from `NET_SKB_PAD`,
`LL_RESERVED_SPACE()` and `skb_cow_head()`.

## net.skb-put-push-pull: Put, push and pull

- section: Moving the data pointers
- relevance: 5 - the basic operations and how each fails
- words: 100

What does each of `skb_put()`, `skb_push()` and `skb_pull()` check, and what
happens when the check fails? What do the double-underscore variants check
instead?

## net.skb-length-usage: Lengths from the wire

- section: Moving the data pointers
- relevance: 5 - an unchecked length is a remote crash
- words: 90

What usage of a length taken from packet contents or from user space with the
put, push and pull helpers is unsafe, and what that looks similar is correct?
Name in-tree code that validates first.

## net.skb-may-pull: Making headers linear

- section: Moving the data pointers
- relevance: 5 - every header parser depends on it
- words: 90

What does `pskb_may_pull()` guarantee on success, for which reasons can it
fail, and which variant reports the reason? What do `pskb_network_may_pull()`
and `pskb_inet_may_pull()` add?

## net.skb-pointer-reload: Pointers after reallocation

- section: Moving the data pointers
- relevance: 5 - a stale header pointer is a use after free nothing in the diff shows
- words: 100

Which buffer helpers can reallocate the linear area, what happens to pointers
into the packet that were computed before the call, and what debugging aid
exists to catch code that keeps a stale pointer? Start from
`__pskb_pull_tail()` and `pskb_expand_head()`.

## net.skb-linearize-usage: Dereferencing headers

- section: Moving the data pointers
- relevance: 5 - reading a header that is not in the linear area reads other memory
- words: 90

What usage of a header pointer obtained from `ip_hdr()` or from a cast of
`skb->data` is unsafe, and what that looks similar is correct? Name in-tree
code that shows the correct order.

## net.skb-header-pointer: Reading without pulling

- section: Moving the data pointers
- relevance: 3 - the alternative when the buffer must not change
- words: 70

How can code read bytes at an offset that may lie in fragments without changing
the buffer, what does the helper return in each case, and when is it preferred
to pulling? Start from `skb_header_pointer()` and `skb_copy_bits()`.

## net.skb-trim-pad: Trimming and padding

- section: Moving the data pointers
- relevance: 3 - one of them frees the buffer on failure
- words: 80

Which helpers shorten a buffer that may have fragments and which pad a short
frame, and what happens to the buffer when padding fails? Start from
`pskb_trim()`, `skb_put_padto()` and `__skb_pad()`.

## net.skb-rcsum: Checksums across a pull

- section: Moving the data pointers
- relevance: 3 - forgetting it produces checksum failures only on some hardware
- words: 70

When a received buffer carries a full checksum from the device, what must code
do when it pulls or pushes bytes, and which helpers do it? Start from
`skb_pull_rcsum()` and `skb_postpull_rcsum()`.

## net.skb-shared-vs-cloned: Shared and cloned

- section: Sharing
- relevance: 5 - the two are confused constantly
- words: 80

What is the difference between a shared buffer and a cloned buffer, which
counter tracks each, and which predicate tests each?

## net.skb-dataref-halves: Payload-only references

- section: Sharing
- relevance: 3 - explains why a clone may still write its headers
- words: 80

How is the data reference count split, what does a payload-only reference
allow lower layers to do, and which predicate should code that only writes
headers use? Start from `skb_header_cloned()` and `__skb_header_release()`.

## net.skb-private-copy: Getting a private buffer

- section: Sharing
- relevance: 5 - the input pointer may be freed on return
- words: 100

What do `skb_share_check()`, `skb_unshare()` and `skb_unclone()` each do, and
for each, what has happened to the original buffer when it fails?

## net.skb-write-helpers: Making data writable

- section: Sharing
- relevance: 4 - which helper to reach for
- words: 110

Which helper should code use before writing to the first bytes of packet data,
before pushing a header, and before writing anywhere in the payload including
fragments, and what does each cost? Start from `skb_ensure_writable()`,
`skb_cow()`, `skb_cow_head()` and `skb_cow_data()`.

## net.skb-write-usage: Writing to packet data

- section: Sharing
- relevance: 5 - silent corruption of someone else's packet
- words: 100

What usage that modifies packet bytes or buffer metadata is unsafe when the
buffer may be shared or cloned, and what that looks similar is correct? Name
in-tree code for both a packet handler on receive and a header rewrite on
transmit.

## net.skb-clone-copy: Clone and copy

- section: Sharing
- relevance: 4 - what a duplicate inherits
- words: 110

What does each of `skb_clone()`, `pskb_copy()`, `skb_copy()` and
`skb_copy_expand()` duplicate and what does it share, and which per-buffer
state (owner socket, destructor, control block, route, extensions) does the new
buffer get?

## net.skb-shared-frags: Fragments owned elsewhere

- section: Sharing
- relevance: 3 - zerocopy and splice pages can change under the stack
- words: 90

When may a buffer's page fragments be modified by someone outside the stack,
how is that marked, and what must code do before it keeps such a buffer for an
unbounded time or writes to those fragments? Start from
`skb_has_shared_frag()`, `skb_orphan_frags()` and `skb_zcopy()`.

## net.skb-free-functions: Free functions

- section: Ownership and freeing
- relevance: 4 - the right one depends on context and on whether it is a drop
- words: 110

Which function frees a buffer in each situation (a drop with a reason, normal
consumption, a driver in hard interrupt or unknown context, a driver's transmit
completion inside NAPI, a list of buffers), and which of them may be called
with interrupts disabled? Start from `sk_skb_reason_drop()` and
`napi_consume_skb()`.

## net.skb-drop-reasons: Drop reasons

- section: Ownership and freeing
- relevance: 4 - new drops are expected to carry one
- words: 100

How are drop reasons defined and grouped by subsystem, which two values are not
drops, and what must a patch that adds a new reason or a new subsystem do?
Start from `include/net/dropreason-core.h` and `include/net/dropreason.h`.

## net.skb-handoff-usage: Use after handoff

- section: Ownership and freeing
- relevance: 5 - the commonest use after free in networking
- words: 100

What usage of a buffer after it has been passed to a queueing, transmit,
receive or hook function is unsafe, and what that looks similar is correct?
Name in-tree code that saves what it needs first.

## net.skb-error-ownership: Ownership on failure

- section: Ownership and freeing
- relevance: 5 - double free or leak depending on which way it is wrong
- words: 120

For the common functions that take a buffer (`dev_queue_xmit()`, `netif_rx()`,
`sock_queue_rcv_skb()`, `sk_add_backlog()`, `skb_put_padto()`, a device's
`ndo_start_xmit`), which free the buffer when they fail and which leave it to
the caller? A table.

## net.skb-owner: Socket ownership of a buffer

- section: Ownership and freeing
- relevance: 4 - the destructor touches the socket
- words: 110

How is a buffer tied to a socket, which destructors are used for send and
receive accounting, what does `skb_orphan()` do, and which helper takes a
socket reference safely when the socket may be on its way out? Start from
`skb_set_owner_w()` and `skb_set_owner_sk_safe()`.

## net.skb-queues-lists: Queues and lists

- section: Ownership and freeing
- relevance: 3 - which lock, and which linkage field
- words: 100

Which lock protects an `sk_buff_head`, how do the double-underscore queue
helpers differ, what does `skb_peek()` promise, and how are buffers chained
outside a queue head (segment lists, receive lists, the fragment list)? Start
from `skb_list_walk_safe()`.

## net.skb-cb: Control block

- section: Per-buffer state
- relevance: 4 - every layer overlays it
- words: 100

How large is the control block, who owns its contents at any moment, what
happens to it on clone and copy, and how do layers make sure their overlay
fits? Name the overlays used by TCP, IP and the queueing layer.

## net.skb-cb-usage: Control block lifetime

- section: Per-buffer state
- relevance: 5 - state read back after another layer has overwritten it
- words: 100

What usage of the control block to carry state from one layer to another, or to
a destructor or completion callback, is unsafe, and what that looks similar is
correct? Where can state that must survive until the buffer is freed be kept?

## net.skb-extensions: Buffer extensions

- section: Per-buffer state
- relevance: 3 - the alternative to growing the buffer structure
- words: 90

What are buffer extensions, which ids does this tree define, how are they
reference counted and copied on write, and which helpers add, find and drop
one? Start from `skb_ext_add()`.

## net.skb-scrub: Crossing namespaces

- section: Per-buffer state
- relevance: 3 - leftover state leaks between namespaces
- words: 80

What state must be cleared when a buffer is injected into another device or
namespace, which helper does it, and what does it leave alone when the
namespace does not change? Start from `skb_scrub_packet()` and
`__dev_forward_skb()`.

## net.skb-checksum-state: Checksum state

- section: Per-buffer state
- relevance: 4 - the values mean different things on receive and transmit
- words: 110

What do the four `ip_summed` values mean on receive and on transmit, which
fields accompany each, and which function resolves a pending checksum in
software? Start from the comment in `include/linux/skbuff.h` and
`skb_checksum_help()`.

## net.skb-gso: Segmentation state

- section: Per-buffer state
- relevance: 4 - untrusted segmentation metadata has caused many crashes
- words: 110

Which fields describe a buffer that must be segmented, what does the flag for
untrusted sources require of the stack, which function segments in software,
and what does it return on failure? Start from `skb_gso_segment()` and
`skb_segment()`.

## net.skb-pkt-type: Packet type

- section: Per-buffer state
- relevance: 2 - small, but user-writable in places
- words: 70

Which values can `pkt_type` take, how wide is the field, who sets it on
receive, and which subset may user-controlled code such as tc or nftables
write? Start from `eth_type_trans()` and `skb_pkt_type_ok()`.

# Sockets

## net.sock-vs-socket: Socket structures

- section: Structures and lifetime
- relevance: 5 - two objects with different lifetimes
- words: 100

What are `struct socket` and `struct sock`, how are they linked, which outlives
the other, what does `sock_orphan()` do, and which of `struct proto_ops` and
`struct proto` belongs to which layer?

## net.sock-release-vs-unlock: Release and unlock

- section: Structures and lifetime
- relevance: 4 - two similar names that do unrelated things
- words: 80

What do `sock_release()` and `release_sock()` each do, which structure does
each take, and what is each one's counterpart? Start from `__sock_release()`
and `__release_sock()`.

## net.sock-kernel-sockets: Kernel sockets

- section: Structures and lifetime
- relevance: 4 - use after free of the namespace from a kernel socket
- words: 100

How does a socket created from kernel code differ from a user socket in what it
holds on its network namespace, what must its owner do when the namespace is
torn down, and how can it be converted to hold a full reference? Start from
`sock_create_kern()` and `sk_alloc()`.

## net.sock-refcount: Socket reference counts

- section: Structures and lifetime
- relevance: 5 - two counters, and the free happens when the second one drains
- words: 110

Which two counters keep a `struct sock` alive, what does each count, which
functions take and drop them, and what runs when each reaches zero? Start from
`sock_put()`, `sk_free()` and `sock_wfree()`.

## net.sock-lookup-refs: References from lookups

- section: Structures and lifetime
- relevance: 4 - not every socket found by a lookup is reference counted
- words: 110

How do the protocol lookup paths get a usable socket under RCU, which sockets
are freed after a grace period and which rely on type-stable memory, and how
does the receive path tell whether the socket it found holds a reference? Start
from `SOCK_RCU_FREE`, `sk_is_refcounted()` and `skb_steal_sock()`.

## net.sock-refcount-usage: Keeping a socket pointer

- section: Structures and lifetime
- relevance: 5 - use after free from timers, work items and private lists
- words: 100

What usage that stores or uses a socket pointer beyond the caller's own
reference (timers, work items, a private list, a pointer taken from a buffer)
is unsafe, and what that looks similar is correct? Start from
`sk_reset_timer()` and `sk_stop_timer()`.

## net.sock-minisocks: Request and timewait sockets

- section: Structures and lifetime
- relevance: 4 - most of struct sock is not there
- words: 100

Which socket-like objects are not full sockets, which fields of `struct sock`
are valid on them, which predicates and converters must code use before
touching the rest, and which put function handles all kinds? Start from
`sk_fullsock()`.

## net.sock-lock: Socket lock

- section: Locking and accounting
- relevance: 5 - the central lock, with two halves
- words: 110

What are the two parts of the socket lock, what does process context take, what
does softirq context take, and what does `release_sock()` do besides unlocking?
Start from `lock_sock_nested()` and `__release_sock()`.

## net.sock-bh-usage: Softirq access to sockets

- section: Locking and accounting
- relevance: 5 - racing with the process that owns the socket
- words: 100

What usage of socket state from softirq context is unsafe, and what that looks
similar is correct? Describe what a protocol receive handler does when the
socket is owned by a process, and what bounds the backlog. Start from
`sk_add_backlog()`.

## net.sock-callbacks: Socket callbacks and user data

- section: Locking and accounting
- relevance: 4 - in-kernel socket users get teardown wrong
- words: 110

Which callbacks on a socket can an in-kernel user replace, which lock protects
them and the user data pointer, how must the user data pointer be read from the
data path, and what must happen before the in-kernel user's state is freed?
Start from `sk_callback_lock` and `rcu_dereference_sk_user_data()`.

## net.sock-lockless-fields: Lockless socket fields

- section: Locking and accounting
- relevance: 4 - reviewers ask for the annotations
- words: 90

Which socket fields are commonly read without the socket lock (from poll, from
diag, from the fast path), and what annotation is required on the reads and on
the writes? Give examples from `include/net/sock.h`.

## net.sock-mem-accounting: Memory accounting

- section: Locking and accounting
- relevance: 4 - leaks show up as a warning at socket destruction
- words: 110

Which counters track memory charged to a socket for receive, for send, for
queued but unsent data and for options, what is forward allocation, and which
helpers charge, uncharge and schedule memory? Start from `sk_mem_charge()` and
`__sk_mem_schedule()`.

## net.sock-rcv-queue: Queueing to a socket

- section: Locking and accounting
- relevance: 4 - the generic receive enqueue most protocols use
- words: 100

What does `sock_queue_rcv_skb_reason()` do in order, what does it return, what
does it change on the buffer, and who owns the buffer when it fails? Start from
`__sock_queue_rcv_skb()`.

## net.sock-drops: Socket drop counters

- section: Locking and accounting
- relevance: 2 - the field has moved
- words: 50

How does a socket count dropped packets in this tree, and which helpers update
and read the count? Start from `sk_drops_inc()`.

## net.sock-sockopt: Socket option handlers

- section: Locking and accounting
- relevance: 4 - short option buffers read kernel stack
- words: 110

How are option values passed to `setsockopt` and `getsockopt` handlers in this
tree, which copy helpers check the user's length against the kernel's
structure, and what usage of `optlen` is unsafe? Start from
`include/linux/sockptr.h` and `struct proto_ops`.

## net.sock-sockaddr: Address arguments

- section: Locking and accounting
- relevance: 3 - the handler must check the length before the family fields
- words: 80

Which type do `bind` and `connect` handlers receive for the address in this
tree, what has the caller already validated about its length, and what must the
handler check itself before reading family-specific fields? Start from
`struct proto_ops` and `include/linux/socket.h`.

## net.sock-dst-cache: Cached route on a socket

- section: Locking and accounting
- relevance: 3 - a stale or unreferenced route
- words: 90

How does a socket cache its output route, how is the cache validated before
use, which helpers read, set and reset it, and what protects a reader that does
not take a reference? Start from `__sk_dst_check()` and `sk_dst_get()`.

# Devices and packet flow

## net.dev-rx-entry: Receive entry points

- section: Packet flow
- relevance: 4 - the wrong one for the context deadlocks or reorders
- words: 110

Which functions may a driver or virtual device use to hand a buffer to the
stack, from which context may each be called, what does each return, and who
owns the buffer afterwards? Start from `netif_rx()`, `netif_receive_skb()` and
`napi_gro_receive()`.

## net.dev-rx-path: Receive path stages

- section: Packet flow
- relevance: 4 - a change has to go at the right stage
- words: 110

List in order what `__netif_receive_skb_core()` does with a buffer, from
generic XDP to protocol delivery, and say what each `rx_handler` result means.

## net.dev-ptype-delivery: Packet handler delivery

- section: Packet flow
- relevance: 4 - a handler never gets an exclusive buffer
- words: 90

Where are packet handlers registered (globally, per namespace, per device),
what reference does a handler receive on the buffer, and what must a handler do
before modifying it? Start from `dev_add_pack()` and `deliver_skb()`.

## net.dev-tx-path: Transmit path stages

- section: Packet flow
- relevance: 4 - where validation and software fallbacks happen
- words: 110

List in order what `__dev_queue_xmit()` does with a buffer, from egress hooks
to the driver, and say where feature validation, software segmentation and
checksum fallback happen. Start from `validate_xmit_skb()` and
`dev_hard_start_xmit()`.

## net.dev-xmit-return: Transmit return codes

- section: Packet flow
- relevance: 4 - decides who frees the buffer
- words: 100

What may `ndo_start_xmit` return and what must the driver have done with the
buffer for each value, and what do `NET_XMIT_SUCCESS` and the other codes
returned by `dev_queue_xmit()` mean to a caller? Start from
`dev_xmit_complete()` and `net_xmit_eval()`.

## net.dev-tx-lock: Transmit locking

- section: Packet flow
- relevance: 3 - the opt-out has moved
- words: 80

Which lock serialises calls to a device's transmit routine, which devices run
without it and how is that marked in this tree, and in which context does the
transmit routine run? Start from `HARD_TX_LOCK()`.

## net.dev-refs: Device references

- section: Device lifetime and locks
- relevance: 4 - a leaked reference hangs unregistration
- words: 110

Which functions take and drop a reference on a `struct net_device`, what are
reference trackers for, and which lookup functions return a held device, an
RCU-protected one or an RTNL-protected one? Start from `netdev_hold()` and
`dev_get_by_index_rcu()`.

## net.dev-lifetime: Registration and teardown

- section: Device lifetime and locks
- relevance: 4 - who frees the device and when
- words: 110

What are the registration states of a device, what does unregistration wait for
and where, and how do `needs_free_netdev` and `priv_destructor` decide who frees
the structure? Start from `unregister_netdevice_many()` and
`netdev_run_todo()`.

## net.dev-skb-dev: Device pointer on a buffer

- section: Device lifetime and locks
- relevance: 4 - the buffer holds no reference on the device
- words: 90

What keeps `skb->dev` valid while a buffer is in the receive path, and what
must code that holds a buffer beyond that (a socket queue, a reassembly queue,
a deferred work item) do about the field?

## net.dev-rtnl: RTNL and per-namespace RTNL

- section: Device lifetime and locks
- relevance: 4 - the global lock is being split
- words: 110

What does RTNL protect, which helpers assert it and dereference under it, and
what is the per-namespace variant: which functions take it, when is it a real
lock, and how do the two nest? Start from `rtnl_net_lock()`.

## net.dev-instance-lock: Device instance lock

- section: Device lifetime and locks
- relevance: 5 - new, and it changes what an ndo may assume
- words: 140

What is the per-device lock in `struct net_device`, which devices have their
operations called under it, which helpers take it conditionally, what does it
protect by itself and together with RTNL, and how does it order against RTNL?
Start from `netdev_lock_ops()` and `netdev_need_ops_lock()`.

## net.dev-locked-variants: Locked and unlocked variants

- section: Device lifetime and locks
- relevance: 4 - calling the wrong one deadlocks or races
- words: 80

How does the naming of core device functions tell a caller whether the function
takes the device instance lock itself or expects it held? Give three pairs.
Start from `net/core/dev_api.c`.

## net.dev-notifiers: Device notifiers

- section: Device lifetime and locks
- relevance: 3 - which events arrive with the instance lock held
- words: 90

Which device notifier events run under the device instance lock and which do
not, what may a handler call in each case, and what must drivers not do from an
ops-locked notification? Start from `Documentation/networking/netdevices.rst`.

## net.dev-sw-stats: Per-device software statistics

- section: Statistics
- relevance: 3 - software devices should not allocate their own
- words: 90

How does a software device get per-CPU packet and byte counters from the core
rather than allocating them, which counter layouts are there, and which helpers
update and sum them? Start from `pcpu_stat_type` and
`dev_sw_netstats_rx_add()`.

## net.snmp-stats: Protocol MIB counters

- section: Statistics
- relevance: 3 - the variants differ in what context they need
- words: 100

How are the per-CPU protocol MIB counters updated, what is the difference
between the plain and double-underscore macros, and what do the 64-bit variants
do on a 32-bit build? Start from `include/net/snmp.h`.

## net.snmp-usage: Counter update context

- section: Statistics
- relevance: 3 - lost or torn updates
- words: 70

What usage of the MIB counter macros is unsafe with respect to preemption and
softirqs, and what that looks similar is correct?

# Namespaces

## net.netns-refs: Namespace references

- section: Network namespaces
- relevance: 4 - two counters with different guarantees
- words: 100

Which counters keep a `struct net` alive and what does each allow its holder to
do, which helper takes a reference only if the namespace is still alive, and
what are reference trackers used for? Start from `get_net()`,
`maybe_get_net()` and `net_passive_inc()`.

## net.netns-pernet: Per-namespace operations

- section: Network namespaces
- relevance: 4 - teardown order and where blocking is allowed
- words: 110

Which callbacks does `struct pernet_operations` have, in what order and under
which locks do they run at namespace teardown, and where may an exit handler
wait for a grace period? Start from `register_pernet_subsys()`.

## net.netns-lookup: Finding the namespace

- section: Network namespaces
- relevance: 3 - the pointer is only good inside the protecting section
- words: 80

How should code find the namespace for a buffer, a device or a socket, under
what protection is the result valid, and what must code do to use it after that
protection ends? Start from `dev_net_rcu()`, `sock_net()` and `read_pnet()`.

# Routes and hooks

## net.dst-refcount: Route entry references

- section: Route cache entries
- relevance: 4 - the counter type and the free path have changed
- words: 110

How is a `struct dst_entry` reference counted in this tree, which helper takes
a reference only if the entry is still live, when is the entry freed, and what
does releasing the device do to entries that are still referenced? Start from
`dst_hold_safe()`, `dst_release()` and `dst_dev_put()`.

## net.dst-noref: Unreferenced routes on a buffer

- section: Route cache entries
- relevance: 5 - the route can be freed under a queued buffer
- words: 110

How does a buffer carry a route without a reference, which helpers set, test,
upgrade and drop it, what does the upgrade return, and at which points does the
stack upgrade on the caller's behalf? Start from `skb_dst_set_noref()` and
`skb_dst_force()`.

## net.dst-noref-usage: Routes under RCU

- section: Route cache entries
- relevance: 5 - use after free once the read section ends
- words: 100

What usage of a route obtained from an input route lookup or from `skb_dst()`
is unsafe once the RCU read section ends, and what that looks similar is
correct? Start from `ip_route_input_noref()` and `ip_route_input()`.

## net.dst-dev: Device behind a route

- section: Route cache entries
- relevance: 4 - the device pointer can change under a live route
- words: 90

How should code read the device of a route entry in this tree, with and without
RCU, and what can happen to that pointer while the entry is still referenced?
Start from `dst_dev()` and `dst_dev_rcu()`.

## net.nf-hook-ownership: Hook verdicts and ownership

- section: Netfilter hooks
- relevance: 5 - the caller loses the buffer in most cases
- words: 120

For each verdict a netfilter hook can return, what happens to the buffer and
what does `nf_hook_slow()` return? How does that differ between calling
`NF_HOOK()` and calling `nf_hook()` directly?

## net.nf-hook-usage: After a netfilter hook

- section: Netfilter hooks
- relevance: 5 - use after free in the caller
- words: 100

What usage of a buffer, or of state reachable only through it, after invoking a
netfilter hook is unsafe, and what that looks similar is correct? Name in-tree
callers of `nf_hook()` that continue with the buffer.

## net.nf-hook-fn: Writing a hook function

- section: Netfilter hooks
- relevance: 3 - the other side of the same contract
- words: 90

What must a hook function do with the buffer for each verdict it returns, how
does it report an errno together with a drop, and what must stay valid for the
whole traversal? Start from `struct nf_hook_state` and `NF_DROP_GETERR()`.

# Particular hazards

## net.xfrm-family: Address families in xfrm state

- section: IPsec state
- relevance: 3 - several family fields that need not agree
- words: 90

Which fields of `struct xfrm_state` carry an address family, what does each
describe, and which helper picks the inner mode for a given packet? Start from
`xfrm_ip2inner_mode()`.

## net.xfrm-family-usage: Header accessors in xfrm

- section: IPsec state
- relevance: 3 - the wrong accessor parses the wrong header
- words: 90

What usage of a state's family field to choose between the IPv4 and IPv6 header
accessors is unsafe, and what that looks similar is correct? Name in-tree code
that takes the family from the packet.

## net.uapi-hdr-alignment: Alignment of wire headers

- section: User-visible headers
- relevance: 2 - one bug class, from one fix
- words: 100

How is the alignment of a user-visible header structure that embeds another
determined, what goes wrong when a field wider than that alignment is appended,
and how does in-tree code guard against it at build time? Start from
`struct virtio_net_hdr_v1_hash_tunnel` and `xmit_skb()` in
`drivers/net/virtio_net.c`.
