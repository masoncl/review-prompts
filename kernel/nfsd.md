# NFSD Subsystem Delta

## Overview

NFSD (fs/nfsd/) implements the Linux NFS server (v2/v3/v4.x). Key subsystems:
XDR codec, stateid/delegation state machine, file handle validation, client
lifecycle, callbacks, session slots. NFSv3 XDR is migrating to auto-generated
code (xdrgen). Reference CS-001 for caller/callee traversal and lock
validation.

## File Applicability

| Files | Domain |
|-------|--------|
| nfs4xdr.c, nfs3xdr.c | XDR codec, page encoding |
| nfs4state.c, nfs4proc.c | NFSv4 state and operations |
| nfs3proc.c, nfsproc.c | NFSv2/v3 operations, page setup |
| vfs.c, nfsfh.c, nfsfh.h | VFS interface, file handles, splice |
| nfs4callback.c | Callbacks |
| nfs4layouts.c | pNFS layouts |
| filecache.c, nfscache.c | File cache, DRC |
| export.c, nfsctl.c, netlink.c | Export mgmt, admin, netlink |
| nfs4copy.c | Copy offload, s2s copy |
| nfs4recover.c | Grace period, reclaim |
| state.h, netns.h | Data structures |

## Dispatch

| Change involves | Sections |
|-----------------|----------|
| XDR decode/encode functions | NFSD-XDR |
| `*_get`, `*_put`, `refcount_*`, `kref_*` | NFSD-REF |
| `fh_verify`, `fh_put`, `fh_dentry` access | NFSD-FH, NFSD-SEC |
| Stateid lookup/create/destroy | NFSD-STID, NFSD-REF |
| Error returns in NFS procedures | NFSD-ERR |
| Lock/unlock, `spin_lock`, `mutex_lock` | NFSD-LOCK |
| Client create/destroy/expire/courtesy | NFSD-CLI |
| `from_kuid`, `make_kuid`, ACL encode | NFSD-NS |
| `nfsd4_run_cb`, callback completion | NFSD-CB |
| Session slot, SEQUENCE processing | NFSD-SLOT |
| `rq_pages`, `rq_next_page`, `rq_page_end` | NFSD-PAGE |
| READ/READDIR/READLINK procedures | NFSD-PAGE, NFSD-ERR |
| Splice read or page handling | NFSD-PAGE |
| COPY, OFFLOAD_CANCEL, OFFLOAD_STATUS | NFSD-COPY, NFSD-REF, NFSD-CB |
| `nfsd4_copy`, `s2s_cp_stateids`, SSC mount | NFSD-COPY, NFSD-LOCK |
| Grace period, reclaim, lease renewal | NFSD-GRACE, NFSD-CLI, NFSD-STID |
| Netlink/genetlink handlers, `nla_policy` | NFSD-NL, NFSD-SEC |
| Resource allocation, `kmalloc`, limits | NFSD-DOS, NFSD-REF |
| Re-export, `NFS_SUPER_MAGIC`, `crossmnt` | NFSD-REEXP, NFSD-FH, NFSD-ERR |
| New procedure or operation handler | NFSD-XDR, NFSD-FH, NFSD-ERR, NFSD-SEC |

---

## XDR Input Trust Boundaries [NFSD-XDR]

#### NFSD-XDR-001: Decode return value checking

**Risk**: Buffer overflow, uninitialized data use

**Details**: Flag `xdr_stream_decode_*()` calls whose return value is not
checked before the decoded variable is used

#### NFSD-XDR-002: Decoded length/count bounds

**Risk**: Resource exhaustion, integer overflow

**Details**: Flag decoded lengths passed to `kmalloc()` without an upper-bound
check; flag decoded counts driving loops without a cap; flag missing
`check_mul_overflow()` on `count * sizeof(...)` calculations

#### NFSD-XDR-003: Array index from client

**Risk**: Out-of-bounds access

**Details**: Flag decoded values used as array indices without prior bounds
check; includes session slot indices against `maxreqs` and opnums

#### NFSD-XDR-004: Response encode space accounting

**Risk**: Buffer overflow, truncated response

**Details**: Flag when client-supplied `maxcount` is used without subtracting
header overhead; flag encode loops that lack space reservation for trailing
fields (eof, count)

#### NFSD-XDR-005: Cross-validation of client identifiers

**Risk**: Unauthorized access to wrong file

**Details**: Flag stateid used without validating it against the file handle
via `fh_match()`; flag lock stateid not verified against its open stateid's
file

#### NFSD-XDR-006: XDR encode return checking

