# SunRPC Subsystem

## Main structures

### Objects and how they relate

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

## Where to look

**Source files**

| Job | File | Easy to miss |
|---|---|---|
| Netlink family, policies, ops table | `net/sunrpc/netlink.c` | generated from `Documentation/netlink/specs/sunrpc_cache.yaml`; covers only the `ip_map` and `unix_gid` caches and a cache flush |
| Netlink `doit` and `dumpit` handlers | `net/sunrpc/svcauth_unix.c` | all five handlers named in `sunrpc_nl_ops[]` are defined here |
| Netlink notify and family registration | `net/sunrpc/cache.c`, `net/sunrpc/sunrpc_syms.c` | `sunrpc_cache_notify()` is the multicast sender; `init_sunrpc()` registers `sunrpc_nl_family` |
| Backchannel, callback receiver | `net/sunrpc/backchannel_rqst.c` | calls are processed by `svc_process_bc()` in `net/sunrpc/svc.c`, called from `svc_recv()`; there is no bc_svc_process() |
| Backchannel, callback sender on sockets | `net/sunrpc/xprtsock.c` | `bc_tcp_ops`; replies arrive in `receive_cb_reply()` in `net/sunrpc/svcsock.c` |
| GSS server side, gss-proxy upcall | `net/sunrpc/auth_gss/gss_rpc_upcall.c`, `net/sunrpc/auth_gss/gss_rpc_xdr.c` | the upcall is `gssp_accept_sec_context_upcall()`, called from `net/sunrpc/auth_gss/svcauth_gss.c` |
| GSS Kerberos mechanism | `net/sunrpc/auth_gss/gss_krb5_mech.c` | module is the five `rpcsec_gss_krb5-y` objects in `net/sunrpc/auth_gss/Makefile`; there is no gss_krb5_keys.c |
| Kerberos enctypes and key derivation | `crypto/krb5/` | `RPCSEC_GSS_KRB5` selects `CRYPTO_KRB5`; `net/sunrpc/auth_gss/gss_krb5_mech.c` calls `crypto_krb5_prepare_encryption()` |
| RDMA module init | `net/sunrpc/xprtrdma/module.c` | `rpc_rdma_init()` only calls `rpcrdma_ib_client_register()`, `svc_rdma_init()`, `xprt_rdma_init()`, and on failure their cleanups |
| RDMA client transport class registration | `net/sunrpc/xprtrdma/transport.c` | `xprt_rdma_init()` registers `xprt_rdma` and `xprt_rdma_bc` |
| RDMA server transport class registration | `net/sunrpc/xprtrdma/svc_rdma.c` | `svc_rdma_init()` registers `svc_rdma_class`, which is defined in `net/sunrpc/xprtrdma/svc_rdma_transport.c`; the file also holds the server sysctls |
| RDMA device registration and removal | `net/sunrpc/xprtrdma/ib_client.c` | `struct ib_client`; `rpcrdma_rn_register()` gives removal notification |
| RDMA client memory registration | `net/sunrpc/xprtrdma/frwr_ops.c` | |
| RDMA backchannel, callback receiver | `net/sunrpc/xprtrdma/backchannel.c` | built only with `CONFIG_SUNRPC_BACKCHANNEL` |
| RDMA backchannel, callback sender | `net/sunrpc/xprtrdma/svc_rdma_backchannel.c` | in `rpcrdma-y`, so built without `CONFIG_SUNRPC_BACKCHANNEL` too; defines the client-type `struct xprt_class xprt_rdma_bc` |

## Server threads and requests

**Per-thread and per-request state**

- There is no svc_rqst_alloc() here; `svc_prepare_thread()` in
  `net/sunrpc/svc.c` allocates the `struct svc_rqst` and links it to the pool.
- `XPT_BUSY` is not held for the length of a request: `svc_xprt_received()`
  clears it, and the receive method calls that before it returns, for example
  `svc_tcp_recvfrom()` and `svc_rdma_recvfrom()`.
- `svc_xprt_release()` does not clear `XPT_BUSY`; another thread can be
  receiving on the same transport while this request is processed.
- `struct svc_serv` has no sv_nrpools field; use `svc_serv_nrpools()`, which
  returns `svc_pool_map.npools` when `sv_is_pooled` is set and 1 otherwise.
- `struct svc_rqst` has no rq_xprt_hlen field.
- `struct svc_pool` has no sp_sockets list; `sp_xprts` is a `struct lwq`
  linked through `xpt_ready`.
- There is no xpo_reserve_space method; the reply reservation is
  `rq_reserved`, added to `xpt_reserved` in `svc_handle_xprt()` after the
  receive method returns.
- `rq_server` and `xpt_server` are uncounted pointers: `struct svc_serv` has
  no reference count, and `svc_destroy()` frees it after only a `WARN_ONCE()`
  if `sv_permsocks` or `sv_tempsocks` is not empty.

**Service thread lifecycle**

| Function | Runs in | Service mutex |
|---|---|---|
| `svc_new_thread()` | controller, or `nfsd()` growing its own pool | held by the caller |
| `svc_thread_init_status()` | the new thread | not taken by the thread; the creator holds it and waits |
| `svc_exit_thread()` | the exiting thread, or `svc_new_thread()` on failure | held by someone: the controller waiting in `svc_stop_kthreads()`, the caller of `svc_new_thread()`, or the thread itself |

- "Service mutex" is the service's own lock: `nfsd_mutex`, `nlmsvc_mutex` or
  `nfs_callback_mutex`; none of the three functions takes or asserts it.
- `svc_prepare_thread()` takes no lock: it changes `sv_nrthreads`,
  `sp_nrthreads` and `sp_all_threads` under the caller's mutex alone, not
  under `sv_lock`.
- `svc_exit_thread()` changes the same three with no lock around them; it
  takes `sv_lock` only afterwards, inside `svc_sock_update_bufs()`.
- Failed initialisation: `svc_thread_init_status()` with a nonzero error ends
  in `kthread_exit()`, so the thread never calls `svc_exit_thread()`;
  `svc_new_thread()` calls it on the thread's behalf.
- `kthread_create_on_node()` failure: `svc_new_thread()` likewise calls
  `svc_exit_thread()` itself.

**Stopping a thread**

- There is no svc_pool_victim() here; `svc_stop_kthreads()` works on the pool
  that `svc_set_pool_threads()` passes it.

| Flag | Set by | Cleared by |
|---|---|---|
| `SP_VICTIM_REMAINS` | `svc_stop_kthreads()` | `svc_exit_thread()`, on every call |
| `SP_NEED_VICTIM` | `svc_stop_kthreads()` | the thread that wins `svc_thread_should_stop()` |
| `RQ_VICTIM` | `svc_thread_should_stop()`, or `nfsd()` directly when it retires itself | never |

- `svc_exit_thread()` never clears `SP_NEED_VICTIM`.
- **Potentially unsafe usage**: a thread calling `svc_exit_thread()` while
  holding no lock.
  - Unsafe: when it left its loop for a reason other than claiming
    `SP_NEED_VICTIM`; `svc_exit_thread()` then changes `sp_nrthreads`,
    `sv_nrthreads` and `sp_all_threads` unlocked, and its clear of
    `SP_VICTIM_REMAINS` can release a controller waiting for another thread.
  - Safe: when `svc_thread_should_stop()` claimed `SP_NEED_VICTIM`, as in
    `lockd()` and `nfs4_callback_svc()`; the caller of `svc_stop_kthreads()`
    holds the service mutex for the whole wait.
  - Safe: when the thread took the service mutex with `mutex_trylock()` and
    holds it across `svc_exit_thread()`, as `nfsd()` does on `-ETIMEDOUT`.
- **Unsafe usage**: a service thread sleeping in `mutex_lock()` on the
  service mutex; the controller holds it while waiting in
  `svc_stop_kthreads()` for that thread to exit.
  - Safe: `mutex_trylock()`, giving up on failure, as `nfsd()` does.
- `kthread_stop()` is not used on a service thread; the only thread functions
  are `nfsd()`, `lockd()` and `nfs4_callback_svc()`.

**Thread count range**

- A pool has a range: `sp_nrthrmin` and `sp_nrthrmax` in `struct svc_pool`,
  set by `svc_set_pool_threads(serv, pool, min_threads, max_threads)`.
- `min_threads` nonzero: the count changes only when outside the range, so a
  pool started from zero runs `min_threads` threads.
- `min_threads` zero, or above `max_threads`: the pool runs exactly
  `max_threads` threads.
- `svc_set_num_threads(serv, min_threads, nrservs)`: divides `nrservs` over
  the pools, gives every pool at least one thread when `nrservs` is nonzero,
  and passes `min_threads` to each pool unchanged.
- `svc_recv()` is `int svc_recv(struct svc_rqst *rqstp, long timeo)`.

| Return | All of these hold |
|---|---|
| `-ETIMEDOUT` | the sleep timed out; `svc_thread_should_sleep()` is still true; `sp_nrthrmin` is nonzero; `sp_nrthreads > sp_nrthrmin` |
| `-EBUSY` | a transport was dequeued; `sp_idle_threads` is empty; `timeo` is nonzero; the sleep did not time out; this thread won `test_and_set_bit()` on `SP_TASK_STARTING` |
| 0 | otherwise |

- `svc_recv()` does not read `sp_nrthrmax`; the caller makes that test.
- `SP_TASK_STARTING` is the limiting flag, not `SP_TASK_PENDING`;
  `svc_recv()` sets it and never clears it.
- `nfsd()` in `fs/nfsd/nfssvc.c` is the only caller that acts on the return:
  it takes `nfsd_mutex` with `mutex_trylock()`, tests the count again, then
  calls `svc_new_thread()` or sets `RQ_VICTIM` on itself.
- `lockd()` and `nfs4_callback_svc()` pass `timeo` 0 and ignore the return;
  with `timeo` 0 neither signal is returned.
- **Unsafe usage**: a thread function that receives `-EBUSY` and leaves
  `SP_TASK_STARTING` set; the pool gets no further `-EBUSY`.
  - Safe: clearing it on every `-EBUSY` path, spawned or not, as `nfsd()`
    does.
  - Safe: passing `timeo` 0, as `lockd()` does; the flag is then never set.

**Request and reply pages**

- Two arrays, allocated separately in `svc_init_buffer()`: `rq_pages` holds
  the Call, `rq_respages` holds the Reply; `rq_respages` is not a pointer
  into `rq_pages`.

| Field | Array | Meaning |
|---|---|---|
| `rq_maxpages` | both | usable entries per array; each allocation has one more entry, a NULL sentinel |
| `rq_pages_nfree` | `rq_pages` | number of leading entries `svc_alloc_arg()` must refill |
| `rq_next_page` | `rq_respages` | next reply slot; also the end of the range released and refilled |
| `rq_page_end` | `rq_respages` | `&rq_respages[rq_maxpages]`, set by `svc_alloc_arg()` |

- `svc_serv_maxpages()` sizes each array, not the pair.
- `svc_init_buffer()` allocates no pages; it sets `rq_pages_nfree` and
  `rq_next_page` so that the first `svc_alloc_arg()` fills both arrays.
- `svc_alloc_arg()` does not scan the whole arrays: it refills
  `rq_pages[0 .. rq_pages_nfree)` and `rq_respages` up to `rq_next_page`,
  then resets `rq_next_page` to `rq_respages`.
- `svc_rqst_release_pages()` walks `rq_respages` only; `svc_xprt_release()`
  releases no `rq_pages` entries.
- A reply slot at or past `rq_next_page` when the request ends is neither
  released nor refilled; `nfsd4_encode_operation()` and the NFSv3 readdir
  code keep `rq_next_page` in step with `xdr->page_ptr` for that reason.
- `net/sunrpc/svcsock.c` writes neither `rq_respages` nor `rq_next_page`;
  `svc_process()` sets `rq_next_page` to `&rq_respages[1]`.
