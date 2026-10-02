# Questions: NFS server (measurement set)

- guide: nfsd.md
- title: NFS Server Subsystem

A wide set of questions about the in-kernel NFS server (`fs/nfsd/`), used to
measure what a model already knows before deciding what the built guide should
spend its words on. The hand-written guide it will replace is 2,848 words and
was never checked against current sources. The RPC server layer, lockd and the
NFS client are out of scope except where NFSD code depends on them. Format:
`../../../docs/subsystem-questions.md`.

# Finding your way

## nfsd.file-map: File map

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 130

Which files under `fs/nfsd/` hold: RPC dispatch and thread startup, the NFSv2,
NFSv3 and NFSv4 procedures, the XDR for each version, generated XDR, NFSv4
state, callbacks, client recovery records, layouts, file handles, the VFS glue,
the open file cache, the duplicate reply cache, exports, the control
filesystem, netlink, LOCALIO and debugfs? Name the header that declares the
main structures of each. A table.

## nfsd.entry-points: Entry points

- section: Finding your way
- relevance: 4 - where to start reading for each job
- words: 110

For each job, which function do you start reading from: dispatching an RPC,
running an NFSv4 compound, verifying a file handle, checking a stateid before
I/O, OPEN, LOCK, granting a delegation, breaking one, sending a callback,
moving READ and WRITE data, the periodic cleanup of NFSv4 state? A table.

## nfsd.docs: Documentation

- section: Finding your way
- relevance: 3 - several rules live only there
- words: 80

Which files under `Documentation/` describe NFSD for contributors, exporting
and re-exporting, LOCALIO, the I/O modes, the pNFS server, and the XDR and
netlink specifications that code is generated from?

# Request processing

## nfsd.dispatch: RPC dispatch

- section: Request path
- relevance: 4 - every procedure runs inside it
- words: 90

In what order does the NFSD dispatch function decode the arguments, consult the
duplicate reply cache, call the procedure, encode the result and update the
cache, and what does its return value tell the RPC layer? What happens to the
cache entry when encoding fails or the request is dropped? Start from
`nfsd_dispatch()`.

## nfsd.thread-local: Per-thread request state

- section: Request path
- relevance: 3 - state that used to live elsewhere
- words: 60

What per-thread structure does an nfsd thread attach to its `struct svc_rqst`,
through which field, what does it carry, and who writes and reads each member?
Start from `struct nfsd_thread_local_info`.

## nfsd.compound-loop: Compound processing checks

- section: Request path
- relevance: 5 - every NFSv4 operation depends on what ran before its handler
- words: 110

List in order the checks `nfsd4_proc_compound()` makes for each operation
before calling its handler, and what it does after the handler returns, up to
encoding and release. Which statuses end the loop early?

## nfsd.op-flags: Operation flags

- section: Request path
- relevance: 4 - a wrong flag skips a check or a cache
- words: 110

Give a table of the flags in `enum nfsd4_op_flags`: what each makes the
compound code do, and one operation that sets it. Start from `nfsd4_ops` in
`fs/nfsd/nfs4proc.c`.

## nfsd.new-operation: Adding an NFSv4 operation

- section: Request path
- relevance: 3 - several tables must stay in step
- words: 90

What has to be added to wire up a new NFSv4 operation: the tables, the
argument and result union, the reply size estimate, the release hook, the
current-stateid hooks, the statistics and trace names? Start from
`struct nfsd4_operation`, `nfsd4_dec_ops` and `nfsd4_enc_ops`.

## nfsd.drc: Duplicate reply cache

- section: Request path
- relevance: 3 - non-idempotent requests rely on it
- words: 90

Which requests does the duplicate reply cache cover, what is the lookup key,
which states can an entry be in, and how does an NFSv4 compound decide whether
it is cached at all? Start from `nfsd_cache_lookup()` and
`nfsd4_cache_this_op()`.

# Status codes

## nfsd.errno-mapping: Errno to NFS status

- section: Status codes
- relevance: 4 - an unmapped errno becomes an I/O error
- words: 80

How does `nfserrno()` turn a negative errno into an NFS status, what does it do
with an errno it has no entry for, and what do `ENOMEM`, `EAGAIN`,
`ETIMEDOUT`, `EOPENSTALE` and `EBADF` map to?

## nfsd.version-status-maps: Per-version status filtering

- section: Status codes
- relevance: 4 - shared code returns statuses older versions do not define
- words: 100

