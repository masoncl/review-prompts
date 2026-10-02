# Questions: SunRPC Subsystem

- guide: sunrpc.md
- title: SunRPC Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/sunrpc-measurement.md` is the
wider set the readers were measured on and `catalogue/sunrpc-measurement-results.md` says what
they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## sunrpc.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## sunrpc.core-files: Source files

- section: Finding your way
- relevance: 4 - every reader missed the netlink file and misplaced the Kerberos code

A table and nothing else, job to file under `net/sunrpc/`: the client call state machine; the task
scheduler; the client transport core; the client socket transports; client multipath; the server
core; the server transport core; the server socket transports; the upcall caches; the netlink
interface; the backchannel; and under `net/sunrpc/auth_gss/` and `net/sunrpc/xprtrdma/`, the
client side, the server side and the mechanism or registration code of each. Start from
`net/sunrpc/Makefile`.

# Server threads and requests

## sunrpc.server-objects: Per-thread and per-request state

- section: Server threads and requests
- relevance: 4 - the vocabulary for everything else on the server

Does a `struct svc_rqst` stand for one thread or for one request? What does it borrow from a
`struct svc_xprt` for the length of one request? How do a `struct svc_serv`, its pools, its
threads and its transports refer to one another?

## sunrpc.thread-lifecycle: Service thread lifecycle

- section: Server threads and requests
- relevance: 4 - the start and exit protocol has been reworked

How is a service thread created, how does it report whether its own
initialisation succeeded, and what must it call as its last act? Name the
functions and say which lock the caller must hold for each. Start from
`svc_new_thread()`, `svc_thread_init_status()` and `svc_exit_thread()`.

## sunrpc.thread-stop-handshake: Stopping a thread

- section: Server threads and requests
- relevance: 5 - one reader had the flags backwards, and the old rule about kthread_stop no longer applies

How is one service thread asked to exit, and how does the controller know that
it has: which side sets and which clears each flag involved? What must a
thread that exits for some other reason do, and does any path in this tree use
kthread_stop() on a service thread? Start from `svc_stop_kthreads()` and
`svc_thread_should_stop()`.

## sunrpc.dynamic-threads: Thread count range

- section: Server threads and requests
- relevance: 4 - no reader had the return values of the receive call right

Does this tree let a pool run between a minimum and a maximum number of
threads? If so, how does `svc_recv()` tell its caller that a thread should be
added or may retire, which pool flag limits that signal, and who acts on it?
Start from `svc_set_pool_threads()`.

## sunrpc.rqst-pages: Request and reply pages

- section: Server threads and requests
- relevance: 5 - every reader described one page array; there are two, and a count none recognised

How many page arrays does a `struct svc_rqst` have, and which of `rq_next_page`,
`rq_page_end`, `rq_pages_nfree` and `rq_maxpages` refers to which? Who refills
which entries before the next request, and what must a transport's receive path
do when it takes pages out of the request for its own use, so that the refill
is right? Start from `svc_init_buffer()`, `svc_alloc_arg()` and the comment
above `svc_serv_maxpages()`.

## sunrpc.svc-process-flow: Processing one request

- section: Server threads and requests
- relevance: 4 - the release hook now runs after the send, and one status value does not exist

Relative to sending the reply, when does a procedure's release hook run and who calls it? Who
releases the transport's resources for the request? What does each `enum svc_auth_status` value
make `svc_process_common()` do? Start from `svc_process()`.

## sunrpc.replace-page-usage: Replacing a reply page

- section: Server threads and requests
- relevance: 4 - the function checks the bound now; the caller checks the result

What does `svc_rqst_replace_page()` check itself, what does it return, and what happens to the
page it displaces? What are the requirements for a caller of `svc_rqst_replace_page()` in order to
assure safe usage? Name one in-tree caller.

# Server transports

## sunrpc.xpt-flags: Server transport flags

- section: Server transports
- relevance: 4 - every lifecycle rule is phrased in these

Which bits of a server transport's `xpt_flags` ask a thread to do something when it dequeues the
transport, and who is expected to clear each of those? Which bits only record a property of the
transport? Start from `include/linux/sunrpc/svc_xprt.h`.

## sunrpc.xpt-busy: Transport busy bit

- section: Server transports
- relevance: 5 - a path that forgets to clear it parks the transport for ever, and the old guide had the rule wrong

Who sets `XPT_BUSY` and who clears it? For each branch of `svc_handle_xprt()`
say whether that function calls `svc_xprt_received()` itself, leaves it to the
transport's receive method, or leaves the bit set on purpose. What does
`svc_xprt_received()` do besides clearing the bit?

## sunrpc.xprt-enqueue-conditions: Enqueue conditions

- section: Server transports
- relevance: 4 - explains a transport that has data and is not being served

Under what conditions does `svc_xprt_enqueue()` actually queue a transport, and
how do write space, the space reserved for replies (`xpt_reserved`,
`svc_reserve()`) and the per-connection request limit come into it? Which
memory barriers pair up to stop two CPUs each deciding the other will enqueue?
Start from `svc_xprt_ready()`.

## sunrpc.svc-xprt-refs: Server transport references

- section: Server transports
- relevance: 5 - each reader had a different holder of a reference wrong

What holds a reference on a `struct svc_xprt`, and what points to one and holds no reference? What
are the requirements for code that hands a `struct svc_xprt` to work that completes later, as
`svc_tcp_handshake()` does, in order to assure safe usage? Start from `svc_xprt_get()`,
`svc_xprt_dequeue()` and `svc_tcp_handshake()`.

## sunrpc.xprt-close-paths: Closing a server transport

- section: Server transports
- relevance: 4 - the two close calls are for different contexts

What is the difference between `svc_xprt_close()` and
`svc_xprt_deferred_close()`, which contexts may use each, and what does
`svc_delete_xprt()` then do, in order, including which reference it drops and
who is told?

## sunrpc.deferred-requests: Deferred requests

- section: Server transports
- relevance: 4 - ownership of the transport context changes hands twice

When a request is deferred while a cache upcall is pending and later
revisited, who owns the transport's per-request context (`rq_xprt_ctxt`) at
each step, which requests cannot be deferred, and what frees a deferred request
whose transport has died? Start from `svc_defer()`, `svc_revisit()` and
`svc_deferred_recv()`.

## sunrpc.svcsock-callbacks: Server socket callbacks

- section: Server transports
- relevance: 4 - a child socket can run the listener's callback

Which socket can run a callback that the server installed on a different one? What are the
requirements for reading `sk_user_data` in the server's socket callbacks in `net/sunrpc/svcsock.c`
in order to assure safe usage? What ordering does `svc_setup_socket()` rely on? Start from
`svc_tcp_listen_data_ready()`.

## sunrpc.svc-tcp-receive: TCP record reassembly

- section: Server transports
- relevance: 4 - partial records live in the socket, not the request

When the server reads an RPC record from a TCP socket and the marker or the
body arrives short, where are the partial record and its pages kept until the
next call, where is the record length bounded and against what, and what makes
the receive path close the connection? Start from `svc_tcp_recvfrom()` and
`svc_tcp_read_marker()`.

# Client transports

## sunrpc.xprt-state-bits: Client transport state bits

- section: Client transports
- relevance: 4 - connection logic is phrased in these

In a client transport's `state` word, which bit serialises senders and who may
clear it, which bits gate binding, connecting and closing, and which bit marks
a full slot table and which a full congestion window: which transports use the
window at all? Start from `XPRT_LOCKED` in `include/linux/sunrpc/xprt.h`.

## sunrpc.xprt-locks: Client transport locks

- section: Client transports
- relevance: 5 - two readers took the spinlocks from softirq, which no code does

In a `struct rpc_xprt`, what does each of `transport_lock`, `reserve_lock`,
`queue_lock` and the `XPRT_LOCKED` state bit protect, and what does the socket
transport's `recv_mutex` add? A table. Say whether any of them is taken from
softirq or completion context.

## sunrpc.slot-lifecycle: Request slots

- section: Client transports
- relevance: 4 - a leaked slot is a hung mount

What happens to a task when no request slot is free, where is a slot released
for a task that completes and for one that fails before it transmits, and what
else does `xprt_release()` free? Start from `xprt_reserve()` and
`rpc_release_resources_task()`.

## sunrpc.send-recv-queues: Transmit and receive queues

- section: Client transports
- relevance: 4 - reply matching races with retransmission

How are requests queued for transmission and for matching replies: which data structure is each
queue, and in what order is a request put on the receive queue and transmitted? How is a request
kept alive while a reply is being copied into it? Start from `xprt_request_enqueue_receive()`,
`xprt_lookup_rqst()` and `xprt_pin_rqst()`.

## sunrpc.connect-and-reconnect: Connecting and backoff

- section: Client transports
- relevance: 4 - an immediate retry is a connection storm

What serialises a client transport's connect attempts, how is the delay before
a reconnect computed and grown and what resets it, and what is the connect
cookie for? Start from `xprt_connect()`, `xs_connect()` and
`xprt_reconnect_delay()`.

## sunrpc.xs-callbacks-teardown: Client socket teardown

- section: Client transports
- relevance: 4 - the old guide and one reader have the order reversed

In what order does the client tear down a socket: when is `sk_user_data`
cleared relative to restoring the socket's original callbacks and under which
locks, how is the socket itself released, and from which context must this
run? Start from `xs_reset_transport()`.

# RDMA client

## sunrpc.rdma-client-objects: RDMA client objects

- section: RDMA client
- relevance: 4 - the vocabulary for the client transport

Which of the RDMA client's objects (transport, endpoint, request, reply, MR,
send context, registered buffer) are reference counted, and by what? Which
belong to the transport and survive a reconnect, and which belong to one
connection and are set up again, and when? Start from
`net/sunrpc/xprtrdma/xprt_rdma.h`.

## sunrpc.rdma-ownership-invariants: Reply-side ownership rules

- section: RDMA client
- relevance: 4 - the tree states its invariants and every reader said it does not

Does this tree write down, in a comment, the ownership rules for a Receive
buffer, a request, its registered MRs and its Send buffer on the RDMA client?
If so, where, and what does each rule say in one line? Start from the comments
around `rpcrdma_reply_handler()` in `net/sunrpc/xprtrdma/rpc_rdma.c`.

## sunrpc.rdma-mr-registration: Registering memory

- section: RDMA client
- relevance: 4 - every reader gave the old interface

What does `frwr_map()` take and return in this tree, where a reader's memory
offers a segment array, how does a caller walk a whole `xdr_buf` with it, and
how is a failed DMA mapping detected and unwound? Start from
`net/sunrpc/xprtrdma/frwr_ops.c` and the callers in
`net/sunrpc/xprtrdma/rpc_rdma.c`.

## sunrpc.rdma-credits-receives: Credits and posted receives

- section: RDMA client
- relevance: 3 - every reader and the old guide have the order backwards

In the client's reply handler, in what order are the credit grant applied and
new Receives posted, how is the grant from the wire sanitised, and how many
Receives are asked for? Start from `rpcrdma_reply_handler()`,
`rpcrdma_update_cwnd()` and `rpcrdma_post_recvs()`.

## sunrpc.rdma-ep-references: Endpoint references

- section: RDMA client
- relevance: 4 - two readers had the wrong events drop the reference

Which connection manager events take or drop a reference on a
`struct rpcrdma_ep`, how are events that can arrive before the connection is
established kept from dropping one that was never taken, and how does device
removal reach the transport? Start from `rpcrdma_cm_event_handler()` and
`net/sunrpc/xprtrdma/ib_client.c`.

## sunrpc.rdma-completion-fields: Work completion fields

- section: RDMA client
- relevance: 4 - reading a field of a failed completion is reading garbage

Which members of a `struct ib_wc` may a completion handler rely on when `status` is not
`IB_WC_SUCCESS`? How do the client's and the server's Send and Receive handlers treat a flushed
completion? Start from `rpcrdma_wc_receive()` and `svc_rdma_wc_send()`.

## sunrpc.rdma-mr-invalidation: Invalidating MRs

- section: RDMA client
- relevance: 5 - the server can still write into an MR that was not fenced

Which of `frwr_unmap_sync()` and `frwr_unmap_async()` is used when, and which completes the RPC
itself, and from where? At what point may an MR be reused or the memory behind it handed back to
the caller?

## sunrpc.rdma-remote-invalidation: Remote and failed invalidation

- section: RDMA client
- relevance: 5 - decides whether an MR is still registered when the RPC completes

What does the client still have to invalidate when the server has invalidated an MR remotely, and
how does it learn which MR that is? What happens to the MR and to the connection when an
invalidation fails or is flushed? Start from `frwr_reminv()`.

# RDMA server

## sunrpc.svcrdma-ctxt-release: Releasing send contexts

- section: RDMA server
- relevance: 4 - every reader had the put do something it does not

Where are a send context's DMA mappings and pages released, what triggers that,
and in the Send completion handler what is the order of putting the context and
marking the transport for close when the completion was flushed? Start from
`svc_rdma_send_ctxt_put()`, `svc_rdma_send_ctxts_drain()` and
`svc_rdma_wc_send()`.

## sunrpc.svcrdma-sq-accounting: Server Send Queue accounting

- section: RDMA server
- relevance: 4 - a waiter that skips its turn stalls every sender behind it, and no reader knew the scheme

Which completions return Send Queue entries on the RDMA server, in what order
are threads that wait for entries served and what must every waiter do whether
it succeeds or the connection closes, and which close function must the
completion handlers call so that the waiters are woken? Start from
`svc_rdma_sq_wait()`, `svc_rdma_wake_send_waiters()` and
`svc_rdma_xprt_deferred_close()`.

## sunrpc.svcrdma-post-send-usage: After posting a Send

- section: RDMA server
- relevance: 5 - the completion can run before the post returns

What are the requirements for code that reads or writes a `struct svc_rdma_send_ctxt` after
`ib_post_send()` has been called on its chain in order to assure safe usage? What does the server
do when `ib_post_send()` fails after it accepted part of a chain? Start from
`svc_rdma_post_send()` and `svc_rdma_post_send_err()`.

# RPCSEC_GSS

## sunrpc.gss-files: Kerberos crypto and token formats

- section: RPCSEC_GSS
- relevance: 4 - every reader put the Kerberos primitives in files that are gone

Where are the Kerberos encryption and checksum primitives that RPCSEC_GSS uses
implemented, where a reader's memory offers files under
`net/sunrpc/auth_gss/`, how is the list of encryption types that is offered
chosen, and which token formats and context versions are still supported?
Start from `net/sunrpc/auth_gss/gss_krb5_mech.c`.

## sunrpc.gss-server-context-cache: Server context cache

- section: RPCSEC_GSS
- relevance: 4 - a lookup returns a reference someone must drop

What reference does the server's lookup of the context for an incoming GSS call
return and where is it dropped, and what extra reference is kept for wrapping
the reply? Is the credential handed to the request a copy of the context's or
shared with it, so what does releasing the request free and what does
`free_svc_cred()` free? Start from `gss_svc_searchbyctx()` and
`svcauth_gss_accept()`.

## sunrpc.gss-cred-lifetime: Client credential and context lifetime

- section: RPCSEC_GSS
- relevance: 4 - three objects, three counts, some freed by RCU

How are a client `struct rpc_cred`, the `struct gss_cred` around it and its
`struct gss_cl_ctx` each reference counted and freed, and which lookups are
under RCU? Start from `gss_cred_get_ctx()` and `put_rpccred()`.

## sunrpc.gss-seq-window: Server sequence window

- section: RPCSEC_GSS
- relevance: 4 - no reader knew a failed check closes the connection

What does the server do with a GSS sequence number that is below the window or
has been seen before, and what does that outcome make the RPC layer do to the
request and to the connection? What are the window size and the largest number
accepted, and which lock covers the window? Start from `gss_check_seq_num()`
and `svcauth_gss_verify_header()`.

## sunrpc.gss-deferred-revisit: Revisited GSS requests

- section: RPCSEC_GSS
- relevance: 3 - skipping the checks is required, not a saving

Which verification steps does the server skip when a deferred GSS request is
replayed, in which functions, and given what `svc_defer()` saved would
repeating each be merely slow or actually wrong? Start from the tests of
`rq_deferred` in
`net/sunrpc/auth_gss/svcauth_gss.c`.

## sunrpc.gss-status-checks: Results of GSS calls

- section: RPCSEC_GSS
- relevance: 4 - an unchecked status is an authentication bypass, yet one status is sent anyway

What do `gss_verify_mic()`, `gss_get_mic()`, `gss_wrap()` and `gss_unwrap()`
return, what must a caller do with it, and how do the server and the client
each turn a failure into an RPC-level outcome? Name in-tree callers that show
it.

# Upcall caches and network namespaces

## sunrpc.cache-upcall-channels: Cache upcall channels

- section: Upcall caches and network namespaces
- relevance: 4 - no reader knew the netlink interface

Through which channels does a cache miss reach user space and the answer come
back, and does this tree also have a netlink interface for the caches? If so,
which caches use it, what is sent as a multicast, and where is the interface
defined? Start from `sunrpc_cache_notify()` and
`Documentation/netlink/specs/sunrpc_cache.yaml`.

## sunrpc.cache-check-results: Cache lookup results

- section: Upcall caches and network namespaces
- relevance: 4 - the reference is consumed on every result but one

What can `cache_check()` return, what does each value mean, and what happens to
the caller's reference on the entry in each case? How does `cache_check_rcu()`
differ, and what does passing no request change?

## sunrpc.netns: Network namespaces

- section: Upcall caches and network namespaces
- relevance: 4 - the helper the old guide names is not the one the tree uses

Which calls create sockets and RDMA connection identifiers in an RPC object's network namespace,
and where does the namespace come from on the server? What are the requirements for the `struct
net` that code under `net/sunrpc/` passes when it creates a socket or looks up per-net state, in
order to assure safe usage? Start from `struct sunrpc_net`.

## sunrpc.init-net-uses: Uses of the initial namespace

- section: Upcall caches and network namespaces
- relevance: 4 - a reviewer has to tell a use that is left on purpose from a new one

What is each use of `init_net` that remains under `net/sunrpc/` for?

# Model gaps

## sunrpc.model-gaps: Other mistakes models make

- drafts: all
- relevance: 5 - a model that is told how it is wrong can correct for it

Going by what each reader said from memory for every question in this guide, which is given
below, what do models believe about this code that is wrong in this tree? One bullet per mistake:
the belief, put plainly as a model would hold it, then what is true here and where to see it.
Cover names that are gone and what does the job now, numbers and limits that have changed,
behaviour that has changed, rules the readers state more broadly than the code supports, and what
is new that none of them knew. Most consequential first: a belief that would make a reviewer
approve a bug or reject correct code comes before a file that moved. Leave out what the readers
had right, and a slip only one of them made that the others show is not a belief. One or two lines to
a bullet: the belief and the truth. Every section of this guide already corrects what models
get wrong about its subject, and what a section covers is taken out of this list afterwards, so what
matters most here is what no question above asks about.
