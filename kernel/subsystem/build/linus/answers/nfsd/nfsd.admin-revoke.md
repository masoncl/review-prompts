| Action | Handler | Scope |
|---|---|---|
| write to nfsdfs `unlock_filesystem` | `write_unlock_fs()` | superblock |
| netlink `NFSD_CMD_UNLOCK_FILESYSTEM` | `nfsd_nl_unlock_filesystem_doit()` | superblock |
| netlink `NFSD_CMD_UNLOCK_EXPORT` | `nfsd_nl_unlock_export_doit()` | export path |

- `unlock_ip` and `NFSD_CMD_UNLOCK_IP`: release NLM locks only.
- `expire` written to a client's `ctl` file: destroys the client; marks
  nothing revoked.
- `nfsd4_revoke_states()`: takes `struct nfsd_net *`, not `struct net *`.
- `nfsd4_revoke_export_states()`: matches `sc_export->ex_path` with
  `path_equal()`; a stateid with no `sc_export` is never matched.
- Precondition of both: `nfsd_mutex` held and `NFSD_NET_UP` set. The handlers
  return `-EINVAL` otherwise.
- `write_unlock_fs()`: calls `nlmsvc_unlock_all_by_sb()` first, outside
  `nfsd_mutex`, so NLM locks are released even when it returns `-EINVAL`.
- What is skipped: stateids whose `sc_status` is not 0, clients that are
  unconfirmed or for which `is_client_expired()` is true, and `SC_TYPE_COPY`.
- Layout stateids: included; `revoke_one_stid()` marks them and calls
  `nfsd4_close_layout()`.
- Delegations: `unhash_delegation_locked()` then `revoke_delegation()`. No
  recall is sent.
- `nfserr_admin_revoked`: besides `nfsd4_lookup_stateid()`, it comes from
  `nfsd4_verify_open_stid()`, reached through `nfsd4_lock_ol_stateid()`,
  `nfsd4_stid_check_stateid_generation()` and, for TEST_STATEID,
  `nfsd4_validate_stateid()`.
- SEQUENCE: sets `SEQ4_STATUS_ADMIN_STATE_REVOKED` while `cl_admin_revoked`
  is non-zero.
- TEST_STATEID: frees nothing for a v4.1+ client; FREE_STATEID does, through
  `nfsd4_drop_revoked_stid()`.
