- `GENL_ADMIN_PERM`: `netlink_capable()` always checks against
  `&init_user_ns`, whether or not the family sets `netnsok`.
- Opener check: `__netlink_ns_capable()` in `net/netlink/af_netlink.c` skips
  `file_ns_capable()` when the skb has `NETLINK_SKB_DST`.
  `netlink_sendmsg()` sets that flag whenever the sender passed a
  destination address. `ns_capable()` on the current task is always
  required.