**Risk**: NULL dereference, state corruption

**Details**: Flag `xdr_reserve_space()` return used without NULL check; flag
`xdr_stream_encode_*()` return ignored; flag state modifications performed
before encode success is confirmed

#### NFSD-XDR-007: State committed before encode

**Risk**: Irrecoverable state corruption on retry

**Details**: Flag irreversible state changes (close, revoke, rename) that
occur before the response is encoded; flag stateid copied after
`nfs4_put_stid()` rather than before

#### NFSD-XDR-008: Replay cache after encode failure

**Risk**: Corrupted cached response

**Details**: Flag `so_replay` / `rp_buf` population that is not guarded by
encode success; unconditional `memcpy` to `rp_buf` after encode error caches
garbage

#### NFSD-XDR-009: Required XDR fields conditionally skipped

**Risk**: Malformed response, protocol violation

**Details**: Flag RFC-required structure members that are conditionally
skipped (e.g., when `maxcount==0`); every defined field must be encoded

**Acceptable**:
- xdrgen code (nfs3xdr_gen.c, nfs4xdr_gen.c) has built-in validation
- Metadata from `fh_dentry` after `fh_verify()` is trusted

---

## Reference Counting [NFSD-REF]

#### NFSD-REF-001: Early assignment before validation

**Risk**: Dangling pointer, cleanup complexity

**Details**: Flag resource assigned to a struct field before validation
completes; use temp variables until validation passes; pattern from
nfsd_set_fh_dentry() fix (b3da9b141578)

#### NFSD-REF-002: Multiple counters on same object

**Risk**: Wrong lifetime guarantee

**Details**: Flag `cl_rpc_users` used where `cl_ref` is appropriate, or
vice versa; `cl_rpc_users` prevents unhashing while `cl_ref` prevents
freeing only. Both `nfsd4_run_cb()` and async copy workers require
`cl_rpc_users` to hold the client alive past the compound's lifetime

**Acceptable**:
- Transfer semantics where function "steals" a reference

---

## File Handle Lifecycle [NFSD-FH]

#### NFSD-FH-001: Access before verification

**Risk**: NULL dereference, stale data access

**Details**: Flag access to `fh_dentry`, `fh_export`, or `d_inode()` without
a prior successful `fh_verify()`; `fh_dentry` is NULL before verification

#### NFSD-FH-002: Permission flag mismatch

**Risk**: Permission bypass

**Details**: Flag `NFSD_MAY_*` flags that do not match the operation: using
MAY_READ before `vfs_write()`, missing EXEC for directory traversal, missing
SATTR for setattr

#### NFSD-FH-003: File type check

**Risk**: Type confusion

**Details**: Flag `fh_verify(rqstp, fhp, 0, ...)` when the caller assumes a
specific file type; pass `S_IFREG`/`S_IFDIR` to enforce

**Acceptable**:
- Request-scoped handles in args structs are released by framework
- COMPOUND framework manages cstate handle lifecycle

---

## NFSv4 Stateid Lifecycle [NFSD-STID]

#### NFSD-STID-001: Delegation callback reference

**Risk**: Use-after-free

**Details**: Flag `nfsd4_run_cb()` without a prior
`refcount_inc(&dp->dl_stid.sc_count)`; without a reference, concurrent
DELEGRETURN may free the delegation

#### NFSD-STID-002: SC_STATUS_CLOSED check

**Risk**: State modification on closed stateid

**Details**: Flag state-modifying operations that do not check `sc_status`
under `st_mutex` or `cl_lock` first; check-and-modify must be atomic

#### NFSD-STID-003: Generation increment

**Risk**: Replay attack, protocol violation

**Details**: Flag manual `si_generation` increment instead of
`nfs4_inc_and_copy_stateid()`; flag stateid copy without generation bump
on state-modifying operations

#### NFSD-STID-004: CLAIM_DELEG_CUR file verification

**Risk**: Unauthorized file access

**Details**: Flag delegation lookup that does not verify the filehandle via
`fh_match()` against `sc_file->fi_fhandle`; stateid-only lookup allows
access to the wrong file

#### NFSD-STID-005: Third-party lease safety

**Risk**: Type confusion crash

**Details**: Flag `fl_owner` cast to `nfs4_delegation` without first checking
`fl->fl_lmops == &nfsd_lease_mng_ops`; non-NFSD leases have a different
`fl_owner` type

#### NFSD-STID-006: Delegation type validation

**Risk**: Incorrect timestamp suppression

