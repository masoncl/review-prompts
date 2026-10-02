- There is no nfs4_unhash_stid() in this tree.

| Kind | Bit | Lock held by the writer |
|---|---|---|
| open, lock | every bit | `cl_lock` |
| open | `SC_STATUS_CLOSED` in `nfsd4_close()` | `st_mutex` as well |
| open, lock | `SC_STATUS_ADMIN_REVOKED` | `st_mutex` as well |
| delegation | the bit passed to `unhash_delegation_locked()` | `deleg_lock`, not `cl_lock` |
| delegation | `SC_STATUS_FREEABLE`, `SC_STATUS_FREED`, and `SC_STATUS_CLOSED` set by `nfsd4_free_stateid()` | `cl_lock`, not `deleg_lock` |
| layout | `SC_STATUS_CLOSED` | `ls_lock` |
| layout | `SC_STATUS_ADMIN_REVOKED` | `cl_lock` |

- `release_open_stateid()`: sets `SC_STATUS_CLOSED` under `cl_lock` only; it
  does not take `st_mutex`.
- Admin revocation: the test and set are in `revoke_ol_stid()` and
  `revoke_one_stid()`, not in `nfsd4_revoke_states()`.
- Teardown of open and lock stateids: gated on the return value of
  `unhash_ol_stateid()`, `unhash_lock_stateid()` or `unhash_open_stateid()`
  under `cl_lock`, not on `sc_status`. A true return is what entitles the
  caller to put the hash reference, as in `release_lock_stateid()`.
- `SC_STATUS_FREEABLE` against `SC_STATUS_FREED`: `revoke_delegation()` and
  `nfsd4_free_stateid()` each test the other's bit under `cl_lock`; whichever
  runs second leaves the delegation off `cl_revoked`.
- **Unsafe usage**: testing `sc_status`, dropping the lock, then setting a
  bit or releasing access on the strength of the test.
  - Safe: test `sc_status == 0` and set the bit in one `cl_lock` hold with
    `st_mutex` held throughout, as `revoke_ol_stid()` does; it asserts
    `st_mutex`.
  - Safe: for an open or lock stateid, put the hash reference only when the
    unhash helper returned true under `cl_lock`, as `release_lock_stateid()`
    does.
  - Safe: for a delegation, act only when `unhash_delegation_locked()`
    returned true under `deleg_lock`, as `destroy_delegation()` does.
- **Unsafe usage**: setting `SC_STATUS_ADMIN_REVOKED` without incrementing
  `cl_admin_revoked`; the final put decrements it when the bit is set.
  - Safe: increment in the same critical section, as `revoke_ol_stid()` does.
