# Networking Subsystem Details

## SKB Buffer Operations

`skb_put()`, `skb_push()`, and `skb_pull()` modify the data boundaries of a
socket buffer. Each operation has a bounds check that triggers a kernel panic
on violation:

- `skb_put(skb, len)` extends the tail. Panics via `skb_over_panic()` if
  `skb->tail > skb->end`.
- `skb_push(skb, len)` prepends to head. Panics via `skb_under_panic()` if
  `skb->data < skb->head`.
- `skb_pull(skb, len)` consumes from head. Calls `BUG()` if
  `skb->len < skb->data_len`.

Code that constructs or modifies packets must validate lengths before calling
these functions. Passing untrusted or unchecked lengths causes a kernel panic
(DoS) — the bounds check fires before memory is corrupted, so it is a crash
rather than a silent overflow, but it is still a bug.

## SKB Shared and Cloned Buffers

SKBs can be shared (`skb->users > 1`) or cloned (`skb_cloned()`). Modifying
a shared or cloned SKB corrupts other users of the same buffer.

- `skb_shared(skb)` returns true when `refcount_read(&skb->users) != 1`
- `skb_cloned(skb)` returns true when the data area is shared with another SKB

Use `skb_unshare(skb, gfp)` to get an exclusive copy. If the buffer is
cloned, it copies the SKB and frees the original (even on allocation
failure). If not cloned, it returns the original unchanged. Always use the
returned pointer — the input pointer may have been freed. A NULL return
means allocation failed and the original SKB is already gone.

## Header Linearization

Packet headers may span paged fragments and cannot be safely dereferenced
without first ensuring the bytes are in the linear region (`skb->data`).
`pskb_may_pull(skb, len)` guarantees at least `len` bytes are contiguous
in the linear part, pulling from fragments if necessary.

```c
if (!pskb_may_pull(skb, sizeof(struct iphdr)))
    return -EINVAL;

iph = ip_hdr(skb);  /* safe: header is now in linear region */
```

Any code that parses protocol headers from received packets must call
`pskb_may_pull()` before dereferencing header pointers.

## Socket Locking vs Socket Release

Two commonly confused functions:

- `release_sock(sk)` releases the socket lock acquired by `lock_sock()`.
  It processes the backlog queue and wakes waiters. The socket remains alive.
- `sock_release(sock)` closes and destroys the socket structure, releasing
  the protocol stack and associated inode.

There is no function called `socket_release()` in the kernel.

After `release_sock()`, the socket is still valid but unlocked — other
threads may now operate on it. After `sock_release()`, the socket structure
is freed and must not be accessed.

## Socket Reference Counting

Socket lifetime is managed through `sk_refcnt`:

- `sock_hold(sk)` increments `sk->sk_refcnt`
- `sock_put(sk)` decrements `sk->sk_refcnt` and calls `sk_free()` when it
  reaches zero

A socket can outlive its file descriptor. Code that holds a pointer to a
socket outside the file descriptor's lifetime must hold a reference with
`sock_hold()` and release it with `sock_put()`.

## Netfilter Hook Ownership

`NF_HOOK()` and `NF_HOOK_COND()` pass an SKB through the netfilter hook
chain. The hook verdict determines what happens to the SKB:

| Verdict | Meaning | SKB Ownership |
|---------|---------|---------------|
| `NF_ACCEPT` | Continue processing | `okfn()` is called with the SKB |
| `NF_DROP` | Reject packet | Netfilter frees the SKB via `kfree_skb_reason()` |
| `NF_STOLEN` | Hook consumed packet | Hook took ownership |

In all cases, the caller of `NF_HOOK()` loses ownership of the SKB and must
not access it after the call.

Device pointers (`in`, `out`) passed to `NF_HOOK()` must remain valid
throughout hook traversal. Set `skb->dev` before calling `NF_HOOK()` when
the routing path depends on it.

## Buffer Handoff Safety

Once an SKB is passed to another subsystem (queued, enqueued, handed to a
protocol handler), the caller loses ownership. Accessing the SKB after
handoff is a use-after-free because the receiver may free it at any time,
including before the handoff function returns.

## Byte Order Conversions

Network protocols use big-endian byte order. The kernel uses `__be16`,
`__be32`, and `__be64` types to annotate network-order values. Common byte
order bugs:

- Comparing a `__be16` port with a host-order constant without `htons()`
- Performing arithmetic on network-order values without converting first
- Double-converting (applying `htons()` to an already network-order value)

Sparse catches these at build time via `__bitwise` type annotations
(enabled when Sparse defines `__CHECKER__`; run with `make C=1`).

## RCU Protection for Routing

Routing table lookups (FIB lookups, dst entries) are protected by RCU.
Callers must hold `rcu_read_lock()` during the lookup and while accessing
the result:

```c
rcu_read_lock();
reason = ip_route_input_noref(skb, dst, src, dscp, devin);
if (!reason) {
    skb_dst_force(skb);  /* take refcount if needed beyond RCU */
    if (!skb_dst(skb))
        reason = SKB_DROP_REASON_NOT_SPECIFIED;
}
rcu_read_unlock();
```

`skb_dst_set_noref()` stores an RCU-protected dst entry without taking a
reference — it asserts that `rcu_read_lock()` or `rcu_read_lock_bh()` is
held. If the dst needs to survive beyond the RCU read-side critical section,
use `skb_dst_force()` to upgrade to a refcounted reference.

## Per-CPU Network Statistics

Per-CPU network statistics can race with BH (bottom half) processing. The
SNMP stat macros handle this at the appropriate level:

- `SNMP_INC_STATS()` / `SNMP_ADD_STATS()` use `this_cpu_inc()`/`this_cpu_add()`
  which are safe for single-word counters on all architectures
- `SNMP_ADD_STATS64()` / `SNMP_UPD_PO_STATS64()` wrap updates in
  `local_bh_disable()`/`local_bh_enable()` and use `u64_stats` seqcounts on
  32-bit systems (`#if BITS_PER_LONG==32`) where a 64-bit update is not atomic

Driver-specific statistics should follow the guidelines in
`Documentation/networking/statistics.rst`.

## Packet Type Constants

The `skb->pkt_type` field classifies received packets:

| Constant | Value | Meaning |
|----------|-------|---------|
| `PACKET_HOST` | 0 | Destined for this host |
| `PACKET_BROADCAST` | 1 | Link-layer broadcast |
| `PACKET_MULTICAST` | 2 | Link-layer multicast |
| `PACKET_OTHERHOST` | 3 | Destined for another host (promiscuous) |
| `PACKET_OUTGOING` | 4 | Outgoing packet |
| `PACKET_LOOPBACK` | 5 | MC/BRD frame looped back |

## Special Port Constants

`VMADDR_PORT_ANY` is defined as `-1U` (0xFFFFFFFF) in
`include/uapi/linux/vm_sockets.h` for the vsock subsystem. Port allocation
logic that iterates or wraps around port ranges must explicitly exclude this
sentinel value to avoid binding to the wildcard port.

## Quick Checks
- Validate packet lengths before `skb_put()`/`skb_push()`/`skb_pull()`
- Call `pskb_may_pull()` before dereferencing protocol headers
- Check `skb_shared()`/`skb_cloned()` before modifying SKB data
- Verify `htons()`/`ntohs()` conversions on all port and protocol comparisons
- Hold `rcu_read_lock()` during routing table lookups
- Use BH-safe stat update macros for per-CPU network counters
- Do not access an SKB after handing it to another subsystem
- Mask status/flag bits before exact-value comparisons on packet fields
- Check for flag value collisions when adding flags shared across subsystems