A status that a protocol version does not define must not reach that version's
clients. Where is that filtering done for NFSv2, for NFSv3 and for each NFSv4
minor version, and how does an NFSv2 or NFSv3 procedure hand back its NFS
status as distinct from its RPC accept status? Start from
`nfsd3_map_status()`.

## nfsd.status-type-usage: Mixing errno and NFS status

- section: Status codes
- relevance: 4 - the value still compiles and is wrong on the wire
- words: 90

What usage of `__be32` NFS status values and negative errno values is unsafe
(mixing them, converting twice, returning one where the other is expected),
and what that looks similar is correct? What catches such mistakes at build
time? Name in-tree code that converts correctly.

## nfsd.internal-status-codes: Internal status values

- section: Status codes
- relevance: 3 - they must never reach a client
- words: 80

Which `nfserr_` values are internal to the server and never sent to a client,
what does each signal, and where is each consumed? Start from the end of the
`nfserr_` definitions in `fs/nfsd/nfsd.h`.

# File handles and exports

## nfsd.fh-layout: File handle layout

- section: File handles
- relevance: 3 - decoding bugs here are remote
- words: 90

How is an NFSD file handle laid out in `struct knfsd_fh`: the header bytes, the
fsid types and their lengths, where the filesystem's own file id starts, and
the maximum size for each NFS version? Start from `fs/nfsd/nfsfh.h`.

## nfsd.svc-fh-fields: In-core file handle

- section: File handles
- relevance: 4 - which members are valid when
- words: 90

What does `struct svc_fh` hold besides the wire handle, which members are valid
only after a successful verify, and which record state that must be undone
when the handle is released?

## nfsd.fh-lifetime: Handle references

- section: File handles
- relevance: 4 - a missing release leaks a dentry and an export
- words: 90

Which references does a `struct svc_fh` own, which function drops them, who is
responsible for calling it for procedure arguments, for results and for the
NFSv4 current and saved handles, and what do `fh_copy()` and `fh_dup2()` do
about references?

## nfsd.fh-signing: Signed file handles

- section: File handles
- relevance: 3 - a new check on the decode path
- words: 80

Does this tree sign file handles? If so, what enables it, where is the
signature appended and where checked, which handles are exempt, and what
status does a bad signature produce? Start from `fh_append_mac()`. If the tree
has nothing of the kind, say so and stop.

## nfsd.fh-verify-steps: File handle verification steps

- section: Verifying a handle
- relevance: 5 - the trust boundary for every request
- words: 120

List in order what `fh_verify()` does on the first call for a handle and what
it repeats on later calls for the same handle. Include what its type argument
accepts (zero, a file type, a negated file type) and its side effect on the
calling thread's credentials. Start from `__fh_verify()` and
`nfsd_set_fh_dentry()`.

## nfsd.may-flags: Access flags

- section: Verifying a handle
- relevance: 4 - the wrong flag checks the wrong permission
- words: 120

Give a table of the `NFSD_MAY_` flags: which ask for a kind of access, which
are hints that change how the check is done, and which checks each hint skips.
Start from `fs/nfsd/vfs.h` and `nfsd_permission()`.

## nfsd.fh-verify-usage: Using a handle before verification

- section: Verifying a handle
- relevance: 5 - skipping verification is a remote hole and nothing in a diff shows it
- words: 110

What usage of `fh_dentry`, `fh_export` or the inode behind a `struct svc_fh`
is unsafe, and what that looks similar is correct? Cover helpers that rely on
their caller having verified, handles filled in by `fh_compose()`, and NFSv4
operations allowed to run with no verified current handle. Name in-tree code
for each.

## nfsd.pseudoroot: Pseudo-root exports

- section: Verifying a handle
- relevance: 3 - a version gate that is easy to lose
- words: 70

What is a `NFSEXP_V4ROOT` export, what may a client reach through it, and where
are NFSv2 and NFSv3 requests kept out of it? Start from `check_pseudo_root()`.

## nfsd.export-caches: Export caches

- section: Exports and credentials
- relevance: 3 - lookups can fail in several ways
- words: 90

How are `struct svc_export` and `struct svc_expkey` looked up, what fills them,
how are they reference counted, and what can the lookup functions return
besides an export? Start from `rqst_exp_find()` and `exp_get()`.

## nfsd.export-security: Export security policy

- section: Exports and credentials
- relevance: 4 - decides who may use an export
- words: 100

