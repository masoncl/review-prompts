Client side:

- `struct rpc_clnt` reaches transports two ways: `cl_xprt` is the main
  transport, and the embedded `cl_xpi` (`struct rpc_xprt_iter`) points at the
  `struct rpc_xprt_switch`. Both pointers are RCU; a clone takes a reference
  on each of the parent's, see `__rpc_clone_client()` in `net/sunrpc/clnt.c`.
- `struct rpc_task`: its transport is `tk_xprt`, not `cl_xprt`.
  `rpc_task_set_transport()` takes it from the iterator, or from `cl_xprt`
  with `RPC_TASK_NO_ROUND_ROBIN`, and keeps it unless the task is
  `RPC_TASK_MOVEABLE` and the transport is `XPRT_OFFLINE`.
- `struct rpc_xprt` has a single `xprt_switch` list link, so it sits on one
  switch's `xps_xprt_list` at a time.
- `struct rpc_message`: `rpc_cred` is a `const struct cred *`, not a
  `struct rpc_cred`. The task references it only without
  `RPC_TASK_CRED_NOREF`, which `rpc_run_task()` sets for every sync task.
- `struct rpc_cred` belongs to the `struct rpc_rqst` (`rq_cred`), bound by
  `rpcauth_bindcred()` in `net/sunrpc/auth.c`. `tk_op_cred` on the task is
  set only to force one particular `struct rpc_cred`.
- `struct rpc_auth` is not one per client: `null_auth`, `unix_auth` and
  `tls_auth` are static objects shared by every client of that flavour.
  `gss_create()` shares one auth among clones that use the same switch,
  flavour and target name.
- Credential cache: only `net/sunrpc/auth_gss/auth_gss.c` calls
  `rpcauth_init_credcache()`. `unx_lookup_cred()` allocates a new
  `struct rpc_cred` on each lookup.
- `struct rpc_wait_queue` is a priority queue only when set up with
  `rpc_init_priority_wait_queue()`. Of the four queues in `struct rpc_xprt`,
  `xprt_init()` does that for `backlog` only.
- Waking a task: `rpc_make_runnable()` queues work for an async task, and for
  a sync task wakes the thread that sleeps in `__rpc_execute()`.
- `struct sunrpc_net` in `net/sunrpc/netns.h` lists clients (`all_clients`);
  it holds no list of transports.

Server side:

- `struct svc_pool`: one per NUMA node that has CPUs, and only for a service
  made by `svc_create_pooled()`, whose one caller is `fs/nfsd/nfssvc.c`. A
  `svc_create()` service (lockd, NFS callback) has exactly one pool.
- Per-CPU and global pool modes do not exist. `pool_mode_names` in
  `net/sunrpc/svc.c` is accepted on write and selects nothing.
- `struct svc_xprt` is not tied to a pool. Each `svc_xprt_enqueue()` picks one
  with `svc_pool_for_cpu()`: the pool of the calling CPU's node, or the next
  pool that has threads.
- Pool queues: ready transports are on `sp_xprts` (a `struct lwq`), idle
  threads on `sp_idle_threads`. A thread takes work from its own pool only.
- `struct svc_serv`: `sv_programs` is an array of `sv_nprogs`
  `struct svc_program`, not a linked list.

Where client and server objects cross (backchannel):

- Receiving callbacks on a client connection: `struct rpc_xprt` points at a
  `struct svc_serv` through `bc_serv`. The incoming call is a
  `struct rpc_rqst` queued on `sv_cb_list`; a thread of pool 0 runs it with
  `svc_process_bc()`.
- In `svc_process_bc()` the `struct svc_rqst` has `rq_xprt` NULL and borrows
  the buffers of the `struct rpc_rqst`. Use `SVC_NET()` for the namespace.
- Sending callbacks on a server connection: `struct svc_xprt` and
  `struct rpc_xprt` point at each other through `xpt_bc_xprt` and `bc_xprt`.
  The reply arrives in the server receive path, which finds the
  `struct rpc_rqst` by XID; see `receive_cb_reply()` in
  `net/sunrpc/svcsock.c`.
