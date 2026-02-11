# NFS Error Code Mapping

Returning the wrong error code to an NFS client causes protocol
violations — the client may misinterpret the server's response, retry
an operation that should fail permanently, or abort when it should
retry. Each NFS version has a different set of valid error codes, and
leaking a version-specific code to the wrong version confuses clients.

## errno to nfserr Conversion

`nfserrno()` in `fs/nfsd/vfs.c` converts Linux `errno` values to
`nfserr_*` wire codes. It uses a static table mapping each `errno` to
its NFS equivalent. Unmapped errnos trigger `WARN_ONCE` and return
`nfserr_io` as a fallback.

Notable mappings:
- `-ETIMEDOUT`, `-ERESTARTSYS`, `-EAGAIN`, `-EWOULDBLOCK`,
  `-ENOMEM` all map to `nfserr_jukebox` (tells client to retry later).
- `-EBADF` and `-ESTALE` and `-EOPENSTALE` all map to `nfserr_stale`.
- `-EOPNOTSUPP` maps to `nfserr_notsupp`.

**REPORT as bugs**: VFS or internal API calls in NFSD that return
a Linux errno directly to the client without passing through
`nfserrno()` or an equivalent mapping function.

## NFSv3 Status Mapping

`nfsd3_map_status()` in `fs/nfsd/nfs3proc.c` remaps NFSv4-specific
error codes that are not valid in NFSv3:

| Internal code | NFSv3 code | Reason |
|---------------|------------|--------|
| `nfserr_nofilehandle` | `nfserr_badhandle` | NFSv3 name |
| `nfserr_wrongsec` | `nfserr_acces` | Not in NFSv3 |
| `nfserr_file_open` | `nfserr_acces` | Not in NFSv3 |
| `nfserr_symlink_not_dir` | `nfserr_notdir` | Not in NFSv3 |
| `nfserr_symlink` | `nfserr_inval` | Not in NFSv3 |
| `nfserr_wrong_type` | `nfserr_inval` | Not in NFSv3 |

Every NFSv3 procedure in `fs/nfsd/nfs3proc.c` calls
`nfsd3_map_status()` before returning.

**REPORT as bugs**: NFSv3 procedure functions that return without
calling `nfsd3_map_status()` on the status code, or new NFSv3
procedures that omit this call.

## NFSv4 Error Codes

NFSv4 procedures in `fs/nfsd/nfs4proc.c` use `nfserr_*` codes
directly. NFSv4 defines a richer set of error codes than NFSv3, so
most internal codes are valid. However, NFSv2/v3-only codes should
not appear in NFSv4 responses.

## Quick Checks

- **New VFS calls**: any new call to a VFS or internal kernel function
  that returns an errno must have its return value mapped via
  `nfserrno()` before being used as an NFS status.
- **New NFSv3 procedures**: must call `nfsd3_map_status()` before
  returning.
- **Error code provenance**: when an `nfserr_*` code is passed between
  functions, verify it originated from the correct version's error
  space.
