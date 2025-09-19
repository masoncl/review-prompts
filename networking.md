# Networking Subsystem Delta

## Networking-Specific Patterns [NET]

| Pattern ID | Check | Risk | Details |
|------------|-------|------|---------|
| NET-001 | Packet length validation | Buffer overflow | Validate before skb_put/pull operations |
| NET-002 | Socket lifecycle | Use-after-free | No access after release_sock()/socket_release() |
| NET-003 | Port special values | Binding errors | Exclude VMADDR_PORT_ANY (-1U) in wraparound |
| NET-004 | Packet bit field masking | Wrong matches | Mask status bits before exact comparisons |
| NET-005 | NF_HOOK device setup | Wrong routing | Set skb->dev before NF_HOOK calls |
| NET-006 | Cross-subsystem flag collisions | Wrong behavior | Check flag value collisions between subsystems |
| NET-007 | Buffer handoff safety | Use-after-free | No access after enqueue/handoff operations |

## SKB Management
- SKBs can be cloned/shared - check skb_shared() before modifying
- skb_put/push/pull must stay within skb->end boundary
- pskb_may_pull() required before accessing variable-length headers

## Socket References
- sock_hold()/sock_put() for reference counting
- sk_refcnt reaching zero triggers sk_free()
- Socket can outlive its file descriptor

## Netfilter Hooks
- NF_HOOK* macros consume the skb on NF_STOLEN
- Device pointers must be valid throughout hook traversal
- okfn function called only on NF_ACCEPT

## Special Constants
- VMADDR_PORT_ANY = -1U (must exclude from port allocation)
- PACKET_HOST/BROADCAST/MULTICAST/OTHERHOST for pkt_type

## Quick Checks
- Header parsing from untrusted sources needs length validation
- Check for htons/ntohs byte order conversions
- RCU protection for routing table lookups
- BH (bottom half) disabled for per-cpu network stats
