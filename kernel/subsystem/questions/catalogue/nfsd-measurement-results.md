# What the nfsd measurement found

Three models were asked the 90 questions in `nfsd-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader C was the most current (it
assumed kernels from 6.12 to 6.19), reader A close behind it (6.12 to 6.18),
and reader B older and much weaker (it ranged from 4.1 to 6.16, and four
fifths of what it wrote was rewritten). The hand-written guide was never
checked against current sources, so differences between it and the built guide
are expected and are noted near the end.

Readers A and C know the architecture of the server: the dispatch path, the
compound loop, the state structures and how they hang together, the file
handle layout, the slot sequence check, the errno table. What they get wrong
is what this tree has reworked since they last saw it, and the fine print of
who holds which reference and which lock. This tree has reworked a great deal:
per-thread request state, the reply page array, the delegation lock, async
copy state, the per-net flags, the netlink family, signed file handles and
directory delegations are all different from what any reader described.

## What all three readers got wrong

- **Per-thread request state.** All three put the reply cache type and the
  lease breaker in `struct svc_rqst` fields that do not exist (rq_cachetype,
  rq_lease_breaker). They are `ntli_cachetype` and `ntli_lease_breaker` in
  `struct nfsd_thread_local_info`, a stack local of `nfsd()` reached through
  `rq_private`. Readers A and C said outright that they did not know the
  structure.
- **The reply page array.** All three described one array shared by call and
  reply, with `rq_respages` pointing into `rq_pages`. `rq_respages` is a second
  array allocated by `svc_init_buffer()`; `rq_next_page` and `rq_page_end`
  point into it, and `svc_rqst_replace_page()` bounds against it. The scratch
  page is `rq_scratch_folio`; there is no rq_vec.
- **The delegation lock.** All three named a global state_lock. The lock is
  the per-net `deleg_lock` in `struct nfsd_net`, and it nests outside
  `client_lock`, not inside. Every reader had at least one pair of the lock
  order inverted or invented: `s2s_cp_lock` nests inside `cl_lock` (through
  `nfs4_put_stid()`), `async_lock` inside `client_lock`, `flc_lock` inside
  `fi_lock` (in `check_for_locks()`), `sc_lock` is innermost, `se_lock` and
  `nfsd_ssc_lock` nest with nothing, and no function holds `st_mutex`
  together with `deleg_lock`.
- **Async copy state.** No reader recognised `struct nfsd4_async_copy` or
  `nfs4_alloc_copy_stid()`. The offload stateid is an `SC_TYPE_COPY`
  `struct nfs4_stid` in the client's `cl_stateids`, hidden from generic
  stateid operations by `find_stateid_locked()`; `s2s_cp_stateids` holds only
  COPY_NOTIFY stateids. The copy has its own `refcount` with separate
  references for list membership, the kthread and CB_OFFLOAD, and the
  callback pins the client with `cl_ref`, not `cl_rpc_users`. Going over the
  async limit returns `nfserr_jukebox`; it does not fall back to a
  synchronous copy.
- **Signed file handles.** All three said the tree does not sign handles. It
  does: `NFSEXP_SIGN_FH`, `fh_append_mac()`, `fh_verify_mac()`, a key set
  through netlink, root handles exempt, `nfserr_stale` on a bad signature.
- **Directory delegations.** All three said CB_NOTIFY and
  `nfsd_handle_dir_event()` were not merged. Both are in the tree.
- **Per-net flags.** All three named booleans (nfsd_net_up, grace_ended,
  somebody_reclaimed). They are bits in `flags` of `struct nfsd_net`:
  `NFSD_NET_UP`, `NFSD_NET_GRACE_ENDED` and the rest of `enum nfsd_net_flag`.
  The two-lease limit on grace is measured from `boot_time_bt`.
- **File handle verification.** `__fh_verify()` does not call
  `check_nfsd_access()`; it calls `check_xprtsec_policy()` and
  `check_security_flavor()` itself, after `check_pseudo_root()`,
  `nfsd_setuser_and_check_port()` and `nfsd_mode_check()`, and repeats all of
  them on every call. NLM requests skip the transport check, and with
  `NFSEXP_NOAUTHNLM` everything after the type check. All three repeated the
  comment above `fh_verify()` that a negated type means "not this type";
  `nfsd_mode_check()` takes a `umode_t` and knows only zero and an exact
  match.
- **Release and status mapping in the compound loop.** `op_release` is called
  by `nfsd4_proc_compound()`, not by `nfsd4_encode_operation()`.
  `nfsd4_map_status()` is in `fs/nfsd/nfs4xdr.c` and runs in
  `nfsd4_encode_operation()` after the encoder. NFSv2 and NFSv3 procedures
  always return `rpc_success` and put the filtered status in `resp->status`.
  There is no nfserr_dropit; a reply is dropped with `RQ_DROPME`.
- **Client counters.** No reader knew `put_client_no_renew()` and
  `put_client_no_renew_locked()`, which the laundromat and the revocation
  walks use so as not to revive a courtesy client. drop_client() is gone;
  `cl_ref` is dropped by `nfsd4_put_client()`. The laundromat and
  `lookup_clientid()` take `cl_rpc_users` with a bare `atomic_inc()`.
- **Courtesy clients.** `get_client_locked()` and `renew_client_locked()` set
  `NFSD4_ACTIVE` whatever the state was, so an expirable client can become
  active again. What never happens is active to expirable.
  `NFSD_COURTESY_CLIENT_TIMEOUT` is defined and unused.
- **Stateid references.** The reference set at allocation is the creator's;
  hashing takes its own. `nfsd_break_one_deleg()` uses
  `refcount_inc_not_zero()` because the CB_NOTIFY paths reach it without
  `flc_lock`. The final `nfs4_put_stid()` also drops the export reference
  after `sc_free`. `revoke_delegation()` has no minor-version test, so an
  NFSv4.0 delegation also goes on `cl_revoked`.
- **Administrative revocation and netlink.** No reader knew the unlock-export
  command, `nfsd4_revoke_export_states()`, `nfsd_file_close_export()` or
  `nfsd4_cancel_copy_by_sb()`, nor the export, expkey, cache-flush and
  statistics commands of the netlink family, some of whose handlers are in
  `fs/nfsd/export.c`. `GENL_ADMIN_PERM` is on two of the dump commands as
  well, and is checked against the initial user namespace.
- **Session slots.** There is no slot_bytes() and no DRC memory accounting.
  The table is an xarray, grows by a fifth under `GFP_NOWAIT` up to the lower
  of `NFSD_MAX_SLOTS_PER_SESSION` and the thread ceiling, shrinks through a
  shrinker, and keeps a freed slot's sequence id as an xarray value entry.
- **Callbacks.** `prepare` returns bool and false means nothing is sent.
  `nfsd4_run_cb()` never looks at `NFSD4_CALLBACK_RUNNING`; callers set it.
  `cl_cb_session` is `__rcu`.
- **The open file cache.** `nfsd_file_acquire_local()` is not garbage
  collected, `nfsd_file_acquire_dir()` exists, unlink and rename close cached
  files only for `EXPORT_OP_CLOSE_BEFORE_UNLINK`, and the worker skips dirty
  files only for `EXPORT_OP_FLUSH_ON_CLOSE`.
- **The maintainer profile.** Each reader supplied rules of its own (ban new
  procfs files, always use tracepoints). The document is milder and more
  specific; see the built guide.

## What readers A and B got wrong as well

- `EBADF` maps to `nfserr_stale`, not `nfserr_io` (reader A).
- `struct knfsd_fh` has no union; it is a size and a byte array, and the
  header names are macros.
- `rqst_exp_find()` tries the IP domain first and the GSS domain second.
- The ACL decoder's bound is the remaining stream length over 20, returning
  `nfserr_fbig`; NFS4_ACL_MAX does not exist.
- An NFSv4.0 replay over `NFSD4_REPLAY_ISIZE` is kmalloc'd, not dropped;
  there is no rp_mutex.
- Where `rq_next_page` is advanced and where NFSv4 brings it back in step
  (`nfsd4_encode_operation()`, after every operation).
- The preconditions for a delegation: a confirmed owner, `delegation_blocked()`,
  the setuid check, no write delegation for NFSv4.0, and
  `nfsd4_cb_channel_good()` accepting an unknown channel on sessions.
- Delegated timestamps: the recorded times are a baseline set at grant, and
  the inode is stamped with the current time, not the client's.
- The client tracking order (the usermode helper is tried before the legacy
  directory) and when `create` runs.

## What only reader B got wrong

Almost everything else. The parts that would change a review: it gave the
stateid kinds the names of a much older tree (NFS4_OPEN_STID and so on), said
`sc_type` is set before the stateid is published, put all stateid status under
`cl_lock`, said the slot table is fixed at CREATE_SESSION, said
`replay_matches_cache()` compares opcodes, said result encoders run on every
error, invented file names for the generated XDR and netlink code, and said
`nfsd_user_namespace()` takes an export.

## What only reader C got wrong

- A handful of helper names (nfsd4_cache_this, nfsd4_enc_sequence_replay).
- `cs_count` of a COPY_NOTIFY state starts at two.
- The attribute encoder table: unsupported slots are not all no-ops, and the
  supported masks are in `fs/nfsd/attr4.h`.
- It marked get and dump netlink commands as never privileged.

## What the readers already knew

Readers A and C: the file map and the entry points, the dispatch order, the
operation flags, the errno table (reader C without error), how the pseudo-root
is fenced off, the splice actor's page handling, generation numbers, the slot
sequence check (both without error), the backchannel slot handling (reader C),
the laundromat's steps (reader C), client creation and teardown (reader C),
what each state lock covers, and the outline of every state structure. Reader
B knew the outline of the protocol and the older names.

## Where the hand-written guide is stale

`nfsd.md` is a list of past fixes written as rules, with a file table and no
map of the state. Against this tree:

- Its lock hierarchy is wrong in three places. `deleg_lock` nests outside
  `client_lock`, `cl_lock` outside `fi_lock` and outside `s2s_cp_lock`, and
  `st_mutex`, a sleeping lock, cannot be innermost under spinlocks. It lists
  grace_ended as a field; it is a flag bit.
- It says an expirable client cannot return to active. `get_client_locked()`
  makes it active.
- It says NFSv3 procedures must return `nfsd3_map_status(resp->status)` and
  not bare `rpc_success`. They store the mapped status and return
  `rpc_success`. It says NFSv2 needs `nfserrno()`; NFSv2 has
  `nfsd_map_status()`. It says `EOPENSTALE` must not become `nfserr_stale`;
  `nfserrno()` maps it so, after the open path has retried once.
- It tells callback code to test `cl_cb_state` under `cl_lock` and to touch
  `cl_cb_client` only under that lock. The code relies on the client's
  callback workqueue for both. It asks for locking around `se_cb_seq_nr`; the
  held slot is what serialises it. `cl_cb_session` is now `__rcu`.
- Its page array section describes one array based at `rq_pages`.
- Its copy offload section is about an IDR that no longer holds copy
  stateids, and it pairs async copies with `cl_rpc_users` where the code uses
  `cl_ref`.
- Its netlink section asks for a `capable()` call in each handler and a policy
  entry per attribute. The policy and the `GENL_ADMIN_PERM` flag are generated
  from `Documentation/netlink/specs/nfsd.yaml`.
- Its re-export section turns on tests for an NFS superblock. No such test is
  in `fs/nfsd/`; the code consults `EXPORT_OP_` flags and
  `exportfs_cannot_lock()`.
- It recommends `check_mul_overflow()`, which `fs/nfsd/` does not use, and
  names two fixes by SHA.
- Its reference pairs are right as far as they go, and its account of
  `release_openowner()` is correct.

## What was left out of the build set and why

Forty-two of the ninety questions are in the build set, chosen so that the
budgets land on the hand-written guide's size. Left out because readers A and
C answer them well enough: the entry points, the documentation list, dispatch,
the operation flags, the duplicate reply cache, the errno table, the file
handle layout and lifetime, the pseudo-root, the access flags, the splice
actor, generation numbers, owner references, what each lock covers, client
creation and teardown, the laundromat, the slot sequence check and replay.
Left out for room, although readers were wrong about them: the read and write
paths and I/O modes, READDIR buffers, the attribute encoder table, the
NFSv4.0 owner replay cache, export caches and the security policy checks
(the verification steps cover the order), request credentials, the open file
cache's entries and acquire variants, delegation kinds, delegated timestamps,
GETATTR against a write delegation, the breaker's own delegation (the
per-thread state covers where it is recorded), callback channel state and
backchannel slots, stateid lookup masks, the grace checks list, client
tracking, OFFLOAD_CANCEL and COPY_NOTIFY, layouts, byte-range lock state,
server start and stop, and LOCALIO.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader A          277        45%      7     55   6.12 to 6.18
reader B          337        80%      2     87   4.1 to 6.16
reader C          245        30%     24     26   6.12 to 6.19

question                         reader A      reader B      reader C
nfsd.file-map                     1% ( 2)      14% ( 7)       5% ( 1)
nfsd.entry-points                 5% ( 1)      14% ( 3)       0% ( 0)
nfsd.docs                        28% ( 1)      79% ( 4)      29% ( 1)
nfsd.dispatch                    21% ( 1)      76% ( 2)      15% ( 2)
nfsd.thread-local                79% ( 2)      89% ( 1)      77% ( 1)
nfsd.compound-loop               21% ( 2)      82% ( 1)      23% ( 2)
nfsd.op-flags                    10% ( 2)      56% ( 2)       5% ( 1)
nfsd.new-operation               29% ( 1)      80% ( 1)      16% ( 1)
nfsd.drc                         42% ( 1)      87% ( 2)      11% ( 1)
nfsd.errno-mapping                3% ( 2)      72% ( 2)       0% ( 0)
nfsd.version-status-maps         53% ( 3)      78% ( 4)      34% ( 4)
nfsd.status-type-usage           32% ( 1)      64% ( 2)       9% ( 1)
nfsd.internal-status-codes       67% ( 2)      86% ( 3)      54% ( 3)
nfsd.fh-layout                   59% ( 3)      83% ( 6)      35% ( 1)
nfsd.svc-fh-fields               45% ( 1)      83% ( 2)      38% ( 3)
nfsd.fh-lifetime                 54% ( 1)      78% ( 4)      24% ( 2)
nfsd.fh-signing                  91% ( 1)      97% ( 1)      90% ( 1)
nfsd.fh-verify-steps             57% ( 4)      83% ( 6)      43% ( 3)
nfsd.may-flags                   20% ( 3)      68% ( 5)      29% ( 4)
nfsd.fh-verify-usage             25% ( 1)      86% ( 4)      18% ( 2)
nfsd.pseudoroot                  16% ( 1)      81% ( 1)      23% ( 1)
nfsd.export-caches               55% ( 3)      85% ( 6)      33% ( 4)
nfsd.export-security             59% ( 2)      93% ( 3)      23% ( 2)
nfsd.cred-setup                  29% ( 2)      85% ( 5)      18% ( 3)
nfsd.user-namespace              49% ( 2)      86% ( 3)      39% ( 3)
nfsd.xdr-decode-conventions      46% ( 6)      86% ( 5)      24% ( 3)
nfsd.xdr-decode-bounds           39% ( 3)      85% ( 2)      18% ( 1)
nfsd.xdr-encode-conventions      31% ( 2)      78% ( 4)       8% ( 2)
nfsd.xdr-encode-failure          36% ( 2)      86% ( 3)      39% ( 1)
nfsd.xdrgen                      69% ( 3)      91% ( 6)      34% ( 3)
nfsd.fattr-encoding              20% ( 3)      83% ( 2)      73% ( 5)
nfsd.seqid-replay                48% ( 4)      94% ( 3)      44% ( 2)
nfsd.page-arrays                 64% ( 2)      79% ( 5)      61% ( 4)
nfsd.next-page-usage             61% ( 4)      91% ( 3)      14% ( 1)
nfsd.read-paths                  50% ( 4)      84% ( 3)      28% ( 1)
nfsd.splice-actor                22% ( 1)      74% ( 2)       7% ( 1)
nfsd.write-path                  34% ( 4)      90% ( 4)      43% ( 3)
nfsd.readdir-encoding            59% ( 3)      84% ( 3)      39% ( 2)
nfsd.filecache-objects           48% ( 3)      82% ( 5)       0% ( 0)
nfsd.filecache-acquire           30% ( 4)      64% ( 4)      23% ( 4)
nfsd.filecache-lifetime          78% ( 5)      87% ( 6)      53% ( 5)
nfsd.state-objects               19% ( 3)      40% ( 8)       7% ( 6)
nfsd.stateowner-refs             22% ( 3)      62% ( 3)       8% ( 2)
nfsd.state-limits                29% ( 3)      47% ( 5)      13% ( 3)
nfsd.stid-fields                 67% ( 8)      96% ( 5)      21% ( 7)
nfsd.stid-status-locks           33% ( 2)      85% ( 2)      25% ( 3)
nfsd.stid-refcount               41% ( 3)      84% ( 3)      38% ( 2)
nfsd.stid-lookup                 62% ( 2)      88% ( 2)      15% ( 2)
nfsd.preprocess-stateid          46% ( 5)      84% ( 6)      42% ( 5)
nfsd.stateid-generation          15% ( 2)      69% ( 4)       2% ( 1)
nfsd.open-stid-race              58% ( 2)      76% ( 3)      15% ( 1)
nfsd.client-refs                 48% ( 6)      85% ( 6)      53% ( 5)
nfsd.client-lifecycle            27% ( 3)      77% ( 2)       7% ( 1)
nfsd.courtesy-clients            42% ( 3)      91% ( 3)      13% ( 2)
nfsd.laundromat                  46% ( 1)      88% ( 3)       0% ( 0)
nfsd.admin-revoke                54% ( 2)      88% ( 4)      53% ( 3)
nfsd.lock-order                  78% ( 7)      87% (12)      43% ( 9)
nfsd.lock-scope                  14% ( 4)      29% ( 1)       9% ( 3)
nfsd.nfsd-mutex                  75% ( 4)      82% ( 3)      55% ( 5)
nfsd.deleg-refs                  50% ( 4)      86% ( 3)      15% ( 4)
nfsd.deleg-grant                 70% ( 5)      87% ( 5)      62% ( 4)
nfsd.deleg-break                 47% ( 3)      76% ( 3)      28% ( 2)
nfsd.deleg-conflict-self         60% ( 4)      79% ( 1)      29% ( 2)
nfsd.deleg-revoke                54% ( 5)      83% ( 4)      26% ( 1)
nfsd.deleg-types                 43% ( 2)      86% ( 5)      28% ( 3)
nfsd.deleg-timestamps            75% ( 4)      86% ( 3)      20% ( 2)
nfsd.deleg-getattr               57% ( 2)      86% ( 1)      18% ( 4)
nfsd.dir-delegations             90% ( 2)      88% ( 1)      78% ( 2)
nfsd.cb-lifecycle                35% ( 4)      92% ( 6)      61% ( 3)
nfsd.cb-serialization            45% ( 3)      95% ( 4)      32% ( 2)
nfsd.cb-slots                    33% ( 3)      94% ( 3)       7% ( 1)
nfsd.cb-usage                    47% ( 6)      88% ( 5)      26% ( 6)
nfsd.session-slots               28% ( 5)      90% ( 7)      29% ( 3)
nfsd.slot-seqid                   6% ( 1)      74% ( 3)       0% ( 0)
nfsd.slot-replay                 44% ( 3)      76% ( 4)      17% ( 4)
nfsd.grace-checks                75% ( 3)      95% ( 5)      33% ( 2)
nfsd.grace-end                   65% ( 3)      80% ( 3)      39% ( 3)
nfsd.client-tracking             59% ( 2)      84% ( 4)      17% ( 1)
nfsd.copy-objects                60% ( 7)      79% ( 6)      52% ( 7)
nfsd.copy-lifecycle              53% ( 4)      96% ( 3)      40% ( 4)
nfsd.copy-cancel-status          72% ( 3)      86% ( 2)      48% ( 1)
nfsd.copy-notify                 35% ( 2)      84% ( 2)      46% ( 4)
nfsd.layouts                     59% ( 5)      81% ( 5)      29% ( 4)
nfsd.lock-state                  35% ( 4)      84% ( 4)      37% ( 2)
nfsd.netlink-spec                26% ( 5)      76% ( 5)      48% ( 5)
nfsd.netlink-perms               33% ( 2)      85% ( 4)      49% ( 4)
nfsd.server-lifecycle            66% ( 3)      88% ( 5)      42% ( 3)
nfsd.reexport                    40% ( 7)      86% ( 6)      16% ( 4)
nfsd.localio                     61% ( 5)      86% ( 4)      47% ( 6)
nfsd.coding-style                69% ( 5)      73% ( 6)      72% ( 7)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `nfsd.svc-fh-fields`, `nfsd.fh-lifetime`, `nfsd.export-security`, `nfsd.read-paths`, `nfsd.stid-lookup`, `nfsd.deleg-refs`, `nfsd.deleg-conflict-self`, `nfsd.grace-checks`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `nfsd.dispatch`, `nfsd.op-flags`, `nfsd.errno-mapping`, `nfsd.may-flags`, `nfsd.cred-setup`, `nfsd.xdr-decode-conventions`, `nfsd.xdr-encode-conventions`, `nfsd.write-path`, `nfsd.filecache-objects`, `nfsd.client-lifecycle`, `nfsd.deleg-types`, `nfsd.cb-serialization`, `nfsd.slot-seqid`, `nfsd.slot-replay`.

## Questions reorganised

66 questions before, 64 after, by subject: requests and replies (7), compounds and XDR (7), file
handles, exports and credentials (9), stateids (7), clients and state locks (6), delegations (7),
sessions and callbacks (6), grace (2), copy offload (2), data transfer and the file cache (4),
configuration and netlink (3), conventions (1). Merged: `nfsd.svc-fh-fields` and
`nfsd.fh-lifetime` into `nfsd.svc-fh-state`; `nfsd.xdr-decode-conventions` and
`nfsd.xdr-encode-conventions` into `nfsd.xdr-conventions` (signatures and basic-type helpers are a
lookup). Nothing else dropped. Inventories reworded: `nfsd.file-map`, `nfsd.state-objects`,
`nfsd.op-flags`, `nfsd.may-flags`, `nfsd.state-limits`, `nfsd.new-operation`, `nfsd.coding-style`.