- **Unsafe usage**: a receive path that sets an `rq_pages` entry to NULL and
  leaves it outside `rq_pages[0 .. rq_pages_nfree)`; `svc_alloc_arg()` does
  not refill it and the next receive uses a NULL page.
  - Safe: move the leading n entries out, NULL each, and set
    `rq_pages_nfree` to n, as `svc_tcp_save_pages()` and
    `svc_rdma_clear_rqst_pages()` do.
  - Safe: overwrite an entry with another page after releasing the old one,
    with no count, as `svc_tcp_restore_pages()` and `svc_rdma_read_complete()`
    do.
  - Safe: NULL `rq_respages` entries below `rq_next_page` in a send path, as
    `svc_rdma_save_io_pages()` does; the reply refill covers that range.

**Processing one request**

- `pc_release` runs after the reply is sent: `svc_process()` calls
  `svc_send()`, then `svc_release_rqst()`, which is the only caller of
  `pc_release` in the tree.
- `svc_process_common()` does not call `pc_release`.
- Request dropped by `svc_process_common()`: `svc_process()` calls
  `svc_release_rqst()` before `svc_drop()`.
- `svc_release_rqst()` clears `rq_procinfo`, and `svc_process()` clears it on
  entry, so the hook runs at most once per request.
- `svc_xprt_release()` is called from `svc_handle_xprt()` after
  `svc_process()` returns, not from `svc_send()` or `svc_drop()`;
  `svc_drop()` only traces.
- Order for a sent reply: `svc_send()`, `pc_release`, `svc_xprt_release()`;
  the hook runs with `rq_xprt` set.
- There is no SVC_SYSERR or SVC_NEGOTIATE value in `enum svc_auth_status`.

| Value | `svc_process_common()` |
|---|---|
| `SVC_OK` | goes on to `pg_init_request` and the dispatch |
| `SVC_DENIED` | sends an `RPC_AUTH_ERROR` denial with `rq_auth_stat` unchanged |
| `SVC_DROP` | `svc_authorise()`, returns 0; no reply, transport not closed |
| `SVC_GARBAGE` | sets `rq_auth_stat` to `rpc_autherr_badcred`, sends an `RPC_AUTH_ERROR` denial; does not encode `rpc_garbage_args` |
| `SVC_CLOSE` | `svc_authorise()`, then `svc_xprt_close()` only if `rq_xprt` has `XPT_TEMP`; no reply |
| `SVC_COMPLETE` | the reply is encoded but not sent; goes through `svc_authorise()` and returns 1 so `svc_process()` sends it |
| `SVC_VALID`, `SVC_NEGATIVE`, `SVC_PENDING` | `pr_warn_once()`, `rq_auth_stat` set to `rpc_autherr_failed`, `RPC_AUTH_ERROR` denial |

**Replacing a reply page**

- `svc_rqst_replace_page()` checks one thing: that `rq_next_page` lies from
  `rq_respages` to `rq_page_end`, both ends included; it does not look at
  `rq_pages` or at `page`.
- At `rq_page_end` the call succeeds and writes the sentinel entry that
  `svc_init_buffer()` allocates; one slot further it returns `false`.
- Returns `bool`; on `false` nothing is stored and `rq_next_page` does not
  move.
- Displaced page: goes through `svc_rqst_page_release()` into `rq_fbatch`
  (`struct svc_rqst` has no rq_batch field), freed when the batch fills or in
  `svc_rqst_release_pages()`; it is not passed to `put_page()` directly.
- New page: the function takes its own reference with `get_page()`; the
  caller keeps the one it has.
- `svc_rqst_replace_page()` has no position argument and touches no `rq_res`
  field: the caller keeps `rq_next_page` at the reply's next data slot and
  maintains `rq_res.page_base` and `rq_res.page_len`.
- `nfsd_splice_actor()` in `fs/nfsd/vfs.c` is the only caller.
- **Unsafe usage**: counting a page's bytes into `rq_res.page_len` after
  `svc_rqst_replace_page()` returned `false`; the reply then covers a page
  it does not hold.
  - Safe: fail the read first, as `nfsd_splice_actor()` returns `-EIO`
    before it adds `sd->len`.
- **Potentially unsafe usage**: installing the page that already sits in
  `*(rq_next_page - 1)`.
  - Unsafe: when the reply data so far ends inside that page, so
    `rq_res.page_base + rq_res.page_len` is not page aligned; the page would
    be listed twice for one contiguous range.
  - Safe: when the data so far ends on a page boundary; the same page can
    legitimately repeat, and `nfsd_splice_actor()` skips the call only in the
    unaligned case.
- **Unsafe usage**: splicing pages into a reply whose `rq_res.page_len` is
  already nonzero from XDR encoding; `nfsd_splice_actor()` sets
  `rq_res.page_base` only when `rq_res.page_len` is 0.
  - Safe: refuse first, as `nfsd4_encode_splice_read()` returns
    `nfserr_serverfault` when `xdr->buf->page_len` is nonzero.
  - Safe: with no test in `nfsd_read()`, reached only from the NFSv2 and
    NFSv3 READ procedures; `svc_process()` set `rq_res.page_len` to 0 and
    nothing is encoded into pages before the procedure runs.

## Server transports

**Server transport flags**

- Bits that make a transport ready: the five that `svc_xprt_ready()` tests,
  `XPT_CONN`, `XPT_CLOSE`, `XPT_HANDSHAKE`, `XPT_DATA`, `XPT_DEFERRED`.
- `svc_handle_xprt()`: tests `XPT_CLOSE`, then `XPT_LISTENER`, then
  `XPT_HANDSHAKE`, and otherwise receives; it tests neither `XPT_CONN` nor
  `XPT_DATA`, so an `xpo_accept` or `xpo_recvfrom` that leaves its bit set
  with nothing pending is dequeued again at once.
- `XPT_CONN`: cleared by `xpo_accept`, not by `xpo_recvfrom`;
  `svc_tcp_accept()` sets it again after a successful accept,
  `svc_rdma_accept()` while `sc_accept_q` is not empty.
- `XPT_DATA` on RDMA: `svc_rdma_recvfrom()` clears it only when
  `sc_rq_dto_q` is empty; the socket methods clear it on entry and set it
  again if more may be queued.
- `XPT_KILL_TEMP`: a request, not a property; honoured only in the
  `XPT_CLOSE` branch of `svc_handle_xprt()`. `svc_xprt_close()` and
  `svc_clean_up_xprts()` reach `svc_delete_xprt()` without calling
  `xpo_kill_temp_xprt`.
- `XPT_CHNGBUF`: does not make a transport ready; it waits for the next
  `svc_udp_recvfrom()`, which test-and-clears it. `svc_sock_update_bufs()`
  sets it on every transport on `sv_permsocks`, and no other receive method
  consumes it.
- `XPT_RPCB_UNREG`: set by `svc_udp_init()` and, for a listener, by
  `svc_tcp_init()`; `svc_delete_xprt()` tests it and unregisters from
  rpcbind. That code casts the transport to `struct svc_sock`, so only a
  socket transport may set the bit.
- `XPT_PEER_VALID`: set once, on an `XPT_TEMP` transport only, by
  `svc_xprt_set_valid()`, which also decrements `sv_tmpcnt`;
  `svc_check_conn_limits()` closes only transports without it.

**Transport busy bit**

- Setters: `svc_xprt_init()` (a new transport starts busy),
  `svc_xprt_enqueue()` and `svc_xprt_close()`. Only `svc_xprt_received()`
  clears; no transport code touches the bit.
- `XPT_HANDSHAKE` branch: `svc_handle_xprt()` calls `svc_xprt_received()`
  after `xpo_handshake` returns; `svc_tcp_handshake()` does not, so the bit
  is held for the whole handshake wait.
- Deferred branch: `svc_deferred_recv()` calls `svc_xprt_received()`;
  `svc_handle_xprt()` does not.
- `svc_xprt_received()`: after clearing the bit it calls
  `svc_xprt_enqueue()` only if one of `XPT_CONN`, `XPT_CLOSE`,
  `XPT_HANDSHAKE`, `XPT_DATA`, `XPT_DEFERRED` is set.
- A bit added to `svc_xprt_ready()` and not to the mask in
  `svc_xprt_received()`: an event that sets it while the transport is busy
  is not picked up when the owner releases the transport.
- `svc_xprt_received()` does not change `xpt_reserved` or `xpt_nr_rqsts`.
- **Potentially unsafe usage**: changing state that `svc_xprt_ready()` reads
  and relying on the busy owner's `svc_xprt_received()` to notice it,
  without setting one of the five bits.
  - Unsafe: when the change alone is meant to make the transport ready, with
    none of the five bits set; `svc_xprt_received()` then skips
    `svc_xprt_enqueue()`.
  - Safe: set the bit, then call `svc_xprt_enqueue()`, as
    `svc_data_ready()` and `svc_revisit()` do; the mask in
    `svc_xprt_received()` then covers the case where the transport was busy.
  - Safe: when the state only gates `XPT_DATA` or `XPT_DEFERRED` in
    `svc_xprt_ready()` (write space, `xpt_nr_rqsts`), as in
    `svc_xprt_resource_released()` and `svc_write_space()`; both bits are
    in the mask in `svc_xprt_received()`.

**Enqueue conditions**

- `svc_reserve()` and `svc_xprt_release_slot()`: neither calls
  `svc_xprt_enqueue()` directly. Both call `svc_xprt_resource_released()`,
  which enqueues only if `XPT_DATA` or `XPT_DEFERRED` is set and `XPT_BUSY`
  is clear.
- Barriers: `smp_rmb()` at the top of `svc_xprt_ready()`, `smp_mb()` in
  `svc_xprt_resource_released()` between the counter update and the flags
  read, `smp_mb__before_atomic()` before the clear in
  `svc_xprt_received()`. `net/sunrpc/svc_xprt.c` has no `smp_wmb()`.
- `xpt_reserved`: read only by `svc_udp_has_wspace()`. For TCP and RDMA the
  reservation is kept but does not decide readiness.
- `svc_tcp_has_wspace()`: 1 for a listener, otherwise the inverse of
  `SOCK_NOSPACE` on the socket; it does no arithmetic on send space.
- `svc_rdma_has_wspace()`: 0 while any sender waits on `sc_send_wait` or
  `sc_sq_ticket_wait`.
- Request limit: module parameter `svc_rpc_per_connection_limit`, tested
  against `xpt_nr_rqsts` in `svc_xprt_slots_in_range()`; it is not a
  transport credit count.
- `svc_handle_xprt()` adds `sv_max_mesg` to `xpt_reserved` after
  `xpo_recvfrom` or `svc_deferred_recv()` has already cleared `XPT_BUSY`, so
  a second thread can pass the write-space test before the first
  reservation is counted.
- `svc_write_space()`: calls `svc_xprt_enqueue()` without setting a bit; the
  transport is queued only if one of the five ready bits is already set.

**Server transport references**

- `sp_xprts` queue entry: no reference. `svc_xprt_enqueue()` takes none;
  `svc_xprt_dequeue()` takes the thread's reference after `lwq_dequeue()`.
- `bc_xprt` in `struct rpc_xprt`: no reference; `xs_setup_bc_tcp()` and
  `xprt_setup_rdma_bc()` assign it plainly. The reverse pointer
  `xpt_bc_xprt` does hold one on the `struct rpc_xprt`.
- nfsd holds references in `cn_xprt` (`alloc_conn()`, dropped by
  `free_conn()`) and in `cl_cb_conn.cb_xprt` (`fs/nfsd/nfs4callback.c`).
- `svc_find_xprt()` and `svc_find_listener()`: return with a reference that
  the caller must put.
- `svc_age_temp_xprts()`: skips a transport whose `kref_read()` is above 1,
  so any long-held reference also exempts the connection from idle ageing.
- `svc_tcp_handshake()`: takes `svc_xprt_get()` before
  `tls_server_hello_x509()`; `svc_tcp_handshake_done()` puts it as its last
  step, after `complete_all()`.
- `svc_tcp_handshake()` puts the reference itself on the two paths where the
  callback never runs: `tls_server_hello_x509()` failed, or
  `tls_handshake_cancel()` returned true.
- `tls_handshake_cancel()` returning false: the callback is in flight;
  `svc_tcp_handshake()` then does `wait_for_completion()` and leaves the put
  to the callback.
