# Questions: SunRPC (measurement set)

- guide: sunrpc.md
- title: SunRPC Subsystem

A wide set of questions about `net/sunrpc/`: the server side (services, thread
pools, request buffers, transports, the socket transports), the client side
(tasks and the call state machine, the transport core, the socket transports,
multipath), RPC-over-RDMA on both sides, RPCSEC_GSS on both sides, the
authentication caches, network namespaces, XDR and the backchannel. It is used
to measure what a model already knows before deciding what the built guide
should spend its words on. The hand-written guide it will replace is 1,143
words. NFSD, lockd and the NFS client have their own guides; this set stops at
the RPC layer. Format: `../../../docs/subsystem-questions.md`.

# The subsystem

## sunrpc.core-files: Source files

- section: Finding your way
- relevance: 4 - four domains in three directories, and new files no reader has seen
- words: 150

Which files under `net/sunrpc/` hold the client call state machine, the task
scheduler, the client transport core, the client socket transports, client
multipath, the server core, the server transport core, the server socket
transports, the authentication flavours on each side, the upcall caches, XDR,
the rpcbind client, rpc_pipefs, sysfs, the netlink interface and the
backchannel, and what do `auth_gss/` and `xprtrdma/` each hold? A table. Say
which are built only under a config option. Start from `net/sunrpc/Makefile`.

## sunrpc.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 130

For each job, which function do you start reading from: issue a synchronous
call, issue an asynchronous call, run one step of a client task, wait for and
handle the next request in a server thread, authenticate and dispatch one
request, send a reply, accept a TCP connection on the server, connect a client
TCP socket, read replies from a client TCP socket, handle a Receive completion
on the RDMA client, handle one on the RDMA server? A table.

## sunrpc.docs-and-tests: Documentation, tests and tracing

- section: Finding your way
- relevance: 3 - says what is written down and what is not
- words: 100