**Details**: Flag `FMODE_NOCMTIME` set for delegation types other than
`OPEN_DELEGATE_WRITE_ATTRS_DELEG`; flag `dl_atime`/`dl_mtime` access on
non-WRITE_ATTRS delegations

#### NFSD-STID-007: Multi-client delegation conflict

**Risk**: Other clients' delegations not broken

**Details**: Flag same-client short-circuit that returns without breaking
OTHER clients' delegations; `if (same_client) return` without an else clause
that recalls other-client delegations

#### NFSD-STID-008: VFS operations during delegation release

**Risk**: Delegation break re-triggered

**Details**: Flag `notify_change()` during `nfs4_unlock_deleg_lease()` without
`ATTR_DELEG` in `ia.ia_valid`; its absence causes the delegation being
released to be re-broken

#### NFSD-STID-009: Layout stateid locking

**Risk**: Sleeping under spinlock, race condition

**Details**: Flag sleeping operations (segment manipulation, allocation) under
`ls_lock`; these require `ls_mutex` instead

**Acceptable**:
- Destructor field access during final put is safe

---

## Error Code Mapping [NFSD-ERR]

#### NFSD-ERR-001: Missing NFSv3 status mapping

**Risk**: Protocol violation

**Details**: Flag NFSv3 procedures that return `rpc_success` instead of
`nfsd3_map_status(resp->status)`; flag NFSv2 procedures returning raw
status without `nfserrno()` conversion

#### NFSD-ERR-002: Leaking internal errors

**Risk**: Client receives unparseable error

**Details**: Flag `PTR_ERR()` values returned to the RPC layer without
`nfserrno()` conversion; negative errno values must not reach the wire

#### NFSD-ERR-003: Cross-version error leakage

**Risk**: Client confusion, interoperability failure

**Details**: Flag NFSv4-only errors (e.g., `nfserr_delay`) in shared code
(vfs.c, nfsfh.c) reachable from v2/v3 paths

#### NFSD-ERR-004: Double mapping

**Risk**: Corrupted error value

**Details**: Flag `nfserrno()` applied to a `__be32` nfs status rather than
a negative errno; the value is converted exactly once

#### NFSD-ERR-005: Invalid error for NFS version

**Risk**: Protocol violation

**Details**: Flag NFSERR_INVAL in NFSv2 (not defined by RFC 1094); flag
`nfserr_file_open` for non-regular-files; flag session errors returned from
pre-v4.1 paths

#### NFSD-ERR-006: EOPENSTALE propagation

**Risk**: Broken stale filehandle recovery

**Details**: Flag direct conversion of `EOPENSTALE` to `nfserr_stale`;
`EOPENSTALE` requires retry at a higher level

---

## Locking Correctness [NFSD-LOCK]

#### NFSD-LOCK-001: Lock ordering violation

**Risk**: ABBA deadlock

**Details**: Flag acquisition that violates nesting order: `client_lock` ->
`state_lock` -> `s2s_cp_lock` -> `fi_lock` -> `cl_lock`; reverse order
deadlocks under load. `nfsd_ssc_lock` is independent; it must not be held
simultaneously with `s2s_cp_lock`

#### NFSD-LOCK-002: Wrong lock for stateid type

**Risk**: Inadequate protection, race condition

**Details**: Flag `sc_status` modification under the wrong lock: open/lock
stateids require `st_mutex` or `cl_lock`; delegations require `state_lock`;
layouts require `ls_mutex`

#### NFSD-LOCK-003: Wrong lock scope (client vs namespace)

**Risk**: Race condition

**Details**: Flag `cl_time`, `cl_lru`, `cl_idhash`, `grace_ended` accessed
without `nn->client_lock` (per-namespace); flag `cl_openowners`,
`cl_sessions`, `cl_revoked`, `cl_reclaim_complete` accessed without
`clp->cl_lock` (per-client)

#### NFSD-LOCK-004: Lookup-to-lock window (TOCTOU)

**Risk**: Race with concurrent unhash

**Details**: Flag gap between `find_stateid_locked()` under `cl_lock` and
`mutex_lock(&stp->st_mutex)` without a subsequent
`nfsd4_verify_open_stid()` check

#### NFSD-LOCK-005: VFS callback lock interaction

**Risk**: Deadlock

**Details**: Flag `nfs4_put_stid()` in a VFS break callback path (under
`flc_lock`); the put may acquire `cl_lock` via `refcount_dec_and_lock()`;
use `refcount_dec()` when refcount cannot reach zero

---

## Client State Transitions [NFSD-CLI]

#### NFSD-CLI-001: Invalid state transition