Which checks decide whether a request's transport security and RPC security
flavor are acceptable for an export, in what order do they run, which callers
may bypass the flavor check, and what status is returned on failure? Start
from `check_nfsd_access()`.

## nfsd.cred-setup: Request credentials

- section: Exports and credentials
- relevance: 4 - squashing and capabilities are set here
- words: 90

How are a request's credentials turned into the task's credentials: squashing,
the anonymous ids, supplementary groups, capabilities? Which function does it
and when in request processing does it run? Start from `nfsd_setuser()`.

## nfsd.user-namespace: User namespace for ids

- section: Exports and credentials
- relevance: 4 - wrong namespace gives wrong owners in a container
- words: 100

Which user namespace must uids and gids on the wire be converted in, and which
helper returns it? Do any NFSD paths use `init_user_ns` directly, and are they
correct? What usage of the results of `make_kuid()` or `from_kuid()` in NFSD is
unsafe, and what that looks similar is correct? Start from
`nfsd_user_namespace()`.

# XDR

## nfsd.xdr-decode-conventions: NFSv4 argument decoding

- section: XDR
- relevance: 4 - the conventions every decoder follows
- words: 110

What conventions do the NFSv4 argument decoders follow: their return type and
failure value, how memory that must outlive decoding is allocated and freed,
how a large opaque payload such as WRITE data is referenced without copying,
and what happens to the rest of a compound when one operation fails to decode?
Start from `nfsd4_decode_compound()` and `svcxdr_tmpalloc()`.

## nfsd.xdr-decode-bounds: Client-supplied lengths and counts

- section: XDR
- relevance: 5 - untrusted input reaches allocation sizes and loop bounds
- words: 100

What usage of a decoded length, count, bitmap length or index is unsafe, and
what that looks similar is correct? Name in-tree decoders that bound a count
before allocating or looping, and say which limits they use. Start from
`nfsd4_decode_bitmap4()` and the ACL decoders in `fs/nfsd/nfs4xdr.c`.

## nfsd.xdr-encode-conventions: NFSv4 result encoding

- section: XDR
- relevance: 4 - the conventions every encoder follows
- words: 100

What conventions do the NFSv4 result encoders follow: their signature, what
they return when the reply buffer is full, which small helpers encode the
basic types, and whether an encoder runs when its operation failed? Start from
`nfsd4_enc_ops` and `nfsd4_encode_operation()`.

## nfsd.xdr-encode-failure: Replies that do not fit

- section: XDR
- relevance: 5 - state has changed and the reply cannot be sent
- words: 110

An operation that changed something cannot be undone if its reply turns out
not to fit. How does NFSD avoid that, what does it do when an encoder still
fails or the reply exceeds the session or transport limit, and what does that
make unsafe in an operation's handler or encoder? Start from
`nfsd4_check_resp_size()` and `op_rsize_bop`.

## nfsd.xdrgen: Generated XDR code

- section: XDR
- relevance: 4 - new XDR is expected to be generated
- words: 100

Which NFSD XDR code is generated, from which specification files and by which
tool, how are the generated functions named, what do they return, and how is
the code regenerated? How does hand-written code call it? Start from
`fs/nfsd/nfs4xdr_gen.c` and `fs/nfsd/Makefile`.

## nfsd.fattr-encoding: Attribute encoding

- section: XDR
- relevance: 3 - the usual place a new attribute goes
- words: 100

How is a GETATTR or READDIR attribute list encoded: where are the
per-attribute encoders, what arguments do they get, how is the set of
supported attributes for each minor version defined, and what must be added
for a new attribute? Start from `nfsd4_encode_fattr4()`.

## nfsd.seqid-replay: NFSv4.0 owner replay cache

- section: XDR
- relevance: 3 - garbage here is replayed to the client
- words: 90

For NFSv4.0 operations that advance an owner's seqid, where is the last reply
kept, when is it saved and how much of it, what happens when it does not fit
the inline buffer, and how is a replay detected and answered? Start from
`struct nfs4_replay` and `nfsd4_encode_replay()`.

# Data transfer

## nfsd.page-arrays: Request and reply pages

- section: Data transfer
- relevance: 4 - the layout has changed and indexes are unchecked
- words: 100

Which page arrays and pointers does `struct svc_rqst` have for the call and for
the reply, what does each point to, which are allocated separately, and who
resets them between requests? Start from `include/linux/sunrpc/svc.h`.

## nfsd.next-page-usage: Reply page accounting

- section: Data transfer
- relevance: 4 - an off-by-one sends or frees the wrong page
- words: 110

