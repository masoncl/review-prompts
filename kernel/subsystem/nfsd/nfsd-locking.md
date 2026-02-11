# NFSD Locking

Violating NFSD's lock ordering hierarchy causes ABBA deadlocks.
Sleeping while holding a spinlock (`state_lock`, `client_lock`,
`cl_lock`, `fi_lock`) causes scheduler errors. Accessing state
without the correct lock held causes data races and corruption.

## Lock Ordering Hierarchy

The primary ordering rule:

```
nn->client_lock (outermost)
  → state_lock
    → fp->fi_lock
      → clp->cl_lock (innermost)
```

**REPORT as bugs**: Code that acquires `client_lock` while holding
`state_lock`, or acquires any outer lock while holding an inner lock
from this hierarchy.

## Global Locks

- `state_lock` — `DEFINE_SPINLOCK` in `fs/nfsd/nfs4state.c`. Protects
  `del_recall_lru`, file hash table, and `sc_status` for delegation
  stateids.
- `nfsd_mutex` — `DEFINE_MUTEX` in `fs/nfsd/nfssvc.c`. Protects
  `nn->nfsd_serv` pointer and `svc_serv` members (`sv_temp_socks`,
  `sv_permsocks`); also protects global variables during nfsd startup.
- `blocked_delegations_lock` — spinlock in `fs/nfsd/nfs4state.c`.
  Protects the blocked delegations bloom filter.
- `nfsd_session_list_lock` — spinlock in `fs/nfsd/nfs4state.c`.
  Protects the global session list.
- `nfsd_devid_lock` — spinlock in `fs/nfsd/nfs4layouts.c`. Protects
  pNFS device ID mappings.
- `nfsd_notifier_lock` — mutex in `fs/nfsd/nfssvc.c`. Protects
  `nfsd_serv` during network events.
- `nfsd_gc_lock` — mutex in `fs/nfsd/filecache.c`. Disables shrinker
  during garbage collection.

## Per-Namespace Locks (struct nfsd_net in netns.h)

**Spinlocks:**
- `client_lock` — protects `client_lru`, `close_lru`,
  `del_recall_lru`, and session hash table.
- `blocked_locks_lock` — protects `blocked_locks_lru`.
- `s2s_cp_lock` — protects server-to-server copy state
  (`s2s_cp_stateids` IDR).
- `nfsd_ssc_lock` — protects server-to-server copy mounts.
- `local_clients_lock` — protects `local_clients` list
  (`CONFIG_NFS_LOCALIO`).

**Seqlocks:**
- `writeverf_lock` — protects write verifier for NFSv3 COMMIT.

## Per-Object Locks

**Stateid structures:**
- `sc_lock` (in `struct nfs4_stid`) — spinlock protecting stateid
  fields, notably `si_generation` during
  `nfs4_inc_and_copy_stateid()`.
- `st_mutex` (in `struct nfs4_ol_stateid`) — protects open/lock
  stateid and `sc_status` for open stateids. Uses lockdep
  subclasses: `OPEN_STATEID_MUTEX` (0) and `LOCK_STATEID_MUTEX` (1)
  to allow nesting open→lock without false lockdep warnings; see
  `mutex_lock_nested()` calls in `fs/nfsd/nfs4state.c`.
- `ls_lock` (in `struct nfs4_layout_stateid`) — spinlock protecting
  layout stateid fields.
- `ls_mutex` (in `struct nfs4_layout_stateid`) — protects layout
  operations.

**Client structures:**
- `cl_lock` (in `struct nfs4_client`) — protects all client info
  needed by callbacks; also protects `sc_status` for open and lock
  stateids.
- `async_lock` (in `struct nfs4_client`) — protects `async_copies`
  list.

**Session/File structures:**
- `se_lock` (in `struct nfsd4_session`) — protects session fields.
- `fi_lock` (in `struct nfs4_file`) — protects file state including
  delegations, stateids, access counts.

**Other:**
- `cn_lock` (in `struct cld_net`) — protects client tracking upcall
  info in `fs/nfsd/nfs4recover.c`.
- `cache_lock` (in `struct nfsd_drc_bucket`) — protects DRC bucket
  in `fs/nfsd/nfscache.c`.

## Spinlock Context Constraints

`state_lock`, `client_lock`, `cl_lock`, `fi_lock`, `se_lock`, and
`sc_lock` are all spinlocks — no sleeping operations are permitted
while held. This means no `fh_verify()`, no VFS operations, no
memory allocation with `GFP_KERNEL`, and no `mutex_lock()`.

`st_mutex`, `ls_mutex`, and `nfsd_mutex` are mutexes and allow
sleeping, but verify no spinlocks are held when acquiring them.

## Quick Checks

- **Lock drop and reacquire**: when a lock is dropped and retaken
  (common pattern in nfs4state.c hot paths), verify the code
  re-validates all protected state after reacquiring.
- **lockdep_assert_held**: verify assertions match actual lock
  protection needs — `state_lock` for delegation/file state,
  `cl_lock` for client-level state.
- **st_mutex subclass**: open stateid operations use
  `OPEN_STATEID_MUTEX`, lock stateid operations use
  `LOCK_STATEID_MUTEX` via `mutex_lock_nested()`.