**Risk**: Protocol violation, state corruption

**Details**: Flag transitions that violate INIT -> CONFIRMED -> ACTIVE ->
COURTESY -> EXPIRED; flag EXPIRED returning to ACTIVE (only COURTESY may
return to ACTIVE on reconnect)

#### NFSD-CLI-002: COURTESY client without expiry

**Risk**: Memory exhaustion

**Details**: Flag transition to COURTESY without laundromat integration;
`cl_time` must be set and laundromat must check and expire after timeout

#### NFSD-CLI-003: Admin interface race

**Risk**: Use-after-free

**Details**: Flag admin sysfs/procfs writes that access state without holding
`nfsd_mutex` or without checking `nn->nfsd_serv`

#### NFSD-CLI-004: Child stateid orphaning

**Risk**: List corruption, crash

**Details**: Flag parent destruction paths that do not free child stateids
(copynotify); `release_openowner()` may skip
`nfs4_free_cpntf_statelist()`

#### NFSD-CLI-005: Double initialization

**Risk**: Kernel panic (BUG_ON)

**Details**: Flag init functions reachable from multiple call paths; second
invocation triggers BUG_ON

---

## Grace Period and Lease Management [NFSD-GRACE]

#### NFSD-GRACE-001: Missing grace check before state creation

**Risk**: Protocol violation, lock conflicts

**Details**: Flag OPEN, LOCK, or size-changing SETATTR that creates
new state without a prior `nfsd4_grace_period()` check; non-reclaim
operations must return `nfserr_grace` during the grace period
(RFC 8881 section 9.6)

#### NFSD-GRACE-002: Reclaim type mismatch

**Risk**: Unauthorized state recovery

**Details**: Flag reclaim paths that accept claim types other than
`CLAIM_PREVIOUS` or `CLAIM_DELEGATE_PREV` for opens, or
`lk_reclaim=true` for locks; non-reclaim claim types must be
rejected during grace

#### NFSD-GRACE-003: Grace end vs active reclaim race

**Risk**: Premature state loss

**Details**: Flag `nfsd4_end_grace()` that does not account for
clients with reclaims still in progress; ending grace while a client
is mid-reclaim causes that client to lose state

#### NFSD-GRACE-004: Lease time source inconsistency

**Risk**: Premature expiry or unbounded lease

**Details**: Flag lease expiry checks that use a hard-coded value
instead of `nn->nfsd4_lease`; flag grace duration not derived from
`nn->nfsd4_grace`; all timing must reference the per-namespace
configuration

#### NFSD-GRACE-005: Lease clock API mismatch

**Risk**: Incorrect expiry after suspend/resume

**Details**: Flag `cl_time` updates or comparisons using
`ktime_get()` instead of `ktime_get_boottime_seconds()`; lease
times must survive suspend, so boot-time monotonic clock is
required

#### NFSD-GRACE-006: Reclaim record persistence

**Risk**: Reclaim failure after crash

**Details**: Flag client state creation that bypasses
`nfsd4_client_record_create()` for persistent storage; in-memory-only
reclaim records are lost on crash, preventing the client from
reclaiming after the subsequent grace period

#### NFSD-GRACE-007: Post-grace client cleanup

**Risk**: Resource leak, memory exhaustion

**Details**: Flag grace-end paths that do not expire clients which
failed to complete reclaim; clients that never issued
RECLAIM_COMPLETE must be destroyed after the grace period ends

**Acceptable**:
- Reclaim operations (CLAIM_PREVIOUS, lk_reclaim) during grace

---

## User Namespace ID Conversion [NFSD-NS]

#### NFSD-NS-001: Wrong namespace source

**Risk**: Container escape, host UID exposure

**Details**: Flag `from_kuid`/`from_kgid` in request paths using
`init_user_ns` or `current_user_ns()` instead of
`nfsd_user_namespace(rqstp)`; NFSD kthreads have `init_user_ns` as
`current_user_ns()`. Similarly, flag inter-server socket creation
using `current->nsproxy->net_ns` instead of `nn->net`

#### NFSD-NS-002: Missing uid_valid/gid_valid check

**Risk**: Invalid UID stored, privilege escalation

**Details**: Flag `make_kuid()`/`make_kgid()` results used without
`uid_valid()`/`gid_valid()` validation; mapping invalid IDs to
`GLOBAL_ROOT_UID` is privilege escalation

#### NFSD-NS-003: ACL entries without conversion

**Risk**: Cross-namespace permission grants

**Details**: Flag ACL encoding that uses raw `kuid_t` values without
`from_kuid_munged(ns, ...)`; each ACL entry must be converted