What usage of `rq_next_page` by NFSD procedures and encoders is unsafe, and
what that looks similar is correct? Cover the NFSv3 READ, READLINK and READDIR
procedures, NFSv4 operations that put data in pages, and loops that consume
pages. Does any common NFSv4 code bring it back in step with the XDR stream,
and where?

## nfsd.read-paths: Read paths

- section: Data transfer
- relevance: 4 - three paths with different constraints
- words: 100

Which ways does NFSD have of reading file data into a reply (splice, vectored,
direct), which function implements each, and what decides which one a given
READ uses for NFSv3 and for NFSv4? Start from `nfsd_read()` and
`nfsd_read_splice_ok()`.

## nfsd.splice-actor: Splice read page handling

- section: Data transfer
- relevance: 3 - page replacement has been fixed more than once
- words: 80

How does the splice read path put page cache pages into the reply, when does
it skip adding a page, what bounds check protects the reply page array, and
what does it return when the array is full? Start from `nfsd_splice_actor()`.

## nfsd.write-path: Write path

- section: Data transfer
- relevance: 4 - stability and the verifier are promises to the client
- words: 110

How does NFSD write data: which function, how the payload reaches it, how the
stable-how argument and export options change what is done, what the write
verifier is and when it is reset, and what the configurable I/O modes change?
Start from `nfsd_vfs_write()` and
`Documentation/filesystems/nfs/nfsd-io-modes.rst`.

## nfsd.readdir-encoding: Directory reply buffers

- section: Data transfer
- relevance: 3 - count arguments are client controlled
- words: 90

How do the NFSv3 and NFSv4 READDIR implementations size and lay out their
reply buffers from the client's count arguments, what bounds the cost of each
entry, and how are unused reply pages given back afterwards?

# Open file cache

## nfsd.filecache-objects: Cache entries

- section: Open file cache
- relevance: 4 - two kinds of entry with different lifetimes
- words: 100

What is a `struct nfsd_file`, what is it keyed and matched on, what do its flag
bits mean, and how do garbage-collected and non-garbage-collected entries
differ in lifetime? Start from the comment at the top of
`fs/nfsd/filecache.c`.

## nfsd.filecache-acquire: Acquiring an open file

- section: Open file cache
- relevance: 3 - the variant chosen decides when the file closes
- words: 100

Give a table of the functions whose names begin `nfsd_file_acquire`: what each
takes, whether the result is garbage collected, and which protocol paths use
it.

## nfsd.filecache-lifetime: Closing cached files

- section: Open file cache
- relevance: 3 - a lingering open file blocks unmount and delete
- words: 100

What keeps an unused cache entry alive and what closes it: the LRU and its
worker, the shrinker, fsnotify events, unlink and rename, export removal,
server shutdown? Which of these wait for the close to finish? Start from
`nfsd_file_put()` and `nfsd_file_close_inode_sync()`.

# NFSv4 state

## nfsd.state-objects: State objects

- section: State objects
- relevance: 5 - nothing else in the NFSv4 code makes sense without it
- words: 140

List the NFSv4 state structures (client, session, the kinds of stateid, open
and lock owners, file, delegation, layout, blocked lock, copy state) and say
for each what it embeds or is embedded in, and which lists and tables it sits
on. A table. Start from `fs/nfsd/state.h`.

## nfsd.stateowner-refs: Owner references

- section: State objects
- relevance: 3 - hash membership and counted references differ
- words: 90

What holds a counted reference on a `struct nfs4_stateowner`, which memberships
are not counted, which lookups return a reference, and how many references does
`release_openowner()` consume? What usage around it is unsafe, and what that
looks similar is correct?

## nfsd.state-limits: Resource limits

- section: State objects
- relevance: 4 - each is a bound on what a remote client can allocate
- words: 120

Which limits bound what a client can make the server allocate: clients,
delegations, session slots and their reply caches, operations per compound,
async copies, blocked locks, tag and owner lengths? For each give the constant
or counter, written in full, and what is returned when it is hit.

## nfsd.stid-fields: Stateid type and status

- section: Stateids
- relevance: 5 - every stateid check is phrased in these
- words: 110

What values can `sc_type` and `sc_status` in `struct nfs4_stid` take, what does
each status bit mean, which kinds of stateid can carry it, and when is
`sc_type` set relative to the stateid going into the client's id table? Write
the constant names in full.

## nfsd.stid-status-locks: Locks for stateid status

