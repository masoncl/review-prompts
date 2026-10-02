- `nfsd4_decode_bitmap4()`: no fixed cap on the word count.
  `xdr_stream_decode_uint32_array()` bounds it by the stream, stores at most
  `bmlen` words, and a longer bitmap still returns `nfs_ok`.
- `nfsd4_decode_acl()`: bound is `xdr_stream_remaining() / 20`, error
  `nfserr_fbig`. There is no NFS4_ACL_MAX in this tree.
- `nfsd4_decode_posixacl()` (under `CONFIG_NFSD_V4_POSIX_ACLS`): bound is
  `NFS_ACL_MAX_ENTRIES`, error `nfserr_inval`.
- `nfsd4_decode_component4()`: calls `check_filename()` in the decoder;
  longer than `NFS4_MAXNAMLEN` gives `nfserr_nametoolong`.
- `nfsd4_decode_compound()`: clamps `opcnt` to `NFSD_MAX_OPS_PER_COMPOUND`
  with `min_t()` and keeps the client's value in `client_opcnt`; it does not
  reject. A tag longer than `NFSD4_MAX_TAGLEN` makes it return false.
- `nfsd4_decode_test_stateid()`: allocates each item before decoding it;
  `ts_num_ids` itself is never bounded, the stream ends the loop.
- Counts used only to loop, with no allocation per count, have no explicit
  bound; each iteration must consume stream bytes. For example
  `nfsd4_decode_cb_sec()` and the source server loop in
  `nfsd4_decode_copy()`.
- **Potentially unsafe usage**: sizing an allocation from a length read off
  the wire.
  - Unsafe: when nothing has yet compared the length with a constant or
    with the stream.
  - Safe: after `xdr_inline_decode()` of that many bytes succeeded, since
    that bounds it by the request, as `svcxdr_dupstr()` in
    `nfsd4_decode_create()` (also capped by `NFS4_MAXPATHLEN`).
