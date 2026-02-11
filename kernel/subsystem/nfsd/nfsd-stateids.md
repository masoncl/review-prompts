# NFSv4 Stateid Lifecycle

Incorrect stateid reference counting causes use-after-free (accessing a
stateid after the final `nfs4_put_stid()` triggers `idr_remove()` and
`sc_free()`), resource leaks (failing to release references on error
paths), or protocol violations (reusing a stale stateid generation that
the client treats as an error).

## Stateid Types

All stateids embed `struct nfs4_stid` (defined in `fs/nfsd/state.h`)
which holds `sc_count` (`refcount_t`), `sc_type`, `sc_status`,
`sc_stateid`, `sc_client`, and `sc_file`. The `sc_type` field uses:

| Type constant | Meaning |
|---------------|---------|
| `SC_TYPE_OPEN` | Open stateid (`struct nfs4_ol_stateid`) |
| `SC_TYPE_LOCK` | Lock stateid (`struct nfs4_ol_stateid`) |
| `SC_TYPE_DELEG` | Delegation (`struct nfs4_delegation`) |
| `SC_TYPE_LAYOUT` | Layout stateid (`struct nfs4_layout_stateid`) |

## Allocation and Initialization

`nfs4_alloc_stid()` in `fs/nfsd/nfs4state.c` allocates from a slab
cache, assigns an IDR slot under `cl_lock`, sets `sc_client` and
`sc_free` (the type-specific destructor), and sets
`refcount_set(&stid->sc_count, 1)`. Type-specific allocators (e.g.,
`nfs4_alloc_open_stateid()`, `nfs4_set_delegation()`) wrap this and
initialize subtype fields.

## Lookup and Validation

`nfsd4_lookup_stateid()` in `fs/nfsd/nfs4state.c` looks up a stateid
from a client-provided `stateid_t`, filters by `typemask` and
`statusmask`, and increments `sc_count` before returning. The caller
must call `nfs4_put_stid()` when done.

Key status flags checked during lookup (defined in `fs/nfsd/state.h`):

| Flag | Meaning |
|------|---------|
| `SC_STATUS_CLOSED` | Stateid closed, no further operations allowed |
| `SC_STATUS_REVOKED` | Delegation revoked by server |
| `SC_STATUS_ADMIN_REVOKED` | Administratively revoked |
| `SC_STATUS_FREEABLE` | Marked for deferred cleanup |
| `SC_STATUS_FREED` | Already freed |

**REPORT as bugs**: Code that accesses stateid fields (`sc_file`,
`sc_client`, type-specific fields) without holding a reference from
a successful lookup or allocation.

## Release and Destruction

`nfs4_put_stid()` in `fs/nfsd/nfs4state.c` uses
`refcount_dec_and_lock(&s->sc_count, &clp->cl_lock)` to atomically
drop the last reference and acquire `cl_lock`. When the refcount
reaches zero it calls `idr_remove()` to remove the stateid from the
client's IDR tree, then calls `s->sc_free(s)` and
`put_nfs4_file(fp)`.

**REPORT as bugs**: Code that uses a stateid after calling
`nfs4_put_stid()` on it — the object may already be freed.

## Stateid Generation (RFC 8881 section 9.1.4)

The `si_generation` field in `sc_stateid` must increment on every
state-modifying operation to prevent the client from confusing old
and new state. Use `nfs4_inc_and_copy_stateid()` which atomically
increments under `sc_lock` and copies the result:

```c
// CORRECT — single atomic increment-and-copy
nfs4_inc_and_copy_stateid(&resp->stateid, &stp->st_stid);

// WRONG — double increment
stp->st_stid.sc_stateid.si_generation++;
nfs4_inc_and_copy_stateid(&resp->stateid, &stp->st_stid);
```

## Open/Lock Stateids

`struct nfs4_ol_stateid` (for both `SC_TYPE_OPEN` and `SC_TYPE_LOCK`)
holds `st_stateowner` (reference-counted via `nfs4_get_stateowner()` /
`nfs4_put_stateowner()`) and inherits `sc_file` from `nfs4_stid`.

State changes to open/lock stateids must be serialized with
`st_mutex`. Check `sc_status` under the mutex before modifying state:

```c
// CORRECT — check status under mutex
mutex_lock(&stp->st_mutex);
if (stp->st_stid.sc_status & SC_STATUS_CLOSED) {
    mutex_unlock(&stp->st_mutex);
    return nfserr_bad_stateid;
}
// ... perform state change ...
mutex_unlock(&stp->st_mutex);

// WRONG — TOCTOU race without mutex
if (!(stp->st_stid.sc_status & SC_STATUS_CLOSED))
    stp->st_stid.sc_stateid.si_generation++;
```

## Delegations

`struct nfs4_delegation` embeds `dl_stid` (`struct nfs4_stid`) and
has three reference sources (documented in `fs/nfsd/state.h`):

1. One reference while the delegation is in force (taken at allocation,
   released on return or revocation).
2. One reference while a recall RPC (`dl_recall` callback) is in
   progress (taken when the lease is broken, released when the RPC
   completes).
3. Ephemeral references for nfsd threads operating on the delegation
   without holding `cl_lock`.

**Recall**: `nfsd4_run_cb(&dp->dl_recall)` sends CB_RECALL
asynchronously. The callback infrastructure holds a reference for the
duration of the RPC — code that initiates recall must ensure a
reference is taken before the callback is queued.

**Revocation**: Must set `SC_STATUS_REVOKED` under `cl_lock`, remove
from `dl_perclnt` list, and call `nfs4_put_stid()`:

```c
spin_lock(&clp->cl_lock);
dp->dl_stid.sc_status |= SC_STATUS_REVOKED;
list_del_init(&dp->dl_perclnt);
spin_unlock(&clp->cl_lock);
nfs4_put_stid(&dp->dl_stid);
```

## Quick Checks

- **Lookup/put balance**: every `nfsd4_lookup_stateid()` or
  `find_stateid_by_type()` call that returns a stid must have a
  matching `nfs4_put_stid()` on all paths.
- **sc_status before operations**: verify `SC_STATUS_CLOSED` is
  checked before performing state-modifying operations.
- **Generation via helper**: verify `nfs4_inc_and_copy_stateid()` is
  used rather than manual `si_generation++` followed by a copy.
- **Reference across async operations**: delegation callbacks and
  other async work items must hold their own reference.