#### NFSD-NS-004: Inconsistent namespace within operation

**Risk**: Unpredictable permissions

**Details**: Flag functions that mix `init_user_ns` and
`nfsd_user_namespace()` for owner and group conversions within the same
operation

**Acceptable**:
- Host-only internal paths (module init, procfs) may use `init_user_ns`
- Idmap path handles namespace conversion internally

---

## Callback Operations [NFSD-CB]

#### NFSD-CB-001: Missing client reference

**Risk**: Use-after-free on client destruction

**Details**: Flag `nfsd4_run_cb()` without a prior `cl_rpc_users` increment;
the release handler must drop it; without the reference, the client may be
freed while the callback is in flight

#### NFSD-CB-002: Connection state validation

**Risk**: Callback sent to wrong or dead client

**Details**: Flag callback dispatch without checking
`cl_cb_state == NFSD4_CB_UP` under `cl_lock`; flag `cb_client` access
outside the same lock hold

#### NFSD-CB-003: Sequence number atomicity

**Risk**: Callback rejection

**Details**: Flag `cl_cb_seq_nr` modification without `cl_lock`; concurrent
increment causes duplicate sequence numbers and BAD_SEQUENCE rejection

#### NFSD-CB-004: Release handler reference drop

**Risk**: Delegation and client leak

**Details**: Flag callback release handlers that omit dropping delegation
`sc_count` or client `cl_rpc_users`

#### NFSD-CB-005: Client destroyed with callbacks in flight

**Risk**: Use-after-free in completion handler

**Details**: Flag `destroy_client()` paths that do not call
`nfsd4_shutdown_callback()` to drain in-flight callbacks before freeing

#### NFSD-CB-006: NFSv4.0 callback compatibility

**Risk**: NULL dereference on v4.0 clients

**Details**: Flag `cl_session` access without a `cl_minorversion > 0` guard;
`cl_session` is NULL for NFSv4.0 clients

**Acceptable**:
- Deferred release via RPC completion handler

---

## Session Slots [NFSD-SLOT]

#### NFSD-SLOT-001: Slot index bounds

**Risk**: Out-of-bounds array access

**Details**: Flag `se_slots[slotid]` access without prior check
`slotid < se_fchannel.maxreqs`; client-supplied slotid without bounds
check causes crash

#### NFSD-SLOT-002: Seqid validation ordering

**Risk**: Broken replay detection

**Details**: Flag `sl_seqid` modification before comparison with the request
seqid; the original value is needed to distinguish replay (match),
new request (+1), and misordered (other)

#### NFSD-SLOT-003: False retry detection

**Risk**: Cross-client reply leak

**Details**: Flag replay path that returns cached reply without a
`same_creds()` check; without it, an attacker can replay another client's
cached response

#### NFSD-SLOT-004: Slot exclusivity

**Risk**: Reply cache corruption, seqid corruption

**Details**: Flag missing `sl_inuse` set/clear around compound execution;
flag exit paths (error, deferral) that skip clearing `sl_inuse`

#### NFSD-SLOT-005: Session freed with compounds in flight

**Risk**: Use-after-free

**Details**: Flag session teardown that frees slots without first removing
the session from the hash table and draining active compounds

#### NFSD-SLOT-006: Cached reply lifetime

**Risk**: Use-after-free on replay

**Details**: Flag `kfree(slot->sl_reply)` without clearing the pointer;
replay returns freed memory

---

## Security Validation [NFSD-SEC]

#### NFSD-SEC-001: Validation bypass via new code path

**Risk**: Unvalidated filesystem access

**Details**: Flag new branches or early returns before `fh_verify()` that
skip validation; flag new helper functions that access `fh_dentry` without
documenting a caller contract or calling `fh_verify()` directly

#### NFSD-SEC-002: Missing stateid validation

**Risk**: Lock and lease bypass

**Details**: Flag NFSv4 stateful operations (read, write, lock, setattr with
size) that access the file without a prior
`nfs4_preprocess_stateid_op()` call

#### NFSD-SEC-003: Cross-export operation validation

**Risk**: Target handle unvalidated

**Details**: Flag RENAME or LINK with `fh_verify()` removed from either
source or target handle; both must be validated independently

#### NFSD-SEC-004: Pseudo-filesystem exposure

**Risk**: Information leak, version gate bypass

**Details**: Flag code paths that allow NFSv4 pseudo-filesystem access from
v2/v3 procedures; `fh_verify()` enforces the version gate

