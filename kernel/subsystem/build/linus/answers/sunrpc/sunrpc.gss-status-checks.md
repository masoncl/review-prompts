- Statuses from the Kerberos mechanism: `GSS_S_COMPLETE`, `GSS_S_BAD_SIG`,
  `GSS_S_DEFECTIVE_TOKEN`, `GSS_S_FAILURE`, `GSS_S_CONTEXT_EXPIRED`;
  `gss_krb5_errno_to_status()` in `gss_krb5_mech.c` maps `-EBADMSG` and
  `-EPROTO` from `crypto/krb5/` and turns every other errno into
  `GSS_S_FAILURE`.
- **Potentially unsafe usage**: using the output after a status other than
  `GSS_S_COMPLETE`.
  - Unsafe: after `gss_verify_mic()` or `gss_unwrap()`;
    `gss_krb5_unwrap_v2()` returns `GSS_S_CONTEXT_EXPIRED` before it strips
    the token header, so the buffer is not in its final layout.
  - Safe: `GSS_S_CONTEXT_EXPIRED` from `gss_get_mic()` or `gss_wrap()`;
    `gss_krb5_get_mic_v2()` and `gss_krb5_wrap_v2()` test `endtime` last, after
    the token is written. `gss_wrap_req_integ()` and `gss_wrap_req_priv()`
    clear `RPCAUTH_CRED_UPTODATE`, return 0 and send the request.
- Server callers: treat `GSS_S_CONTEXT_EXPIRED` like any other failure.

| Client caller | Failure result |
|---|---|
| `gss_marshal()` | expired `-EKEYEXPIRED`; bad MIC `-EIO`; no space `-EMSGSIZE` |
| `gss_validate()` | bad MIC `-EACCES`; decode failure `-EIO`; never `-EBADMSG` |
| `gss_wrap_req_integ()` | bad MIC `-EIO`; no space `-EMSGSIZE` |
| `gss_wrap_req_priv()` | `-EIO`; `-EAGAIN` from `alloc_enc_pages()` |
| `gss_unwrap_resp_integ()`, `gss_unwrap_resp_priv()` | `-EIO` |

- `gss_validate()`: on `GSS_S_BAD_SIG` it retries the MIC against each entry
  of `rq_seqnos` before failing.
- `rpc_decode_header()` after a verifier failure with
  `RPCAUTH_CRED_UPTODATE` cleared: `rpcauth_invalcred()`, then
  `-EKEYREJECTED` while `tk_cred_retry` lasts, which restarts at
  `call_reserve` with a new XID.
- `rpc_decode_header()` after `-EACCES` with the cred still up to date: the
  task is put back on the receive queue and waits for another reply; nothing
  is retransmitted and the cred is not refreshed.
- `rpc_decode_header()` after `-EIO` from `gss_validate()` with the cred still
  up to date: re-encodes through `call_encode` while `tk_garb_retry` lasts.
- Reply unwrap failure: `call_decode()` stores the errno in `tk_status` with
  `tk_action` already `rpc_exit_task`; there is no retry.

| Server caller | Failure result |
|---|---|
| `svcauth_gss_verify_header()` | `rpcsec_gsserr_credproblem`, `SVC_DENIED` |
| `svcauth_gss_encode_verf()` for `RPC_GSS_PROC_DATA` | `rpcsec_gsserr_ctxproblem`, `SVC_DENIED` |
| `svcauth_gss_unwrap_integ()`, `svcauth_gss_unwrap_priv()` | `-EINVAL`, then `SVC_GARBAGE` |
| `svcauth_gss_wrap_integ()` | `-EINVAL` from `svcauth_gss_release()` |
| `svcauth_gss_wrap_priv()` | `-ENOMEM` for a `gss_wrap()` failure, else `-EINVAL` |

- Reply wrap failure: `svc_authorise()` returns non-zero, so
  `svc_process_common()` sends nothing and calls `svc_xprt_close()` on an
  `XPT_TEMP` transport.
- Absent names: there is no unwrap_integ_data, unwrap_priv_data,
  svcauth_gss_wrap_resp_integ or svc_return_autherr in this tree.