- section: Stateids
- relevance: 5 - check-then-change races have shipped
- words: 90

Which lock protects `sc_status` for each kind of stateid? What usage of a
status check followed by a state change is unsafe, and what that looks similar
is correct? Name in-tree code that checks and changes under one lock hold.

## nfsd.stid-refcount: Stateid references

- section: Stateids
- relevance: 5 - use after free is the recurring bug class
- words: 110

What holds a reference on `sc_count` for each kind of stateid, how is a
reference taken, and what does `nfs4_put_stid()` do on the final put, in order,
including the lock it takes? What usage of a stateid around a put is unsafe,
and what that looks similar is correct?

## nfsd.stid-lookup: Finding a stateid

- section: Stateids
- relevance: 4 - the masks decide which states a caller sees
- words: 110

How does `nfsd4_lookup_stateid()` find a stateid: how the client is
identified, what the type mask and status mask arguments select, which statuses
it always lets through and then turns into errors, which stateids it hides, and
what it does with the special stateids?

## nfsd.preprocess-stateid: Stateid checks before I/O

- section: Stateids
- relevance: 5 - the second trust boundary after the file handle
- words: 120

What does `nfs4_preprocess_stateid_op()` verify before READ, WRITE, SETATTR and
similar operations: special stateids, the generation, that the stateid belongs
to the current file handle, the access mode, grace? What can it hand back to
the caller? Which operations look a stateid up some other way, and what do
they have to check for themselves?

## nfsd.stateid-generation: Generation numbers

- section: Stateids
- relevance: 3 - one helper, easy to bypass
- words: 70

How is a stateid's generation advanced and copied into a reply, what protects
it, how is wraparound handled, and how is a generation supplied by the client
compared? Which operations advance it?

## nfsd.open-stid-race: Racing with CLOSE

- section: Stateids
- relevance: 4 - a gap between two locks
- words: 90

Between finding an open or lock stateid and taking its mutex, the stateid can
be closed or revoked. How does the code detect that, which function wraps the
pattern, which lockdep subclasses does the mutex use, and what usage is
unsafe?

## nfsd.client-refs: Pinning a client

- section: Clients
- relevance: 5 - three counters that are easy to confuse
- words: 130

A `struct nfs4_client` has several counters: `cl_rpc_users`, the `cl_ref`
inside `cl_nfsdfs`, and `cl_cb_inflight`. What does each prevent, who takes and
drops each, who waits for each to drain, and what is the difference between
the put helpers that renew the lease and those that do not?

## nfsd.client-lifecycle: Client creation and destruction

- section: Clients
- relevance: 4 - teardown order is where the races are
- words: 120

How does a client go from SETCLIENTID or EXCHANGE_ID to confirmed, which
tables hold it at each stage, what marks it expired, what refuses to expire
it, and what does `__destroy_client()` tear down and in which order?

## nfsd.courtesy-clients: Courtesy clients

- section: Clients
- relevance: 4 - a small state machine with one-way edges
- words: 110

What are the values of `cl_state`, which function makes each transition and
under what condition, which transitions never happen, and what makes a
courtesy client active again? What part do the lock manager callbacks play?
Start from `nfs4_get_client_reaplist()` and `try_to_expire_client()`.

## nfsd.laundromat: Periodic cleanup

- section: Clients
- relevance: 3 - most expiry work starts here
- words: 100

List in order what one run of `nfs4_laundromat()` does, what decides when it
runs next, and which other workers and shrinkers clean up NFSv4 state.

## nfsd.admin-revoke: Administrative revocation

- section: Clients
- relevance: 3 - state disappears under running operations
- words: 110

Which administrative actions revoke NFSv4 state (by filesystem, by export, by
client), how is the revoked state marked, what does the client see, how is an
NFSv4.0 client's revoked state cleaned up, and what happens to async copies
and cached open files on the same filesystem? Start from
`nfsd4_revoke_states()`.

## nfsd.lock-order: Lock nesting

- section: Locking
- relevance: 5 - an inverted pair is a deadlock lockdep only finds if it runs
- words: 140

In what order do the NFSv4 state locks nest: `client_lock`, `deleg_lock`,
`cl_lock`, `fi_lock`, `s2s_cp_lock`, `async_lock`, `sc_lock`, `se_lock`,
`ls_lock`, `st_mutex`, `ls_mutex`, `nfsd_ssc_lock`, the file lock context's
`flc_lock`, and `nfsd_mutex`? Give the order as a list, outermost first, and
for each adjacent pair name a function that takes both. Which are sleeping
locks?