**Acceptable**:
- Caller already verified fh (documented in function comment/contract)
- Compound framework pre-validates cstate file handles

---

## Netlink Interface [NFSD-NL]

#### NFSD-NL-001: Policy gap for new attribute

**Risk**: Input validation bypass

**Details**: Flag new `NFSD_A_*` enum values in `nfsd_netlink.h`
without a corresponding entry in the `nla_policy` array; attributes
without policy entries reach handlers unvalidated

#### NFSD-NL-002: Missing capability check

**Risk**: Privilege escalation

**Details**: Flag genetlink handler functions that modify NFSD state
or configuration without a `capable(CAP_NET_ADMIN)` or
`ns_capable()` check before any side effects

#### NFSD-NL-003: Unbounded string attribute

**Risk**: Memory exhaustion

**Details**: Flag `NLA_STRING` policy entries without a `.len` field;
use `NLA_NUL_STRING` with an explicit length bound; flag `nla_data()`
on string attributes whose policy does not guarantee null termination

#### NFSD-NL-004: Nested attribute without policy

**Risk**: Unvalidated input

**Details**: Flag `nla_parse_nested()` called with a NULL policy
argument; nested attributes require their own policy array to
validate inner attribute types and lengths

#### NFSD-NL-005: Namespace isolation

**Risk**: Cross-namespace state modification

**Details**: Flag handlers that use `&init_net` or a global
`nfsd_net` pointer instead of `genl_info_net(info)` to obtain the
network namespace; flag `capable()` where `ns_capable()` is needed
for namespace-relative privilege checks

#### NFSD-NL-006: TOCTOU on NFSD state

**Risk**: Race condition

**Details**: Flag `nfsd_running()` or similar state checks not
protected by `nfsd_mutex` through the subsequent modification;
a gap between check and modify allows NFSD to start or stop
concurrently

**Acceptable**:
- Attributes enforced as required by genetlink policy validation

---

## Page Array Management [NFSD-PAGE]

#### NFSD-PAGE-001: Response page pointer saved before read

**Risk**: NULL dereference, data corruption

**Details**: Flag read procedures where `resp->pages` is not saved from
`rqstp->rq_next_page` BEFORE the read call; read operations advance
`rq_next_page`, so encoders that reference `rq_next_page` afterward
use the wrong pointer (fix 7978e9bea278)

#### NFSD-PAGE-002: Page array bounds before dereference

**Risk**: Array overrun, kernel crash

**Details**: Flag loops advancing `rq_next_page` without a
`rq_next_page < rq_page_end` guard in the loop condition; flag
`rq_bvec` indexing without an `rq_maxpages` bound; the advancing
pointer depends on variable-length read data, making overrun a
proven failure mode (fixes e1b495d02c53, 3be7f32878e7)

#### NFSD-PAGE-003: COMPOUND page_ptr / rq_next_page sync

**Risk**: Data corruption, wrong pages sent to client

**Details**: Flag NFSv4 operations that encode to pages and return
before `nfsd4_encode_operation()` can execute
`rqstp->rq_next_page = xdr->page_ptr + 1`; individual operations
must not manually sync -- sync is centralized after each operation
(fix ed4a567a179e)

#### NFSD-PAGE-004: READDIR page recycling

**Risk**: Page array exhaustion, unnecessary allocator pressure

**Details**: Flag READDIR paths that pre-allocate pages but omit
`rqstp->rq_next_page = xdr.page_ptr + 1` after completion; unused
pages are released instead of recycled; flag page count arithmetic
that does not use `(count + PAGE_SIZE - 1) >> PAGE_SHIFT`
(fixes 3c86794ac0e6, 76ed0dd96eeb)

#### NFSD-PAGE-005: Splice continuation detection

**Risk**: Page array corruption, rq_next_page overrun

**Details**: Flag `nfsd_splice_actor()` modifications that remove the
continuation check: when `page == *(rq_next_page - 1)` AND the
offset is not page-aligned, the same page is being continued and
must not be added again; flag missing return value check on
`svc_rqst_replace_page()` (fixes 27c934dd8832, 91e23b1c3982)

Example -- rq_next_page accessed after read advances it:
```diff
     nfsd_read(rqstp, ...);
+    svcxdr_encode_opaque_pages(rqstp, xdr, rqstp->rq_next_page, ...);
+    /* WRONG: rq_next_page already advanced past the data pages */
```

**Acceptable**:
- `nfsd4_encode_operation()` centralizing page_ptr sync

---

## Copy Offload Operations [NFSD-COPY]

#### NFSD-COPY-001: Copy stateid IDR cleanup