- **Potentially unsafe usage**: giving a `struct svc_xprt` pointer to a
  callback that runs later, without `svc_xprt_get()`.
  - Unsafe: when the callback can run, or still be running, after the
    submitter's own reference is put; `svc_xprt_free()` calls `xpo_free`,
    which frees the structure.
  - Safe: take a reference before submitting and put it exactly once on
    every outcome, as `svc_tcp_handshake()` and `svc_tcp_handshake_done()`
    do, and as `svc_defer()` and `svc_revisit()` do.
  - Safe: when `xpo_free` stops the source of callbacks before it frees, as
    `svc_rdma_free()` does: it drains and destroys the QP, the CQs and the
    CM ID before `kfree()`.

**Closing a server transport**

- `svc_xprt_close()`: needs no ownership. It sets `XPT_CLOSE` and tries
  `test_and_set_bit(XPT_BUSY)` itself; it deletes inline only if it won the
  bit.
- `svc_xprt_close()` when `XPT_BUSY` was already set: does not enqueue. The
  owner's `svc_xprt_received()` enqueues the transport, and the thread that
  dequeues it deletes it in `svc_handle_xprt()`.
- `svc_xprt_close()` needs process context: `svc_delete_xprt()` sleeps in
  `lock_sock()` under `svc_sock_detach()` and in `svc_register()`.
- A server thread may call `svc_xprt_close()` on its own `rq_xprt`:
  `svc_process_common()` does so for an `XPT_TEMP` transport; the thread's
  reference keeps the structure until `svc_xprt_release()`.
- `svc_delete_xprt()`, in order:
  1. if `XPT_RPCB_UNREG` is set, `svc_register()` with port 0; this runs
     before the `XPT_DEAD` test;
  2. `test_and_set_bit(XPT_DEAD)`, return if it was set;
  3. `xpo_detach`;
  4. `close` of `xpt_bc_xprt`, if set;
  5. under `sv_lock`: `list_del_init()` of `xpt_list`, and `sv_tmpcnt--`
     only if `XPT_TEMP` is set and `XPT_PEER_VALID` is clear;
  6. `free_deferred()` of everything left on `xpt_deferred`;
  7. `call_xpt_users()`;
  8. `svc_xprt_put()` of the reference from `kref_init()` in
     `svc_xprt_init()`.
- `svc_delete_xprt()` does not call `xpo_kill_temp_xprt` and does not take
  the transport off `sp_xprts`.
- `call_xpt_users()`: runs each callback with `xpt_lock` held, so a callback
  cannot sleep or call `register_xpt_user()` or `unregister_xpt_user()` on
  that transport.

**Deferred requests**

- `svc_defer()` refuses a request on two tests only: `rq_arg.page_len`
  non-zero, or `RQ_USEDEFERRAL` clear in `rq_flags`. There is no
  rq_usedeferral field, and no test for backchannel or transport type.
- `RQ_USEDEFERRAL`: `svc_process_common()` sets it for every request.
  NFSv4 clears it in `nfs4svc_decode_compoundargs()` and
  `nfsd4_proc_compound()`, both after `svc_authenticate()` and
  `pg_authenticate`, so cache lookups during authentication can still defer
  an NFSv4 request.
- The defer hook has a caller outside the cache: `nlmsvc_defer_lock_rqst()`
  in `fs/lockd/svclock.c` calls `rq_chandle.defer`; `retry_deferred_block()`
  later calls `revisit`.
- `svc_revisit()`: sets `XPT_DEFERRED` under `xpt_lock` before it tests
  `too_many` and `XPT_DEAD`, so the bit can be set with nothing queued;
  `svc_deferred_dequeue()` clears it on finding the list empty.
- `free_deferred()`: calls `xpo_release_ctxt` on `dr->xprt_ctxt` before
  `kfree()`; a bare `kfree()` of a deferred request leaks the context (for
  UDP, the skb).
- `xpo_release_ctxt`: is called with a NULL context, by `svc_xprt_release()`
  for a request that has none and by `free_deferred()` after
  `svc_deferred_recv()` took the context back; every implementation must
  accept NULL.
- Service shutdown: `svc_destroy()` calls `cache_clean_deferred()`, which
  calls `svc_revisit()` with `too_many` set, so requests still waiting in
  the cache are freed there.

**Server socket callbacks**

- A child of a listener inherits `sk_user_data` as well as `sk_data_ready`:
  `sk_clone()` in `net/core/sock.c` clears the field only when
  `sk_user_data_is_nocopy()`, and `svc_setup_socket()` stores an untagged
  pointer.
- On the child, `sk_user_data` is therefore non-NULL and points to the
  listener's `struct svc_sock`, on which the child holds no reference; the
  NULL test does not catch this case.
- `svc_tcp_listen_data_ready()` is the only server callback a child
  inherits: `svc_tcp_init()` installs only `sk_data_ready` on a listener.
- The callbacks take no lock: `net/sunrpc/svcsock.c` uses neither
  `sk_callback_lock` nor RCU for `sk_user_data`.
- `svc_setup_socket()` order: save the three original callbacks in
  `struct svc_sock`, `wmb()`, store `sk_user_data`, then `svc_tcp_init()` or
  `svc_udp_init()` runs `svc_xprt_init()` and only then installs the new
  callbacks.
- `svc_tcp_accept()`: resets the child's three callbacks to the listener's
  saved originals before it calls `svc_setup_socket()`; otherwise the
  child's `sk_odata` would be `svc_tcp_listen_data_ready()`.
- **Potentially unsafe usage**: dereferencing `sk_user_data` in a socket
  callback after only the NULL test and `rmb()`.
  - Unsafe: in a callback installed on a listening socket, where it also
    runs on unaccepted children with the listener's pointer.
  - Safe: in a listener callback that returns when `sk_state` is not
    `TCP_LISTEN` before touching the pointer, as
    `svc_tcp_listen_data_ready()` does.
  - Safe: in callbacks installed only on connected TCP or UDP sockets, as
    `svc_data_ready()`, `svc_write_space()` and `svc_tcp_state_change()`
    are; those sockets have no children.

**TCP record reassembly**

- `sk_pages`: a flexible array at the end of `struct svc_sock` with
  `sk_maxpages` entries, sized by `svc_serv_maxpages()` in
  `svc_setup_socket()`.
- `svc_tcp_save_pages()`: besides moving the pages it sets
  `rq_pages_nfree`; `svc_alloc_arg()` refills only that many entries of
  `rq_pages`.
- `svc_tcp_restore_pages()`: releases the thread's own page in each slot
  with `svc_rqst_page_release()` before it puts the saved page there.
- Record length: there is no sk_reclen field; `svc_sock_reclen()` masks
  `sk_marker`. The bound is `sv_max_mesg`, not `svc_max_payload()`.
- Oversized record: `svc_tcp_read_marker()` calls
  `svc_xprt_deferred_close()` itself and returns `-EAGAIN`, so
  `svc_tcp_recvfrom()` takes its no-close exit.
- End of stream: a 0 return from the socket is a short read, not an error;
  the receive path keeps the state and does not close.
  `svc_tcp_state_change()` closes when `sk_state` leaves `TCP_ESTABLISHED`.
- TLS: `svc_tcp_sock_process_cmsg()` turns a fatal alert into `-ENOTCONN`,
  which closes; a non-fatal alert becomes `-EAGAIN`.
- Backchannel reply: `receive_cb_reply()` returns `-EAGAIN` when
  `xpt_bc_xprt` is NULL, no request matches the XID, or the reply buffer is
  too small; the record is dropped and the connection stays open.

## Client transports

**Client transport state bits**

- `XPRT_CONGESTED`: the slot table is full. Set only by `xprt_add_backlog()`,
  cleared by `xprt_wake_up_backlog()` when no waiter is left.
- `XPRT_CWND_WAIT`: the congestion window is full. Set from
  `__xprt_get_cong()`, but not when the head of `xmit_queue` already holds a
  credit; see `xprt_set_congestion_window_wait()`.
- `xprt_reserve_xprt_cong()`: takes no credit, it only tests
  `XPRT_CWND_WAIT`. The credit is taken by `xprt_request_get_cong()` in the
  send path, for example `xs_udp_send_request()` and
  `xprt_rdma_send_request()`, which return `-EBADSLT` when the window is full.
- `xprt_rdma_procs` never sets `XPRT_CONGESTED`: `xprt_rdma_alloc_slot()`
  queues with `xprt_add_backlog_noncongested()`, so
  `xprt_throttle_congested()` never diverts a reserver on that transport.
- The window is used only by ops tables that install
  `xprt_reserve_xprt_cong()`: `xs_udp_ops`, `xprt_rdma_procs` and
  `xprt_rdma_bc_procs`.
- `xprt_rdma_bc_procs` is a backchannel table that installs the congestion
  variants; `bc_tcp_ops` is the one that does not.
- `xs_tcp_ops` also serves TCP with TLS; it and `xs_local_ops` have no window.
- `XPRT_LOCKED` with `snd_task == NULL`: taken by `test_and_set_bit()` or
  `wait_on_bit_lock()` and released with `xprt_release_write(xprt, NULL)`; for
  example `xprt_autoclose()`, `rpc_sysfs_xprt_state_change()`,
  `rpc_xprt_offline()`, and `xs_tcp_tls_setup_socket()` on the lower transport.
- `xprt_destroy()`: takes `XPRT_LOCKED` and never releases it.
- `XPRT_SND_IS_COOKIE`: `snd_task` holds the connect worker's cookie, not a
  task; `xprt_schedule_autoclose_locked()` tests it before waking `snd_task`.
- `xprt_clear_locked()` with `XPRT_CLOSE_WAIT` set: leaves `XPRT_LOCKED` set
  and queues `task_cleanup`, so the lock passes to `xprt_autoclose()`.
- `XPRT_CLOSE_WAIT`: a close has been requested for any reason. Set by
  `xprt_schedule_autoclose_locked()` and by `xs_reset_transport()` when not on
  a worker; `xs_tcp_state_change()` only clears it.
- `XPRT_CLOSE_WAIT` set: `xprt_request_transmit()` returns `-ENOTCONN` and
  `xprt_connect()` does not start a connect.
- `XPRT_CLOSING` set: `xprt_conditional_disconnect()` does nothing, and
  `xprt_connect()` leaves the task asleep on `pending` without connecting.

**Client transport locks**

| Lock | Protects | Easy to miss |
|---|---|---|
| `transport_lock` | `snd_task` and hand-off of `XPRT_LOCKED`; `cong`, `cwnd`, `XPRT_CWND_WAIT`; the `XPRT_CLOSE_WAIT` test in `xprt_clear_locked()` against `xprt_schedule_autoclose_locked()`; arming `timer` | not the receive queue or `rq_pin`; `connect_cookie` is bumped without it; `xprt_clear_congestion_window_wait()` clears `XPRT_CWND_WAIT` before it takes the lock |
| `reserve_lock` | `free`, `num_reqs`, the `xid` counter in `xprt_alloc_xid()`, and `XPRT_CONGESTED` against `xprt_free_slot()` | `xprt_rdma_alloc_slot()` and `rpcrdma_req_release()` call the backlog helpers without it |
| `queue_lock` | `recv_queue`, `xmit_queue`, `rq_pin` increments, `RPC_TASK_NEED_RECV`, `RPC_TASK_NEED_XMIT` | `xprt_schedule_autodisconnect()` reads `recv_queue` without it |
| `XPRT_LOCKED` | right to send, connect and close; keeps `transport->sock` stable for a sender | the only assertion is `WARN_ON_ONCE()` on `xprt_lock_connect()` in `xs_connect()` and `xprt_rdma_connect()`; `xs_tcp_send_request()` takes no mutex |
| `recv_mutex` | `sock`, `inet`, `file` of `struct sock_xprt` for code that does not hold `XPRT_LOCKED` | also taken outside the receive workers, for example by `xs_sock_srcport()` and `xs_sock_srcaddr()` |

- All three spinlocks: every acquisition in the tree is plain `spin_lock()`;
  none is in softirq, hard-irq or a timer callback.
