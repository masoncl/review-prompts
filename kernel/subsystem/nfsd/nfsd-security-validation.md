# NFSD Security-Critical Input Validation

Missing or incorrect security checks allow unauthorized file access,
authentication bypasses, or privilege escalation through crafted NFS
requests. The NFSD security model relies on layered validation:
file handle verification, export policy enforcement, and permission
checks must all pass before any operation proceeds.

## File Handle Verification (fh_verify)

`fh_verify(rqstp, fhp, type, access)` in `fs/nfsd/nfsfh.c` is the
primary security gate. It performs:

1. Dentry lookup from the wire handle via `nfsd_set_fh_dentry()`.
2. Export policy checks — the export must exist and the client must
   be authorized to access it.
3. Pseudo-root restriction via `check_pseudo_root()` — exports with
   `NFSEXP_V4ROOT` only allow access to directories and symlinks that
   are the export root itself. Other entries return `nfserr_stale`.
4. File type validation — `type` parameter (`S_IFDIR`, `S_IFREG`,
   `0` for any) is checked against the actual inode.
5. Permission check via `nfsd_permission()` using the `access` flags.

**REPORT as bugs**: Any NFS procedure that accesses file data or
metadata without first calling `fh_verify()` with appropriate type
and access flags, or that ignores its return value.

## Permission Enforcement (nfsd_permission)

`nfsd_permission()` in `fs/nfsd/vfs.c` enforces:

- **Read-only filesystem**: write/sattr/trunc operations return
  `nfserr_rofs` on read-only exports or mounts.
- **Immutable files**: writes to immutable inodes return
  `nfserr_perm`.
- **Append-only files**: truncation of append-only inodes returns
  `nfserr_perm`.
- **Owner override**: `NFSD_MAY_OWNER_OVERRIDE` allows the file
  owner to bypass mode bits (supports `fchmod(fd, 0)` followed by
  continued access).
- **VFS permission check**: delegates to `inode_permission()` for
  standard UNIX permission bits.
- **Read-if-exec fallback**: `NFSD_MAY_READ_IF_EXEC` allows reading
  binaries with mode 111 (execute-only).

## Export Policy

Export access control is managed through `struct svc_export` in
`fs/nfsd/export.h`. Key flags:

- `NFSEXP_READONLY` — export is read-only.
- `NFSEXP_ROOTSQUASH` — map root UID to anonymous.
- `NFSEXP_ALLSQUASH` — map all UIDs to anonymous.
- `NFSEXP_V4ROOT` — pseudo-root export (NFSv4 only).
- `NFSEXP_SECURITY_LABEL` — support security labels.

`exp_rdonly()` checks both the export flag and credential squashing
before allowing write operations.

## Stateid Validation

NFSv4 stateful operations (READ, WRITE, LOCK, OPEN, CLOSE, etc.)
must validate the client-provided stateid before proceeding. See
`nfsd4_lookup_stateid()` in `fs/nfsd/nfs4state.c` which checks
`sc_type`, `sc_status`, and client ownership.

**REPORT as bugs**: NFSv4 operations that modify state (close, lock,
delegation return) without first validating the stateid via
`nfsd4_lookup_stateid()` or equivalent.

## NFSv4 Pseudo-Filesystem

The NFSv4 pseudo-filesystem (`NFSEXP_V4ROOT` exports) presents a
virtual directory tree to clients. `check_pseudo_root()` in
`fs/nfsd/nfsfh.c` restricts access:

- Only directories and symlinks are accessible.
- Only the export root dentry itself is accessible — any other
  dentry returns `nfserr_stale`.
- This prevents clients from traversing into unexported subtrees.

NFSv2 and NFSv3 clients cannot access pseudo-root exports.

## Quick Checks

- **Access flag completeness**: verify `fh_verify()` access flags
  cover all permissions the operation requires — e.g., rename needs
  `NFSD_MAY_REMOVE` on the source directory and `NFSD_MAY_CREATE`
  on the target.
- **GSS policy enforcement**: exports requiring GSS authentication
  (`NFSD_MAY_BYPASS_GSS` not set) must reject AUTH_SYS credentials.
- **Credential squashing**: verify `NFSEXP_ROOTSQUASH` and
  `NFSEXP_ALLSQUASH` are applied before permission checks, not
  after.
