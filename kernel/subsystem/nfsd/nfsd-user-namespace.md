# NFSD User Namespace Conversion

Using the wrong user namespace when converting between kernel IDs
(`kuid_t`/`kgid_t`) and wire IDs (`uid_t`/`gid_t`) causes incorrect
UID/GID values in responses, permission bypasses in container
environments, or failed ID lookups that silently substitute overflow
IDs.

## Namespace Source

`nfsd_user_namespace()` in `fs/nfsd/nfsd.h` returns the user
namespace for the transport credential:

```c
static inline struct user_namespace *
nfsd_user_namespace(const struct svc_rqst *rqstp)
{
    const struct cred *cred = rqstp->rq_xprt->xpt_cred;
    return cred ? cred->user_ns : &init_user_ns;
}
```

This namespace must be used consistently for all ID conversions
within a single NFS operation. Using `&init_user_ns` directly is
only correct when the transport credential is NULL (non-containerized
server) or when encoding pNFS layout data that uses absolute IDs.

## Kernel-to-Wire Conversion (encoding)

When encoding attributes for the client, use `from_kuid_munged()` /
`from_kgid_munged()` with `nfsd_user_namespace(rqstp)`:

- `fs/nfsd/nfsxdr.c` — `svcxdr_encode_fattr()` for NFSv2.
- `fs/nfsd/nfs3xdr.c` — `svcxdr_encode_fattr3()` for NFSv3.
- `fs/nfsd/nfs4idmap.c` — `nfsd4_encode_user()` and
  `nfsd4_encode_group()` for NFSv4 (encodes as string names).

The `_munged` variants substitute the overflow ID if the kuid/kgid
has no mapping in the target namespace, rather than failing.

## Wire-to-Kernel Conversion (decoding)

When decoding client-provided IDs, use `make_kuid()` / `make_kgid()`
with `nfsd_user_namespace(rqstp)`:

- `fs/nfsd/nfsxdr.c` — `svcxdr_decode_sattr()` for NFSv2.
- `fs/nfsd/nfs3xdr.c` — `svcxdr_decode_sattr3()` for NFSv3.
- `fs/nfsd/nfs4idmap.c` — `nfsd_map_name_to_uid()` and
  `nfsd_map_name_to_gid()` for NFSv4 (decodes from string names).
- `fs/nfsd/nfs4xdr.c` — `nfsd4_decode_authsys_parms()` for
  AUTH_SYS credentials in SECINFO responses.

After `make_kuid()` / `make_kgid()`, check validity with
`uid_valid()` / `gid_valid()` before use.

## init_user_ns Exceptions

Direct use of `&init_user_ns` is legitimate in:

- `fs/nfsd/flexfilelayout.c` and `fs/nfsd/flexfilelayoutxdr.c` —
  pNFS flexible file layout encodes absolute UIDs/GIDs for data
  server access.
- `fs/nfsd/export.c` — `svc_export_parse()` uses
  `current_user_ns()` for parsing admin-provided anonuid/anongid.

**REPORT as bugs**: Code in NFS procedure handlers or XDR
encode/decode functions that uses `&init_user_ns` or
`current_user_ns()` instead of `nfsd_user_namespace(rqstp)` for
client-facing ID conversions.

## Quick Checks

- **Consistent namespace**: all ID conversions within a single NFS
  operation must use the same namespace from
  `nfsd_user_namespace(rqstp)`.
- **ACL IDs**: NFSv4 ACL encode/decode must also use the correct
  namespace for ACE who fields.
- **New SETATTR paths**: any new code that sets `ia_uid` or `ia_gid`
  from client data must use `make_kuid(nfsd_user_namespace(rqstp), ...)`
  and validate the result.
