- `GENL_ADMIN_PERM`: `genl_family_rcv_msg()` in `net/netlink/genetlink.c`
  checks it with `netlink_capable()`, which tests `CAP_NET_ADMIN` in
  `init_user_ns`, for doit and dumpit alike. The owner of the socket's netns
  is not consulted.
- Operations without `GENL_ADMIN_PERM`: the four get doits, plus the
  rpc-status-get and server-stats-get dumps. Any process in the netns can read
  them, including client addresses of in-flight RPCs.
- Dumps with `GENL_ADMIN_PERM`: `NFSD_CMD_SVC_EXPORT_GET_REQS` and
  `NFSD_CMD_EXPKEY_GET_REQS`.
- `exportd` multicast group: its entry in `nfsd_nl_mcgrps[]` sets no `flags`
  (for example `GENL_MCAST_CAP_NET_ADMIN`), so joining needs no capability.
  The event carries only the cache type.
- `nfsd_cache_notify()`: has no request socket; it takes the netns from
  `cd->net` and sends with `genlmsg_multicast_netns()`.
- Credentials: netlink handlers pass `current_cred()` to `nfsd_svc()` and
  `svc_xprt_create_from_sa()`; the nfsctl files pass `file->f_cred`.
- Handlers not confined to the socket's netns:
  - `nfsd_nl_unlock_ip_doit()`: `nlmsvc_unlock_all_by_ip()` walks the global
    `nlm_files` table in `fs/lockd/svcsubs.c`; the netns is used only for the
    tracepoint.
  - `nfsd_nl_unlock_filesystem_doit()`: `nlmsvc_unlock_all_by_sb()` is global
    in the same way and runs before the `NFSD_NET_UP` test; only the NFSv4
    revocation is per-net.
