- `ipc_validate_msg()`: called only from `ipc_msg_send_request()`, after the
  wait; not from `handle_response()` or `handle_generic_event()`.
- Size rule: the computed size must equal `entry->msg_sz` exactly; a message
  that is merely large enough is rejected.
- Every case first rejects `entry->msg_sz` below the fixed struct size.

| Request type | Checked in `ipc_validate_msg()` |
|---|---|
| `KSMBD_EVENT_RPC_REQUEST` | size = struct + `payload_sz`, with `check_add_overflow()` |
| `KSMBD_EVENT_SPNEGO_AUTHEN_REQUEST` | size = struct + `session_key_len` + `spnego_blob_len`; plain add of two `__u16` |
| `KSMBD_EVENT_SHARE_CONFIG_REQUEST` | `share_name` has a NUL inside the array; `veto_list_sz <= payload_sz`; size = struct + `payload_sz` always, also for `payload_sz` 0, with `check_add_overflow()` |
| `KSMBD_EVENT_LOGIN_REQUEST_EXT` | non-zero `ngroups` must be in 1..`NGROUPS_MAX` and size = struct + `ngroups * sizeof(gid_t)` |
| `KSMBD_EVENT_LOGIN_REQUEST`, `KSMBD_EVENT_TREE_CONNECT_REQUEST` | no case; policy minimum only, trailing bytes accepted |

- Share config, extra rule: with `flags` not `KSMBD_SHARE_FLAG_INVALID` and
  `KSMBD_SHARE_FLAG_PIPE` clear, `payload_sz <= veto_list_sz` is rejected.
- Login-ext with `ngroups` 0: any length at or above the fixed struct passes.
- `ngroups`: bounded in `ipc_validate_msg()`, not in `ksmbd_alloc_user()`,
  which uses it unchecked for `kmemdup()`.
- NUL termination: `ipc_validate_msg()` checks one string only, `share_name`
  in `struct ksmbd_share_config_response`.
- `ksmbd_nl_policy` entries for `KSMBD_EVENT_RPC_RESPONSE` and
  `KSMBD_EVENT_SPNEGO_AUTHEN_RESPONSE`: empty, so netlink sets no minimum;
  `handle_response()` requires `sizeof(unsigned int)` before it reads the
  handle.
- Permission: no op sets `GENL_ADMIN_PERM`; the only check is
  `netlink_capable(skb, CAP_NET_ADMIN)` in `handle_generic_event()` and
  `handle_startup_event()`, compiled in by
  `CONFIG_SMB_SERVER_CHECK_CAP_NET_ADMIN` (default y in
  `fs/smb/server/Kconfig`).
- Sender identity: `handle_generic_event()` does not compare the sender's port
  id with `ksmbd_tools_pid`.
- `handle_generic_event()`: rejects `type > KSMBD_EVENT_MAX` (so
  `KSMBD_EVENT_MAX` itself is allowed) and a `KSMBD_GENL_VERSION` mismatch.
- `hash_sz`: left to the caller; `ksmbd_alloc_user()` rejects
  `hash_sz > sizeof(resp->hash)`, for the plain login response and for the
  `login_response` inside `struct ksmbd_spnego_authen_response`.
- **Potentially unsafe usage**: using a length field from a response as a copy
  length.
  - Unsafe: when the source array or the destination has a fixed size and
    nothing compares the field with it; `ipc_validate_msg()` ties only the
    fields in the table above to the message length.
  - Safe: `ksmbd_alloc_user()` compares `hash_sz` with `sizeof(resp->hash)`
    (`KSMBD_REQ_MAX_HASH_SZ`) before `memcpy()`.
  - Safe: `ksmbd_krb5_authenticate()` compares `session_key_len` with
    `sizeof(sess->sess_key)` (`CIFS_KEY_SIZE`) and `spnego_blob_len` with
    `*out_len` before copying.
  - Safe: `smb2_read_pipe()` sizes its destination from `payload_sz`, and
    `fsctl_pipe_transceive()` clamps the copy to `out_buf_len`, which
    `smb2_ioctl()` took from `smb2_calc_max_out_buf_len()`.
