- There is no global `ptype_all` list; the only `ptype_all` lists are in
  `struct net_device` and `struct net`.
- `ETH_P_ALL` with neither `pt->dev` nor `pt->af_packet_net`: `ptype_head()`
  returns NULL, `dev_add_pack()` hits `WARN_ON_ONCE()` and registers nothing.
- `ptype_base[]` is the only global list, and holds only handlers with a
  specific type, no device and no `af_packet_net`.
- `ptype_head()` is called before `ptype_lock` is taken, and
  `__dev_remove_pack()` calls it again to find the list.
- **Unsafe usage**: changing `pt->type`, `pt->dev` or `pt->af_packet_net`
  while the handler is registered.
  - Unsafe: when the change makes `ptype_head()` pick another list;
    `__dev_remove_pack()` then searches that list, prints "not found" and
    leaves the entry linked.
  - Safe: remove, change the fields, add again, as `packet_do_bind()` in
    `net/packet/af_packet.c` does with `__unregister_prot_hook()` before it
    writes `po->prot_hook.type` and `po->prot_hook.dev`.
- `deliver_skb()` when `skb_orphan_frags_rx()` fails: returns `-ENOMEM`
  without calling that handler and without freeing; the buffer goes on to the
  later handlers.
- `dev_queue_xmit_nit()`: makes one `skb_clone()` for all transmit taps and
  hands it out through `deliver_skb()` (the last tap is called directly), so
  transmit taps share one buffer just as receive handlers do.
