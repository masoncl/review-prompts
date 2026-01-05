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
| nfs4xdr.c, nfs3xdr.c | XDR codec |
| nfs4state.c, nfs4proc.c | NFSv4 state and operations |
| nfs3proc.c, nfsproc.c | NFSv2/v3 operations |
| vfs.c, nfsfh.c, nfsfh.h | VFS interface, file handles |
| nfs4callback.c | Callbacks |
| nfs4layouts.c | pNFS layouts |
| filecache.c, nfscache.c | File cache, DRC |
| export.c, nfsctl.c | Export mgmt, admin |
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
| New procedure or operation handler | NFSD-XDR, NFSD-FH, NFSD-ERR, NFSD-SEC |

---

## XDR Input Trust Boundaries [NFSD-XDR]

**Scan for**: `xdr_stream_decode_*`, `xdr_reserve_space`,
`xdr_stream_encode_*`, `xdr_inline_decode`, `maxcount`, `so_replay`,
`rp_buf`, response encode loops

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

Example -- bounds check removed from decode path:
```diff
-    if (count > NFS3_FHSIZE)
-        return nfserr_bad_xdr;
     p = xdr_inline_decode(xdr, count);
```

**Acceptable**:
- xdrgen code (nfs3xdr_gen.c, nfs4xdr_gen.c) has built-in validation
- Metadata from `fh_dentry` after `fh_verify()` is trusted
- Pre-reserved fixed-size encodes need no per-call check

---

## Reference Counting [NFSD-REF]

**Scan for**: `*_get`, `*_put`, `refcount_inc`, `refcount_dec`,
`kref_get`, `kref_put`, `refcount_inc_not_zero`, `kfree`, `kfree_rcu`,
`goto retry`, error-path returns after lookup

#### NFSD-REF-001: Acquisition/release balance

**Risk**: Use-after-free, resource leak

**Details**: Flag `*_get()` / `refcount_inc()` / `kref_get()` without a
matching release on all exit paths; flag `find_*` return values used without
a corresponding put

#### NFSD-REF-002: Early assignment before validation

**Risk**: Dangling pointer, cleanup complexity

**Details**: Flag resource assigned to a struct field before validation
completes; use temp variables until validation passes; pattern from
nfsd_set_fh_dentry() fix (b3da9b141578)

#### NFSD-REF-003: Use-after-put ordering

**Risk**: Use-after-free on embedded fields

**Details**: Flag field access on an object after `nfs4_put_stid()` or
similar put call; the put may free the containing struct
(fix 1116e0e372eb)

#### NFSD-REF-004: Unconditional field overwrite

**Risk**: Reference leak

**Details**: Flag assignment to a struct field that may already hold a
reference, without checking or releasing the old value first
(fix 8072e34e1387)

#### NFSD-REF-005: Retry path reference leak

**Risk**: Cumulative resource leak

**Details**: Flag `goto retry` without releasing the reference acquired in
the current iteration (fix 8a7926176378)

#### NFSD-REF-006: Object access after lock release

**Risk**: Use-after-free

**Details**: Flag when an object found under lock is accessed after lock
release without a prior `refcount_inc_not_zero()`

#### NFSD-REF-007: RCU lookup/free mismatch

**Risk**: Use-after-free under RCU reader

**Details**: Flag `kfree()` on objects found via RCU-protected lookup;
these require `kfree_rcu()` or `call_rcu()` (fix 2530766492ec)

#### NFSD-REF-008: Multiple counters on same object

**Risk**: Wrong lifetime guarantee

**Details**: Flag `cl_rpc_users` used where `cl_ref` is appropriate, or
vice versa; `cl_rpc_users` prevents unhashing while `cl_ref` prevents
freeing only

Example -- field accessed after final put:
```diff
     nfs4_put_stid(&dp->dl_stid);
+    flags = dp->dl_stid.sc_flags;  /* use-after-free */
```

**Acceptable**:
- Transfer semantics where function "steals" a reference
- `refcount_inc_not_zero` failure returning immediately
- Initialization with `refcount_set(1)`
- Conditional get/put with matching conditions

---

## File Handle Lifecycle [NFSD-FH]

**Scan for**: `fh_verify`, `fh_put`, `fh_init`, `fh_dentry`,
`fh_export`, `d_inode`, `NFSD_MAY_*`, `S_IFREG`, `S_IFDIR`

#### NFSD-FH-001: Access before verification

**Risk**: NULL dereference, stale data access

**Details**: Flag access to `fh_dentry`, `fh_export`, or `d_inode()` without
a prior successful `fh_verify()`; `fh_dentry` is NULL before verification