- Socket callbacks such as `xs_data_ready()` and `xs_write_space()`: take none
  of them; they set a `sock_state` bit and queue `recv_worker` or
  `error_worker`.
- `xprt_init_autodisconnect()`: a timer callback that takes no spinlock; it
  sets `XPRT_LOCKED` with `test_and_set_bit()` and queues `task_cleanup`.
- RPC/RDMA completions: both client CQs are `IB_POLL_WORKQUEUE` in
  `rpcrdma_ep_create()`, so `rpcrdma_reply_handler()` takes `queue_lock` in
  process context.
- `xprt_write_space()`: its kerneldoc mentions softirq, but its callers are
  `xs_wake_write()` and functions in `net/sunrpc/xprtrdma/verbs.c`, all
  process context.
- Nesting: `xprt_request_enqueue_transmit()` takes `transport_lock` inside
  `queue_lock`; `xs_udp_data_read_skb()` drops `queue_lock` before it takes
  `transport_lock`.
- **Unsafe usage**: taking one of the three spinlocks from a socket callback or
  other softirq code, for example by calling `xprt_force_disconnect()` there.
  - Unsafe: the holders use plain `spin_lock()`, so a softirq on the same CPU
    would spin on a lock that cannot be released.
  - Safe: record the event and queue a worker, as `xs_run_error_worker()`
    does; `xs_error_handle()` then takes the lock in process context.

**Request slots**

- `XPRT_CONGESTED` already set: `xprt_reserve()` sleeps the task on
  `xprt->backlog` without trying to allocate; `xprt_retry_reserve()` skips
  that test.
- `tk_status` `-EAGAIN` from `xprt_alloc_slot()`: the task sleeps on
  `xprt->backlog`.
- `tk_status` `-ENOMEM` from `xprt_alloc_slot()`: no backlog sleep;
  `call_reserveresult()` does `rpc_delay()` and goes to
  `call_retry_reserve()`.
- There is no xprt_lock_and_alloc_slot() here; `xs_udp_ops`, `xs_tcp_ops`,
  `xs_local_ops` and `bc_tcp_ops` all use `xprt_alloc_slot()`.
- RPC/RDMA: `xprt_rdma_alloc_slot()` takes slots from `rpcrdma_buffer_get()`
  and re-checks the pool after joining the backlog.
- `xprt_rdma_free_slot()`: drops a kref; the slot reaches a waiter or the pool
  only in `rpcrdma_req_release()`, after the Send side has dropped its
  reference too.
- `xprt_free_slot()`: hands the slot to the first backlog waiter through
  `xprt_wake_up_backlog()`; the waiter's callback
  `xprt_complete_request_init()` runs `xprt_request_init()`.
- `call_reserveresult()`: never calls `xprt_release()`; status 0 with no slot
  becomes `-EIO`.
- Other callers of `xprt_release()`: search for them; the surprising ones are
  `call_decode()` on `-EKEYREJECTED`, to force a new XID, and
  `rpc_task_set_transport()` when moving a task off an `XPRT_OFFLINE`
  transport.
- `xprt_release()` with no slot: calls `xprt_release_write()` only if
  `task->tk_client` is set.
- `xprt_release()` with a slot, in order:
  1. `xprt_request_dequeue_xprt()`, which waits for pins.
  2. Under `transport_lock`: `release_xprt`, `release_request` if set,
     `xprt_schedule_autodisconnect()`.
  3. `buf_free` if `rq_buffer` is set.
  4. `put_rpccred()` on `rq_cred`.
  5. `rq_release_snd_buf` if set.
  6. Clears `tk_rqstp`, then `free_slot`, or `xprt_free_bc_request()` for a
     preallocated backchannel request.
- There is no xprt_request_dequeue_all() here; `xprt_request_dequeue_xprt()`
  does that job.
- `xprt_release()` does not call `xdr_free_bvec()` itself. The send bvec is
  freed in `xprt_request_dequeue_transmit_locked()`, the receive bvec in
  `xprt_complete_rqst()` or `xprt_request_dequeue_xprt()`.

**Transmit and receive queues**

- `xmit_queue`: a `struct list_head` linked through `rq_xmit`, not an rbtree.
- Order in `xprt_request_enqueue_transmit()`:
  - `rq_cong` set: inserted before the first request that holds no credit.
  - `rq_seqno_count == 0`: appended to the `rq_xmit2` list of the first queued
    request with the same `tk_owner`.
  - Otherwise, which includes every request with a GSS sequence number and no
    credit: tail of `xmit_queue`.
- `xprt_transmit()`: sends from the head, so it sends other tasks' requests,
  each one pinned; `-EBADMSG` from another task's request is treated as 0.
- Dequeuing the head of `xmit_queue`: `xprt_request_dequeue_transmit_locked()`
  calls `abort_send_request`; `xs_stream_abort_send_request()` forces a
  disconnect if part of the record was sent.
- A pin blocks only `xprt_request_dequeue_xprt()`, and so `xprt_release()` and
  re-encoding in `call_encode()`. It does not stop completion or a timeout
  wake-up.
- `xprt_wait_on_pinned_rqst()`: sleeps uninterruptibly, so a pin must always
  be dropped; RPC/RDMA holds one until `rpcrdma_complete_rqst()` or
  `rpcrdma_unpin_rqst()`.
- Copy target: the receiver writes `rq_private_buf`; `call_decode()` reads
  `rq_rcv_buf` only after it sees `rq_reply_bytes_recvd`.
- **Unsafe usage**: using the request from `xprt_lookup_rqst()` after dropping
  `queue_lock` without a pin.
  - Safe: `xprt_pin_rqst()` before unlocking, then `xprt_complete_rqst()` and
    `xprt_unpin_rqst()` under the lock again, as `xs_read_stream_reply()`
    does; `xprt_request_dequeue_xprt()` waits on `rq_pin`.
  - Safe: keep `queue_lock` held across the whole copy and completion with no
    pin, as `receive_cb_reply()` in `net/sunrpc/svcsock.c` does.

**Connecting and backoff**

- `xs_connect()`: moves `XPRT_LOCKED` from the task to the transport pointer
  with `xprt_lock_connect()`, so the lock outlives the
  `xprt_release_write()` at the end of `xprt_connect()`; the worker ends with
  `xprt_unlock_connect()`.
- `XPRT_CONNECTING` on TCP: `xs_tcp_setup_socket()` does not clear it when
  `kernel_connect()` returns 0, `-EINPROGRESS` or `-EALREADY`;
  `xs_tcp_state_change()` clears it on `TCP_ESTABLISHED`, or on `TCP_CLOSE` if
  `XPRT_SOCK_CONNECTING` was set.
- Backoff: `xs_connect()` calls `xprt_reconnect_backoff()` when it schedules
  the attempt, before the outcome is known, and only if `transport->sock` is
  set.
- `reestablish_timeout` set to 0: `xs_data_ready()` on any incoming data,
  `xs_close()`, `xs_tcp_state_change()` on `TCP_FIN_WAIT1`; for RDMA
  `rpcrdma_reply_handler()` and `xprt_rdma_close()`.
- `reestablish_timeout` raised to at least the initial value:
  `xs_tcp_state_change()` on `TCP_CLOSE_WAIT` and `TCP_CLOSING`,
  `xs_tcp_setup_socket()` once the SYN is sent, `rpcrdma_xprt_connect()` after
  `rdma_connect()`.
- `TCP_ESTABLISHED` and `TCP_LAST_ACK`: do not touch `reestablish_timeout`.
- `max_reconnect_timeout`: `to_maxval` of the transport's timeout, or
  `args->reconnect_timeout` in `xs_setup_tcp()`; after setup it can only be
  lowered, by the `set_connect_timeout` method
  (`xs_tcp_set_connect_timeout()`, `xprt_rdma_set_connect_timeout()`). No
  XS_TCP_MAX_REEST_TO exists here.
- AF_LOCAL: `xs_local_connect()` connects synchronously, without
  `xprt_lock_connect()` or the backoff helpers; an async task gets
  `-ENOTCONN`, and a failed connect sleeps 15 s unless the task is soft-connect.
- RPC/RDMA: `xprt_rdma_connect()` queues its worker on `system_dfl_long_wq`,
  not `xprtiod_workqueue`, and delays only if `re_connect_status` is non-zero.
- `connect_cookie` is bumped in more places than `xs_tcp_state_change()`:
  search for it; `xprt_autoclose()` and `xs_sock_reset_connection_flags()`
  are the ones to remember.
- `rq_connect_cookie`: starts at the current cookie minus one in
  `xprt_request_init()`, so a freshly initialised request never matches the
  current cookie.
- The cookie is not checked when a reply is received; replies are matched by
  XID alone, and `xprt_wake_pending_tasks()` does not look at it.
- `xprt_rdma_send_request()`: drops the connection rather than resend a
  request whose `rq_connect_cookie` equals the current cookie.
- `xprt_force_disconnect()` on one request's error is used in the tree on
  purpose: `xprt_rdma_timer()` calls it on a retransmit timeout.

**Client socket teardown**

- Order in `xs_reset_transport()`: `sk_user_data` is set to NULL first, then
  `xs_restore_old_callbacks()` runs.
- Locks: `recv_mutex`, then `lock_sock()`; `sk_callback_lock` is not used
  anywhere in `net/sunrpc`.
- Release: `__fput_sync()` on `transport->file`, after both locks are dropped;
  not `sock_release()`.
- Context: the test is `PF_WQ_WORKER`. Otherwise it warns, sets
  `XPRT_CLOSE_WAIT` and returns with the socket still open.
- `xprt_destroy()`: queues `xprt_destroy_cb()` with `schedule_work()`, so
  `xs_destroy()` runs on a system worker and may cancel `recv_worker` and
  `error_worker` synchronously.
- `xs_destroy()`: cancels `connect_worker` before `xs_close()`, and
  `recv_worker` and `error_worker` after it.
- Socket callbacks: never call `xprt_force_disconnect()` themselves; they
  queue `error_worker`, and `xs_wake_disconnect()` calls it.
- `xs_tcp_ops` has `close = xs_tcp_shutdown()`: with `xprt->reuseport` set and
  the socket in `TCP_ESTABLISHED` or `TCP_CLOSE_WAIT` it only calls
  `kernel_sock_shutdown()`. `xs_reset_transport()` runs on a later autoclose,
  triggered by `TCP_CLOSE`.
- `xs_tcp_tls_finish_connecting()`: moves the socket to the upper transport
  without `xs_reset_transport()`. It repoints `sk_user_data` under
  `lock_sock()` and clears the lower transport's `sock`, `inet` and `file`
  under `recv_mutex`, so the lower transport's later close finds nothing.
- **Unsafe usage**: a socket callback that uses the result of
  `xprt_from_sock()` without a NULL check.
  - Safe: return when it is NULL, as `xs_error_report()` and
    `xs_tcp_state_change()` do; `xs_reset_transport()` clears `sk_user_data`
    while the RPC callbacks are still installed.

## RDMA client

**RDMA client objects**

- `struct rpcrdma_xprt`: has no counter of its own; it lives and dies with
  the `kref` of the embedded `struct rpc_xprt` (`rx_xprt`).
- `rl_kref` in `struct rpcrdma_req`: counts owners that keep the req out of
  its free pool. It does not arbitrate Send against Reply, and matching a
  Reply in `rpcrdma_reply_handler()` neither takes nor drops a reference.
- `rl_kref` RPC-layer reference: `kref_init()` in `xprt_rdma_alloc_slot()`,
  `rpcrdma_bc_rqst_get()` and `rpcrdma_req_release()`; dropped in
  `xprt_rdma_free_slot()` or `xprt_rdma_bc_free_rqst()`.
- `rl_kref` Send-side reference: `kref_get()` at the end of
  `rpcrdma_prepare_send_sges()` for every prepared Send, whatever
  `sc_unmap_count` is; dropped in `rpcrdma_sendctx_unmap()`.
- `rpcrdma_req_release()` in `net/sunrpc/xprtrdma/transport.c`: the only
  release function; there is no rpcrdma_reply_done() or
  rpcrdma_sendctx_done() here. It re-initialises the kref and hands the req
  to `bc_pa_list`, a backlog waiter, or `rb_send_bufs`.
