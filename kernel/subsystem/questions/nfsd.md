# Questions: NFS Server Subsystem

- guide: nfsd.md
- title: NFS Server Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/nfsd-measurement.md` is the
wider set the readers were measured on and `catalogue/nfsd-measurement-results.md` says what they
got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## nfsd.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## nfsd.file-map: File map

- section: Source files
- relevance: 4 - turns a search into a lookup; readers misplaced the generated and netlink files

A table and nothing else, job to file under `fs/nfsd/`: RPC dispatch and thread startup; the
NFSv2, NFSv3 and NFSv4 procedures; the XDR for each version; generated XDR; NFSv4 state;
callbacks; client recovery records; layouts; file handles; the VFS glue; the open file cache; the
duplicate reply cache; exports; the control filesystem; netlink, generated and hand-written;
LOCALIO; debugfs.

# Requests and replies

## nfsd.thread-local: Per-thread request state

- section: Requests and replies
- relevance: 4 - every reader put this state in fields that no longer exist

Where does this tree keep the state NFSD needs for the length of one request,
such as the reply cache type and the lease breaker, where a reader's memory
offers fields of `struct svc_rqst`: what is the structure, how is it reached
from the request, and how long does it live? Start from
`struct nfsd_thread_local_info`.

## nfsd.page-arrays: Request and reply pages

- section: Requests and replies
- relevance: 4 - every reader described one shared array

Are the pages of a call and of its reply in one array of `struct svc_rqst` or
in two, which array do `rq_next_page` and `rq_page_end` point into, and who
resets them between requests? Start from `include/linux/sunrpc/svc.h`.

## nfsd.dispatch: RPC dispatch

- section: Requests and replies
- relevance: 4 - every procedure runs inside it

In what order does the NFSD dispatch function decode the arguments, consult the
duplicate reply cache, call the procedure, encode the result and update the
cache, and what does its return value tell the RPC layer? What happens to the
cache entry when encoding fails or the request is dropped? Start from
`nfsd_dispatch()`.

## nfsd.version-status-maps: Per-version status filtering

- section: Requests and replies
- relevance: 4 - shared code returns statuses older versions do not define

A status that a protocol version does not define must not reach that version's
clients. Where is that filtering done for NFSv2, for NFSv3 and for each NFSv4
minor version, and how does an NFSv2 or NFSv3 procedure hand back its NFS
status as distinct from its RPC accept status? Start from
`nfsd3_map_status()`.

## nfsd.errno-mapping: Errno to NFS status

- section: Requests and replies
- relevance: 4 - an unmapped errno becomes an I/O error

How does `nfserrno()` turn a negative errno into an NFS status, what does it do
with an errno it has no entry for, and what do `ENOMEM`, `EAGAIN`,
`ETIMEDOUT`, `EOPENSTALE` and `EBADF` map to?

## nfsd.status-type-usage: Status and errno types

- section: Requests and replies
- relevance: 4 - the value still compiles and is wrong on the wire

What are the requirements for NFSD code that holds or returns a `__be32` NFS status or a negative
errno, or that converts an errno to a status with `nfserrno()`, in order to assure safe usage?
What catches a violation at build time? Name in-tree code that converts correctly.

## nfsd.next-page-usage: Reply page accounting

- section: Requests and replies
- relevance: 4 - an off-by-one sends or frees the wrong page

What are the requirements for an NFSD procedure or encoder that reads or advances `rq_next_page`
in `struct svc_rqst` in order to assure safe usage? Does any common NFSv4 code bring
`rq_next_page` back in step with the XDR stream, and where?

# NFSv4 compounds and XDR

## nfsd.compound-loop: Compound processing checks

- section: NFSv4 compounds and XDR
- relevance: 5 - every NFSv4 operation depends on what ran before its handler

In what order does `nfsd4_proc_compound()` check each operation before it calls
the handler, so what may a handler assume has been done? After the handler
returns, who calls the operation's release hook and who maps the status for the
minor version: the loop or the encoder? Which statuses end the loop early?

## nfsd.op-flags: Operation flags

- section: NFSv4 compounds and XDR
- relevance: 4 - a wrong flag skips a check or a cache

Which flags in `enum nfsd4_op_flags` make the compound code skip a check it would otherwise make,
and which decide whether the reply is cached or a stateid is cleared? What are the requirements
for the `op_flags` of a new entry in `nfsd4_ops` in order to assure safe usage? Start from
`nfsd4_ops` in `fs/nfsd/nfs4proc.c`.

## nfsd.xdr-conventions: Decoder and encoder conventions

- section: NFSv4 compounds and XDR
- relevance: 4 - the conventions every decoder and encoder follows

What does an NFSv4 argument decoder return on failure, and what does `nfsd4_decode_compound()` do
with the rest of the compound then? Who frees memory from `svcxdr_tmpalloc()`, and when? Does
`nfsd4_encode_operation()` call the result encoder of an operation that failed? Start from
`nfsd4_decode_compound()`, `svcxdr_tmpalloc()` and `nfsd4_encode_operation()`.

## nfsd.xdr-payload-reference: Large payloads in decoders

- section: NFSv4 compounds and XDR
- relevance: 4 - a handler relies on how long the decoded payload stays valid

Does an NFSv4 argument decoder copy a large payload, such as the data of a WRITE, or refer to it
in place? For how long may a handler use what the decoder hands it? Start from
`nfsd4_decode_write()`.

## nfsd.xdr-encode-failure: Reply size checks

- section: NFSv4 compounds and XDR
- relevance: 5 - state has changed and the reply cannot be sent

An operation that changed something cannot be undone if its reply turns out not to fit. How does
NFSD avoid that, and what does it do when an encoder still fails or the reply exceeds the session
or transport limit? What are the requirements for an operation's `op_rsize_bop` estimate and for
its encoder in order to assure safe usage? Start from `nfsd4_check_resp_size()` and
`op_rsize_bop`.

## nfsd.xdr-decode-bounds: Client-supplied lengths and counts

- section: NFSv4 compounds and XDR
- relevance: 5 - untrusted input reaches allocation sizes and loop bounds

What are the requirements for a length or count that a decoder in `fs/nfsd/nfs4xdr.c` reads from
the client, before the decoder allocates or loops with it, in order to assure safe usage? Name
in-tree decoders that bound a count before allocating or looping, and say which limits they use.
Start from `nfsd4_decode_bitmap4()` and the ACL decoders in `fs/nfsd/nfs4xdr.c`.

## nfsd.xdrgen: Generated XDR code

- section: NFSv4 compounds and XDR
- relevance: 4 - new XDR is expected to be generated

Which NFSD XDR code is generated and must not be edited by hand, from what and
by which tool, and what do the generated functions return, as against the
hand-written decoders and encoders, so that code calling both gets each right?
Start from `fs/nfsd/nfs4xdr_gen.c` and `fs/nfsd/Makefile`.

## nfsd.new-operation: Adding an NFSv4 operation

- section: NFSv4 compounds and XDR
- relevance: 3 - several tables must stay in step

What are the requirements for a new operation's entries in `nfsd4_ops`, `nfsd4_dec_ops` and
`nfsd4_enc_ops` in order to assure safe usage? Does anything at build time check that the three
tables agree, and what does the compound code do at run time when an entry leaves a member of
`struct nfsd4_operation` unset? Start from `struct nfsd4_operation`, `nfsd4_dec_ops` and
`nfsd4_enc_ops`.

# File handles, exports and credentials

## nfsd.svc-fh-state: In-core file handle

- section: File handles, exports and credentials
- relevance: 4 - a missing release leaks a dentry and an export, and some members are valid only after a verify

What in a `struct svc_fh` may be used only after a successful `fh_verify()`, and what references
and other state does the structure own that `fh_put()` must undo? Who is responsible for releasing
the handles in procedure arguments and results, and the NFSv4 current and saved handles?

## nfsd.fh-copy-references: Copying a file handle

- section: File handles, exports and credentials
- relevance: 4 - a copied handle is released as well as its source

What do `fh_copy()` and `fh_dup2()` do about the references that the source `struct svc_fh` holds?
What are the requirements for a caller of each in order to assure safe usage?

## nfsd.fh-verify-steps: File handle verification steps

- section: File handles, exports and credentials
- relevance: 5 - the trust boundary for every request

In what order does `fh_verify()` make its checks on the first call for a
handle, and which does it repeat on later calls for the same handle? Which
values of its type argument does the code distinguish (read
`nfsd_mode_check()`, not the comment above `fh_verify()`), and for which kinds
of request are some of the checks skipped? Start from `__fh_verify()` and
`nfsd_set_fh_dentry()`.

## nfsd.may-flags: NFSD_MAY access flags

- section: File handles, exports and credentials
- relevance: 4 - the wrong flag checks the wrong permission

Which of the access flags defined beside `NFSD_MAY_READ` in `fs/nfsd/vfs.h` ask for a kind of
access, and which change how the check is done? Which checks does each flag of the second kind
skip? What are the requirements for a caller that passes a flag of the second kind in order to
assure safe usage? Start from `nfsd_permission()`.

## nfsd.export-security: Export security policy

- section: File handles, exports and credentials
- relevance: 4 - decides who may use an export

Where are an export's requirements on transport security and on the RPC
security flavor checked: by handle verification, by `check_nfsd_access()`, or
by both, and on which paths each? What is allowed to bypass the flavor check,
and what status is returned on failure?

## nfsd.cred-setup: Request credentials

- section: File handles, exports and credentials
- relevance: 4 - squashing and capabilities are set here

When in request processing are a request's credentials turned into the calling
thread's, and by which function? What does it do about squashing, the
anonymous ids, supplementary groups and capabilities, and what credentials does
the thread carry before the first handle of a request has been verified? Start
from `nfsd_setuser()`.

## nfsd.user-namespace: User namespace for ids

- section: File handles, exports and credentials
- relevance: 4 - wrong namespace gives wrong owners in a container

In which user namespace must NFSD convert uids and gids on the wire, and which helper returns it?
Which NFSD paths pass `init_user_ns` and not the namespace of the request, and what do they
convert? What are the requirements for a value that `make_kuid()` or `from_kuid()` returns in NFSD
in order to assure safe usage? Start from `nfsd_user_namespace()`.

## nfsd.fh-signing: Signed file handles

- section: File handles, exports and credentials
- relevance: 3 - every reader said the tree had none

Does this tree sign file handles? If so, what enables it, where is the signature checked, and
which handles are exempt? Write the export flag's name in full. Start from `fh_append_mac()`. If
the tree has nothing of the kind, say so and stop.

## nfsd.fh-signing-status: Bad file handle signature

- section: File handles, exports and credentials
- relevance: 3 - the status decides what a client does with the handle next

What status does NFSD return for a file handle whose signature does not verify? Start from
`fh_verify_mac()`. If the tree does not sign file handles, say so and stop.

## nfsd.reexport: Re-exporting NFS

- section: File handles, exports and credentials
- relevance: 3 - the old guide's rules here name no code

How does NFSD learn that the filesystem behind an export needs special handling, as an NFS mount
does, and where does it test for that? What is required of such an export's fsid, and which
limitations are documented? Write every name in full. Start from
`Documentation/filesystems/nfs/reexport.rst`.

## nfsd.fh-verify-usage: Unverified and composed handles

- section: File handles, exports and credentials
- relevance: 5 - skipping verification is a remote hole and nothing in a diff shows it

What are the requirements for reading `fh_dentry`, `fh_export` or the inode behind a `struct
svc_fh` in order to assure safe usage, for a handle passed to `fh_verify()` and for a handle
filled in by `fh_compose()`? What must the handler of an NFSv4 operation that may run with no
verified current handle do before it reads the handle? Name in-tree code for each.

# Stateids

## nfsd.state-objects: State objects

- section: Stateids
- relevance: 5 - nothing else in the NFSv4 code makes sense without it

How do the NFSv4 state structures nest: which kinds of object embed a
`struct nfs4_stid` and which a `struct nfs4_stateowner`, through which table is
a stateid looked up as against the lists it also sits on, and what does this
tree call the kinds of stateid, where a reader's memory offers older names?
Start from `fs/nfsd/state.h`.

## nfsd.stid-fields: Stateid type and status

- section: Stateids
- relevance: 5 - every stateid check is phrased in these

Which kinds of stateid can carry each bit of `sc_status` in `struct nfs4_stid`? When is `sc_type`
set relative to the stateid going into the client's id table, and what does a lookup in between
see? Write the constant names in full.

## nfsd.stid-lookup: Finding a stateid

- section: Stateids
- relevance: 4 - the masks decide which states a caller sees

What do the type mask and the status mask given to `nfsd4_lookup_stateid()`
select, which statuses does it let through whatever the mask and then turn into
errors, and which stateids does it never return?

## nfsd.preprocess-stateid: Stateid checks before I/O

- section: Stateids
- relevance: 5 - the second trust boundary after the file handle

What does `nfs4_preprocess_stateid_op()` verify about a stateid and the current file handle before
it returns success, and what can it hand back to the caller? Which operations look a stateid up
some other way, and what do they have to check for themselves?

## nfsd.stid-refcount: Stateid references

- section: Stateids
- relevance: 5 - use after free is the recurring bug class

What holds a reference on `sc_count` for each kind of stateid, and whose is the one set at
allocation? What does `nfs4_put_stid()` do on the final put, in order, including the lock it
takes? What are the requirements for code that uses a stateid after a put, or that takes a
reference on `sc_count`, in order to assure safe usage?

## nfsd.stid-status-locks: Locks for stateid status

- section: Stateids
- relevance: 5 - check-then-change races have shipped

Which lock protects `sc_status` in `struct nfs4_stid` for each kind of stateid? What are the
requirements for code that tests `sc_status` and then changes the state of the stateid in order to
assure safe usage? Name in-tree code that shows it.

## nfsd.open-stid-race: Stateid mutex after lookup

- section: Stateids
- relevance: 4 - a gap between two locks

An open or lock stateid can be closed or revoked between the lookup that finds it and the taking
of its `st_mutex`. How does `nfsd4_lock_ol_stateid()` detect that, and what does it return? What
are the requirements for code that takes `st_mutex` on a stateid it has just looked up in order to
assure safe usage?

# Clients and state locks

## nfsd.client-lifecycle: Client creation and destruction

- section: Clients and state locks
- relevance: 4 - teardown order is where the races are

Which tables hold a client between SETCLIENTID or EXCHANGE_ID and
confirmation, and which after it, what marks a client expired and what refuses
to expire it, and in which order does `__destroy_client()` tear things down?

## nfsd.client-refs: Client reference counters

- section: Clients and state locks
- relevance: 5 - three counters that every reader partly confused

A `struct nfs4_client` has several counters: `cl_rpc_users`, the `cl_ref` inside `cl_nfsdfs`, and
`cl_cb_inflight`. What does each prevent and who waits for it to drain, and which should a
callback or an async copy hold?

## nfsd.client-put-helpers: Client put helpers

- section: Clients and state locks
- relevance: 5 - the choice decides whether a put renews the client's lease

What is the difference between `put_client_renew()` and `put_client_no_renew()`, and which callers
must use the second?

## nfsd.courtesy-clients: Courtesy clients

- section: Clients and state locks
- relevance: 4 - a small state machine whose edges readers got wrong

Which transitions between the values of `cl_state` happen and which never do,
what makes a courtesy or an expirable client active again, and what part do
the lock manager callbacks play? Write the state names in full. Start from
`nfs4_get_client_reaplist()` and `try_to_expire_client()`.

## nfsd.admin-revoke: Administrative revocation

- section: Clients and state locks
- relevance: 3 - state disappears under running operations

Which administrative actions revoke NFSv4 state? How is the state they revoke marked, and what
status does the client get when it next uses that state? Start from `nfsd4_revoke_states()`.

## nfsd.admin-revoke-cleanup: Cleanup after administrative revocation

- section: Clients and state locks
- relevance: 3 - copies and open files use the filesystem whose state is revoked

When an administrator revokes the NFSv4 state on a filesystem, what happens to async copies and to
cached open files on that filesystem? How is the revoked state of an NFSv4.0 client freed? Start
from the callers of `nfsd4_revoke_states()`.

## nfsd.state-limits: Resource limits

- section: Clients and state locks
- relevance: 4 - each is a bound on what a remote client can allocate

What bounds the number of clients, of delegations and of each other kind of object that a remote
client can make the NFSv4 server allocate, and what is returned when the bound is hit? Write the
constants and counters in full.

## nfsd.lock-order: Lock nesting

- section: Clients and state locks
- relevance: 5 - every reader had at least one pair inverted

Which of these NFSv4 state locks does code take while it holds another of them: `client_lock`,
`deleg_lock`, `cl_lock`, `fi_lock`, `s2s_cp_lock`, `async_lock`, `sc_lock`, `se_lock`, `ls_lock`,
`st_mutex`, `ls_mutex`, `nfsd_ssc_lock`, the file lock context's `flc_lock`, and `nfsd_mutex`? For
each such pair, name the outer lock, the inner lock and a function that takes both. Which are
sleeping locks?

# Delegations

## nfsd.deleg-types: Delegation kinds

- section: Delegations
- relevance: 4 - fields valid for one kind are read for another

Which kinds of delegation can this server grant, and which helpers classify `dl_type`? Which
members of a `struct nfs4_delegation` are valid only for some kinds of delegation, and for which
kinds?

## nfsd.deleg-grant: Granting a delegation

- section: Delegations
- relevance: 4 - several locks and several reasons to refuse

What conditions must hold for OPEN to hand out a delegation and which kind does
it choose, which locks are held when the delegation is hashed, and what happens
when the same client already holds one on the file? Write the delegation type
names in full. Start from `nfs4_open_delegation()` and
`nfs4_set_delegation()`.

## nfsd.deleg-refs: Delegation references

- section: Delegations
- relevance: 4 - three kinds of reference on one object

Which references are held on a `struct nfs4_delegation` over its life, what is each held for, and
who drops each? Start from the comment above the structure in `fs/nfsd/state.h`.

## nfsd.deleg-break: Lease break callback

- section: Delegations
- relevance: 5 - runs under a VFS spinlock

In what context and under which locks does the VFS call NFSD's lease break
callback, so what may the callback do itself and what is left to the callback
work item? What may and may not be done with stateid references there, and
why, and how does a break affect a courtesy client? Start from
`nfsd_break_deleg_cb()`.

## nfsd.deleg-conflict-self: Breaker's own delegation

- section: Delegations
- relevance: 4 - a shortcut that must not hide other clients

When an NFSv4 operation would break a lease held for a delegation, how does
NFSD recognise that the delegation belongs to the client making the request
and where is that client recorded, what still has to happen to delegations
held by other clients, and how does the code tell an NFSD lease from someone
else's before treating the lease owner as a delegation? Start from
`nfsd_breaker_owns_lease()`.

## nfsd.deleg-revoke: Recall timeout and revocation

- section: Delegations
- relevance: 4 - the state machine after a recall is ignored

When a recalled delegation is not returned in time, who notices and how is the delegation marked?
What does `revoke_delegation()` do with it for an NFSv4.0 client, and what for an NFSv4.1 or later
client? What finally frees the delegation? Start from `revoke_delegation()`.

## nfsd.dir-delegations: Directory delegations

- section: Delegations
- relevance: 3 - every reader said they were not implemented

Does this tree implement directory delegations? If so, how do directory
changes reach NFSD, what bounds the queue of events waiting to be sent, and
what causes a recall in place of a notification? Start from
`nfsd_get_dir_deleg()` and `nfsd_handle_dir_event()`. If not, say so and
stop.

# Sessions and callbacks

## nfsd.session-slots: Forward channel slots

- section: Sessions and callbacks
- relevance: 4 - the table now grows and shrinks at run time

How are a session's forward channel slots stored and how does the table grow
and shrink at run time, what is remembered for a slot that was freed, and what
must be checked before the table is indexed with a slot id from the client?
Start from `nfsd4_sequence()` and `free_session_slots()`.

## nfsd.slot-seqid: Slot sequence check

- section: Sessions and callbacks
- relevance: 4 - decides replay, new request or error

What are the possible outcomes of comparing a SEQUENCE request's sequence id
with the slot's, including a slot that is in use and one that was reused, what
status does each give, and when is the slot's sequence id updated? Start from
`check_slot_seqid()`.

## nfsd.slot-replay: Replay from the slot cache

- section: Sessions and callbacks
- relevance: 4 - a cached reply can go to the wrong principal

What is stored in a slot after a compound completes and what never is, which
checks must pass before a cached reply is returned to a retransmission, and
what is returned when the original was not cached? Start from
`nfsd4_store_cache_entry()` and `replay_matches_cache()`.

## nfsd.cb-lifecycle: Callback lifecycle

- section: Sessions and callbacks
- relevance: 4 - the contract every callback type implements

What do the return values of a callback's `prepare` and `done` operations
mean and when is `release` called, what do the `cb_flags` bits record and who
sets each, and how is a callback requeued? Write the flag bit names in full.
Start from `nfsd4_init_cb()`.

## nfsd.cb-serialization: Callback channel state

- section: Sessions and callbacks
- relevance: 4 - little locking, much reliance on one workqueue

What serialises access to a client's callback RPC client, callback session and
`cl_cb_state`: a lock or something else? Which flags ask for the channel to be
rebuilt or torn down, and what does code running in RPC context use to read
the callback session safely? Start from `nfsd4_process_cb_update()`.

## nfsd.cb-usage: Queueing a callback

- section: Sessions and callbacks
- relevance: 5 - the object is freed while the RPC is in flight

What are the requirements for a caller of `nfsd4_run_cb()` in order to assure safe usage, before
the call and when the call returns false? What does `nfsd4_run_cb()` take a reference on by
itself, and where is each reference dropped? Name in-tree callers for recall, CB_OFFLOAD and lock
notification.

# Grace period

## nfsd.grace-end: Ending grace

- section: Grace period
- relevance: 4 - the per-net booleans readers named are now flag bits

What ends the grace period and what can delay or force it, what must happen
exactly once when it ends and what guarantees that, and how is the state
recorded, where a reader's memory offers booleans in the per-net structure?
Write each flag bit's name in full. Start from `nfsd4_end_grace()` and
`clients_still_reclaiming()`.

## nfsd.grace-checks: Operations during grace

- section: Grace period
- relevance: 4 - a missing check lets new state in during reclaim

What must an operation that creates or reclaims state check about the grace
period, with which helper for opens and which for locks, and what statuses are
returned for a non-reclaim request during grace and for a reclaim outside it?
Name existing operations that show the pattern. Start from `opens_in_grace()`
and `locks_in_grace()`.

# Copy offload

## nfsd.copy-objects: Copy state objects

- section: Copy offload
- relevance: 4 - no reader recognised the current representation

What represents an NFSv4.2 COPY while it runs synchronously and when it runs asynchronously? What
kind of stateid identifies an async copy, and where is it registered? What do TEST_STATEID and
FREE_STATEID return when they are given that stateid? Start from `struct nfsd4_async_copy` and
`nfs4_alloc_copy_stid()`.

## nfsd.copy-lifecycle: Async copy lifetime

- section: Copy offload
- relevance: 4 - a kthread, a callback, a reaper and client teardown share one object

Which flag bits and reference counts govern an async copy from `nfsd4_copy()`
through the worker thread, CB_OFFLOAD, the reaper and client teardown? In what
order are the results filled in, the callback sent and the copy made
unfindable, and what bounds how many run at once and what is returned beyond
that? Write the flag bit names in full.

# Data transfer and the open file cache

## nfsd.read-paths: Read paths

- section: Data transfer and the open file cache
- relevance: 4 - three paths with different constraints

Which ways does NFSD have of reading file data into a reply, which function implements each, and
what decides which one a given READ uses for NFSv3 and for NFSv4? Start from `nfsd_read()` and
`nfsd_read_splice_ok()`.

## nfsd.write-path: Write path

- section: Data transfer and the open file cache
- relevance: 4 - stability and the verifier are promises to the client

How do the stable-how argument and the export options change what a write
does, what is the write verifier and when is it reset, and what do the
configurable I/O modes change? Start from `nfsd_vfs_write()` and
`Documentation/filesystems/nfs/nfsd-io-modes.rst`.

## nfsd.filecache-objects: Open file cache entries

- section: Data transfer and the open file cache
- relevance: 4 - two kinds of entry with different lifetimes

What is a `struct nfsd_file` keyed and matched on, how do garbage-collected
and non-garbage-collected entries differ in lifetime, and which of the acquire
calls gives which kind? Start from the comment at the top of
`fs/nfsd/filecache.c`.

## nfsd.filecache-lifetime: Closing cached files

- section: Data transfer and the open file cache
- relevance: 3 - a lingering open file blocks unmount and delete

What keeps a `struct nfsd_file` that nothing uses in the cache, and which events close it? Which
of those events wait for the close to finish, and which act only for filesystems that set an
export operation flag? Start from `nfsd_file_put()` and `nfsd_file_close_inode_sync()`.

# Server configuration and netlink

## nfsd.netlink-spec: Netlink family

- section: Server configuration and netlink
- relevance: 3 - generated files must not be edited, and half the commands were unknown to readers

Where is NFSD's generic netlink family specified, what is generated from it
and must not be edited, and where are the handlers, including any outside the
file a reader would look in first? What must change together when a command or
attribute is added?

## nfsd.nfsd-mutex: Server configuration mutex

- section: Server configuration and netlink
- relevance: 4 - control interfaces race with shutdown

What does `nfsd_mutex` protect, and what runs with it held across server start and stop? What are
the requirements for code that reads `nfsd_serv` in `struct nfsd_net`, or other per-net state that
`nfsd_mutex` protects, in order to assure safe usage?

## nfsd.netlink-perms: Netlink privilege and namespaces

- section: Server configuration and netlink
- relevance: 4 - a handler acts for a namespace and a privilege level

How is privilege enforced for NFSD netlink commands, and against which user namespace? What are
the requirements for the network namespace that an NFSD netlink handler acts on in order to assure
safe usage, and how does a handler find that namespace?

# Maintainer conventions

## nfsd.coding-style: Coding conventions

- section: Maintainer conventions
- relevance: 2 - maintainer preferences reviewers enforce

What does the NFSD maintainer profile require of a patch's administrative interfaces, of its
observability and of its coding style? Start from
`Documentation/filesystems/nfs/nfsd-maintainer-entry-profile.rst`.

# Model gaps

## nfsd.model-gaps: Other mistakes models make

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
