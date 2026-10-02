- There is no __udp4_lib_rcv() or __inet_hash() here; UDP receive is
  `udp_rcv()` in `net/ipv4/udp.c` and `udpv6_rcv()` in `net/ipv6/udp.c`, and
  `inet_hash()` sets `SOCK_RCU_FREE` on a TCP listener.
- `udp_rcv()` and `udpv6_rcv()`: `refcounted` covers only the socket from
  `inet_steal_sock()` or `inet6_steal_sock()`; the socket from
  `__udp4_lib_lookup_skb()` or `__udp6_lib_lookup_skb()` is used with no flag
  and no put.
- UDP sockets: not in a `SLAB_TYPESAFE_BY_RCU` cache; under `net/ipv4` and
  `net/ipv6` only the TCP protos set it, so `__udp4_lib_lookup()` and
  `__udp6_lib_lookup()` take no reference and have no key recheck after a
  reference, as `__inet_lookup_established()` has.
- `SOCK_RCU_FREE` is not limited to TCP listeners and UDP; search for
  `sock_set_flag(sk, SOCK_RCU_FREE)`, for example `raw_hash_sk()`.
- Early demux:

| Path | Reference | `skb->destructor` |
|---|---|---|
| `tcp_v4_early_demux()`, `tcp_v6_early_demux()` | always held | `sock_edemux()` |
| `udp_v4_early_demux()`, `udp_v6_early_demux()` | never held | `sock_pfree()` |

- `skb_steal_sock()` in `include/net/request_sock.h` sets `*refcounted`:
  - `skb->sk` NULL: `false`, returns NULL.
  - destructor is not `sock_pfree()`: `true`.
  - destructor is `sock_pfree()` and `sk` is a syncookie request sock
    (`CONFIG_SYN_COOKIES`): `false`, returns `rsk_listener`.
  - destructor is `sock_pfree()`, any other socket: `sk_is_refcounted(sk)`.
- `skb_steal_sock()` syncookie branch: leaves `skb->sk` and `skb->destructor`
  set; `cookie_bpf_check()` in `net/ipv4/syncookies.c` clears them.
- `sock_pfree()`: does nothing when `sk_is_refcounted()` is false; for a
  syncookie request sock it clears `rsk_listener` before `reqsk_free()`,
  because that listener pointer holds no reference.
- `tcp_v4_rcv()` changes `refcounted` after the lookup:
  - `TCP_TW_SYN`: `sk` becomes the `inet_lookup_listener()` result and
    `refcounted = false`.
  - `TCP_NEW_SYN_RECV`, listener still `TCP_LISTEN`: `sock_hold()` on
    `rsk_listener`, `refcounted = true`.
  - `TCP_NEW_SYN_RECV`, listener not `TCP_LISTEN`:
    `reuseport_migrate_sock()` returns a socket already referenced; no
    `sock_hold()`.
- `udp4_lib_lookup()`: compiled only with `CONFIG_NF_TPROXY_IPV4` or
  `CONFIG_NF_SOCKET_IPV4`; `udp6_lib_lookup()` only with the IPv6
  equivalents.
- `sk_lookup()` in `net/core/filter.c` (behind the BPF lookup helpers):
  returns `SOCK_RCU_FREE` sockets unreferenced; `bpf_sk_release()` puts only
  when `sk_is_refcounted()`.