## nfsd.lock-scope: Lock coverage

- section: Locking
- relevance: 4 - which lock to take for which list
- words: 120

What does each of `client_lock`, `cl_lock`, `fi_lock`, `deleg_lock`,
`s2s_cp_lock`, `async_lock` and `blocked_locks_lock` protect? A table of lock,
scope (global, per net namespace, per client, per file) and the lists and
fields it covers.

## nfsd.nfsd-mutex: Server configuration mutex

- section: Locking
- relevance: 4 - control interfaces race with shutdown
- words: 100

What does `nfsd_mutex` protect, which control-file and netlink handlers take
it, which code runs with it held across server start and stop, and what usage
of `nfsd_serv` or per-net state without it is unsafe?

# Delegations

## nfsd.deleg-refs: Delegation references

- section: Delegations
- relevance: 4 - three kinds of reference on one object
- words: 80

Which references exist on a `struct nfs4_delegation` over its life (while
granted, while a recall is in progress, while a thread works on it), and who
drops each? Start from the comment above the structure in `fs/nfsd/state.h`.

## nfsd.deleg-grant: Granting a delegation

- section: Delegations
- relevance: 4 - several locks and several reasons to refuse
- words: 110

What conditions must hold for OPEN to hand out a delegation, which kind does it
choose, which locks are held when the delegation is hashed, and what happens
when the same client already holds one on the file? Start from
`nfs4_open_delegation()` and `nfs4_set_delegation()`.

## nfsd.deleg-break: Lease break callback

- section: Delegations
- relevance: 5 - runs under a VFS spinlock
- words: 110

In what context does the VFS call NFSD's lease break callback, which locks are
held, what is the callback allowed to do there and what is left to the
callback work item, and how does it affect a courtesy client? What may and may
not be done with stateid references in that context, and why? Start from
`nfsd_break_deleg_cb()`.

## nfsd.deleg-conflict-self: Breaker's own delegation

- section: Delegations
- relevance: 4 - a shortcut that must not hide other clients
- words: 110

When an NFSv4 operation would break a lease held for a delegation, how does
NFSD recognise that the delegation belongs to the client making the request,
where is that client recorded, and what still has to happen to delegations
held by other clients? How does the code tell an NFSD lease from someone
else's before treating the lease owner as a delegation? Start from
`nfsd_breaker_owns_lease()`.

## nfsd.deleg-revoke: Recall timeout and revocation

- section: Delegations
- relevance: 4 - the state machine after a recall is ignored
- words: 110

What happens when a recalled delegation is not returned in time: which list it
waits on, who notices, how it is marked, where it goes for NFSv4.0 and for
NFSv4.1 and later, and how FREE_STATEID completes the job? Start from
`revoke_delegation()`.

## nfsd.deleg-types: Delegation kinds

- section: Delegation kinds
- relevance: 4 - fields valid for one kind are read for another
- words: 90

Which delegation types can this server grant (read, write, with delegated
attributes, directory), which helpers classify `dl_type`, and which fields of
`struct nfs4_delegation` are valid only for some kinds?

## nfsd.deleg-timestamps: Delegated timestamps

- section: Delegation kinds
- relevance: 3 - recent and spread over four files
- words: 110

How do delegated timestamps work on the server: which file mode flag is set
and cleared and when, how SETATTR and DELEGRETURN treat the times the client
sends, which delegation fields record them, and what is done to the inode when
the delegation ends? When NFSD itself changes the attributes of a delegated
file, how does it avoid recalling the delegation it is acting on? Start from
`nfsd4_finalize_deleg_timestamps()`.

## nfsd.deleg-getattr: GETATTR against a write delegation

- section: Delegation kinds
- relevance: 3 - a callback in the middle of a GETATTR
- words: 90

What does the server do when another client sends GETATTR for a file that is
write-delegated: which callback it sends, how long it waits, what it does with
the answer, and what happens on timeout? Start from
`nfsd4_deleg_getattr_conflict()`.

## nfsd.dir-delegations: Directory delegations

- section: Delegation kinds
- relevance: 3 - a new kind of state with its own callback
- words: 110

Does this tree implement directory delegations? If so: which operation grants
one, how directory changes reach NFSD, how events are queued and sent, what
bounds the queue, and what causes a recall instead of a notification? Start
from `nfsd_get_dir_deleg()` and `nfsd_handle_dir_event()`. If not, say so and
stop.

