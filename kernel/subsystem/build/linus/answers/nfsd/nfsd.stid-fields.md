| Bit | Kinds that carry it | Set by |
|---|---|---|
| `SC_STATUS_CLOSED` | open, lock, delegation, layout | `nfsd4_close()`, `release_open_stateid()`; `unhash_lock_stateid()`; `unhash_delegation_locked()`, `nfsd4_free_stateid()`; `nfsd4_return_file_layouts()` |
| `SC_STATUS_REVOKED` | delegation of a v4.1+ client | `unhash_delegation_locked()` called from `nfs4_laundromat()` |
| `SC_STATUS_ADMIN_REVOKED` | open, lock, delegation, layout | `revoke_ol_stid()`, `revoke_one_stid()`, `unhash_delegation_locked()` |
| `SC_STATUS_FREEABLE` | delegation | `revoke_delegation()`, when it puts the delegation on `cl_revoked` |
| `SC_STATUS_FREED` | delegation | `nfsd4_free_stateid()` (revoked), `nfsd4_drop_revoked_stid()` (admin-revoked) |

- `SC_TYPE_COPY` stateid: no code sets a status bit on it.
- `sc_type` for open, lock, delegation and layout: set in the same `cl_lock`
  hold that hashes the stateid, in `init_open_stateid()`,
  `init_lock_stateid()`, `hash_delegation_locked()` and
  `nfsd4_alloc_layout_stateid()`.
- `SC_TYPE_COPY`: set by `nfs4_alloc_copy_stid()` straight after
  `nfs4_alloc_stid()` returns, without `cl_lock`.
- Lookup by id in between: `find_stateid_locked()` returns NULL while
  `sc_type` is 0, so `nfsd4_lookup_stateid()`, `nfsd4_validate_stateid()`
  and `nfsd4_free_stateid()` all give `nfserr_bad_stateid` with no test of
  their own.
- Walk of `cl_stateids` in between (`find_one_sb_stid()`, `states_show()`):
  sees the entry. `nfs4_alloc_stid()` fills `sc_client`, `sc_free`,
  `sc_stateid` and `sc_count` after it drops `cl_lock`, and `sc_file` is set
  later still.
- **Potentially unsafe usage**: reading a field of a stid found by walking
  `cl_stateids`.
  - Unsafe: dereferencing a pointer field such as `sc_file` before testing
    `sc_type`; the entry may still be untyped with the pointer NULL.
  - Safe: under `cl_lock`, test `sc_type` against a type mask and
    `sc_status == 0` first, as `find_one_sb_stid()` does before it reads
    `sc_file`; `move_to_close_lru()` sets `sc_file` to NULL on a closed open
    stateid.
  - Safe: testing a bit of `sc_status` first, as
    `nfs40_clean_admin_revoked()` does; `nfs4_alloc_stid()` zero-allocates
    and every writer of `sc_status` acts on a typed stid.
