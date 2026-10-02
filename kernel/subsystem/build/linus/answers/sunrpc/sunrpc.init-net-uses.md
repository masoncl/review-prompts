- `init_net` is named in two places under `net/sunrpc/`; search for
  `init_net` and skip function names such as `sunrpc_init_net()`.
- `proc_dodebug()` in `net/sunrpc/sysctl.c`: a write to the `rpc_debug`
  sysctl calls `rpc_show_tasks(&init_net)`, which prints the tasks of
  clients on the initial namespace's `all_clients` list only.
- `proc_dodebug()` and `rpc_show_tasks()` are both compiled only under
  `CONFIG_SUNRPC_DEBUG`; the table is registered once with
  `register_sysctl()`, not per namespace.
- `NET_NAME()` in `net/sunrpc/rpc_pipe.c`: compares a pointer with
  `&init_net` to append " (init_net)" to two `dprintk()` messages, in
  `rpc_fill_super()` and `rpc_kill_sb()`; it selects no state.
- rpcbind, client creation, the `unix_gid` and `ip_map` caches, and the code
  under `net/sunrpc/auth_gss/` and `net/sunrpc/xprtrdma/` do not name
  `init_net`; no socket or connection identifier is created in it by
  default.
- `init_sunrpc()` in `net/sunrpc/sunrpc_syms.c` does not name `init_net`;
  per-net setup goes through `register_pernet_subsys()`.
- `&init_user_ns` (for example in `unix_gid_hash()` and
  `svcauth_unix_accept()`) is the user namespace, a different object.