**Risk**: Stale state, resource leak

**Details**: Flag async copy completion paths that omit IDR removal
under `s2s_cp_lock`; stale entries allow clients to query freed state
via OFFLOAD_STATUS; IDR removal must precede the final put

#### NFSD-COPY-002: Cancellation race with completion

**Risk**: Use-after-free, double free

**Details**: Flag OFFLOAD_CANCEL that modifies copy state without an
atomic state transition under lock; a window between check and cancel
allows the copy to complete and free its resources concurrently

#### NFSD-COPY-003: CB_OFFLOAD result ordering

**Risk**: Race condition, stale data sent to client

**Details**: Flag result fields (`wr_bytes_written`, `wr_stable_how`)
modified after `nfsd4_run_cb()` queues the CB_OFFLOAD callback; the
callback may read results before the assignment completes

#### NFSD-COPY-004: S2S credential lifetime

**Risk**: Authentication failure during long copy

**Details**: Flag inter-server copy that caches an RPC credential
without verifying validity before each chunk; GSS credentials may
expire during multi-hour copies

#### NFSD-COPY-005: COPY_NOTIFY authorization validation

**Risk**: Unauthorized cross-server access

**Details**: Flag `nfsd4_setup_inter_ssc()` that proceeds without
verifying the `cnr_stateid` from COPY_NOTIFY exists, belongs to the
requesting client, and has not expired

#### NFSD-COPY-006: Unbounded async copy queue

**Risk**: Memory exhaustion

**Details**: Flag async copy submission paths that lack per-client or
global limits; an attacker can exhaust memory by issuing unbounded
concurrent COPY operations

**Acceptable**:
- Synchronous copy uses compound-scoped references directly

---

## Denial of Service Vectors [NFSD-DOS]

#### NFSD-DOS-001: Unbounded state accumulation

**Risk**: Memory exhaustion

**Details**: Flag `nfs4_alloc_stid()`, `alloc_init_deleg()`,
`alloc_lock_stateid()`, or `create_session()` without a preceding
per-client limit check; a single client must not consume unbounded
stateids, delegations, locks, or sessions; flag global limits
without a corresponding per-client limit

#### NFSD-DOS-002: Limit checked after allocation

**Risk**: OOM on limit enforcement

**Details**: Flag allocation followed by a limit check and free;
the limit must be verified before the allocation to avoid transient
OOM under heavy load

#### NFSD-DOS-003: COMPOUND operation count

**Risk**: CPU exhaustion

**Details**: Flag NFSv4 COMPOUND dispatch loops without an upper
bound on `args->opcnt`; unbounded compounds allow a single request
to monopolize a worker thread; the server should return
`nfserr_resource` when the limit is exceeded

#### NFSD-DOS-004: Work queue exhaustion

**Risk**: Worker pool starvation

**Details**: Flag `queue_work()` calls driven by client requests
without per-client limits on pending work items; key queues to
audit: `nfsd4_callback_wq`, `nfsd_copy_wq`, `laundry_wq`

#### NFSD-DOS-005: Limit counter leak on error

**Risk**: Limit drift, eventual exhaustion

**Details**: Flag `atomic_inc()` on a resource counter before
allocation without a matching `atomic_dec()` on all error paths;
leaked increments gradually consume the limit budget without
corresponding resources; this covers admission-control counters
(`num_delegations`, `num_opens`, etc.), not object lifetime
refcounts

#### NFSD-DOS-006: Amplification via expensive attributes

**Risk**: CPU and memory exhaustion

**Details**: Flag READDIR or GETATTR paths that honor arbitrary
client `maxcount` without capping; flag expensive attribute
encoding (ACLs, security labels, owner name idmap lookups)
without per-entry or per-response size limits

**Acceptable**:
- Server-generated limits (session slot count after CREATE_SESSION)
- Allocations bounded by fixed protocol maximums

---

## NFS Re-export Safety [NFSD-REEXP]

#### NFSD-REEXP-001: File handle uses local inode number

**Risk**: Handle instability after upstream reconnect

**Details**: Flag `fh_compose()` or file handle encoding that uses
`i_ino` on an NFS superblock (`s_magic == NFS_SUPER_MAGIC`); inode
numbers on NFS are not stable across upstream reconnects; the
upstream file handle (`NFS_FH()`) must be embedded instead

#### NFSD-REEXP-002: ESTALE masked or retried

**Risk**: Infinite loop, stale data served

**Details**: Flag VFS operation error paths that retry on `-ESTALE`
from an NFS-backed filesystem without propagating the error to the
client; ESTALE indicates permanent handle invalidity on the upstream
server and retrying cannot resolve it

