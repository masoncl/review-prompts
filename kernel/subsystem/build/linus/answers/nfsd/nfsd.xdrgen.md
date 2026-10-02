- Generated for NFSD: `fs/nfsd/nfs4xdr_gen.c`, `fs/nfsd/nfs4xdr_gen.h` and
  `include/linux/sunrpc/xdrgen/nfs4_1.h`, all from
  `Documentation/sunrpc/xdr/nfs4_1.x`. There are no generated NFSv2 or NFSv3
  files in `fs/nfsd`.
- lockd has its own generated set, for example `fs/lockd/nlm4xdr_gen.c`.
- `fs/nfsd/Makefile` has a phony `xdrgen` target with one rule per file
  (`xdrgen definitions`, `xdrgen declarations`, `xdrgen source`). The output
  is checked in and a normal build does not run the tool.
- Only types marked `pragma public` in the `.x` file get a non-static
  function and a prototype in `fs/nfsd/nfs4xdr_gen.h`; the rest are
  `static bool __maybe_unused`. Calling a new one needs a `pragma public`
  line and regeneration, not an edit of the `.c` file.
- A false return is mapped by the caller, and the mapping depends on the
  caller's own convention, for example:
  - decoders in `fs/nfsd/nfs4xdr.c`: `nfserr_bad_xdr`
  - encoders in `fs/nfsd/nfs4xdr.c`: `nfserr_resource`
  - `decode_cb_fattr4()` in `fs/nfsd/nfs4callback.c`: `-EIO`
  - `nfsd4_encode_notify_event()`: NULL;
    `nfsd4_encode_dir_attr_change()`: `ERR_PTR(-ENOBUFS)`
- Generated enum decoders return false for a value that is not an
  enumerator, for example `xdrgen_decode_posixacetag4()`.
- `xdrgen_decode_fattr4_time_deleg_access()` and
  `xdrgen_decode_fattr4_time_deleg_modify()` make no range check on
  `nseconds`; `nfsd4_decode_fattr4()` checks it itself after the call.
