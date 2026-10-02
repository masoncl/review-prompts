# What the sunrpc measurement found

Three models were asked the 64 questions in `sunrpc-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader C was the most current (it
assumed kernels from 6.12 to 7.0), reader A a little behind it (6.10 to 6.17),
and reader B older and much weaker: four answers in five of its were mostly
rewritten. For reader B the check of three questions (client objects, the call
state machine, the state function rules) came back empty the first time, and
those three were run again on their own; the numbers below include the second
run. After the runs seven questions were reworded to take out a clause that
leaned towards an answer ("which branch deliberately leaves the bit set" became
a three-way choice, "which may be taken from softirq" became "whether any");
what they ask for did not change. The hand-written guide was never checked
against current sources, so differences between it and the built guide are
expected and are noted near the end.

Readers A and C know the architecture on both sides, the socket transports and
most of the GSS protocol handling. What all three get wrong is what has been
reworked in the last few releases: the server's page arrays and thread
management, where a request's release hook runs, the RDMA server's Send Queue
and send-context handling, the RDMA client's registration interface, where the
Kerberos crypto lives, and the netlink side of the caches. They also share a
handful of wrong beliefs about who takes a reference or clears a bit.

## What all three readers got wrong

- **The server's page arrays.** All three described one `rq_pages` array with
  `rq_respages` pointing into it. `struct svc_rqst` has two separate arrays,
  `rq_pages` for the Call and `rq_respages` for the Reply, each allocated by
  `svc_init_buffer()` with `rq_maxpages + 1` entries and no pages.
  `rq_next_page` and `rq_page_end` index `rq_respages`. None recognised
  `rq_pages_nfree`: a transport that takes pages out of `rq_pages`
  (`svc_tcp_save_pages()`, `svc_rdma_clear_rqst_pages()`) must NULL the
  entries and set the count, because `svc_alloc_arg()` refills only that many
  entries and the reply range up to the old `rq_next_page`.
- **Thread count range.** A pool has `sp_nrthrmin` and `sp_nrthrmax`;
  `svc_recv()` returns `-ETIMEDOUT` when a thread above the minimum sat idle
  and `-EBUSY`, limited by `SP_TASK_STARTING`, when it took work and no thread
  was left idle; `nfsd()` acts on both under `mutex_trylock()`. Reader B said
  none of this exists, reader A hedged, reader C left out the conditions.
- **Where the release hook runs.** `svc_process()` calls `svc_send()` itself
  and then `svc_release_rqst()`, so `pc_release` runs after the reply is sent.
  Reader C had it run before the send, reader A did not know who calls it, and
  reader B had the receive method call `svc_process()`. Readers A and B also
  listed an SVC_SYSERR status that is not in `enum svc_auth_status`, and had
  `SVC_GARBAGE` produce a garbage-arguments reply; it produces an
  authentication error with `rpc_autherr_badcred`.
- **References on a server transport.** Readers A and B said
  `svc_xprt_enqueue()` takes a reference for the ready queue. It takes none;
  `svc_xprt_dequeue()` takes a new one. Reader C said `svc_tcp_handshake()`
  hands the transport to its callback without a reference (and gave the
  timeout as 20 seconds); it calls `svc_xprt_get()` first,
  `svc_tcp_handshake_done()` puts it, and `SVC_HANDSHAKE_TO` is 5 seconds.
  A deferred request holds no reference once it is queued on `xpt_deferred`.
- **The RDMA client states its own invariants.** All three said there is no
  such comment. "Reply-side ownership invariants", I1 to I5, is directly above
  `rpcrdma_reply_handler()`.
- **`frwr_map()`.** All three gave the old interface: a segment array in, the
  next segment or an error pointer out. It takes a
  `struct rpcrdma_xdr_cursor` and an MR the caller supplies and returns 0 or
  `-EIO`; the encoders loop until `rpcrdma_xdr_cursor_done()`. The
  rpcrdma_convert_iovs() all three named is gone.
- **Credits and Receives.** All three said Receives are posted before the
  credit grant is applied, and gave the reason. In `rpcrdma_reply_handler()`
  `rpcrdma_update_cwnd()` runs right after the XID lookup and
  `rpcrdma_post_recvs()` runs last; the grant is clamped to `re_max_requests`
  in the handler; the batch is `re_recv_batch`.
- **RDMA server send contexts.** Readers A and C had
  `svc_rdma_send_ctxt_put()` queue work on a workqueue, reader B had it unmap
  and free. It adds the context to `sc_send_release_list` and, when the list
  was empty, sets `XPT_DATA` and enqueues the transport;
  `svc_rdma_send_ctxts_drain()` does the unmapping from four callers.
- **RDMA server Send Queue.** Waiters are ordered by tickets
  (`sc_sq_ticket_head`, `sc_sq_ticket_tail`, `sc_sq_ticket_wait`); reader A had
  the two counters swapped, reader B said there is no ordering, reader C did
  not name them. Readers A and C had Write completions return entries; only
  `svc_rdma_wc_send()`, `svc_rdma_wc_read_done()` and
  `svc_rdma_post_send_err()` do. All three named `svc_xprt_deferred_close()`
  where the handlers call `svc_rdma_xprt_deferred_close()`, which also wakes
  both wait queues.
- **Kerberos.** All three put the encryption and checksum code in
  `gss_krb5_crypto.c` and a gss_krb5_keys.c, chosen by
  CONFIG_RPCSEC_GSS_KRB5_ENCTYPES options. The primitives are in
  `crypto/krb5/`; `gss_krb5_enctypes[]` lists six candidates that
  `gss_krb5_prepare_enctype_priority_list()` probes at module init; only the
  `KG2_TOK_` token formats and version 2 contexts remain. Readers A and C also
  named a KUnit test that went with the old code.
- **Netlink for the caches.** Reader C said it does not exist, reader A did
  not know, reader B said there are no get or set commands.
  `net/sunrpc/netlink.c` is generated from
  `Documentation/netlink/specs/sunrpc_cache.yaml`; `ip_map` and `unix_gid` use
  `sunrpc_cache_notify()`; the multicast group is `exportd`.
- **A GSS sequence failure closes the connection.** Readers A and C said the
  request is silently dropped, reader B that it is refused.
  `svcauth_gss_accept()` turns `SVC_DROP` from `svcauth_gss_verify_header()`
  into `SVC_CLOSE`, and a temporary transport is then closed.
- **`XPRT_SOCK_UPD_TIMEOUT`** is cleared by `xs_sock_reset_state_flags()`; two
  readers said it is deliberately kept and the third had a different caller
  wrong.
- **Moving a task to another transport.** All three missed the second path, on
  `XPRT_REMOVE` in `call_connect_status()`.
- **Swap and allocation context.** `rpc_task_gfp_mask()` depends only on
  `PF_WQ_WORKER`; nothing under `net/sunrpc/` sets `RPC_TASK_SWAPPER`; no
  connect worker enters a no-filesystem scope. Each reader had one of these
  wrong.
- **Endpoint references.** Only `RDMA_CM_EVENT_DISCONNECTED` drops the
  reference taken at `RDMA_CM_EVENT_ESTABLISHED`. Reader B had device removal
  and connect errors drop one, reader C had address change drop one. Device
  removal does not come through the CM handler at all:
  `net/sunrpc/xprtrdma/ib_client.c` calls `rpcrdma_ep_removal_done()`.

## What readers A and B got wrong as well

- `XPRT_CONGESTED` marks a full slot table (`xprt_add_backlog()`); a full
  congestion window is `XPRT_CWND_WAIT`, and only UDP, the RDMA client and the
  RDMA backchannel use the window at all.
- None of `transport_lock`, `reserve_lock` and `queue_lock` is taken from
  softirq: every site uses plain `spin_lock()`, socket callbacks queue work
  and the RDMA completion queues poll from a workqueue.
- `RQ_DATA` means the thread holds a per-connection request slot. RQ_SPLICE_OK
  and RQ_BUSY are not in the enum. `struct svc_pool` has no lock of its own.
- `cache_check()` with no request never makes an upcall and turns "pending"
  into `-ENOENT`; `-EAGAIN` means deferred, `-ETIMEDOUT` means neither valid
  nor deferred, and an upcall with no listener negates the entry.
- Sockets are created with `__sock_create()`, not sock_create_kern().
- A client wrap that gets `GSS_S_CONTEXT_EXPIRED` sends the request anyway.
- `__gss_find_upcall()` matches on uid and service; the downcall is matched by
  `gss_find_downcall()`, which is what tests for a message in flight.
- The client remembers up to three GSS sequence numbers in `rq_seqnos[]`, one
  per encode, not one field per request.
- `rq_cred` on the server is a shallow copy of the context's credential;
  `svcauth_gss_release()` drops only the group list.
- `gss_update_rslack()` runs once per `struct rpc_auth` and sets
  `au_rslack` to `au_verfsize` plus the trailing words.
- On a reconnect the RDMA client posts its first Receive before
  `rdma_connect()` and sets up send contexts, requests and MRs only once the
  connection is established.
- The deferred GSS request skips the MIC check, the integrity check and the
  decryption, not only the sequence window.

## What only reader B got wrong

Most of the rest, of which the parts that would change a review: it had the
stop handshake set `RQ_VICTIM` under a pool lock; `svc_rqst_replace_page()`
return void; the server callbacks take `sk_callback_lock`; a short send on TCP
retried with MSG_MORE rather than closing the connection; the client clear
`sk_user_data` after restoring the callbacks and release the socket with
`sock_release()`; binding and connecting come before encoding; rpc_task_get()
and rpc_clnt_get() exist; the sequence window be 32; tasks short of a slot
sleep on `sending`; and `xprt_reconnect_delay()` double the timeout.

## What only reader C got wrong

- The svc_pool_victim() it named no longer exists; `svc_stop_kthreads()` sets
  the two pool flags itself.
- The callbacks registered with `register_xpt_user()` run under `xpt_lock` and
  cannot sleep.
- A failed `receive_cb_reply()` does not close the connection.
- In `rpcrdma_xprt_disconnect()` the send contexts are destroyed before the
  requests are reset, and `rpcrdma_req_reset()` releases MRs left on
  `rl_registered`.

## What the readers already knew

All three: where to start reading for each job. Readers A and C: the server
and client objects and how they are counted (apart from `rpc_hold_client()`),
most of the branches of `svc_handle_xprt()` and who clears `XPT_BUSY`, the
listener callback that a child socket inherits and the barrier in
`svc_setup_socket()`, TCP record reassembly, that the server no longer corks,
write-space coupling, deferral and who owns `rq_xprt_ctxt`, the transmit and
receive queues and pinning, the GSS context cache, the sequence window
arithmetic, and client socket teardown (reader A exactly). Reader C also had
the call state machine, the state function rules, `cache_check()` and the GSS
status handling right.

## Where the hand-written guide is stale

`sunrpc.md` is a list of past bugs written as rules. Against this tree:

- CORE-003 speaks of kthread_stop() winning a race. No service thread is
  stopped that way; `svc_exit_thread()` always clears `SP_VICTIM_REMAINS`, and
  a thread that exits unasked takes the service mutex with `mutex_trylock()`.
- CORE-004 asks for a bounds check before `svc_rqst_replace_page()`. The
  function checks the bounds itself and returns false; the caller's job is to
  look at the result.
- CORE-005 says every exit of `svc_handle_xprt()` calls
  `svc_xprt_received()`. The receive branch leaves it to the transport's
  method or to `svc_deferred_recv()`, and the close branch leaves the bit set
  on purpose.
- CORE-011 gives a race with `svc_xprt_enqueue()` as the reason for atomic bit
  operations on `rq_flags`. Nothing outside the owning thread writes the word
  now; the one outside reader is nfsd's status dump.
- SOCK-004 gives the teardown order as restore callbacks, clear
  `sk_user_data`, `sock_release()`. The tree clears first, restores second,
  holds `recv_mutex` as well, and releases with `__fput_sync()`.
- SOCK-005 is about cork balance on the server. Only the client corks.
- RDMA-006 wants `XPT_CLOSE` set before a context is put. The completion
  handlers put first and then call `svc_rdma_xprt_deferred_close()`.
- RDMA-007 has device removal and address change arrive before the connection
  is established. Device removal no longer comes through the CM handler, and
  address change is settled with an exchange on `re_connect_status`.
- RDMA-009 says to post Receives before updating the window. The tree does the
  opposite.
- GSS-005 has `free_svc_cred()` release the request's credential. It frees the
  cached context's; the request drops only the group list.
- GSS-006 has `__gss_find_upcall()` match on in-flight state. That test is in
  `gss_find_downcall()`.
- GSS-007 calls skipping verification on a revisit a saving. Repeating it
  would reject the request as a replay.
- The namespace section names sock_create_kern(), serv->sv_net and
  rdma_dev_access_netns(); the tree uses `__sock_create()`, passes the
  namespace to `svc_xprt_create()`, and does not call the last. The two uses of
  `init_net` that remain are debugging output.
- The quick reference lists rpc_get_task and put_task. A task reference is
  taken with `atomic_inc()` on `tk_count` and dropped with `rpc_put_task()`.

## Left out of the build set

The hand-written guide is 1,143 words, so the build set holds 25 of the 64
questions. Kept: what every reader got wrong, the rules where the old guide now
points the wrong way, and the one table of files. Left out although a reader
got them wrong: the flag tables for `xpt_flags`, `rq_flags`, the client
`state` word and `sock_state` (long, and the headers carry comments); thread
start-up; enqueue conditions, the two close calls and dead-transport checks
(readers A and C were close); the server socket paths and both TLS
handshakes; slots, multipath, timeouts, reconnect backoff and the congestion
window on the client; allocation context; the RDMA object lists,
completion fields and what a reconnect rebuilds; GSS slack, upcall matching,
client sequence numbers and credential lifetime; XDR decoding, the
backchannel and the change checklist. Left out because readers A and C had
them right: entry points, the object lists, socket callbacks, write space,
deferral, the transmit and receive queues, the call state machine.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A: 158 corrections, 40% rewritten on average
reader B: 214 corrections, 79% rewritten on average
reader C: 131 corrections, 27% rewritten on average

question                            reader A      reader B      reader C
sunrpc.core-files                     18% ( 4)       22% ( 6)        6% ( 2)
sunrpc.entry-points                    0% ( 0)        7% ( 2)        0% ( 0)
sunrpc.docs-and-tests                 39% ( 3)       65% ( 5)       42% ( 4)
sunrpc.server-objects                  1% ( 1)       56% ( 3)       10% ( 1)
sunrpc.thread-lifecycle               28% ( 3)       79% ( 1)       14% ( 1)
sunrpc.thread-stop-handshake          28% ( 2)       79% ( 1)        7% ( 1)
sunrpc.dynamic-threads                72% ( 1)       94% ( 1)       43% ( 1)
sunrpc.rq-flags                       31% ( 2)       75% ( 1)       22% ( 1)
sunrpc.rqst-pages                     75% ( 5)       83% ( 6)       71% ( 5)
sunrpc.replace-page-usage             15% ( 2)       82% ( 3)       20% ( 2)
sunrpc.svc-process-flow               40% ( 4)       73% ( 5)       43% ( 3)
sunrpc.xpt-flags                      30% ( 3)       78% ( 5)       20% ( 4)
sunrpc.xpt-busy                       23% ( 1)       69% ( 2)       11% ( 2)
sunrpc.xprt-enqueue-conditions        29% ( 1)       89% ( 4)       22% ( 2)
sunrpc.xprt-close-paths               33% ( 1)       85% ( 2)       45% ( 2)
sunrpc.svc-xprt-refs                  42% ( 5)       81% ( 8)       29% ( 3)
sunrpc.dead-transport-checks          39% ( 2)       82% ( 5)       29% ( 1)
sunrpc.deferred-requests              30% ( 2)       85% ( 4)       15% ( 2)
sunrpc.svcsock-callbacks               5% ( 5)       65% ( 9)        0% ( 2)
sunrpc.svc-tcp-receive                12% ( 1)       81% ( 4)       14% ( 3)
sunrpc.svc-tcp-send                   15% ( 1)       82% ( 3)       13% ( 1)
sunrpc.svc-write-space                 0% ( 1)       87% ( 2)        0% ( 0)
sunrpc.svc-tls-handshake              51% ( 1)       86% ( 2)       30% ( 3)
sunrpc.client-objects                 13% ( 3)       71% ( 4)       14% ( 2)
sunrpc.call-fsm-order                 34% ( 2)       77% ( 2)        0% ( 0)
sunrpc.task-action-rules              44% ( 5)       71% ( 3)        5% ( 0)
sunrpc.slot-lifecycle                 56% ( 7)       85% ( 6)       34% ( 2)
sunrpc.xprt-switch                    71% ( 4)       82% ( 2)       47% ( 2)
sunrpc.client-memory-context          66% ( 3)       95% ( 3)       57% ( 3)
sunrpc.xprt-locks                     47% ( 4)       60% ( 5)       15% ( 5)
sunrpc.xprt-state-bits                38% ( 5)       60% ( 5)       11% ( 3)
sunrpc.send-recv-queues               25% ( 1)       84% ( 2)       23% ( 1)
sunrpc.congestion-window              45% ( 3)       94% ( 5)       22% ( 1)
sunrpc.retransmit-timeouts            29% ( 1)       87% ( 2)       17% ( 4)
sunrpc.connect-and-reconnect          32% ( 3)       88% ( 3)       32% ( 4)
sunrpc.xs-callbacks-teardown           5% ( 1)       80% ( 3)       28% ( 3)
sunrpc.xs-sock-state-flags            78% ( 3)       85% ( 3)       34% ( 3)
sunrpc.client-tls                     21% ( 3)       90% ( 3)       39% ( 2)
sunrpc.rdma-client-objects            24% ( 2)       57% ( 3)       11% ( 2)
sunrpc.rdma-ownership-invariants      94% ( 1)       90% ( 2)       85% ( 2)
sunrpc.rdma-mr-registration           46% ( 1)       85% ( 1)       39% ( 2)
sunrpc.rdma-mr-invalidation           46% ( 1)       82% ( 1)       51% ( 2)
sunrpc.rdma-completion-fields         62% ( 4)       81% ( 3)       47% ( 1)
sunrpc.rdma-ep-references             56% ( 1)       90% ( 2)       39% ( 1)
sunrpc.rdma-credits-receives          57% ( 1)       86% ( 2)       69% ( 1)
sunrpc.rdma-reconnect-buffers         73% ( 1)       93% ( 1)       39% ( 2)
sunrpc.svcrdma-sq-accounting          62% ( 6)       81% ( 4)       74% ( 6)
sunrpc.svcrdma-post-send-usage        38% ( 1)       85% ( 2)       36% ( 1)
sunrpc.svcrdma-ctxt-release           60% ( 2)       92% ( 3)       73% ( 2)
sunrpc.gss-files                      59% ( 4)       77% ( 5)       47% ( 3)
sunrpc.gss-seq-window                 28% ( 1)       81% ( 2)       17% ( 1)
sunrpc.gss-server-context-cache       24% ( 1)       83% ( 3)        6% ( 1)
sunrpc.gss-deferred-revisit           52% ( 1)       86% ( 1)        7% ( 1)
sunrpc.gss-status-checks              57% ( 1)       83% ( 4)        7% ( 2)
sunrpc.gss-slack                      32% ( 1)       84% ( 5)       22% ( 2)
sunrpc.gss-upcall-matching            32% ( 4)       81% ( 3)       11% ( 1)
sunrpc.gss-client-seqno               48% ( 2)       86% ( 4)       25% ( 1)
sunrpc.gss-cred-lifetime              32% ( 3)       88% ( 3)       28% ( 1)
sunrpc.cache-check-results            50% ( 4)       72% ( 4)        8% ( 2)
sunrpc.cache-upcall-channels          67% ( 2)       92% ( 4)       61% ( 2)
sunrpc.netns                          46% ( 2)       72% ( 4)       14% ( 2)
sunrpc.xdr-stream-usage               28% ( 4)       71% ( 3)       16% ( 3)
sunrpc.backchannel                    44% ( 4)       89% ( 5)       11% ( 3)
sunrpc.change-checklist               54% ( 4)       84% ( 5)       21% ( 3)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `sunrpc.slot-lifecycle`, `sunrpc.rdma-completion-fields`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `sunrpc.server-objects`, `sunrpc.thread-lifecycle`, `sunrpc.xpt-flags`, `sunrpc.xprt-enqueue-conditions`, `sunrpc.xprt-close-paths`, `sunrpc.deferred-requests`, `sunrpc.svcsock-callbacks`, `sunrpc.svc-tcp-receive`, `sunrpc.xprt-state-bits`, `sunrpc.send-recv-queues`, `sunrpc.connect-and-reconnect`, `sunrpc.rdma-client-objects`, `sunrpc.gss-server-context-cache`, `sunrpc.gss-cred-lifetime`.

## Questions reorganised

43 questions before and 43 after, every id kept, by subject after the file table: server threads
and requests (7), server transports (8), client transports (6), RDMA client (7), RDMA server (3),
RPCSEC_GSS (6), upcall caches and network namespaces (3). "Names that moved" and "Rules with two
sides" are gone and every question has a section. Nothing merged or dropped. Moved: the server
half of `sunrpc.gss-cred-lifetime` to `sunrpc.gss-server-context-cache`, the layout of
`auth_gss/` from `sunrpc.gss-files` to the file table. Inventories reworded: the two object lists
ask what is per thread or survives a reconnect, the two flag tables (`sunrpc.xpt-flags`,
`sunrpc.xprt-state-bits`) which bits ask for work or act as locks. Longer questions cut to three.