#### NFSD-FH-002: Permission flag mismatch

**Risk**: Permission bypass

**Details**: Flag `NFSD_MAY_*` flags that do not match the operation: using
MAY_READ before `vfs_write()`, missing EXEC for directory traversal, missing
SATTR for setattr

#### NFSD-FH-003: Missing fh_put on verified handles

**Risk**: Dentry reference leak, prevents unmount

**Details**: Flag exit paths after successful `fh_verify()` that skip
`fh_put()`; flag stack-allocated handles without `fh_init()` or
`SVC_FH3_INIT`

#### NFSD-FH-004: File type check

**Risk**: Type confusion

**Details**: Flag `fh_verify(rqstp, fhp, 0, ...)` when the caller assumes a
specific file type; pass `S_IFREG`/`S_IFDIR` to enforce

**Acceptable**:
- Request-scoped handles in args structs are released by framework
- fh_verify failure paths need no fh_put
- COMPOUND framework manages cstate handle lifecycle

---

## NFSv4 Stateid Lifecycle [NFSD-STID]

**Scan for**: `nfsd4_lookup_stateid`, `nfs4_put_stid`, `nfs4_get_stid`,
`sc_count`, `sc_status`, `sc_type`, `si_generation`,
`nfs4_inc_and_copy_stateid`, `nfsd4_run_cb`, `fl_lmops`, `fh_match`,
`CLAIM_DELEG_CUR`, `nfs4_unlock_deleg_lease`

#### NFSD-STID-001: Lookup without matching put

**Risk**: Use-after-free, resource leak

**Details**: Flag exit paths after `nfsd4_lookup_stateid()` that lack
`nfs4_put_stid()`; flag field access after the final put

#### NFSD-STID-002: Delegation callback reference

**Risk**: Use-after-free

**Details**: Flag `nfsd4_run_cb()` without a prior
`refcount_inc(&dp->dl_stid.sc_count)`; without a reference, concurrent
DELEGRETURN may free the delegation

#### NFSD-STID-003: SC_STATUS_CLOSED check

**Risk**: State modification on closed stateid

**Details**: Flag state-modifying operations that do not check `sc_status`
under `st_mutex` or `cl_lock` first; check-and-modify must be atomic

#### NFSD-STID-004: Generation increment

**Risk**: Replay attack, protocol violation

**Details**: Flag manual `si_generation` increment instead of
`nfs4_inc_and_copy_stateid()`; flag stateid copy without generation bump
on state-modifying operations

#### NFSD-STID-005: CLAIM_DELEG_CUR file verification

**Risk**: Unauthorized file access

**Details**: Flag delegation lookup that does not verify the filehandle via
`fh_match()` against `sc_file->fi_fhandle`; stateid-only lookup allows
access to the wrong file

#### NFSD-STID-006: Third-party lease safety

**Risk**: Type confusion crash

**Details**: Flag `fl_owner` cast to `nfs4_delegation` without first checking
`fl->fl_lmops == &nfsd_lease_mng_ops`; non-NFSD leases have a different
`fl_owner` type

#### NFSD-STID-007: Delegation type validation

**Risk**: Incorrect timestamp suppression

**Details**: Flag `FMODE_NOCMTIME` set for delegation types other than
`OPEN_DELEGATE_WRITE_ATTRS_DELEG`; flag `dl_atime`/`dl_mtime` access on
non-WRITE_ATTRS delegations

#### NFSD-STID-008: Multi-client delegation conflict

**Risk**: Other clients' delegations not broken

**Details**: Flag same-client short-circuit that returns without breaking
OTHER clients' delegations; `if (same_client) return` without an else clause
that recalls other-client delegations

#### NFSD-STID-009: VFS operations during delegation release

**Risk**: Delegation break re-triggered

**Details**: Flag `notify_change()` during `nfs4_unlock_deleg_lease()` without
`ATTR_DELEG` in `ia.ia_valid`; its absence causes the delegation being
released to be re-broken

#### NFSD-STID-010: Layout stateid locking

**Risk**: Sleeping under spinlock, race condition

**Details**: Flag sleeping operations (segment manipulation, allocation) under
`ls_lock`; these require `ls_mutex` instead

Example -- missing put on error path:
```diff
     stp = nfsd4_lookup_stateid(cstate, stateid, ...);
+    if (check_something(stp))
+        return nfserr_bad_stateid;
+    /* leaked: no nfs4_put_stid() before return */
```

**Acceptable**:
- Allocation sets initial refcount (no matching get needed)
- Lookup failure paths need no put
- Destructor field access during final put is safe

---

