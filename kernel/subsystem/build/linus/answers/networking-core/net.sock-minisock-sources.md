- Egress `skb->sk` can be a timewait sock, not only a request sock:
  `ip_send_unicast_reply()` and `tcp_v6_send_response()` re-own the RST or
  ACK reply to the original socket with `skb_set_owner_edemux()`.
- Reply sent through the per-cpu control socket (`ipv4_tcp_sk`): the control
  socket builds the skb, but `skb->sk` on the wire path is the original
  timewait or full socket when the caller passed one.
- `sk_listener_or_tw()` in `include/net/sock.h`: tests for a listener,
  request or timewait sock; its one caller is `fq_classify()` in
  `net/sched/sch_fq.c`, on egress `skb->sk`.
- `tcp_make_synack()` by `synack_type`:

| Type | `skb->sk` |
|---|---|
| `TCP_SYNACK_NORMAL`, `TCP_SYNACK_RETRANS` | request sock, `skb_set_owner_edemux()` |
| `TCP_SYNACK_COOKIE` | none |
| `TCP_SYNACK_FASTOPEN` | listener, `skb_set_owner_w()` |

- `bpf_sk_lookup_tcp()`: for a request sock returns its listener; for a
  timewait sock returns NULL; see `bpf_sk_lookup_full_sk()` in
  `net/core/filter.c`.
- `bpf_sk_assign_tcp_reqsk()` in `net/core/filter.c`: puts an unhashed
  syncookie request sock in ingress `skb->sk` with `sock_pfree()`.
- There is no inet_diag_dump_icsk() here; `tcp_diag_dump()` in
  `net/ipv4/tcp_diag.c` walks ehash and puts with `sock_gen_put()`.
- `tcp_v4_early_demux()` is a static function in `net/ipv4/ip_input.c`, and
  `tcp_v6_early_demux()` in `net/ipv6/ip6_input.c`.