What in-tree documentation covers the RPC layer (the caches, server-side GSS,
the sysctls, NFS over RDMA, the maintainers' process), are there KUnit or other
tests under `net/sunrpc/`, is there fault injection, and which trace event
headers belong to it? Start from `Documentation/filesystems/nfs/rpc-cache.rst`
and `MAINTAINERS`.

# The server

## sunrpc.server-objects: Server objects

- section: Server threads and pools
- relevance: 4 - the vocabulary for everything else on the server
- words: 100

What do `struct svc_serv`, `struct svc_pool`, `struct svc_rqst`,
`struct svc_xprt`, `struct svc_program` and `struct svc_procedure` each
represent, how are they linked, and which of them is per thread rather than per
request? One line each.

## sunrpc.thread-lifecycle: Service thread lifecycle

- section: Server threads and pools
- relevance: 4 - the start and exit protocol has been reworked
- words: 110

How is a service thread created, how does it report whether its own
initialisation succeeded, and what must it call as its last act? Name the
functions and say which lock the caller must hold for each. Start from
`svc_new_thread()`, `svc_thread_init_status()` and `svc_exit_thread()`.

## sunrpc.thread-stop-handshake: Stopping a thread

- section: Server threads and pools
- relevance: 5 - a missed step hangs whoever is changing the thread count
- words: 120

Which pool flags and request flag take part in asking one service thread to
exit, who sets and who clears each, and what does the controller wait on? What
must a thread that exits for some other reason do, and does any path in this
tree use kthread_stop() on a service thread? Start from `svc_stop_kthreads()`
and `svc_thread_should_stop()`.

## sunrpc.dynamic-threads: Thread count range

- section: Server threads and pools
- relevance: 4 - a return value of the receive call now carries meaning
- words: 110

Does this tree let a pool run between a minimum and a maximum number of
threads? If so, how does `svc_recv()` tell its caller that a thread should be
added or may retire, which pool flag limits that signal, and who acts on it?
Start from `svc_set_pool_threads()`.

## sunrpc.rq-flags: Request flags

- section: Server threads and pools
- relevance: 3 - atomic or not depends on who else can touch the word
- words: 90

What does each bit in a request's `rq_flags` mean, which code outside the
owning thread can read or change the word, and what usage of non-atomic bit
operations on it is unsafe? Start from the enum in `include/linux/sunrpc/svc.h`.

## sunrpc.rqst-pages: Request and reply pages

- section: Server request buffers
- relevance: 5 - the page arrays were split and the refill rules changed
- words: 140

How many page arrays does a `struct svc_rqst` have, how are they sized, and what
do `rq_next_page`, `rq_page_end`, `rq_pages_nfree` and `rq_maxpages` mean? Who
refills which entries before the next request, and what must a transport
receive path do when it takes pages out of the request for its own use? Start
from `svc_init_buffer()`, `svc_alloc_arg()` and the comment above
`svc_serv_maxpages()`.

## sunrpc.replace-page-usage: Replacing a reply page

- section: Server request buffers
- relevance: 4 - who checks the bound decides where the bug is
- words: 90

What does `svc_rqst_replace_page()` check itself, what does it return, and what
happens to the page it displaces? What usage by a caller is unsafe, and what
does a correct caller do? Name one in-tree caller.

## sunrpc.svc-process-flow: Processing one request

- section: Server request buffers
- relevance: 4 - who sends and who releases has moved
- words: 130

In order, what happens to one request from the transport's receive method to
the release of its resources: decoding the header, authentication, the
program's own checks, dispatch, sending, the procedure's release hook, the
transport release? Say which function does each step and what each
`enum svc_auth_status` value makes the caller do. Start from `svc_process()`
and `svc_process_common()`.

## sunrpc.xpt-flags: Server transport flags

- section: Server transport lifecycle
- relevance: 4 - every lifecycle rule is phrased in these
- words: 150

Give a table of the bits in a server transport's `xpt_flags`: what each means,
who sets it and who clears it. Start from `include/linux/sunrpc/svc_xprt.h`.

## sunrpc.xpt-busy: Transport busy bit

- section: Server transport lifecycle
- relevance: 5 - a path that forgets to clear it parks the transport for ever
- words: 130

Who sets `XPT_BUSY` and who clears it? For each branch of `svc_handle_xprt()`
say whether that function calls `svc_xprt_received()` itself, leaves it to the
transport's receive method, or leaves the bit set on purpose. What does
`svc_xprt_received()` do besides clearing the bit?

## sunrpc.xprt-enqueue-conditions: Enqueue conditions

- section: Server transport lifecycle
- relevance: 4 - explains a transport that has data and is not being served
- words: 120

Under what conditions does `svc_xprt_enqueue()` actually queue a transport, and
how do write space, the space reserved for replies (`xpt_reserved`,
`svc_reserve()`) and the per-connection request limit come into it? Which
memory barriers pair up to stop two CPUs each deciding the other will enqueue?
Start from `svc_xprt_ready()`.

## sunrpc.xprt-close-paths: Closing a server transport

- section: Server transport lifecycle
- relevance: 4 - the two close calls are for different contexts
- words: 120

What is the difference between `svc_xprt_close()` and
`svc_xprt_deferred_close()`, which contexts may use each, and what does
`svc_delete_xprt()` then do, in order, including which reference it drops and
who is told?

## sunrpc.svc-xprt-refs: Server transport references

- section: Server transport lifecycle
- relevance: 5 - use-after-free from a callback is the classic bug here
- words: 120

Which of these hold a reference on a `struct svc_xprt`: the service's lists, a
request being processed, a deferred request, the ready queue, an asynchronous
callback? What usage around work that completes later is unsafe, and what does
correct in-tree code do? Start from `svc_xprt_get()`, `svc_xprt_dequeue()` and
`svc_tcp_handshake()`.

## sunrpc.dead-transport-checks: Dead transport checks

- section: Server transport lifecycle
- relevance: 3 - the check belongs under a particular lock
- words: 90

Where does server code test whether a transport is closing or dead before
using it, under which lock, and with which helper? Where is such a test not
needed? Start from `svc_xprt_is_dead()` and `svc_tcp_sendto()`.

## sunrpc.deferred-requests: Deferred requests

- section: Server transport lifecycle
- relevance: 4 - ownership of the transport context changes hands twice
- words: 130

How is a request deferred while a cache upcall is pending and later revisited:
what is copied, who owns the transport's per-request context (`rq_xprt_ctxt`)
at each step, which requests cannot be deferred, and what frees a deferred
request whose transport has died? Start from `svc_defer()`, `svc_revisit()`
and `svc_deferred_recv()`.

## sunrpc.svcsock-callbacks: Server socket callbacks

- section: Server sockets
- relevance: 4 - a child socket can run the listener's callback
- words: 120

Which socket callbacks does the server install on a listening socket and on a
connected one, and what does each do? What usage of `sk_user_data` in those
callbacks is unsafe, what ordering does `svc_setup_socket()` rely on, and what
does correct code check first? Start from `svc_tcp_listen_data_ready()`.

## sunrpc.svc-tcp-receive: TCP record reassembly

- section: Server sockets
- relevance: 4 - partial records live in the socket, not the request
- words: 120

How does the server read one RPC record from a TCP socket: how is a short read
of the marker or the body carried over to the next call, where are the pages
kept meanwhile, where is the record length bounded and against what, and what
closes the connection? Start from `svc_tcp_recvfrom()` and
`svc_tcp_read_marker()`.

## sunrpc.svc-tcp-send: Sending a TCP reply

- section: Server sockets
- relevance: 3 - the send path was rewritten around spliced pages
- words: 110

How does the server send a reply on TCP: how are the record marker and the
reply's pages handed to the socket, which lock keeps replies from interleaving,
and what happens on a short or failed send? Does the server send path cork the
socket in this tree? Start from `svc_tcp_sendto()`.

## sunrpc.svc-write-space: Write space coupling

- section: Server sockets
- relevance: 3 - a stalled sender must be restarted by a callback
- words: 80

Why does the server stop receiving on a connection it cannot send on, what
does the socket's write-space callback have to do to restart it, and what does
the TCP `xpo_has_wspace` method test? Start from `svc_write_space()`.

## sunrpc.svc-tls-handshake: Server TLS handshake

- section: Server sockets
- relevance: 3 - an asynchronous callback with a timeout and a cancel race
- words: 110

How does the server perform a TLS handshake on a connection: which transport
flags are involved, which method runs it, what pins the transport across the
completion callback, what happens on timeout, and what happens to data that
arrives meanwhile? Start from `svc_tcp_handshake()` and `svc_data_ready()`.

# The client

## sunrpc.client-objects: Client objects

- section: Client tasks
- relevance: 4 - the vocabulary for everything else on the client
- words: 110

What do `struct rpc_clnt`, `struct rpc_task`, `struct rpc_rqst`,
`struct rpc_xprt` and `struct rpc_xprt_switch` each represent, how are they
linked, and how is each reference counted? Name the get and put function for
each, and say if one of the get functions can fail.

## sunrpc.call-fsm-order: Call state machine

- section: Client tasks
- relevance: 4 - the order of the states is not the order people remember
- words: 120

List in order the states a normal call passes through, from `call_start()` to
decoding the reply, naming the function for each. Where does XDR encoding
happen relative to binding, connecting and transmitting, and why?

## sunrpc.task-action-rules: State function rules

- section: Client tasks
- relevance: 4 - a state that forgets its successor stalls the task
- words: 130

What must a `call_` state function arrange before it returns, how does a state
end the task with an error, and what does a NULL `tk_action` mean to
`__rpc_execute()`? What is the difference between `tk_status` and
`tk_rpc_status`, and what does `tk_callback` override? Start from `rpc_exit()`
and `rpc_call_rpcerror()`.

## sunrpc.slot-lifecycle: Request slots

- section: Client tasks
- relevance: 4 - a leaked slot is a hung mount
- words: 120

How is a request slot reserved and released: which functions, what happens when
none is free, where does the release happen for a task that completes and for
one that fails early, and what else does `xprt_release()` free? Start from
`xprt_reserve()` and `rpc_release_resources_task()`.

## sunrpc.xprt-switch: Multipath transport selection

- section: Client tasks
- relevance: 3 - a task can be moved to another transport
- words: 100

How does a task pick a transport from its client's transport switch, when may a
task that already has one be given another, and what must be released before
the new one is assigned? Start from `rpc_task_set_transport()` and
`net/sunrpc/xprtmultipath.c`.

## sunrpc.client-memory-context: Allocation context

- section: Client tasks
- relevance: 3 - the client runs under writeback and sometimes under swap
- words: 100

Which allocation context do the client's workqueue paths run in: where is a
no-filesystem-reclaim scope entered, what does `rpc_task_gfp_mask()` return
and when, and how is a transport that carries swap treated? Start from the
callers of `memalloc_nofs_save()` under `net/sunrpc/`.

## sunrpc.xprt-locks: Client transport locks

- section: Client transport core
- relevance: 5 - three spinlocks and a bit lock, each with its own territory
- words: 130

In a `struct rpc_xprt`, what does each of `transport_lock`, `reserve_lock`,
`queue_lock` and the `XPRT_LOCKED` state bit protect, and what does the socket
transport's `recv_mutex` add? A table. Say whether any of them is taken from
softirq or completion context.

## sunrpc.xprt-state-bits: Client transport state bits

- section: Client transport core
- relevance: 4 - connection logic is phrased in these
- words: 140

Give a table of the bits in a client transport's `state` word: what each means
and who sets and clears it. Start from the `XPRT_` definitions in
`include/linux/sunrpc/xprt.h`.

## sunrpc.send-recv-queues: Transmit and receive queues

- section: Client transport core
- relevance: 4 - reply matching races with retransmission
- words: 120

How are requests queued for transmission and for matching replies: which data
structure is each queue, why is a request put on the receive queue before it is
transmitted, and how is a request kept alive while a reply is being copied into
it? Start from `xprt_request_enqueue_receive()`, `xprt_lookup_rqst()` and
`xprt_pin_rqst()`.

## sunrpc.congestion-window: Congestion control

- section: Client transport core
- relevance: 3 - only some transports use it
- words: 100

What are `cong` and `cwnd` in a client transport, which lock covers them, which
transports use them, and which functions take and return a congestion credit?
Start from `xprt_request_get_cong()` and `xprt_adjust_cwnd()`.

## sunrpc.retransmit-timeouts: Timeouts and retransmission

- section: Client transport core
- relevance: 3 - the clamp and the major timeout decide soft-mount errors
- words: 120

What do the fields of `struct rpc_timeout` mean, how does a request's timeout
grow and where is it clamped, what is the difference between a minor and a
major timeout, and what does a major timeout do to a soft, a soft-connect and a
hard task? Start from `xprt_adjust_timeout()` and `rpc_check_timeout()`.

## sunrpc.connect-and-reconnect: Connecting and backoff

- section: Client transport core
- relevance: 4 - an immediate retry is a connection storm
- words: 120

How is a client connect scheduled: which workqueue, what serialises connect
attempts, how is the delay before a reconnect computed and grown, what resets
it, and what is the connect cookie for? Start from `xprt_connect()`,
`xs_connect()` and `xprt_reconnect_delay()`.

## sunrpc.xs-callbacks-teardown: Client socket teardown

- section: Client sockets
- relevance: 4 - callbacks can be running while the socket is torn down
- words: 120

In what order does the client tear down a socket: which locks are taken, when
is `sk_user_data` cleared relative to restoring the socket's original
callbacks, how is the socket itself released, and from which context must this
run? Start from `xs_reset_transport()`.

## sunrpc.xs-sock-state-flags: Socket state flags

- section: Client sockets
- relevance: 3 - a new flag must also be reset
- words: 100

What are the `XPRT_SOCK_` bits in a socket transport's `sock_state`, which of
them are cleared when the connection is reset and where, and which are
deliberately not? Start from `xs_sock_reset_state_flags()` and
`include/linux/sunrpc/xprtsock.h`.

## sunrpc.client-tls: Client TLS transport

- section: Client sockets
- relevance: 3 - a transport stacked on another transport
- words: 110

How does the client set up RPC-with-TLS: which transport class, what are the
stages of connecting, what probes the server first, how long may the handshake
take, and why does `xs_connect()` take a reference on the client only for such
transports? Start from `xs_tcp_tls_setup_socket()`.

# RPC over RDMA

## sunrpc.rdma-client-objects: RDMA client objects

- section: RDMA client
- relevance: 4 - the vocabulary for the client transport
- words: 120

What do `struct rpcrdma_xprt`, `struct rpcrdma_ep`, `struct rpcrdma_req`,
`struct rpcrdma_rep`, `struct rpcrdma_mr`, `struct rpcrdma_sendctx` and
`struct rpcrdma_regbuf` each represent, and which of them is reference counted
and by what? One line each. Start from `net/sunrpc/xprtrdma/xprt_rdma.h`.

## sunrpc.rdma-ownership-invariants: Reply-side ownership rules

- section: RDMA client
- relevance: 4 - the tree may state its own invariants
- words: 130

Does this tree write down, in a comment, the ownership rules for a Receive
buffer, a request, its registered MRs and its Send buffer on the RDMA client?
If so, where, and what does each rule say in one line? Start from the comments
around `rpcrdma_reply_handler()` in `net/sunrpc/xprtrdma/rpc_rdma.c`.

## sunrpc.rdma-mr-registration: Registering memory

- section: RDMA client
- relevance: 4 - the interface of the mapping function has changed
- words: 120

What is the contract of `frwr_map()`: what does it take, what does it return,
how does the caller walk a whole `xdr_buf` with it, and how is a failed DMA
mapping detected and unwound? Start from `net/sunrpc/xprtrdma/frwr_ops.c` and
the callers in `net/sunrpc/xprtrdma/rpc_rdma.c`.

## sunrpc.rdma-mr-invalidation: Invalidating MRs

- section: RDMA client
- relevance: 5 - the server can still write into an MR that was not fenced
- words: 120

What is the difference between `frwr_unmap_sync()` and `frwr_unmap_async()`,
which one completes the RPC and from where, what does remote invalidation
change, and at what point may an MR be reused? What happens when an
invalidation fails or is flushed?

## sunrpc.rdma-completion-fields: Work completion fields

- section: RDMA client
- relevance: 4 - reading a field of a failed completion is reading garbage
- words: 100

Which fields of a `struct ib_wc` may a completion handler rely on when the
status is not success, and how do the client's and the server's Send and
Receive handlers treat a flushed completion? Start from `rpcrdma_wc_receive()`
and `svc_rdma_wc_send()`.

## sunrpc.rdma-ep-references: Endpoint references

- section: RDMA client
- relevance: 4 - an unbalanced put frees the endpoint under the CM
- words: 120

Which connection manager events take or drop a reference on a
`struct rpcrdma_ep`, how are events that can arrive before the connection is
established kept from dropping one that was never taken, and how does device
removal reach the transport? Start from `rpcrdma_cm_event_handler()` and
`net/sunrpc/xprtrdma/ib_client.c`.

## sunrpc.rdma-credits-receives: Credits and posted receives

- section: RDMA client
- relevance: 3 - senders woken by a credit need a receive to land in
- words: 110

In the client's reply handler, in what order are the credit grant applied and
new Receives posted, how is the grant from the wire sanitised, and how many
Receives are asked for? Start from `rpcrdma_reply_handler()`,
`rpcrdma_update_cwnd()` and `rpcrdma_post_recvs()`.

## sunrpc.rdma-reconnect-buffers: Buffers across a reconnect

- section: RDMA client
- relevance: 3 - what disconnect unmaps, connect must map again
- words: 110

What does the RDMA client unmap, reset or destroy when a connection is torn
down, and what does it map or create again before posting Receives on the new
one? Start from `rpcrdma_xprt_disconnect()` and `rpcrdma_xprt_connect()`.

## sunrpc.svcrdma-sq-accounting: Server Send Queue accounting

- section: RDMA server
- relevance: 4 - a waiter that skips its turn stalls every sender behind it
- words: 130

How does the RDMA server reserve and return Send Queue entries, in what order
are threads that wait for entries served, what must every waiter do whether it
succeeds or the connection closes, and what wakes the waiters on close? Start from
`svc_rdma_sq_wait()`, `svc_rdma_wake_send_waiters()` and
`svc_rdma_xprt_deferred_close()`.

## sunrpc.svcrdma-post-send-usage: After posting a Send

- section: RDMA server
- relevance: 5 - the completion can run before the post returns
- words: 110

What usage of a send context after `ib_post_send()` has been called is unsafe,
and what does correct in-tree code do instead? What does the server do when
the post fails after part of a chain was accepted? Start from
`svc_rdma_post_send()` and `svc_rdma_post_send_err()`.

## sunrpc.svcrdma-ctxt-release: Releasing send contexts

- section: RDMA server
- relevance: 4 - release was moved out of the completion handler
- words: 120

Where are a send context's DMA mappings and pages released, what triggers that,
and in the Send completion handler what is the order of putting the context and
marking the transport for close when the completion was flushed? Start from
`svc_rdma_send_ctxt_put()`, `svc_rdma_send_ctxts_drain()` and
`svc_rdma_wc_send()`.

# RPCSEC_GSS

## sunrpc.gss-files: GSS layout and Kerberos crypto

- section: GSS server
- relevance: 4 - the Kerberos code may no longer be where readers remember
- words: 130

Which files under `net/sunrpc/auth_gss/` hold the client flavour, the server
flavour, the mechanism switch, the Kerberos mechanism and the gss-proxy upcall?
Where are the Kerberos encryption and checksum primitives implemented, which
encryption types are offered and how is the list chosen, and are any older
token formats still supported? Start from
`net/sunrpc/auth_gss/gss_krb5_mech.c`.

## sunrpc.gss-seq-window: Server sequence window

- section: GSS server
- relevance: 4 - replay protection rests on it
- words: 110

How does the server check a GSS sequence number: the window size, the largest
number accepted, which lock covers the window, what happens to a number below
the window or seen before, and what each outcome makes the RPC layer do. Start
from `gss_check_seq_num()` and `svcauth_gss_verify_header()`.

## sunrpc.gss-server-context-cache: Server context cache

- section: GSS server
- relevance: 4 - a lookup returns a reference someone must drop
- words: 120

How does the server find the context for an incoming GSS call, what reference
does the lookup return and where is it dropped, what extra reference is kept
for wrapping the reply, how is the credential handed to the request, and how
does a destroy call remove the context? Start from `gss_svc_searchbyctx()` and
`svcauth_gss_accept()`.

## sunrpc.gss-deferred-revisit: Revisited GSS requests

- section: GSS server
- relevance: 3 - skipping a check has to be safe, not just fast
- words: 90

Which verification steps does the server skip when a deferred GSS request is
replayed, in which functions, and given what `svc_defer()` saved would
repeating each be merely slow or actually wrong? Start from the tests of
`rq_deferred` in
`net/sunrpc/auth_gss/svcauth_gss.c`.

## sunrpc.gss-status-checks: Results of GSS calls

- section: GSS server
- relevance: 4 - an unchecked status is an authentication bypass
- words: 110

What do `gss_verify_mic()`, `gss_get_mic()`, `gss_wrap()` and `gss_unwrap()`
return, what must a caller do with it, and how do the server and the client
each turn a failure into an RPC-level outcome? Name in-tree callers that show
it.

## sunrpc.gss-slack: Reply slack and alignment

- section: GSS client
- relevance: 3 - the receive buffer is laid out from these estimates
- words: 110

What do `au_cslack`, `au_rslack`, `au_ralign` and `au_verfsize` in
`struct rpc_auth` mean, when are they recomputed, and why can the alignment and
the slack differ for a Kerberos privacy reply? Start from `gss_update_rslack()`
and `gss_unwrap_resp_priv()`.

## sunrpc.gss-upcall-matching: Client context upcalls

- section: GSS client
- relevance: 3 - the wrong match hands one user another's context
- words: 110

How does the client ask user space for a GSS context, what identifies an upcall
that is already in flight so that a second one is not sent, and how is a
downcall matched to its upcall? Start from `__gss_find_upcall()`,
`gss_add_msg()` and `gss_pipe_downcall()`.

## sunrpc.gss-client-seqno: Client sequence numbers

- section: GSS client
- relevance: 3 - retransmission and the server's window interact
- words: 110

How does the client assign a GSS sequence number to a request, which numbers
does it remember across retransmissions and where, when must a request be
encoded again before it is resent, and which number is a reply checked against?
Start from `gss_xmit_need_reencode()` and `xprt_rqst_add_seqno()`.

## sunrpc.gss-cred-lifetime: Credential and context lifetime

- section: GSS client
- relevance: 4 - three objects, three counts, some freed by RCU
- words: 120

How are a client `struct rpc_cred`, the `struct gss_cred` around it and its
`struct gss_cl_ctx` each reference counted and freed, which lookups are under
RCU, and on the server what owns the memory behind a `struct svc_cred` and what
frees it? Start from `gss_cred_get_ctx()`, `put_rpccred()` and
`free_svc_cred()`.

# Shared infrastructure

## sunrpc.cache-check-results: Cache lookup results

- section: Caches and namespaces
- relevance: 4 - the reference is consumed on some results and not others
- words: 110

What can `cache_check()` return, what does each value mean, and what happens to
the caller's reference on the entry in each case? How does `cache_check_rcu()`
differ, and what does passing no request change?

## sunrpc.cache-upcall-channels: Cache upcall channels

- section: Caches and namespaces
- relevance: 4 - there may be a second way to reach user space
- words: 120

How does a cache miss reach user space and how does the answer come back: which
files under procfs or rpc_pipefs, and does this tree also have a netlink
interface for the caches? If so, which caches use it, what is multicast, and
which commands exist. Start from `sunrpc_cache_notify()` and
`Documentation/netlink/specs/sunrpc_cache.yaml`.

## sunrpc.netns: Network namespaces

- section: Caches and namespaces
- relevance: 4 - every object has to carry the right one
- words: 120

Where does each RPC object keep its network namespace (server transport, client
transport, client, cache, per-namespace state), how are sockets and RDMA
connection identifiers created in it, and what usage of the initial namespace
or the current task's namespace is unsafe? Which uses of `init_net` remain under
`net/sunrpc/`, and is any of them a problem? Start from `struct sunrpc_net`.

## sunrpc.xdr-stream-usage: XDR stream decoding

- section: XDR, backchannel and change
- relevance: 3 - the decoder returns NULL and someone must look
- words: 110

What are the parts of a `struct xdr_buf`, what does `xdr_inline_decode()` return
when the data is not there or straddles a page, what is the scratch buffer for
and how is it set in this tree, and what usage of a decoded pointer is unsafe?
Start from `include/linux/sunrpc/xdr.h`.

## sunrpc.backchannel: Backchannel

- section: XDR, backchannel and change
- relevance: 3 - a client transport and a server transport share one connection
- words: 120

How do NFSv4.1 callbacks travel in each direction over an existing connection:
on the client, how is an incoming call recognised, which preallocated request
carries it and how does it reach a service thread; on the server, which fields
tie a `struct svc_xprt` to the client transport used to send callbacks? Start
from `svc_process_bc()` and `net/sunrpc/backchannel_rqst.c`.

## sunrpc.change-checklist: Changing the transport core

- section: XDR, backchannel and change
- relevance: 3 - the core is shared by more transports than come to mind
- words: 110

What must a change to the generic server or client transport code keep working:
which transport classes are registered on each side, which upper layers create
services and clients, what holds module references, and which tracepoints and
statistics do tools depend on? Start from `svc_reg_xprt_class()` and
`xprt_register_transport()`.
