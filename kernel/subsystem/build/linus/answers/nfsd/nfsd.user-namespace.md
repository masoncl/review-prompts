- `nfsd_user_namespace()` in `fs/nfsd/auth.c`: returns
  `rqstp->rq_xprt->xpt_cred->user_ns`, or `&init_user_ns` when `xpt_cred` is
  NULL.
- `nfsd_user_namespace()` dereferences `rq_xprt` unconditionally; it does not
  use `xpt_net` or `current_user_ns()`.
- Paths in `fs/nfsd` and `fs/nfs_common` that pass `&init_user_ns` whatever
  the request's namespace:
  - NFSACL v2/v3 ACL entries, in `xdr_nfsace_encode()` and
    `xdr_nfsace_decode()` in `fs/nfs_common/nfsacl.c`.
  - Flexfile layout uid and gid, in `nfsd4_ff_proc_layoutget()` and
    `nfsd4_ff_encode_layoutget()`.
- No tracepoint in `fs/nfsd` converts with `init_user_ns`.
- Export `anonuid`/`anongid` parsing uses `current_user_ns()` of the writer,
  in both the cache-channel and the netlink parser in `fs/nfsd/export.c`;
  `exp_flags()` displays with the reader's `f_cred->user_ns`.
- **Potentially unsafe usage**: `from_kuid()` or `from_kgid()` to produce a
  wire id.
  - Unsafe: with `nfsd_user_namespace()`, whose map may not cover the id; the
    result is `(uid_t)-1`.
  - Safe: with `&init_user_ns`, whose map in `kernel/user.c` covers every
    valid id, as `xdr_nfsace_encode()` does; the id sent is then the initial
    namespace's, not the request's.
  - Safe: `from_kuid_munged()` with the request's namespace, as
    `nfsd4_encode_user()` does.
