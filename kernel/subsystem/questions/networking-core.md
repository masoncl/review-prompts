# Questions: Networking Core

- guide: networking-core.md
- title: Networking Core: SKB, Sockets, and Packet Flow

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/networking-core-measurement.md`
is the wider set the readers were measured on and
`catalogue/networking-core-measurement-results.md` says what they got wrong. No number says how
long an answer or the guide should be. Format: `../../docs/subsystem-questions.md`.

# Main structures

## net.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## net.core-files: Core files

- section: Finding your way
- relevance: 4 - helpers have moved between files and headers

A table and nothing else, job to file: the socket buffer implementation and its header; software
segmentation and receive offload; the device receive and transmit paths; the helpers that take
the device instance lock; generic socket code and the socket system calls; datagram helpers;
route cache entries; network namespaces; drop reasons; the netfilter hook core; the protocol MIB
macros. Where a reader is likely to look for a file that does not exist in this tree, say so in
the row. Start from `net/core/` and `include/net/`.

## net.conventions: Netdev conventions

- section: Finding your way
- relevance: 3 - reviewers enforce them, and they are remembered as stricter than they are written

How strongly does the networking maintainers' document state each of its rules that differ from
the rest of the kernel (order of local variable declarations, scope-based cleanup and guard
helpers, device-managed allocation, stand-alone clean-up patches, exports meant only for the
core): refused, discouraged, or allowed under a condition? Say which of them a reviewer is likely
to remember as a ban that the document does not state. Start from
`Documentation/process/maintainer-netdev.rst`.

# Buffer layout

## net.skb-geometry: Linear area and paged data

- section: Buffer layout
- relevance: 5 - nothing else about buffers makes sense without it

How is a packet's data spread over the linear area, the page fragments and the fragment list, and
which of `skb->len`, `skb->data_len` and `skb_headlen()` covers which of them? What are the
requirements for reading packet bytes through `skb->data` in order to assure safe usage? Start
from `skb_headlen()`.

## net.skb-frags: Page fragments

- section: Buffer layout
- relevance: 4 - the fragment type has changed and old accessors can return NULL

What does a `skb_frag_t` hold in this tree, where a reader's memory offers a page pointer, what
do the page and address accessors return when the fragment is not ordinary kernel memory, and
what bounds the number of fragments? Start from `skb_frag_page()` and `skb_frag_netmem()`.

## net.skb-unreadable: Unreadable payload

- section: Buffer layout
- relevance: 4 - touching such data from the CPU is a crash or a leak

When is a buffer's paged data not readable by the CPU, and how is that marked on the buffer? Which
core operations refuse or fail on such a buffer, and how does each one fail? Start from
`skb_frags_readable()`. If this tree has no such notion, say so and stop.

## net.skb-headroom: Buffer headroom

- section: Buffer layout
- relevance: 4 - pushing a header without room is a panic

How much headroom do the receive allocators reserve, how does a sender learn how much a device
needs, and what must code do before pushing a header when it cannot know that the room is there
and private? Start from `NET_SKB_PAD`, `LL_RESERVED_SPACE()` and `skb_cow_head()`.

# Data pointers and header access

## net.skb-put-push-pull: Put, push and pull

- section: Data pointers and header access
- relevance: 5 - the basic operations and how each fails

What does each of `skb_put()`, `skb_push()` and `skb_pull()` check, and what happens when the
check fails? What do the double-underscore variants check instead?

## net.skb-may-pull: Making headers linear

- section: Data pointers and header access
- relevance: 5 - every header parser depends on it

What does `pskb_may_pull()` guarantee on success, and for which reasons can it fail? What do
`pskb_network_may_pull()` and `pskb_inet_may_pull()` add?

## net.skb-length-usage: Lengths from the wire

- section: Data pointers and header access
- relevance: 5 - an unchecked length is a remote crash

What are the requirements for a length taken from packet contents or from user space before it is
passed to `skb_put()`, `skb_push()` or `skb_pull()`, in order to assure safe usage? Name in-tree
code that validates first.

## net.skb-linearize-usage: Dereferencing headers

- section: Data pointers and header access
- relevance: 5 - reading a header that is not in the linear area reads other memory

What are the requirements for dereferencing a header pointer obtained from `ip_hdr()` or from a
cast of `skb->data` in order to assure safe usage? Name in-tree code that shows the correct order.

## net.skb-pointer-reload: Pointers after reallocation

- section: Data pointers and header access
- relevance: 5 - a stale header pointer is a use after free nothing in the diff shows

Which families of buffer helper can reallocate the linear area? What are the requirements for a
pointer into packet data that was computed before a call to one of them, in order to assure safe
usage? What debugging aid exists to catch code that keeps a stale pointer? Start from
`__pskb_pull_tail()` and `pskb_expand_head()`.

## net.xfrm-family-usage: Header accessors in xfrm

- section: Data pointers and header access
- relevance: 3 - the wrong accessor parses the wrong header

In xfrm code that has both a `struct xfrm_state` and a packet, what are the requirements for
choosing between `ip_hdr()` and `ipv6_hdr()` in order to assure safe usage? Name in-tree code that
shows it.

## net.uapi-hdr-alignment: Alignment of wire headers

- section: Data pointers and header access
- relevance: 2 - one bug class, from one fix

How is the alignment of a user-visible header structure that embeds another determined? What are
the requirements for appending a field to such a structure in order to assure safe usage, and how
does in-tree code check them at build time? Start from `struct virtio_net_hdr_v1_hash_tunnel` and
`xmit_skb()` in `drivers/net/virtio_net.c`.

# Sharing and writing

## net.skb-shared-vs-cloned: Shared and cloned

- section: Sharing and writing
- relevance: 5 - the two are confused constantly

What is the difference between a shared buffer and a cloned buffer, and which counter and which
predicate go with each? What do two clones have in common? Which operations require that a buffer
is not shared, yet accept a clone?

## net.skb-clone-copy: Clone and copy

- section: Sharing and writing
- relevance: 4 - what a duplicate inherits

What does each of `skb_clone()`, `pskb_copy()`, `skb_copy()` and `skb_copy_expand()` duplicate and
what does it share with the original, and which per-buffer state does the new buffer get? A table.

## net.skb-private-copy: Getting a private buffer

- section: Sharing and writing
- relevance: 5 - the input pointer may be freed on return

What do `skb_share_check()`, `skb_unshare()` and `skb_unclone()` each do, and for each, what has
happened to the original buffer when it fails?

## net.skb-write-helpers: Making data writable

- section: Sharing and writing
- relevance: 4 - which helper to reach for

Which of `skb_ensure_writable()`, `skb_cow()`, `skb_cow_head()` and `skb_cow_data()` should code
use before writing to the first bytes of packet data, before pushing a header, and before writing
anywhere in the payload including fragments? Which of them may not be handed a shared buffer, and
what must the caller do first then? Start from `skb_ensure_writable()`, `skb_cow()`,
`skb_cow_head()` and `skb_cow_data()`.

## net.skb-write-usage: Writing to packet data

- section: Sharing and writing
- relevance: 5 - silent corruption of someone else's packet

What are the requirements for modifying the packet bytes or the metadata of a buffer that may be
shared or cloned, in order to assure safe usage? Name in-tree code for both a packet handler on
receive and a header rewrite on transmit.

# Per-buffer state

## net.skb-checksum-state: Checksum state

- section: Per-buffer state
- relevance: 4 - the values mean different things on receive and transmit

What do the four `ip_summed` values mean on receive and on transmit, what else on the buffer
has to be valid with each, and which function resolves a pending checksum in software? A table.
Start from the comment in `include/linux/skbuff.h` and `skb_checksum_help()`.

## net.skb-owner: Socket ownership of a buffer

- section: Per-buffer state
- relevance: 4 - the destructor touches the socket

What does the destructor do when a buffer owned by a socket is freed, for a buffer charged to the
send side and for one charged to the receive side? What does `skb_orphan()` give up? What are the
requirements for setting the owner of a buffer when the socket may already be on its way out, in
order to assure safe usage? Start from `skb_set_owner_w()` and `skb_set_owner_sk_safe()`.

## net.skb-gso: Segmentation state

- section: Per-buffer state
- relevance: 4 - untrusted segmentation metadata has caused many crashes

What does `SKB_GSO_DODGY` require of the stack, and where is that enforced? What can
`skb_gso_segment()` return, and what are the requirements for testing its result in order to
assure safe usage? Start from `skb_gso_segment()` and `net_gso_ok()`.

## net.skb-cb-lifetime: Control block lifetime

- section: Per-buffer state
- relevance: 5 - state read back after another layer has overwritten it

Who owns the contents of `skb->cb` at any moment? What are the requirements for carrying state in
`skb->cb` from one layer to another, or to a destructor or completion callback, in order to assure
safe usage? Name in-tree code that shows it. Where can state that must survive until the buffer is
freed be kept?

# Ownership and freeing

## net.skb-free-functions: Free functions

- section: Ownership and freeing
- relevance: 4 - the right one depends on context and on whether it is a drop

Which function frees a buffer in each situation (a drop with a reason, normal consumption, a
driver in hard interrupt or unknown context, a driver's transmit completion inside NAPI, a list
of buffers), and which of them may be called with interrupts disabled? Start from
`sk_skb_reason_drop()` and `napi_consume_skb()`.

## net.skb-drop-reasons: Drop reasons

- section: Ownership and freeing
- relevance: 4 - new drops are expected to carry one

Where does a patch that adds a drop reason have to write it, by hand or through a generator, and
what must a subsystem that wants reasons of its own do: does every such subsystem register its
names? Which values of the type are not drops? Start from `include/net/dropreason-core.h` and
`include/net/dropreason.h`.

## net.skb-error-ownership: Ownership on failure

- section: Ownership and freeing
- relevance: 5 - double free or leak depending on which way it is wrong

For the common functions that take a buffer (`dev_queue_xmit()`, `netif_rx()`,
`sock_queue_rcv_skb()`, `sk_add_backlog()`, `skb_put_padto()`, a device's `ndo_start_xmit`),
which free the buffer when they fail and which leave it to the caller? A table.

## net.nf-hook-ownership: Netfilter verdicts and ownership

- section: Ownership and freeing
- relevance: 5 - the caller loses the buffer in most cases

For each verdict a netfilter hook can return, what happens to the buffer and what does
`nf_hook_slow()` return? How does that differ between calling `NF_HOOK()` and calling
`nf_hook()` directly?

## net.skb-handoff-usage: After a buffer handoff

- section: Ownership and freeing
- relevance: 5 - the commonest use after free in networking

What are the requirements for touching a buffer after it has been passed to a function that takes
it over, such as `dev_queue_xmit()` or `netif_rx()`, in order to assure safe usage? Name in-tree
code that shows it.

## net.nf-hook-usage: After a netfilter hook

- section: Ownership and freeing
- relevance: 5 - use after free in the caller

What are the requirements for using a buffer, or state reachable only through it, after
`nf_hook()` or `NF_HOOK()` returns, in order to assure safe usage? Name in-tree callers of
`nf_hook()`, and of `NF_HOOK()` if there are any, that continue with the buffer.

# Receive and transmit paths

## net.dev-rx-path: Receive path stages

- section: Receive and transmit paths
- relevance: 4 - a change has to go at the right stage

In `__netif_receive_skb_core()`, where do generic XDP, the taps, ingress classification, the
`rx_handler` and protocol delivery run relative to each other, and what does each `rx_handler`
result make the core do with the buffer? Say only what a change that adds a step would have to
get right.

## net.dev-rx-entry: Receive entry points

- section: Receive and transmit paths
- relevance: 4 - the wrong one for the context deadlocks or reorders

A table of the functions a driver or virtual device chooses between to hand a buffer to the
stack: the context each may be called from, what it returns, and who owns the buffer afterwards.
Start from `netif_rx()`, `netif_receive_skb()` and `napi_gro_receive()`.

## net.dev-ptype-delivery: Packet handler delivery

- section: Receive and transmit paths
- relevance: 4 - a handler never gets an exclusive buffer

Packet handlers can be registered for one device, for one namespace or for all: what decides
which list a handler lands on? What reference does a handler receive on the buffer, and what must
it do before modifying it? Start from `dev_add_pack()` and `deliver_skb()`.

## net.dev-tx-path: Transmit path stages

- section: Receive and transmit paths
- relevance: 4 - where validation and software fallbacks happen

On the way from `__dev_queue_xmit()` to the driver, in what order do the netfilter egress hook,
egress classification and the queueing discipline see a buffer, and where do feature
validation, software segmentation and the checksum fallback happen relative to the transmit
lock? Where a reader is likely to name a helper on this path that is gone, give the current one.
Start from `validate_xmit_skb()` and `dev_hard_start_xmit()`.

## net.dev-xmit-return: Transmit return codes

- section: Receive and transmit paths
- relevance: 4 - decides who frees the buffer

What may `ndo_start_xmit` return, and what must the driver have done with the buffer for each
value? What happens to a buffer the driver reports busy for, on a device with a queueing
discipline and on one with no queue? What do the codes returned by `dev_queue_xmit()` mean to
its caller? Start from `dev_xmit_complete()` and `net_xmit_eval()`.

# Socket references and kinds

## net.sock-refcount: Socket reference counts

- section: Socket references and kinds
- relevance: 5 - two counters, and the free happens when the second one drains

Which two counters keep a `struct sock` alive, what does each count, and what runs when each
reaches zero? When is the memory finally freed if packets the socket sent are still in flight?
Start from `sock_put()`, `sk_free()` and `sock_wfree()`.

## net.sock-lookup-refs: References from lookups

- section: Socket references and kinds
- relevance: 4 - not every socket found by a lookup is reference counted

Which protocol lookups hand back a socket with a reference and which without one, what keeps an
unreferenced one safe to use, and how does the receive path tell which kind it holds? Start from
`SOCK_RCU_FREE`, `sk_is_refcounted()` and `skb_steal_sock()`.

## net.sock-minisocks: Request and timewait sockets

- section: Socket references and kinds
- relevance: 4 - most of struct sock is not there

Which socket-like objects are not full sockets? What are the requirements for reading a `struct
sock` member through a pointer that may be one of them, in order to assure safe usage? Which put
function is right for every kind? Start from `sk_fullsock()`.

## net.sock-minisock-sources: Sources of non-full sockets

- section: Socket references and kinds
- relevance: 4 - code that is handed a socket it did not look up cannot tell from the call what kind it holds

On which paths does code receive a `struct sock` pointer that may not be a full socket without
having asked for one? Start from `sk_fullsock()`.

## net.sock-refcount-usage: Keeping a socket pointer

- section: Socket references and kinds
- relevance: 5 - use after free from timers, work items and private lists

What are the requirements for keeping a socket pointer where it outlives the caller's own
reference, such as in a timer, in order to assure safe usage? What do `sk_reset_timer()` and
`sk_stop_timer()` do with the socket reference when the timer was already pending and when it was
not? Start from `sk_reset_timer()` and `sk_stop_timer()`.

# Socket lock, accounting and options

## net.sock-release-vs-unlock: Socket release versus unlock

- section: Socket lock, accounting and options
- relevance: 4 - two similar names that do unrelated things

What do `sock_release()` and `release_sock()` each do, which structure does each take, and what
is each one's counterpart? Start from `__sock_release()` and `__release_sock()`.

## net.sock-lock: Socket lock

- section: Socket lock, accounting and options
- relevance: 5 - the central lock, with two halves

Which part of the socket lock does process context take and which does softirq context take? Does
process context always take both? What does `release_sock()` do besides unlocking? Start from
`lock_sock_nested()` and `__release_sock()`.

## net.sock-rcv-queue: Queueing to a socket

- section: Socket lock, accounting and options
- relevance: 4 - the generic receive enqueue most protocols use

What does `sock_queue_rcv_skb_reason()` return on success and for each kind of refusal, and how
does the older `sock_queue_rcv_skb()` map that for its callers? What does it charge and change
on the buffer before queueing it? Start from `__sock_queue_rcv_skb()`.

## net.sock-mem-accounting: Memory accounting

- section: Socket lock, accounting and options
- relevance: 4 - leaks show up as a warning at socket destruction

Which counters of the socket do `sk_mem_charge()` and `sk_mem_uncharge()` change, what is forward
allocation and when is it given back? What are the requirements for changing a buffer's `truesize`
after the buffer has been charged to a socket, in order to assure safe usage? Start from
`sk_mem_charge()`, `__sk_mem_schedule()` and `pskb_expand_head()`.

## net.sock-sockopt: Socket option handlers

- section: Socket lock, accounting and options
- relevance: 4 - short option buffers read kernel stack

How are option values passed to `setsockopt` and `getsockopt` handlers in this tree, and which
methods of `struct proto_ops` does the core call for each? Which copy helpers check the user's
length against the kernel's structure, and what are the requirements for a handler's use of
`optlen` in order to assure safe usage? Start from `include/linux/sockptr.h` and
`do_sock_getsockopt()`.

## net.sock-bh-usage: Softirq access to sockets

- section: Socket lock, accounting and options
- relevance: 5 - racing with the process that owns the socket

What are the requirements for reading or changing a socket's state from softirq context in order
to assure safe usage? What does a protocol receive handler do when `sock_owned_by_user()` is true,
and what bounds the backlog? Start from `sk_add_backlog()`.

## net.sock-lockless-fields: Lockless socket fields

- section: Socket lock, accounting and options
- relevance: 4 - reviewers ask for the annotations

What are the requirements for reading, and for writing, a socket member that some code reads
without the socket lock, in order to assure safe usage? How does a reviewer tell that a member is
one of those? Give two examples from `include/net/sock.h`.

# Routes

## net.dst-refcount: Route entry references

- section: Routes
- relevance: 4 - the counter type and the free path have changed

How is a `struct dst_entry` reference counted in this tree, what does `dst_hold_safe()` return
when the entry is no longer live and what does a caller do then, and when is the entry freed?
Start from `dst_hold_safe()` and `dst_release()`.

## net.dst-dev: Device behind a route

- section: Routes
- relevance: 4 - a reference on the route does not pin its device

What does a reference on a route entry not keep alive: what happens to the entry's device
pointer when the device goes away while the entry is still referenced? How must code read the
device of a route with and without RCU, and can the result be NULL? Start from `dst_dev()`,
`dst_dev_rcu()` and `dst_dev_put()`.

## net.dst-noref-lifetime: Unreferenced routes on a buffer

- section: Routes
- relevance: 5 - the route can be freed under a queued buffer

What does `skb_dst_force()` return? What are the requirements for using a route obtained from
`ip_route_input_noref()` or from `skb_dst()` after the RCU read section ends, in order to assure
safe usage? At which points does the stack upgrade the route on the caller's behalf? Start from
`skb_dst_set_noref()`, `skb_dst_force()` and `ip_route_input_noref()`.

# Devices and their locks

## net.dev-instance-lock: Device instance lock

- section: Devices and their locks
- relevance: 5 - new, and it changes what an ndo may assume

What does the per-device lock in `struct net_device` protect by itself and what together with
RTNL, for which devices are the driver's operations and which notifier events called under it,
and how does it order against RTNL? Start from `netdev_need_ops_lock()` and the comment on the
`lock` member in `include/linux/netdevice.h`.

## net.dev-locked-variants: Locked and unlocked device functions

- section: Devices and their locks
- relevance: 4 - calling the wrong one deadlocks or races

How does the naming of core device functions tell a caller whether the function takes the
device instance lock itself or expects it held? Give three pairs. Which helpers take the lock
only for devices that asked for it, and what is the helper that asserts it called, where a
reader's memory may offer a name that does not exist? Start from `net/core/dev_api.c` and
`include/net/netdev_lock.h`.

## net.dev-rtnl: RTNL and per-namespace RTNL

- section: Devices and their locks
- relevance: 4 - the global lock is being split

Which helpers assert that RTNL is held, and which dereference an RCU pointer under it? When is the
per-namespace RTNL a real lock, and how does it nest with the global RTNL? Start from
`rtnl_net_lock()`.

## net.dev-refs: Device references

- section: Devices and their locks
- relevance: 4 - a leaked reference hangs unregistration

Which device lookups return a held device, which an RCU-protected one and which one that is only
safe under RTNL, and which of the older lookups are deprecated in favour of what? What does a
reference tracker add? Start from `netdev_hold()` and `dev_get_by_index_rcu()`.

## net.dev-lifetime: Registration and teardown

- section: Devices and their locks
- relevance: 4 - who frees the device and when

What does unregistration wait for and where, how do `needs_free_netdev` and `priv_destructor`
decide who frees the structure, and which of them apply after a registration that failed? Start
from `unregister_netdevice_many()` and `netdev_run_todo()`.

## net.dev-skb-dev: Device pointer on a buffer

- section: Devices and their locks
- relevance: 4 - the buffer holds no reference on the device

What keeps `skb->dev` valid while a buffer is in the receive path, and what must code that holds
a buffer beyond that (a socket queue, a reassembly queue, a deferred work item) do about the
field?

# Network namespaces

## net.netns-refs: Namespace references

- section: Network namespaces
- relevance: 4 - two counters with different guarantees

Which two counts keep a `struct net` alive, and what does each allow its holder to do? What are
the requirements for using a `struct net` pointer found under RCU in order to assure safe usage?
Where does the main count live in this tree, where a reader's memory offers a member of the
namespace itself? Start from `get_net()`, `maybe_get_net()` and `net_passive_inc()`.

## net.sock-kernel-sockets: Kernel sockets

- section: Network namespaces
- relevance: 4 - use after free of the namespace from a kernel socket

How does a socket created from kernel code differ from a user socket in what it holds on its
network namespace, what must its owner do when the namespace is torn down, and how can it be
converted to hold a full reference? Start from `sock_create_kern()` and `sk_alloc()`.

## net.netns-pernet: Per-namespace operations

- section: Network namespaces
- relevance: 4 - teardown order and where blocking is allowed

In what order and under which locks do the exit callbacks of `struct pernet_operations` run when
namespaces are torn down, which of them runs under RTNL and what is it called in this tree, and
where may an exit handler wait for a grace period and where must it not? Start from
`register_pernet_subsys()`.

# Protocol statistics

## net.snmp-counters: Protocol MIB counters

- section: Protocol statistics
- relevance: 3 - lost or torn updates, and the variants differ in what context they need

How do the plain and the double-underscore MIB counter macros differ in the context they need, and
what are the requirements for calling each with respect to preemption and softirqs in order to
assure safe usage? What do the 64-bit variants do on a 32-bit build, the double-underscore one
included? Start from `include/net/snmp.h`.

# Model gaps

## net.model-gaps: Other mistakes models make

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