## Error Code Mapping [NFSD-ERR]

**Scan for**: `nfserrno`, `nfserr_*`, `PTR_ERR`, `rpc_success`,
`nfsd3_map_status`, `EOPENSTALE`, `nfserr_delay`, `nfserr_file_open`

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

**Acceptable**:
- `nfserr_*` constants in version-specific code
- `nfserrno()` applied to VFS/errno returns

---

## Locking Correctness [NFSD-LOCK]

**Scan for**: `spin_lock`, `spin_unlock`, `mutex_lock`, `mutex_unlock`,
`client_lock`, `state_lock`, `cl_lock`, `fi_lock`, `ls_lock`, `se_lock`,
`st_mutex`, `ls_mutex`, `cancel_work`, `flc_lock`, `refcount_dec_and_lock`

#### NFSD-LOCK-001: Lock ordering violation

**Risk**: ABBA deadlock

**Details**: Flag acquisition that violates nesting order: `client_lock` ->
`state_lock` -> `fi_lock` -> `cl_lock`; reverse order deadlocks under load

#### NFSD-LOCK-002: Sleeping under spinlock

**Risk**: System hang

**Details**: Flag `mutex_lock()`, `msleep()`, `GFP_KERNEL` allocation, or
other sleeping ops under `state_lock`, `client_lock`, `cl_lock`, `fi_lock`,
`ls_lock`, or `se_lock` (all are spinlocks)

#### NFSD-LOCK-003: Wrong lock for stateid type

**Risk**: Inadequate protection, race condition

**Details**: Flag `sc_status` modification under the wrong lock: open/lock
stateids require `st_mutex` or `cl_lock`; delegations require `state_lock`;
layouts require `ls_mutex`

#### NFSD-LOCK-004: Wrong lock scope (client vs namespace)

**Risk**: Race condition

**Details**: Flag `cl_time`, `cl_lru`, `cl_idhash` accessed without
`nn->client_lock` (per-namespace); flag `cl_openowners`, `cl_sessions`,
`cl_revoked` accessed without `clp->cl_lock` (per-client)

#### NFSD-LOCK-005: Lookup-to-lock window (TOCTOU)

**Risk**: Race with concurrent unhash

**Details**: Flag gap between `find_stateid_locked()` under `cl_lock` and
`mutex_lock(&stp->st_mutex)` without a subsequent
`nfsd4_verify_open_stid()` check

#### NFSD-LOCK-006: VFS callback lock interaction

**Risk**: Deadlock

**Details**: Flag `nfs4_put_stid()` in a VFS break callback path (under
`flc_lock`); the put may acquire `cl_lock` via `refcount_dec_and_lock()`;
use `refcount_dec()` when refcount cannot reach zero

#### NFSD-LOCK-007: Shutdown synchronization

**Risk**: Use-after-free

**Details**: Flag `cancel_work()` during shutdown; non-synchronous cancel
allows the work to run after resource destruction; use `cancel_work_sync()`

Example -- reverse lock ordering:
```diff
+    spin_lock(&clp->cl_lock);
+    spin_lock(&nn->client_lock);  /* ABBA: cl_lock before client_lock */
```

**Acceptable**:
- RCU read-side access for RCU-protected data
- Initialization before object is visible needs no lock
- Single-threaded teardown with exclusive refcount access

---

## Client State Transitions [NFSD-CLI]

**Scan for**: `cl_state`, `COURTESY`, `EXPIRED`, `CONFIRMED`,
`destroy_client`, `nfsd_mutex`, `nfsd_serv`, `cl_time`,
`release_openowner`, `nfs4_free_cpntf_statelist`, `laundromat`

#### NFSD-CLI-001: Invalid state transition

**Risk**: Protocol violation, state corruption

**Details**: Flag transitions that violate INIT -> CONFIRMED -> ACTIVE ->
COURTESY -> EXPIRED; flag EXPIRED returning to ACTIVE (only COURTESY may
return to ACTIVE on reconnect)

#### NFSD-CLI-002: COURTESY client without expiry

**Risk**: Memory exhaustion

**Details**: Flag transition to COURTESY without laundromat integration;
`cl_time` must be set and laundromat must check and expire after timeout

#### NFSD-CLI-003: State modification without lock

**Risk**: Race condition

**Details**: Flag `cl_state` modification without `client_lock` held; flag
check-then-modify on `cl_state` that is not atomic under lock

#### NFSD-CLI-004: Missing cleanup on transition

**Risk**: Resource leak

**Details**: Flag `destroy_client()` paths that skip revoking delegations,
freeing stateids (open, lock), or cleaning up sessions

