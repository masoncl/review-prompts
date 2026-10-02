- Two generic-netlink families carry cache upcalls, beside the `channel`
  files:

  | Family | Caches | Spec | Notify helper | Handlers |
  |---|---|---|---|---|
  | `sunrpc` | `ip_map`, `unix_gid` | `Documentation/netlink/specs/sunrpc_cache.yaml` | `sunrpc_cache_notify()` | `net/sunrpc/svcauth_unix.c` |
  | `nfsd` | `svc_export`, `expkey` | `Documentation/netlink/specs/nfsd.yaml` | `nfsd_cache_notify()` in `fs/nfsd/nfsctl.c` | `fs/nfsd/export.c`; the flush handler is in `fs/nfsd/nfsctl.c` |

- Other caches (for example `auth.rpcsec.init`, `nfs4.idtoname`,
  `dns_resolve`): no `cache_notify` member set, so file channel only.
- Multicast: `SUNRPC_CMD_CACHE_NOTIFY` on group `SUNRPC_NLGRP_EXPORTD`
  ("exportd"), carrying one u32, `SUNRPC_A_CACHE_NOTIFY_CACHE_TYPE`; no
  request contents.
- `sunrpc_cache_notify()`: sends in `cd->net` with
  `genlmsg_multicast_netns()`; returns `-ENOLINK` without sending when
  `genl_has_listeners()` is false.
- `cache_do_upcall()`: calls `detail->cache_notify` after the request is on
  `cd->requests`, and ignores its return value.
- One queue for both channels: every request is queued on `cd->requests`
  whether or not a netlink listener exists.
- Fetch: a dump (`SUNRPC_CMD_IP_MAP_GET_REQS`,
  `SUNRPC_CMD_UNIX_GID_GET_REQS`) built from
  `sunrpc_cache_requests_snapshot()`; it reports only `CACHE_PENDING` entries
  and removes nothing from the queue.
- Reply: a do (`SUNRPC_CMD_IP_MAP_SET_REQS`,
  `SUNRPC_CMD_UNIX_GID_SET_REQS`); the entry is found by key, the `seqno`
  attribute is not read.
- Netlink handlers pick the cache from `genl_info_net(info)` (do) or
  `sock_net(skb->sk)` (dump); the get and set handlers return `-ENODEV` when
  the cache pointer is NULL, `sunrpc_nl_cache_flush_doit()` skips a NULL
  cache and returns 0.
- `sunrpc_nl_cache_flush_doit()`: calls `cache_purge()` on the caches in the
  mask; both when the mask is absent.
- Generated files `net/sunrpc/netlink.c` and `net/sunrpc/netlink.h` hold only
  policies, the ops table, the multicast group table, `sunrpc_nl_family` and
  the handler prototypes; `init_sunrpc()` registers the family.
- There is no cache_make_upcall(), sunrpc_cache_pipe_upcall() or
  sunrpc_cache_pipe_upcall_timeout() here; `cache_check_rcu()` calls
  `detail->cache_upcall()`, and caches use `sunrpc_cache_upcall()` or
  `sunrpc_cache_upcall_warn()`.
- `sunrpc_cache_upcall()`: queues even when nothing listens; `ip_map_upcall()`,
  `expkey_upcall()` and `svc_export_upcall()` use it.
- `sunrpc_cache_upcall_warn()`: returns `-EINVAL` without queueing or
  notifying when `cache_listeners_exist()` is false; `unix_gid_upcall()` uses
  it.
- `cache_listeners_exist()`: tests only `writers` and `last_close`, which
  `cache_open()` and `cache_release()` maintain for the `channel` file;
  netlink group membership is not tested.
- `rsc_upcall()`: returns `-EINVAL`, so a miss in `auth.rpcsec.context` never
  goes to user space; its `channel` is used for writes only.
- Request text: `cache_do_upcall()` queues a buffer with `len` 0;
  `cache_read()` calls the `cache_request` op on first read. Netlink dumps do
  not call `cache_request`.
- `struct cache_detail` has no queue member; requests are on `requests`,
  open readers on `readers`, each `struct cache_request` has a `seqno` from
  `next_seqno`.
- There is no cache_channel_operations_procfs or
  cache_channel_operations_pipefs; the tables are `cache_channel_proc_ops`
  and `cache_file_operations_pipefs`.
- rpc_pipefs files exist only for a cache registered with
  `sunrpc_cache_register_pipefs()`; `procfs` and `pipefs` share a union in
  `struct cache_detail`. `nfs_cache_register_sb()` in `fs/nfs/cache_lib.c` is
  the caller.
- `write_flush()`: checks that the input is a number, then ignores the value
  and flushes every entry.