- Unsignaled Send: its sendctx, and so its req reference, stays held until
  a later Send completion walks the ring (`rpcrdma_sendctx_put_locked()`)
  or until disconnect (`rpcrdma_sendctxs_destroy()`).
  `rpcrdma_buffer_create()` allocates `rpcrdma_req_pool_slack()` extra reqs
  to cover that delay.
- `struct rpcrdma_rep`: survives a reconnect. Created only on demand by
  `rpcrdma_rep_create()` from `rpcrdma_post_recvs()`; freed only by
  `rpcrdma_reps_destroy()` from `rpcrdma_buffer_destroy()`. Disconnect only
  DMA-unmaps it (`rpcrdma_reps_unmap()`). There is no rr_temp field.
- `rpcrdma_rep_resize()`: reallocates a surviving rep's buffer when the new
  connection's `re_inline_recv` is larger.
- `struct rpcrdma_mr`: belongs to one connection. Every MR is destroyed at
  disconnect: those on `rl_registered` by `rpcrdma_req_reset()`, the rest by
  `rpcrdma_mrs_destroy()`.
- `rpcrdma_req_reset()`: frees `rl_rdmabuf` and calls `frwr_mr_release()` on
  MRs still registered; it does not call `frwr_reset()`.
- `ep->re_write_pad_mr`: one MR taken at connect by `frwr_wp_create()`, with
  `mr_req` NULL and on no req list; `rpcrdma_xprt_connect()` fails if it
  cannot be made. `frwr_mr_put()` dereferences `mr_req`, so this MR must
  never reach it.
- `rl_rdmabuf`: the one regbuf that is per connection; allocated and mapped
  by `rpcrdma_req_setup()`, freed at disconnect. `rl_sendbuf` and
  `rr_rdmabuf` survive and are remapped on next use.
- `struct rpcrdma_sendctx` ring: per connection; `rpcrdma_sendctxs_create()`
  allocates it and `rpcrdma_sendctxs_destroy()` frees it.
- Per-connection setup in `rpcrdma_xprt_connect()`: sendctxs, `rl_rdmabuf`,
  MRs and the write-pad MR are built only after the connection is
  established; the first Receives are posted before `rdma_connect()`.
- `rpcrdma_xprt_disconnect()`: also runs from `xprt_rdma_connect_worker()`
  when `rpcrdma_xprt_connect()` fails, so each teardown step must tolerate
  objects that were never set up.

**Reply-side ownership rules**

- The rules are written down: a comment block titled "Reply-side ownership
  invariants" sits directly above the kerneldoc of
  `rpcrdma_reply_handler()` in `net/sunrpc/xprtrdma/rpc_rdma.c`. It has
  rules I1 to I5 and a "Non-hazards" list.

| Rule | Says | Assertion in code |
|---|---|---|
| I1 | a rep belongs to the HCA from `ib_post_recv()` to its Receive completion, then to the CPU until `rpcrdma_rep_put()` | `WARN_ON_ONCE(rep->rr_rqst)` in `rpcrdma_post_recvs()` |
| I2 | a rep reachable through `rl_reply` is not re-posted; `rpcrdma_reply_put()` clears `rl_reply` before `rpcrdma_rep_put()` | none |
| I3 | on entry to `rpcrdma_complete_rqst()` every MR of the req is invalidated and DMA-unmapped | `WARN_ON_ONCE()` in `rpcrdma_complete_rqst()` if `rl_registered` is not empty |
| I4 | `rl_kref` holds an RPC-layer and a Send-side reference; the req is pooled only after both drop | `WARN_ON_ONCE(req->rl_sendctx)` in `rpcrdma_req_release()` |
| I5 | the RPC layer owns a req from slot acquisition to `xprt_rdma_free_slot()` or `xprt_rdma_bc_free_rqst()`; pools hold no req with work outstanding | none |

- I2 in the comment: claims `rpcrdma_reply_put()` WARNs; the function in
  `net/sunrpc/xprtrdma/verbs.c` has no WARN.
- I4 in the comment: names xprt_rdma_bc_rqst_get, which does not exist; the
  function is `rpcrdma_bc_rqst_get()` in
  `net/sunrpc/xprtrdma/backchannel.c`.
- `rpcrdma_rep_put()`: clears `rr_rqst` itself, which is what the I1
  assertion relies on.
- I4 consequence: an RPC may complete while its Send is still outstanding.
  Only the return of the req to its pool waits for
  `rpcrdma_sendctx_unmap()`.
- `xprt_rdma_free()`: does not touch `rl_kref`.

**Registering memory**

- `frwr_map()`: takes `struct rpcrdma_xdr_cursor *cur` in place of a segment
  array and count, and returns `int`: 0, or `-EIO`.
- There is no struct rpcrdma_mr_seg, rl_segments or rpcrdma_convert_iovs()
  in this tree; `frwr_map()` builds `mr->mr_sg` straight from `cur->xc_buf`.
- `struct rpcrdma_xdr_cursor` in `net/sunrpc/xprtrdma/xprt_rdma.h`: holds
  the `xdr_buf`, `xc_page_offset`, and the flags `XC_HEAD_DONE`,
  `XC_PAGES_DONE`, `XC_TAIL_DONE`. A set flag means "nothing left to
  register", whether already registered or excluded.
- `rpcrdma_xdr_cursor_init()`: selects the regions by presetting flags. A
  non-zero `pos` excludes the head; `rpcrdma_readch` and `rpcrdma_writech`
  exclude the tail.
- Caller loop in the three encoders: `do { rpcrdma_mr_prepare(); encode one
  segment; } while (!rpcrdma_xdr_cursor_done(&cur))`. The loop ends on the
  cursor; no segment count is passed to or returned by `frwr_map()`.
- `rpcrdma_mr_prepare()`: returns `int` and hands the MR back through
  `struct rpcrdma_mr **mr`; `-EAGAIN` when no MR is free.
- One `frwr_map()` call: takes at most `re_max_fr_depth` entries. Without
  `IB_MR_TYPE_SG_GAPS` it stops gathering right after the head, and before
  a tail that would leave a gap; what it gathered is still registered.
- `frwr_map()` advances the cursor before it DMA-maps, so after `-EIO` the
  cursor is past data that was not registered. Callers abandon the cursor on
  error.
- Failed `ib_dma_map_sg()`: `frwr_map()` returns `-EIO` and leaves
  `mr->mr_device` NULL. `mr_dir` is never set to `DMA_NONE`.
- Failed `ib_map_mr_sg()`: `-EIO` with `mr->mr_device` already set, so the
  later unmap runs.
- Unwind: `rpcrdma_marshal_req()` calls `frwr_reset()`, which moves every MR
  on `rl_registered`, the failed one included, to `rl_free_mrs`. There is no
  rpcrdma_mr_put().
- **Unsafe usage**: setting `mr->mr_device` to a device before
  `ib_dma_map_sg()` has succeeded.
  - Unsafe: `frwr_mr_unmap()` treats a non-NULL `mr_device` as "mapped" and
    calls `ib_dma_unmap_sg()`.
  - Safe: assign `mr_device` only after a non-zero `ib_dma_map_sg()` return,
    as `frwr_map()` and `frwr_wp_create()` do.

**Credits and posted receives**

- Order in `rpcrdma_reply_handler()`:
  1. decode the four header words;
  2. sanitise the grant, before the version check and before
     `rpcrdma_is_bcall()`;
  3. look up and pin the rqst;
  4. `rpcrdma_update_cwnd()`, if the grant changed;
  5. attach the rep, then `frwr_unmap_async()` or `rpcrdma_complete_rqst()`;
  6. `rpcrdma_post_recvs()`, last, at `out_post`.
- Receives are therefore posted after the congestion window has been
  updated and after the RPC was completed or its LOCAL_INV chain posted.
- Upper clamp of the grant: `r_xprt->rx_ep->re_max_requests`.
- Count passed: `credits + (buf->rb_bc_srv_max_requests << 1)`.
- `rpcrdma_post_recvs()`: takes two arguments, `r_xprt` and `needed`; there
  is no `temp` argument.
- Count posted: nothing while `re_receive_count > needed`; otherwise up to
  `needed - re_receive_count + ep->re_recv_batch`.
  `re_recv_batch` is `re_max_requests >> 2`, set in `frwr_query_device()`.
  The client does not use `RPCRDMA_MAX_RECV_BATCH`; only the server does.
- `out_norqst`: posts with the sanitised wire grant but does not update the
  congestion window.
- `out_badversion` and `out_shortreply`: post with the stored
  `buf->rb_credits`, not the value from the wire.
- Backchannel call: when `rpcrdma_is_bcall()` returns true the handler
  returns without calling `rpcrdma_post_recvs()` or
  `rpcrdma_update_cwnd()`.

**Endpoint references**

- Three references exist on a connected `struct rpcrdma_ep`:

| Taken | For | Dropped |
|---|---|---|
| `kref_init()` in `rpcrdma_ep_create()` | the transport | `rpcrdma_xprt_disconnect()` |
| `rpcrdma_ep_get()` in `rpcrdma_xprt_connect()`, before the first `rpcrdma_post_recvs()` | posted Receives | `rpcrdma_xprt_drain()` |
| `rpcrdma_ep_get()` on `RDMA_CM_EVENT_ESTABLISHED` | the connection | `RDMA_CM_EVENT_DISCONNECTED` |

- `RDMA_CM_EVENT_DISCONNECTED`: the only event that drops a reference; the
  put is unconditional, with no test of `re_connect_status`.
- `RDMA_CM_EVENT_ADDR_CHANGE`: never drops a reference. Old status 0 wakes
  `re_connect_wait`; old status 1 calls `rpcrdma_force_disconnect()` and
  returns 0, leaving the ESTABLISHED reference for the DISCONNECTED case.
- `RDMA_CM_EVENT_ADDR_ERROR` and `RDMA_CM_EVENT_ROUTE_ERROR`: set
  `re_async_rc` and complete `re_done`; they do not touch
  `re_connect_status` or `re_connect_wait`.
- `RDMA_CM_EVENT_DEVICE_REMOVAL`: has no case in
  `rpcrdma_cm_event_handler()`; it falls to `default` and returns 0.
- `rpcrdma_rn_register()`: called as the last step of
  `rpcrdma_create_id()`, after route resolution. It returns `-ENETUNREACH`
  when the device has `RPCRDMA_RD_F_REMOVING` set, which fails the connect.
- `rpcrdma_ep_removal_done()`: calls `xprt_force_disconnect()` directly, not
  `rpcrdma_force_disconnect()`, so `re_force_disconnect` does not gate it.
- `rpcrdma_rn_unregister()`: uses `rn_done` as the "registered" marker and
  is a no-op when it is NULL; `svc_rdma_free()` relies on that after
  `rpcrdma_rn_register()` failed in `svc_rdma_accept()`.
- `rpcrdma_ep_destroy()`: also drops the module reference that
  `rpcrdma_ep_create()` took.

**Work completion fields**

- When `status` is not `IB_WC_SUCCESS`: handlers under
  `net/sunrpc/xprtrdma/` read only `wr_cqe` and `status`, and get the
  transport from `cq->cq_context`, not from `wc->qp`.
- `vendor_err`: read only by the tracepoint classes in
  `include/trace/events/rpcrdma.h`, never by handler logic.
- Client handlers: never test `IB_WC_WR_FLUSH_ERR` and never log. A flush
  and any other error take the same path through
  `rpcrdma_flush_disconnect()`.
- `svc_rdma_wc_receive()` with `IB_WC_SUCCESS`: still drops the Receive and
  closes the transport when `svc_rdma_refresh_recvs()` fails.
- `svc_rdma_wc_receive()`: copies `wc->byte_len` only after that repost
  step, not straight after the status test.

**Invalidating MRs**

- `frwr_unmap_async()`: called only from `rpcrdma_reply_handler()`, in
  Receive completion context.
- `frwr_unmap_sync()`: called only from `xprt_rdma_free()`, in process
  context; it never runs on the reply path and never completes an RPC.