#### NFSD-CLI-005: Admin interface race

**Risk**: Use-after-free

**Details**: Flag admin sysfs/procfs writes that access state without holding
`nfsd_mutex` or without checking `nn->nfsd_serv`

#### NFSD-CLI-006: Child stateid orphaning

**Risk**: List corruption, crash

**Details**: Flag parent destruction paths that do not free child stateids
(copynotify); `release_openowner()` may skip
`nfs4_free_cpntf_statelist()`

#### NFSD-CLI-007: Double initialization

**Risk**: Kernel panic (BUG_ON)

**Details**: Flag init functions reachable from multiple call paths; second
invocation triggers BUG_ON

**Acceptable**:
- Initial state assignment during allocation, before visibility
- Read-only state checks for logging
- Atomic transition helpers that encapsulate proper locking

---

## User Namespace ID Conversion [NFSD-NS]

**Scan for**: `from_kuid`, `from_kgid`, `make_kuid`, `make_kgid`,
`uid_valid`, `gid_valid`, `init_user_ns`, `current_user_ns`,
`nfsd_user_namespace`, `from_kuid_munged`, `GLOBAL_ROOT_UID`

#### NFSD-NS-001: Wrong namespace source

**Risk**: Container escape, host UID exposure

**Details**: Flag `from_kuid`/`from_kgid` in request paths using
`init_user_ns` or `current_user_ns()` instead of
`nfsd_user_namespace(rqstp)`; NFSD kthreads have `init_user_ns` as
`current_user_ns()`

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
- `from_kuid_munged()` for GETATTR encoding
- Idmap path handles namespace conversion internally

---

## Callback Operations [NFSD-CB]

**Scan for**: `nfsd4_run_cb`, `cl_rpc_users`, `cl_cb_state`, `NFSD4_CB_UP`,
`cl_cb_seq_nr`, `nfsd4_shutdown_callback`, `cl_session`,
`cl_minorversion`, callback release handlers, `cb_client`

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

#### NFSD-CB-003: Unbounded retry

**Risk**: Resource exhaustion, blocked clients

**Details**: Flag callback retry loops without backoff or bound; unbounded
retry on an unreachable client holds delegations indefinitely

#### NFSD-CB-004: Sequence number atomicity

**Risk**: Callback rejection

**Details**: Flag `cl_cb_seq_nr` modification without `cl_lock`; concurrent
increment causes duplicate sequence numbers and BAD_SEQUENCE rejection

#### NFSD-CB-005: Release handler reference drop

**Risk**: Delegation and client leak

**Details**: Flag callback release handlers that omit dropping delegation
`sc_count` or client `cl_rpc_users`

#### NFSD-CB-006: Client destroyed with callbacks in flight

**Risk**: Use-after-free in completion handler

**Details**: Flag `destroy_client()` paths that do not call
`nfsd4_shutdown_callback()` to drain in-flight callbacks before freeing

#### NFSD-CB-007: NFSv4.0 callback compatibility

**Risk**: NULL dereference on v4.0 clients

**Details**: Flag `cl_session` access without a `cl_minorversion > 0` guard;
`cl_session` is NULL for NFSv4.0 clients

**Acceptable**:
- Callback queue creation at server start
- Read-only state checks for logging
- Deferred release via RPC completion handler

---

## Session Slots [NFSD-SLOT]

**Scan for**: `se_slots`, `slotid`, `maxreqs`, `sl_seqid`, `sl_inuse`,
`sl_reply`, `same_creds`, `nfsd4_slot`, `SEQUENCE`,
`CREATE_SESSION`, `DESTROY_SESSION`

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

**Acceptable**:
- Read-only slot access for tracing
- Slot init during CREATE_SESSION before visibility
- `maxreqs` immutable after creation

---

## Security Validation [NFSD-SEC]

**Scan for**: `fh_verify`, `fh_dentry`, `nfs4_preprocess_stateid_op`,
`NFSD_MAY_*`, new procedure handlers, `nfsd_rename`, `nfsd_link`,
pseudo-filesystem access

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
- Export cache lookups in nfsd_fh_init path (no dentry yet)

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
`nfsd_net_try_get`/`nfsd_net_put`.

**Lock hierarchy** (outer to inner): `nn->client_lock` -> `state_lock` ->
`fp->fi_lock` -> `clp->cl_lock` -> `stp->st_mutex`. All except st_mutex are
spinlocks.

**Trust boundaries**: XDR decode (untrusted) -> `fh_verify()` ->
`nfs4_preprocess_stateid_op()` -> VFS data (trusted).

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
conversion paths changed; changes exceed 100 lines touching multiple core
files.