# Callbacks

## nfsd.cb-lifecycle: Callback lifecycle

- section: Callbacks
- relevance: 4 - the contract every callback type implements
- words: 120

What is the life of a `struct nfsd4_callback` from `nfsd4_init_cb()` to
release: what the `prepare`, `done` and `release` operations are for and what
their return values mean, what the `cb_flags` bits mean, what `nfsd4_run_cb()`
returns, and how a callback is requeued?

## nfsd.cb-serialization: Callback channel state

- section: Callbacks
- relevance: 4 - little locking, much reliance on one workqueue
- words: 110

What serialises access to a client's callback RPC client, callback session and
connection state, which flags ask for the channel to be rebuilt or torn down,
what are the values of `cl_cb_state` and who sets them, and what does code
running in RPC context use to read the callback session safely? Start from
`nfsd4_process_cb_update()`.

## nfsd.cb-slots: Backchannel slots

- section: Callbacks
- relevance: 3 - sequence errors wedge the backchannel
- words: 110

How are backchannel slots handed out and returned, where are the per-slot
sequence numbers, who advances them and under what protection, and what is
done for each CB_SEQUENCE error? Start from `nfsd41_cb_get_slot()` and
`nfsd4_cb_sequence_done()`.

## nfsd.cb-usage: Queueing a callback

- section: Callbacks
- relevance: 5 - the object is freed while the RPC is in flight
- words: 120

What usage of `nfsd4_run_cb()` is unsafe, and what that looks similar is
correct? Cover what the caller must pin beforehand (the object embedding the
callback, the client), what the queueing function pins by itself, queueing
twice, what to do when it returns false, and where the pinned references are
dropped. Name in-tree callers for recall, CB_OFFLOAD and lock notification.

# Sessions

## nfsd.session-slots: Forward channel slots

- section: Sessions
- relevance: 4 - the table now grows and shrinks at run time
- words: 120

How are a session's forward channel slots stored, how large is each slot's
reply cache, how does the slot table grow and shrink at run time, what is
remembered for a slot that was freed, and what must be checked before indexing
the table with a slot id from the client? Start from `nfsd4_sequence()` and
`free_session_slots()`.

## nfsd.slot-seqid: Slot sequence check

- section: Sessions
- relevance: 4 - decides replay, new request or error
- words: 90

What are the possible outcomes of comparing a SEQUENCE request's sequence id
with the slot's, including a slot that is in use and one that was reused, what
status does each give, and when is the slot's sequence id updated? Start from
`check_slot_seqid()`.

## nfsd.slot-replay: Replay from the slot cache

- section: Sessions
- relevance: 4 - a cached reply can go to the wrong principal
- words: 110

What is stored in a slot after a compound completes, what is never stored,
which checks must pass before a cached reply is returned to a retransmission,
and what is returned when the original was not cached? When is the in-use flag
set and when cleared? Start from `nfsd4_store_cache_entry()` and
`replay_matches_cache()`.

# Grace and recovery

## nfsd.grace-checks: Operations during grace

- section: Grace and recovery
- relevance: 4 - a missing check lets new state in during reclaim
- words: 100

Which operations refuse non-reclaim requests during the grace period and
refuse reclaims outside it, which helper does each use, and what statuses are
returned? Start from `opens_in_grace()` and `locks_in_grace()`.

## nfsd.grace-end: Ending grace

- section: Grace and recovery
- relevance: 4 - must happen once, and not too soon
- words: 110

What ends the grace period, what can delay or force it, which per-net flag
bits track it, what must happen exactly once, and which clock and per-net
fields give the lease and grace durations? Start from `nfsd4_end_grace()` and
`clients_still_reclaiming()`.

## nfsd.client-tracking: Stable storage of clients

- section: Grace and recovery
- relevance: 3 - decides who may reclaim after a restart
- words: 100

Which client tracking back ends does this tree have, how is one chosen, what
does each operation in `struct nfsd4_client_tracking_ops` do and when is it
called, and which back ends are behind a config option?

# Copy offload

## nfsd.copy-objects: Copy state objects

- section: Copy offload
- relevance: 4 - the representation has been reworked
- words: 100

What represents an NFSv4.2 COPY while it runs synchronously and when it runs
asynchronously, what kind of stateid identifies an async copy and where is it
registered, and how do generic stateid operations treat it? Start from
`struct nfsd4_async_copy` and `nfs4_alloc_copy_stid()`.