- `frwr_wc_localinv_done()`: completes the RPC from the Send CQ's completion
  context, since `mr_cqe` belongs to a Send Queue WR.
- Empty `rl_registered` in the reply handler: `rpcrdma_complete_rqst()` is
  called directly. No `rl_kref` operation is involved in completing an RPC.
- `frwr_unmap_sync()` on return: guarantees only that `rl_registered` is
  empty. `frwr_wc_localinv_wake()` wakes the waiter whatever the status, and
  there is no wait at all when `bad_wr == first`.
- After a failed or unposted LOCAL_INV in `frwr_unmap_sync()`: the memory
  goes back to the caller with the MR still DMA-mapped; the forced
  disconnect is the recovery.
- **Potentially unsafe usage**: calling `frwr_reset()` to make a req's MRs
  reusable without invalidating them.
  - Unsafe: once `frwr_send()` has posted the req's `IB_WR_REG_MR` WRs; the
    rkeys may then be valid on the HCA.
  - Safe: after a failed marshal, as `rpcrdma_marshal_req()` does;
    `frwr_send()` is the only place that posts those WRs and it runs after
    marshalling.

**Remote and failed invalidation**

- `frwr_reminv()`: has no MR state to set. It unlinks the matching MR and
  calls `frwr_mr_put()`; FRWR_IS_INVALID and FRWR_FLUSHED_LI do not exist in
  this tree.
- No match for `rr_inv_rkey` in `frwr_reminv()`: the list is left unchanged
  and every MR goes through `frwr_unmap_async()`.
- Failed or flushed LOCAL_INV: there is no rpcrdma_mr_recycle() here.
  `frwr_mr_done()` and `frwr_wc_localinv_done()` simply skip
  `frwr_mr_put()`, so the MR is on no req list and stays DMA-mapped.
- Destruction of such an MR: `rpcrdma_mrs_destroy()` finds it on
  `rb_all_mrs` at disconnect and calls `frwr_mr_release()`.
- MRs still on `rl_registered` at disconnect: destroyed earlier, by
  `rpcrdma_req_reset()`, which unlinks them from `rb_all_mrs` first.
- `mrs_recycled` and `mrs_orphaned` in `struct rpcrdma_stats`: printed by
  `xprt_rdma_print_stats()` but never incremented.

## RDMA server

**Releasing send contexts**

- `svc_rdma_send_ctxt_put()` in `net/sunrpc/xprtrdma/svc_rdma_sendto.c`:
  releases nothing; it only adds the ctxt to `rdma->sc_send_release_list`.
- No workqueue is involved: there is no svcrdma_wq and no
  svc_rdma_send_ctxt_put_async() in this tree, and
  `struct svc_rdma_send_ctxt` has no work item.
- `svc_rdma_send_ctxt_release()`: the only place mappings and pages are
  released, other than SGE 0; its only caller is
  `svc_rdma_send_ctxts_drain()`, which takes the whole
  `sc_send_release_list` and runs in the calling thread.
- `svc_rdma_send_ctxt_release()` order: `svc_rdma_send_ctxt_unmap()` (chunk
  rw contexts, then `ib_dma_unmap_page()` on `sc_sges[1]` upward), then
  `release_pages()` on `sc_pages`, then `llist_add()` to `sc_send_ctxts`.
- SGE 0: unmapped only by `svc_rdma_send_ctxts_destroy()`, with
  `ib_dma_unmap_single()`.
- Drain triggers: search for callers of `svc_rdma_send_ctxts_drain()`. The
  usual one is `svc_rdma_release_ctxt()` (`xpo_release_ctxt`), which drains
  even when its context argument is NULL.
- Easy-to-miss drain callers: `svc_rdma_send_ctxt_get()` when the free list
  is empty, `svc_rdma_sq_wait()` after a slow-path success, and
  `svc_rdma_free()`.
- Self-trigger: when `svc_rdma_send_ctxt_put()` adds to an empty release
  list it sets `XPT_DATA` and calls `svc_xprt_enqueue()`, so an idle
  connection still gets a drain.
- Self-trigger refused: `svc_rdma_has_wspace()` returns 0 while
  `sc_send_wait` or `sc_sq_ticket_wait` has a sleeper, so `svc_xprt_ready()`
  rejects that enqueue; `svc_rdma_sq_wait()` drains for this reason.
- Error paths that never posted: use the same `svc_rdma_send_ctxt_put()`, so
  their release is deferred to a drain too.
- Teardown: `svc_rdma_free()` in `net/sunrpc/xprtrdma/svc_rdma_transport.c`
  calls `ib_drain_qp()`, then `svc_rdma_send_ctxts_drain()`, and only later
  `svc_rdma_send_ctxts_destroy()`, which walks `sc_send_ctxts` only.
- `svc_rdma_wc_send()` on any status other than `IB_WC_SUCCESS`, in order:
  1. `svc_rdma_wake_send_waiters()` with `ctxt->sc_sqecount`
  2. `trace_svcrdma_wc_send_flush()` for `IB_WC_WR_FLUSH_ERR`, otherwise
     `trace_svcrdma_wc_send_err()`
  3. `svc_rdma_send_ctxt_put()`
  4. `svc_rdma_xprt_deferred_close()`
- After step 3 the handler does not touch the ctxt; `rdma` comes from
  `cq->cq_context`.

**Server Send Queue accounting**

- Completions that return entries: `svc_rdma_wc_send()` returns
  `sc_sqecount`, `svc_rdma_wc_read_done()` returns `cc_sqecount`.
- `svc_rdma_write_done()` and `svc_rdma_reply_done()` in
  `net/sunrpc/xprtrdma/svc_rdma_rw.c`: return no entries; on error they
  trace and call `svc_rdma_xprt_deferred_close()`.
- Write and Reply chunk entries: `svc_rdma_cc_link_wrs()` adds `cc_sqecount`
  to `sc_sqecount`, so `svc_rdma_wc_send()` returns them.
- Chained chunk WRs: `rdma_rw_ctx_wrs()` installs its `cqe` only when
  `chain_wr` is NULL, and `svc_rdma_cc_link_wrs()` always passes the existing
  chain.
- There is no svc_rdma_wc_write() or svc_rdma_wc_reply_done() in this tree.
- `svc_rdma_sq_wait()` in `net/sunrpc/xprtrdma/svc_rdma_sendto.c`: the only
  place that reserves entries; `svc_rdma_post_send()` and
  `svc_rdma_post_chunk_ctxt()` both call it before `ib_post_send()`.
- Order: ticket order. A caller that fails the fast path takes a ticket from
  `sc_sq_ticket_head` and sleeps on `sc_sq_ticket_wait` until
  `sc_sq_ticket_tail` equals its ticket.
- Head of the line: only the thread whose ticket is being served sleeps on
  `sc_send_wait`.
- Both `wait_event()` calls are non-exclusive; the order comes from the
  tickets, not from the waitqueue.
- Fast path: tried first with no ticket, so a new caller takes entries ahead
  of ticket holders when enough are free.
- `XPT_CLOSE`: tested only on the slow path, in and after each
  `wait_event()`; the fast path returns 0 on a closing transport.
- Every ticket holder, on success and at `out_close`: increments
  `sc_sq_ticket_tail` exactly once, then `wake_up()` on `sc_sq_ticket_wait`.
- At `out_close` no entries are held: each failed `atomic_sub_return()` is
  undone at once by `atomic_add()`, so there is nothing to return.
- **Unsafe usage**: a slow-path exit from `svc_rdma_sq_wait()` that skips the
  increment of `sc_sq_ticket_tail`.
  - Unsafe: every later ticket holder sleeps on `sc_sq_ticket_wait` until the
    transport closes.
  - Safe: both slow-path exits of `svc_rdma_sq_wait()` increment and wake.
- `svc_rdma_wake_send_waiters()`: wakes `sc_send_wait` only, never
  `sc_sq_ticket_wait`.
- `svc_rdma_xprt_deferred_close()` in
  `net/sunrpc/xprtrdma/svc_rdma_transport.c`: calls
  `svc_xprt_deferred_close()`, then `wake_up_all()` on `sc_sq_ticket_wait`
  and on `sc_send_wait`.
- Server RDMA code calls `svc_xprt_deferred_close()` nowhere else; every
  completion handler and the forward paths use the wrapper.
- **Unsafe usage**: calling `svc_xprt_deferred_close()` on `rdma->sc_xprt`
  from a completion handler.
  - Unsafe: it sets `XPT_CLOSE` and enqueues but wakes neither waitqueue, so
    the close itself does not wake sleepers in `svc_rdma_sq_wait()`.
  - Safe: `svc_rdma_xprt_deferred_close()`, as `svc_rdma_wc_send()` and
    `svc_rdma_wc_read_done()` do.
- `svc_xprt_close()` path: does not go through the wrapper;
  `svc_rdma_detach()` does the two `wake_up_all()` calls itself.

**After posting a Send**

- A chain is one ctxt: `sc_wr_chain` heads the Write and Reply chunk WRs
  that `svc_rdma_cc_link_wrs()` linked ahead of `sc_send_wr`; `sc_send_wr`
  is last and its `next` stays NULL.
- Reuse after completion: once `svc_rdma_wc_send()` has queued the ctxt, any
  thread that calls `svc_rdma_send_ctxts_drain()` releases it, and
  `svc_rdma_send_ctxt_get()` then resets `sc_sqecount`, `sc_wr_chain`,
  `sc_page_count` and `num_sge`.
- `svc_rdma_post_send()` return values: only 0 or `-ENOTCONN`.

  | Return | Posted | SQ entries | Who puts the ctxt |
  |---|---|---|---|
  | 0 | whole chain | held until completion | `svc_rdma_wc_send()` |
  | 0 | part of the chain | not returned | not the caller |
  | `-ENOTCONN` | nothing | never taken, or returned | the caller |

- **Potentially unsafe usage**: reading or writing the ctxt after
  `ib_post_send()` was called on its chain.
  - Unsafe: when `svc_rdma_post_send()` returned 0; the ctxt may already be
    released and re-initialised for another Reply.
  - Safe: values copied before the post, as `svc_rdma_post_send()` does with
    `cid`, `sqecount` and `first_wr`; `trace_svcrdma_post_send()` runs before
    `ib_post_send()`.
  - Safe: after a negative return, because `svc_rdma_post_send_err()` returns
    `-ENOTCONN` only when `bad_wr == first_wr`.
- **Potentially unsafe usage**: calling `svc_rdma_send_ctxt_put()` after
  `svc_rdma_post_send()`.
  - Unsafe: when it returned 0, which includes a partial post; the ctxt is
    no longer the caller's.
  - Safe: when it returned a negative value, as `svc_rdma_sendto()`,
    `svc_rdma_send_error_msg()` and `rpcrdma_bc_send_request()` do.
- `svc_rdma_post_send_err()` in `net/sunrpc/xprtrdma/svc_rdma_sendto.c`:
  handles every `ib_post_send()` failure, for `svc_rdma_post_send()` and for
  `svc_rdma_post_chunk_ctxt()`.
- `svc_rdma_post_send_err()` always: traces, then calls
  `svc_rdma_xprt_deferred_close()`, not `svc_xprt_deferred_close()`.
- Partial post (`bad_wr != first_wr`): `svc_rdma_post_send_err()` returns 0,
  returns no SQ entries and puts nothing.
- Nothing posted (`bad_wr == first_wr`): `svc_rdma_post_send_err()` itself
  returns all `sqecount` entries through `svc_rdma_wake_send_waiters()` and
  returns `-ENOTCONN`.
- `svc_rdma_post_send_err()` never puts a ctxt and never returns entries for
  only part of a chain.
- `svc_rdma_wc_send()`: the only completion handler that puts a send ctxt or
  returns its `sc_sqecount`; see "Server Send Queue accounting" for the
  chunk handlers.

## RPCSEC_GSS

**Kerberos crypto and token formats**

