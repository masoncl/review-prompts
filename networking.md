# Networking Patterns

| Pattern | Check | Risk | Example |
|---------|-------|------|---------|
| **Packet Length** | Validate header->len before skb_put/pull | Buffer overflow | `len = le32_to_cpu(hdr->len); skb_put(skb, len)` needs bounds |
| **Socket UAF** | No access after release_sock() or socket_release() | Use-after-free | Check smc_listen_out_connected() cleanup paths |
| **Port Allocation** | Exclude VMADDR_PORT_ANY (-1U) in wraparound | Binding errors | Static counter wraparound to special values |
| **Packet Bit Fields** | Mask status bits before exact comparisons | Wrong matches | Event_Type with status in bits 5-6 needs `& DATA_MASK` |
| **NF_HOOK Device** | Set skb->dev before NF_HOOK calls | Wrong in/out devs | `skb->dev = new; NF_HOOK(..., skb->dev, ...)` |
| **Cross-Subsystem Flags** | Check flag value collisions between subsystems | Wrong behavior | SPLICE_F_NONBLOCK == MSG_PEEK collision |
| **Buffer Enqueue** | Extract data before enqueue/return operations | Use-after-free | After enqueue_reassembly(), buffer owned by other thread |

## Checks
- If header lengths are from an untrusted source, check values validated against actual skb size
  - Don't try to force defensive programming unless you can prove the header lengths are untrusted
- Socket fields not accessed after cleanup/release operations  
- Special port values excluded from allocation ranges
- Packet metadata bits masked before equality checks
- Device fields set correctly before netfilter hooks
- Flag conversions validated at subsystem boundaries
- No buffer access after handoff to other context
