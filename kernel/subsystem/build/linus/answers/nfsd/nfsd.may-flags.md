- Access kinds are the bits inside `NFSD_MAY_MASK`; `NFSD_MAY_MASK` itself is
  a mask, not a flag to pass.
- There is no NFSD_MAY_LOCK here; `NFSD_MAY_NLM` is the lockd flag, and it
  lies inside `NFSD_MAY_MASK`.
- `NFSD_MAY_NLM` is rewritten nowhere; `nlm_fopen()`, the only code that
  passes it, passes
  `NFSD_MAY_NLM | NFSD_MAY_OWNER_OVERRIDE | NFSD_MAY_BYPASS_GSS` itself.
- `NFSD_MAY_LOCAL_ACCESS`: skips only the read-only export or mount test and
  the `IS_IMMUTABLE()` test in `nfsd_permission()`; squashing is untouched.
- `NFSD_MAY_READ_IF_EXEC`: the retry with `MAY_EXEC` needs
  `(acc & NFSD_MAY_MASK) == NFSD_MAY_READ` and this flag or
  `NFSD_MAY_OWNER_OVERRIDE`; bits outside the mask do not disable it, a set
  `NFSD_MAY_NLM` does.
- `NFSD_MAY_BYPASS_GSS`: skips nothing; `check_security_flavor()` gains one
  passing case: the request is `RPC_AUTH_NULL` or `RPC_AUTH_UNIX` and the
  export lists a flavor at or above `RPC_AUTH_DES`.
- `NFSD_MAY_BYPASS_GSS_ON_ROOT`: the same, only when the dentry is the export
  root; passed only by NFSv2 and NFSv3 procedures, for example
  `nfsd3_proc_getattr()` and `nfsd3_proc_fsinfo()`.
- `NFSD_MAY_64BIT_COOKIE`: passed by `nfsd_file_acquire_dir()`, tested
  nowhere; `nfsd_readdir()` tests `fh_64bit_cookies`.
- `NFSD_MAY_LOCALIO`: tested by no check and reaches only tracepoints;
  `NFSD_FILE_MAY_MASK` names it, but `nf_may` is an `unsigned char`, so the
  bit is dropped and is not part of the `nf_may` match in
  `fs/nfsd/filecache.c`.
- `nfsd_file_do_acquire()` adds `NFSD_MAY_OWNER_OVERRIDE` to every acquire,
  and `nfsd_open()` adds it for `S_IFREG`; in those cases a caller cannot get
  a check without it.
- **Potentially unsafe usage**: passing `NFSD_MAY_BYPASS_GSS` to
  `fh_verify()`.
  - Unsafe: when the caller then returns data or changes the object and
    nothing later repeats the flavor check; an `RPC_AUTH_UNIX` request passes
    an export that lists only stronger flavors.
  - Safe: `nfsd4_putfh()`, which only sets the current handle; the check
    follows in `nfsd4_proc_compound()` when `need_wrongsec_check()` is true,
    and is otherwise left to a next operation flagged `OP_HANDLES_WRONGSEC`.
  - Safe: `nlm_fopen()`, which hands the open file to lockd for locking
    only.
- **Potentially unsafe usage**: passing `NFSD_MAY_LOCAL_ACCESS` to
  `nfsd_permission()`.
  - Unsafe: for a regular file or directory; write access then passes on a
    read-only export.
  - Safe: `nfsd_access()`, which uses `nfs3_anyaccess` only when the object
    is neither `d_is_reg()` nor `d_is_dir()`.