- Crypto location: no encryption, checksum or key-derivation step is under
  `net/sunrpc/auth_gss/`; they are in `crypto/krb5/` and the crypto API
  algorithms it allocates (for example `crypto/krb5enc.c`); encryption and
  checksums are reached through `crypto_krb5_encrypt()`,
  `crypto_krb5_decrypt()`, `crypto_krb5_get_mic()` and
  `crypto_krb5_verify_mic()` in `crypto/krb5/krb5_api.c`
  (`include/crypto/krb5.h`).
- `net/sunrpc/auth_gss/`: there is no gss_krb5_keys.c and no gss_krb5_test.c;
  the Kerberos files are the five objects listed in
  `net/sunrpc/auth_gss/Makefile` plus `gss_krb5_internal.h`.
- `net/sunrpc/auth_gss/gss_krb5_crypto.c`: holds only glue from
  `struct xdr_buf` to scatterlists: `xdr_extend_head()`,
  `gss_krb5_aead_encrypt()`, `gss_krb5_aead_decrypt()`,
  `gss_krb5_mic_build_sg()`.
- Absent names: krb5_encrypt, krb5_decrypt, gss_krb5_checksum,
  krb5_etm_checksum, gss_krb5_aes_encrypt, gss_krb5_aes_decrypt,
  krb5_etm_encrypt, krb5_etm_decrypt, krb5_derive_key_v2, krb5_kdf_hmac_sha2
  and krb5_kdf_feedback_cmac are defined nowhere in this tree.
- Enctype table: there is no struct gss_krb5_enctype and no per-enctype method
  table under `net/sunrpc/auth_gss/`; `struct krb5_ctx` carries `krb5e`, a
  `const struct krb5_enctype *` from `crypto_krb5_find_enctype()`, and
  `gss_krb5_get_mic()`, `gss_krb5_verify_mic()`, `gss_krb5_wrap()`,
  `gss_krb5_unwrap()` call the `_v2` functions directly.
- Key setup: `gss_krb5_import_ctx_v2()` is the one path for all enctypes; it
  keys two `struct crypto_aead` and two `struct crypto_shash` with
  `crypto_krb5_prepare_encryption()` and `crypto_krb5_prepare_checksum()`,
  which do the derivation.
- Build-time selection: there are no CONFIG_RPCSEC_GSS_KRB5_ENCTYPES_AES_SHA1,
  CONFIG_RPCSEC_GSS_KRB5_ENCTYPES_AES_SHA2 or
  CONFIG_RPCSEC_GSS_KRB5_ENCTYPES_CAMELLIA symbols;
  `CONFIG_RPCSEC_GSS_KRB5` selects `CONFIG_CRYPTO_KRB5`.
- Offered list: `gss_krb5_prepare_enctype_priority_list()` walks the fixed
  array `gss_krb5_enctypes` in `gss_krb5_mech.c` and keeps each entry that
  `crypto_krb5_find_enctype()` knows.
- Order of the list: 20, 19, 26, 25, 18, 17 (AES-SHA2, then Camellia, then
  AES-SHA1); all six are unconditionally in `krb5_supported_enctypes` in
  `crypto/krb5/krb5_api.c`.
- `crypto_krb5_find_enctype()`: only searches that table; it does not test
  that the underlying algorithms can be allocated, which is found out in
  `gss_krb5_import_ctx_v2()`.
- Consumers of the list: the client sends it as `enctypes=` in
  `gss_encode_v1_msg()`; the server exposes the same string through
  `read_gss_krb5_enctypes()` in `net/sunrpc/auth_gss/svcauth_gss.c`.
- Tests: `crypto/krb5/selftest.c` under `CONFIG_CRYPTO_KRB5_SELFTESTS`; there
  is no KUnit suite for the SunRPC Kerberos code.

**Server context cache**

- Lookup reference: dropped at `out:` in `svcauth_gss_accept()` on every path
  that found a context, `SVC_OK` included; it never outlives the function.
- Second reference: `cache_get()` stored in the `rsci` field of
  `struct gss_svc_data`, taken only on the successful `RPC_GSS_PROC_DATA`
  path; `svcauth_gss_release()` drops it after wrapping.
- `rq_cred`: a plain struct assignment from `rsci->cred`; only
  `cr_group_info` gets its own reference (`get_group_info()`).
- `cr_principal`, `cr_raw_principal`, `cr_targ_princ`, `cr_gss_mech` in
  `rq_cred`: borrowed from the `struct rsc`; nothing is `kstrdup()`ed and
  `gss_mech_get()` is not called; the reference in `gsd->rsci` keeps them
  alive until `svcauth_gss_release()`.
- `svcauth_gss_release()`: for the cred it only does `put_group_info()` and
  clears `cr_group_info`; no caller in this tree passes `rq_cred` to
  `free_svc_cred()`.
- `free_svc_cred()`: besides the three strings and the group info it does
  `gss_mech_put()` on `cr_gss_mech`, then `init_svc_cred()`.
- `rsc_put()`: on the last `cache_put()` it calls `gss_delete_sec_context()`
  and `free_svc_cred()` at once; only `rsc_free_rcu()`, which frees the handle
  and the `struct rsc`, waits for `call_rcu()`.
- `rsc_free()`: used only on on-stack temporaries, in `rsc_parse()`,
  `gss_proxy_save_rsc()` and `gss_svc_searchbyctx()`; it is not the cache's
  release function.
- **Unsafe usage**: calling `free_svc_cred()` on `rqstp->rq_cred`.
  - Unsafe: it frees strings and puts a mech reference that the `struct rsc`
    still owns; `rsc_put()` then frees them again.
  - Safe: `svcauth_gss_release()` puts only `cr_group_info`, the one
    reference `svcauth_gss_accept()` took.
  - Safe: `free_svc_cred()` on a cred filled by `copy_cred()` in
    `fs/nfsd/nfs4state.c`, which duplicates each string and takes
    `gss_mech_get()`.
- **Potentially unsafe usage**: reading string or mech pointers from
  `rq_cred`.
  - Unsafe: after `svcauth_gss_release()` has dropped `gsd->rsci`, for example
    from an object that outlives the request; `rsc_put()` may already have
    freed them.
  - Safe: before `svc_authorise()` runs, in `pg_authenticate` or the
    procedure, as `check_gss_callback_principal()` in `fs/nfs/callback.c`
    does; `svcauth_gss_accept()` holds the `cache_get()` reference in
    `gsd->rsci` until then. `svc_process_common()` calls `svc_authorise()`
    before the reply is sent.
  - Safe: after a deep copy with `copy_cred()`.

**Client credential and context lifetime**

- `gss_get_ctx()`: plain `refcount_inc()`, not an inc-not-zero; it cannot
  fail and cannot detect a dying context.
- **Unsafe usage**: calling `gss_cred_get_ctx()` on a cred the caller holds
  no reference to.
  - Unsafe: the cred's own context reference may already be gone, and
    `refcount_inc()` on a zero count does not refuse.
  - Safe: with a counted cred, as `gss_marshal()` has in `rq_cred`;
    `gss_destroy_nullcred()` drops the cred's context reference only after
    `cr_count` reached zero.
  - Safe: reading `gc_ctx` fields inside `rcu_read_lock()` without taking a
    reference, as `gss_match()`, `gss_key_timeout()` and
    `gss_stringify_acceptor()` do; `gss_free_ctx()` frees through
    `call_rcu()`.
- `gc_ctx`: installed at most once, because `gss_cred_set_ctx()` returns
  early unless `RPCAUTH_CRED_NEW` is set; it is never swapped, and
  `gss_update_rslack()` does not touch it.
- Clearing `gc_ctx`: done in `gss_destroy_nullcred()` with
  `RCU_INIT_POINTER()`, followed by `gss_put_ctx()`; `gss_destroy_cred()`
  only adds `gss_send_destroy_context()` in front, when
  `RPCAUTH_CRED_UPTODATE` was set.
- `gss_nullops`: its `crdestroy` is `gss_destroy_nullcred()`, so the
  duplicate cred from `gss_dup_cred()` sends no second destroy call.
- `gss_delete_sec_context()`: runs inside the RCU callback, in
  `gss_do_free_ctx()`, not before `call_rcu()`.
- `gss_free_callback()`: the `kref` release of `struct gss_auth`; the cred is
  freed by `gss_free_cred_callback()`.
- `rpcauth_lookup_credcache()`: only the first walk is under
  `rcu_read_lock()`; after a miss it creates a cred and walks the chain again
  under the cache's `lock` before inserting.
- Lookup flags: `RPCAUTH_LOOKUP_NEW` and `RPCAUTH_LOOKUP_ASYNC` only; there
  is no RPCAUTH_LOOKUP_RCU.

**Server sequence window**

- `svcauth_gss_accept()`: turns the `SVC_DROP` from
  `svcauth_gss_verify_header()` into `SVC_CLOSE` at its `drop:` label.
- `MAXSEQ` (0x80000000, `include/linux/sunrpc/auth_gss.h`): the test is
  `gc_seq > MAXSEQ`, so `MAXSEQ` itself is accepted.
- Above `MAXSEQ`: `SVC_DENIED` with `rpcsec_gsserr_ctxproblem`, an auth-error
  reply; the connection is not closed.

**Revisited GSS requests**

- Tests of `rq_deferred`: exactly three, in `svcauth_gss_verify_header()`,
  `svcauth_gss_unwrap_integ()` and `svcauth_gss_unwrap_priv()`;
  `svcauth_gss_accept()` has none of its own.
- `svcauth_gss_verify_header()` on a revisit: still decodes the verifier and
  checks its flavor and length, then skips the header `gss_verify_mic()`, the
  `MAXSEQ` test and `gss_check_seq_num()`.
- `svcauth_gss_unwrap_integ()` on a revisit: returns 0 without running the
  body `gss_verify_mic()` or `xdr_truncate_decode()`.
- `svcauth_gss_unwrap_priv()` on a revisit: decodes the length word, skips the
  length checks and `gss_unwrap()`, and still decodes and compares the
  embedded sequence number.
- `svc_defer()`: saves `rq_arg.len` bytes of the request as it stands at
  deferral, plus addresses and `rq_xprt_ctxt`; it saves no verification
  result, and `svc_revisit()` restores none.
- Deferral point: `svcauth_gss_set_client()` runs after
  `svcauth_gss_accept()`, so the body has already been unwrapped when the copy
  is made.
- Repeating `gss_unwrap()`: wrong; the first pass decrypted in place and
  shrank the buffer, so the saved bytes are plaintext.
- Repeating the body `gss_verify_mic()`: wrong; `xdr_truncate_decode()` had
  already subtracted the checksum from `rq_arg.len`, so the saved copy no
  longer carries the complete message.
- Context-init path: `svcauth_gss_proc_init()` and
  `svcauth_gss_legacy_init()` have no `rq_deferred` test; a request deferred
  by the `cache_check()` on `rsi_cache` is processed again in full.

**Results of GSS calls**

- Statuses from the Kerberos mechanism: `GSS_S_COMPLETE`, `GSS_S_BAD_SIG`,
  `GSS_S_DEFECTIVE_TOKEN`, `GSS_S_FAILURE`, `GSS_S_CONTEXT_EXPIRED`;
  `gss_krb5_errno_to_status()` in `gss_krb5_mech.c` maps `-EBADMSG` and
  `-EPROTO` from `crypto/krb5/` and turns every other errno into
  `GSS_S_FAILURE`.
- **Potentially unsafe usage**: using the output after a status other than
  `GSS_S_COMPLETE`.
  - Unsafe: after `gss_verify_mic()` or `gss_unwrap()`;
    `gss_krb5_unwrap_v2()` returns `GSS_S_CONTEXT_EXPIRED` before it strips
    the token header, so the buffer is not in its final layout.
  - Safe: `GSS_S_CONTEXT_EXPIRED` from `gss_get_mic()` or `gss_wrap()`;
    `gss_krb5_get_mic_v2()` and `gss_krb5_wrap_v2()` test `endtime` last, after
    the token is written. `gss_wrap_req_integ()` and `gss_wrap_req_priv()`
    clear `RPCAUTH_CRED_UPTODATE`, return 0 and send the request.
- Server callers: treat `GSS_S_CONTEXT_EXPIRED` like any other failure.