## nfsd.copy-lifecycle: Async copy lifetime

- section: Copy offload
- relevance: 4 - a kthread, a callback, a reaper and client teardown share one object
- words: 130

Which flag bits and reference counts govern an async copy from `nfsd4_copy()`
through the worker thread, CB_OFFLOAD, the reaper and client teardown? In what
order are the results filled in, the callback sent and the copy made
unfindable, and what bounds how many run at once?

## nfsd.copy-cancel-status: Cancel and status lookups

- section: Copy offload
- relevance: 3 - races with completion
- words: 90

How do OFFLOAD_CANCEL and OFFLOAD_STATUS find an async copy, under which lock,
what pins it while they work, and which races with completion must they
tolerate? Start from `find_async_copy()`.

## nfsd.copy-notify: COPY_NOTIFY state

- section: Copy offload
- relevance: 3 - a stateid that authorises another server
- words: 100

Where are COPY_NOTIFY stateids kept, what links one to its parent stateid, what
frees it (the parent's final put, the laundromat, use), and what does the
destination server's READ have to present to be accepted? Start from
`manage_cpntf_state()` and `nfs4_free_cpntf_statelist()`.

# pNFS and byte-range locks

## nfsd.layouts: Layout state

- section: Layouts and locks
- relevance: 3 - a spinlock and a mutex on the same object
- words: 110

How is layout state represented, what do `ls_lock` and `ls_mutex` each protect,
how is a layout recalled, and what happens when the client does not return it?
Start from `fs/nfsd/nfs4layouts.c`.

## nfsd.lock-state: Byte-range lock state

- section: Layouts and locks
- relevance: 3 - VFS lock and NFSD state must agree
- words: 110

How does LOCK create or find a lock owner and a lock stateid, in what order
does it take the VFS lock and commit NFSD state, what is undone when the VFS
lock fails, and how are blocked locks tracked and the client notified? Start
from `nfsd4_lock()`.

# Administration

## nfsd.netlink-spec: Netlink family

- section: Administration
- relevance: 3 - generated files must not be edited
- words: 110

Where is NFSD's generic netlink family specified, which files are generated
from it, where are the handlers implemented, and what kinds of command does it
have (threads, versions, listeners, exports, unlock, statistics)? What must
change together when a command or attribute is added?

## nfsd.netlink-perms: Netlink handler rules

- section: Administration
- relevance: 4 - a handler acts for a namespace and a privilege level
- words: 100

How is privilege enforced for NFSD netlink commands, which network namespace
must a handler act on and how does it find it, and which handlers must hold
`nfsd_mutex`? What usage in a handler is unsafe, and what that looks similar
is correct?

## nfsd.server-lifecycle: Starting and stopping

- section: Administration
- relevance: 3 - per-net state exists only between two points
- words: 120

What is the sequence from a threads write or netlink command to running nfsd
threads, which per-net state is set up and torn down at each step, which flag
bits in `struct nfsd_net` record it, and how do code paths outside nfsd threads
pin a running server? Start from `nfsd_svc()` and `nfsd_net_try_get()`.

# Re-export and LOCALIO

## nfsd.reexport: Re-exporting NFS

- section: Re-export and LOCALIO
- relevance: 3 - the old guide's rules here name no code
- words: 110

What does the tree say about exporting an NFS mount: the documented
limitations, which `EXPORT_OP_` flags the NFS client sets for it and where NFSD
consults them, and what is required of the export's fsid? Does any NFSD code
test for an NFS superblock directly? Start from
`Documentation/filesystems/nfs/reexport.rst`.

## nfsd.localio: LOCALIO

- section: Re-export and LOCALIO
- relevance: 3 - file handle verification without an RPC request
- words: 100

What is LOCALIO on the server side: what the client calls, how a file handle
is verified without an RPC request, which checks are skipped and why, and how
per-net teardown invalidates local clients? Start from `nfsd_open_local_fh()`
and `fh_verify_local()`.

# Conventions

## nfsd.coding-style: Coding conventions

- section: Conventions
- relevance: 2 - maintainer preferences reviewers enforce
- words: 110

Which conventions do the NFSD maintainers document beyond the kernel coding
style: variable ordering, kernel-doc, function name prefixes, leaking errnos,
observability choices (BUG, WARN, printk, tracepoints), administrative
interfaces, stable tags? Start from
`Documentation/filesystems/nfs/nfsd-maintainer-entry-profile.rst`.