#### NFSD-REEXP-003: Lock state committed before upstream

**Risk**: Client holds lock that re-exporter cannot maintain

**Details**: Flag lock acquisition paths that update local NFSD state
before the VFS lock call (`vfs_lock_file()`) succeeds on the upstream
NFS mount; upstream must be locked first, then local state committed;
failure of the upstream lock must not leave stale local state

#### NFSD-REEXP-004: Mount crossing without filesystem check

**Risk**: Wrong file handle encoding, credential mismatch

**Details**: Flag `nfsd_cross_mnt()` or `follow_down()` usage that
does not check whether the target superblock is an NFS filesystem;
crossing into an NFS mount creates a re-export situation requiring
different handle encoding and credential handling

#### NFSD-REEXP-005: Upstream grace period ignored

**Risk**: Protocol violation, lock conflicts

**Details**: Flag operations on re-exported filesystems that only
check local grace state (`nfsd4_grace_period()`) without handling
upstream grace errors (`-EAGAIN` from NFS client during upstream
grace); upstream grace and local grace are independent

#### NFSD-REEXP-006: Credential double-mapping

**Risk**: Unexpected access denial or privilege escalation

**Details**: Flag credential handling that assumes single-layer
mapping; re-export applies squash and security flavor transforms
twice (re-export settings then upstream mount settings); flag
`no_root_squash` on re-export when the upstream mount uses
`root_squash`

#### NFSD-REEXP-007: Export fsid stability

**Risk**: File handles invalid after remount

**Details**: Flag re-exports where `exp->ex_fsid` or `exp->ex_uuid`
is derived from the NFS mount rather than set explicitly; mount
device numbers change across remounts, invalidating all outstanding
file handles

**Acceptable**:
- Local filesystem exports (s_magic != NFS_SUPER_MAGIC)

---

## Code Style

Reverse-christmas tree variable ordering. `nfs_ok`/`nfserr_*` error
convention. `cpu_to_be32`/`be32_to_cpu` for byte order. New NFSv3 XDR code
should use nfs3xdr_gen.c (xdrgen).

---

## Quick Reference

**Refcount pairs**: `nfs4_get_stid`/`nfs4_put_stid`,
`nfsd_file_get`/`nfsd_file_put`, `exp_get`/`exp_put`, `fh_put` (copy
semantics). Client: `cl_rpc_users` (unhash guard), `cl_ref` (kref).
`nfsd_net_try_get`/`nfsd_net_put`. Async copy:
`refcount`/`nfsd4_put_copy`, `cl_rpc_users`/`put_client_renew`.

**Lock hierarchy** (outer to inner): `nn->client_lock` -> `state_lock` ->
`nn->s2s_cp_lock` -> `fp->fi_lock` -> `clp->cl_lock` -> `stp->st_mutex`.
All except st_mutex are spinlocks. `nn->nfsd_ssc_lock` is independent of
`s2s_cp_lock`; they must not be held simultaneously.

**Trust boundaries**: XDR decode (untrusted) -> `fh_verify()` ->
`nfs4_preprocess_stateid_op()` -> VFS data (trusted).

**Page array pointers**: `rq_pages` (base), `rq_next_page` (next slot),
`rq_page_end` (sentinel), `rq_maxpages` (array size). Save
`resp->pages` before read; bounds-check before advancing; recycle
after READDIR.

**Grace period**: `nn->grace_ended` (per-namespace, under `client_lock`),
`cl_reclaim_complete` (per-client, under `cl_lock`). Lease times use
`ktime_get_boottime_seconds()`; durations from `nn->nfsd4_lease` and
`nn->nfsd4_grace`.

**Invariants**: Verify before dereference; hold reference before async work;
release on all error paths; encode before committing state; use
`nfsd_user_namespace()` for ID conversion.

---

## Stop Conditions

Flag for expert review when: XDR primitives or infrastructure modified;
refcount primitives changed; `fh_verify()` semantics modified; stateid
lifecycle changed; lock ordering changed; client state machine or grace period
logic modified; callback dispatch/completion/retry changed; session slot or
SEQUENCE processing modified; new RPC procedure or NFSv4 op added; namespace
conversion paths changed; page array or splice read infrastructure
modified; copy offload lifecycle or s2s authentication changed; grace
period state machine or lease timing modified; genetlink family or
policy definitions changed; resource limits or allocation patterns
modified; re-export or cross-mount handling changed; changes exceed
100 lines touching multiple core files.