| Client caller | Failure result |
|---|---|
| `gss_marshal()` | expired `-EKEYEXPIRED`; bad MIC `-EIO`; no space `-EMSGSIZE` |
| `gss_validate()` | bad MIC `-EACCES`; decode failure `-EIO`; never `-EBADMSG` |
| `gss_wrap_req_integ()` | bad MIC `-EIO`; no space `-EMSGSIZE` |
| `gss_wrap_req_priv()` | `-EIO`; `-EAGAIN` from `alloc_enc_pages()` |
| `gss_unwrap_resp_integ()`, `gss_unwrap_resp_priv()` | `-EIO` |

- `gss_validate()`: on `GSS_S_BAD_SIG` it retries the MIC against each entry
  of `rq_seqnos` before failing.
- `rpc_decode_header()` after a verifier failure with
  `RPCAUTH_CRED_UPTODATE` cleared: `rpcauth_invalcred()`, then
  `-EKEYREJECTED` while `tk_cred_retry` lasts, which restarts at
  `call_reserve` with a new XID.
- `rpc_decode_header()` after `-EACCES` with the cred still up to date: the
  task is put back on the receive queue and waits for another reply; nothing
  is retransmitted and the cred is not refreshed.
- `rpc_decode_header()` after `-EIO` from `gss_validate()` with the cred still
  up to date: re-encodes through `call_encode` while `tk_garb_retry` lasts.
- Reply unwrap failure: `call_decode()` stores the errno in `tk_status` with
  `tk_action` already `rpc_exit_task`; there is no retry.

| Server caller | Failure result |
|---|---|
| `svcauth_gss_verify_header()` | `rpcsec_gsserr_credproblem`, `SVC_DENIED` |
| `svcauth_gss_encode_verf()` for `RPC_GSS_PROC_DATA` | `rpcsec_gsserr_ctxproblem`, `SVC_DENIED` |
| `svcauth_gss_unwrap_integ()`, `svcauth_gss_unwrap_priv()` | `-EINVAL`, then `SVC_GARBAGE` |
| `svcauth_gss_wrap_integ()` | `-EINVAL` from `svcauth_gss_release()` |
| `svcauth_gss_wrap_priv()` | `-ENOMEM` for a `gss_wrap()` failure, else `-EINVAL` |

- Reply wrap failure: `svc_authorise()` returns non-zero, so
  `svc_process_common()` sends nothing and calls `svc_xprt_close()` on an
  `XPT_TEMP` transport.
- Absent names: there is no unwrap_integ_data, unwrap_priv_data,
  svcauth_gss_wrap_resp_integ or svc_return_autherr in this tree.

## Upcall caches and network namespaces

**Cache upcall channels**

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

**Cache lookup results**

- No request (`rqstp` NULL): `cache_check_rcu()` calls no `cache_upcall`, not
  even for early refresh, defers nothing, and turns `-EAGAIN` into `-ENOENT`.
- No request: the only results are 0 and `-ENOENT`; `-EAGAIN` and
  `-ETIMEDOUT` cannot occur. `gss_svc_searchbyctx()` passes NULL.
- `cache_check_rcu()`: never puts the caller's reference, on any return, so
  a caller that holds a reference still has to put it.
- 0 means `CACHE_VALID` set and `CACHE_NEGATIVE` clear; neither function
  calls `cache_is_expired()`. Lookup filters expired entries
  (`sunrpc_cache_find_rcu()`); a holder of a saved pointer tests expiry
  itself, as `ip_map_cached_get()` and `c_show()` do.
- Entry filled during the in-thread wait: `cache_defer_req()` returns false,
  `cache_is_valid()` runs again, and the result is 0 or `-ENOENT`, not
  `-ETIMEDOUT`.
- `cache_upcall` returning `-EAGAIN`: `cache_fresh_unlocked()` clears
  `CACHE_PENDING`; a not-yet-valid entry then ends as `-ETIMEDOUT`.
- `ip_map_cached_get()` does not call `cache_check()`; its caller
  `svcauth_unix_set_client()` does, and touches the entry only in `case 0`.
- **Unsafe usage**: calling `cache_check_rcu()` with a request inside
  `rcu_read_lock()`.
  - Unsafe: `cache_do_upcall()` allocates with `GFP_KERNEL` and
    `cache_wait_req()` sleeps for up to `req->thread_wait`.
  - Safe: pass NULL, as `c_show()` in `net/sunrpc/cache.c` and `e_show()` in
    `fs/nfsd/export.c` do between `cache_seq_start_rcu()` and
    `cache_seq_stop_rcu()`.
- **Unsafe usage**: calling `cache_check()` on an entry the caller holds no
  reference on.
  - Unsafe: `cache_check()` calls `cache_put()` on every non-zero return.
  - Safe: take the entry from `sunrpc_cache_lookup_rcu()`, which returns it
    with a reference, as `unix_gid_find()` does through `unix_gid_lookup()`.
  - Safe: with no reference, call `cache_check_rcu()` with NULL inside
    `rcu_read_lock()` instead, as `c_show()` does.

**Network namespaces**

- Socket creators other than `kernel_accept()` in `svc_tcp_accept()`, all
  through `__sock_create()` with `kern` = 1: `xs_create_sock()`,
  `xs_local_setup_socket()`, `svc_create_socket()`, and `rpc_sockname()` in
  `net/sunrpc/clnt.c`.
- Code under `net/sunrpc/` does not call `sock_create_kern()`.
- RDMA: `rpcrdma_create_id()` on the client; on the server
  `svc_rdma_create()` calls `svc_rdma_create_listen_id()`, which calls
  `rdma_create_id()`.
- `svc_rdma_listen_handler()`: on `RDMA_CM_EVENT_ADDR_CHANGE` it creates a
  new listener id with the transport's `xpt_net`.
- `__rdma_create_id()` in `drivers/infiniband/core/cma.c`: takes its own
  `get_net()`, so a `struct rdma_cm_id` pins its namespace; a kernel socket
  does not unless `sk_net_refcnt_upgrade()` was called on it.
- `sk_alloc()`: sets `sk_net_refcnt` to 0 for a `kern` socket; the socket
  takes `net_passive_inc()` and no `get_net_track()` reference on its
  namespace.
- `xs_create_sock()` and `svc_create_socket()`: call
  `sk_net_refcnt_upgrade()` for `IPPROTO_TCP` only, so a TCP socket holds its
  own counted reference; UDP, `AF_LOCAL` and `rpc_sockname()` sockets are
  not upgraded.
- `sk_net_refcnt_upgrade()`: has `WARN_ON_ONCE(sk->sk_net_refcnt)`;
  `svc_addsock()` takes a user socket from `sockfd_lookup()` and does not
  call it.
- `svc_addsock()`: returns `-EINVAL` when `sock_net(so->sk) != net`.
- Client reference: `xprt_init()`, called from `xprt_alloc()`, takes
  `get_net_track()`; `xprt_free()` drops it. `xprt_create_transport()` does
  not touch `xprt_net`.
- `rpc_net_ns()`: reads `xprt_net` of `clnt->cl_xprt` inside
  `rcu_read_lock()` and returns it without taking a reference.
- There is no svc_create_xprt() and `struct svc_serv` has no namespace
  member; the namespace is the `net` argument of `svc_xprt_create()` or
  `svc_xprt_create_from_sa()`.
- Socket transports: `svc_udp_init()` and `svc_tcp_init()` pass
  `sock_net(svsk->sk_sock->sk)` to `svc_xprt_init()`, so `xpt_net` comes from
  the socket, for listeners, accepted sockets and `svc_addsock()` alike.
- `svc_xprt_destroy_all()`: takes `serv`, `net` and a third argument
  `unregister`.
- GSS members of `struct sunrpc_net`: `rsc_cache` and `rsi_cache` are set up
  by `gss_svc_init_net()` through `rpcsec_gss_net_ops`, which
  `init_rpcsec_gss()` registers, not by `sunrpc_init_net()`; `gssp_lock` is
  initialised by `sunrpc_init_net()`.
- `sunrpc_exit_net()`: has `WARN_ON_ONCE(!list_empty(&sn->all_clients))`;
  every client of the namespace must be gone before exit.
- No code under `net/sunrpc/` reads `current->nsproxy`; each namespace comes
  from an object or an argument, apart from `&init_net` in `proc_dodebug()`.
- **Potentially unsafe usage**: passing an uncounted `struct net *` to
  `__sock_create()` or `net_generic()`.
  - Unsafe: when the pointer was read from an object that can be replaced
    or freed meanwhile, and the caller holds no reference on that object or
    on the namespace.
  - Safe: `xprt->xprt_net` while the caller holds the `struct rpc_xprt`, as
    `xs_create_sock()` does; `xprt_init()` took the reference.
  - Safe: `get_net()` inside `rcu_read_lock()` before the call and
    `put_net()` after, as `rpc_localaddr()` does around `rpc_sockname()`;
    `rpc_switch_client_transport()` puts the old `cl_xprt` only after
    `synchronize_rcu()`.
  - Safe: `xprt->xpt_net` while the caller holds the `struct svc_xprt`, as
    `svcauth_unix_set_client()` does; `svc_xprt_init()` took the reference.
  - Safe: the `net` given to a pernet `init` or `exit` callback, as
    `ip_map_cache_create()` uses it.
  - Safe: `genl_info_net(info)` or `sock_net(skb->sk)` inside a netlink
    handler, as `sunrpc_nl_cache_flush_doit()` does.
- **Potentially unsafe usage**: storing a `struct net *` in a long-lived
  object without `get_net()` or `get_net_track()`.
  - Unsafe: when the object can outlive the namespace's pernet exit.
  - Safe: `cd->net` set by `cache_create_net()` for a cache that a pernet
    `init` creates and the matching `exit` destroys, as `sunrpc_init_net()`
    and `sunrpc_exit_net()` do for the `ip_map` and `unix_gid` caches.
  - Safe: `rqstp->rq_bc_net` set by `svc_process_bc()`; it is the
    `xprt_net` of `req->rq_xprt` and is used during that request only, while
    the request holds the `xprt_get()` from `xprt_enqueue_bc_request()`.
  - Safe: `gss_auth->net`, taken with `get_net_track()` in
    `net/sunrpc/auth_gss/auth_gss.c` and dropped with `put_net_track()`.

**Uses of the initial namespace**

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

## Model gaps

### Other mistakes models make

- Models take a bad reply verifier to be retried or to refresh the cred.
  With an up-to-date cred and `-EACCES`, `rpc_decode_header()` returns
  `-EBADMSG`.
- Models take device removal to reach the client as a CM event. Client and
  server both register with `rpcrdma_rn_register()` in
  `net/sunrpc/xprtrdma/ib_client.c`.
- Models do not know the third argument of `svc_xprt_destroy_all()`. It
  decides whether `svc_rpcb_cleanup()` runs.
- Models take the temporary-connection limit to scale with the service.
  `svc_check_conn_limits()` compares `sv_tmpcnt` with `XPT_MAX_TMP_CONN`.
- Models take the thread total to equal the request.
  `svc_set_num_threads()` gives every pool at least one thread when
  `nrservs` is nonzero, so the total may exceed the request.
- Models do not know the write-pad MR. `rpcrdma_encode_write_list()` uses
  `re_write_pad_mr` unchecked.
- Models take `RPCSVC_MAXPAYLOAD` to be 1 MB. It is 4 MB in
  `include/linux/sunrpc/svc.h`.
- Models name rpcrdma_recv_buffer_put(). Here reps go back through
  `rpcrdma_rep_put()` or `rpcrdma_reply_put()`.
- Models name svc_rqst_release_page() and rq_vec. Here:
  `svc_rqst_page_release()`, `rq_bvec`.
- Models do not expect `kzalloc_obj()`, `kzalloc_objs()`, `kzalloc_flex()`
  or `kmalloc_obj()`. They are allocation macros defined in
  `include/linux/slab.h`.
- Models expect del_timer_sync() and from_timer(). This tree has
  `timer_delete_sync()` and `timer_container_of()`.
- Models expect `kernel_bind()` to take a `struct sockaddr`. It takes a
  `struct sockaddr_unsized`; see `svc_create_socket()`.
