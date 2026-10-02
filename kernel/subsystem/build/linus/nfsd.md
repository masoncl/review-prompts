# NFS Server Subsystem

## Main structures

### Objects and how they relate

- Global, not per-netns: `nfs4_file_rhltable` (`fs/nfsd/nfs4state.c`) and
  `nfsd_file_rhltable` (`fs/nfsd/filecache.c`) are single tables shared by
  every `struct nfsd_net`.
  - `struct nfsd_file`: carries `nf_net`, and `nfsd_file_lookup_locked()`
    filters on it.
  - `struct nfs4_file`: carries no netns; `nfsd4_file_hash_lookup()` makes no
    netns test.
- `struct nfs4_file`: hashed by inode pointer, then chosen by `fh_match()` on
  `fi_fhandle`; one inode can have several, marked `fi_aliased`.
- `struct nfsd_file`: hashed by inode pointer only; identity is then
  (`nf_may`, `nf_net`, cred, `NFSD_FILE_GC` bit), see
  `nfsd_file_lookup_locked()`.
  - A garbage-collected and a non-garbage-collected `struct nfsd_file` for
    the same file are different objects.
  - `nfsd_file_acquire_gc()`: used by the v2/v3 I/O paths; the other acquire
    variants (NFSv4 state, localio, directories) return non-GC objects.
- `struct nfsd_file_mark` on a directory: belongs to
  `nfsd_dir_fsnotify_group` and feeds `nfsd_handle_dir_event()`; it does not
  close files.
- `struct nfsd4_compound_state` (`fs/nfsd/xdr4.h`): the per-COMPOUND context;
  there is no nfsd4_compoundstate. It is embedded in
  `struct nfsd4_compoundres` as `cstate`.
- `struct svc_rqst`: one per nfsd kthread, reused for each RPC; see `nfsd()`
  in `fs/nfsd/nfssvc.c`.
- `struct svc_pool`: one per NUMA node that has CPUs, never per CPU; see
  `svc_pool_map_init_pernode()` in `net/sunrpc/svc.c`.
  - `sp_nrthrmin` and `sp_nrthrmax`: the pool's floor and ceiling; `nfsd()`
    retires a thread only while `sp_nrthreads` is above `sp_nrthrmin`, and
    spawns one only while it is below `sp_nrthrmax`.
- `struct nfsd4_copy` in the COMPOUND arguments: the transient COPY argument,
  not valid after the RPC.
- `sc_export` in `struct nfs4_stid`: open, lock, delegation and layout stids
  each hold a reference on the `struct svc_export` they were acquired
  through.
  - `drop_stid_export()` drops it early on admin revoke, so `sc_export` can
    be NULL on a live stid.
- `struct nfs4_delegation`: also represents a directory delegation, see
  `nfsd_get_dir_deleg()`.
  - `struct nfsd_notify_event`: one queued directory change awaiting
    CB_NOTIFY.
- `struct nfs4_layout_stateid`: holds its own reference on a
  `struct nfsd_file` (`ls_file`) and, unless the layout type sets
  `disable_recalls`, its own VFS lease, separate from `fi_fds` of the
  `struct nfs4_file`.
- Lock nesting, outermost first: `st_mutex`, then `deleg_lock`,
  `client_lock`, `cl_lock`, `fi_lock`.
  - Layout list linkage is under `cl_lock` and `fi_lock`, not `deleg_lock`.
- `struct svc_export` and `struct svc_expkey`: filled through netlink as well
  as the cache pipe; see `nfsd_cache_notify()` in `fs/nfsd/nfsctl.c` and
  `nfsd_nl_svc_export_set_reqs_doit()` in `fs/nfsd/export.c`.
- Localio: each `struct nfsd_file` handed to the NFS client by
  `nfsd_open_local_fh()` is paired with a reference on `nfsd_net_ref`;
  `nfsd_shutdown_net()`, when `NFSD_NET_UP` is set, kills that ref and waits
  for it to drain.

## Where to look

**File map**

| Job | File | Easy to miss |
|---|---|---|
| Netlink, hand-written | `fs/nfsd/nfsctl.c` and `fs/nfsd/export.c` | `fs/nfsd/export.c` defines `nfsd_nl_svc_export_get_reqs_dumpit()`, `nfsd_nl_svc_export_set_reqs_doit()`, `nfsd_nl_expkey_get_reqs_dumpit()` and `nfsd_nl_expkey_set_reqs_doit()`; every other handler declared in `fs/nfsd/netlink.h`, and the multicast sender `nfsd_cache_notify()`, is in `fs/nfsd/nfsctl.c` |
| Generated XDR | `fs/nfsd/nfs4xdr_gen.c`, `fs/nfsd/nfs4xdr_gen.h` | generated from `Documentation/sunrpc/xdr/nfs4_1.x` by the `xdrgen` target in `fs/nfsd/Makefile`, which also writes the types to `include/linux/sunrpc/xdrgen/nfs4_1.h`; covers only some NFSv4 types, called from the hand-written `fs/nfsd/nfs4xdr.c` and `fs/nfsd/nfs4callback.c` |
| debugfs | `fs/nfsd/debugfs.c` | built only with `CONFIG_DEBUG_FS`; no other file under `fs/nfsd/` creates debugfs entries, `fs/nfsd/nfsctl.c` only calls `nfsd_debugfs_init()` and `nfsd_debugfs_exit()` |

## Requests and replies

**Per-thread request state**

- `struct svc_rqst` has no rq_cachetype or rq_lease_breaker field in this
  tree; both live in `struct nfsd_thread_local_info` in `fs/nfsd/nfsd.h`, as
  `ntli_cachetype` and `ntli_lease_breaker`.
- `struct nfsd_thread_local_info` is not allocated: it is a zero-initialised
  local variable of `nfsd()` in `fs/nfsd/nfssvc.c`, so it lives on the thread's
  stack until `nfsd()` returns.
- `rq_private` in `struct svc_rqst` is a `void *` that `nfsd()` points at that
  variable once, before its request loop.
- `rq_private` is NULL in any `struct svc_rqst` not owned by an nfsd thread:
  `svc_prepare_thread()` zero-allocates and only `nfsd()` assigns the field.
- `ntli_cachetype`: `nfsd_dispatch()` rewrites it from `pc_cachetype` at the
  start of every request.
- `ntli_lease_breaker`: a `struct nfs4_client **`, set to `&cstate->clp` only
  in `nfsd4_proc_compound()`, after the minor-version and op-ordering checks.
- `ntli_lease_breaker` is never cleared: it is NULL until the thread's first
  such COMPOUND, and during NFSv2/v3 requests it still points into `rq_resp`.
- `nfsd_breaker_owns_lease()` in `fs/nfsd/nfs4state.c` dereferences it only
  after `nfsd_v4client()` on `nfsd_current_rqst()` succeeds.
- `nfsd4_deleg_getattr_conflict()` dereferences it with no test of its own;
  its one caller is in `fs/nfsd/nfs4xdr.c`.

**Request and reply pages**

- Two arrays: `rq_pages` holds the call and `rq_respages` holds the reply.
- `svc_init_buffer()` in `net/sunrpc/svc.c` allocates each array separately
  with `rq_maxpages + 1` entries; `rq_respages` is not a pointer into
  `rq_pages`.
- `rq_next_page` and `rq_page_end` point into `rq_respages`.
- `svc_alloc_arg()` sets `rq_arg.pages` to `rq_pages + 1`; `svc_process()`
  sets `rq_res.pages` to `&rq_respages[1]`.

| Where | What it does to the reply pointers |
|---|---|
| `svc_init_buffer()` | `rq_next_page = rq_respages + rq_maxpages`, so the first refill covers all `rq_maxpages` slots |
| `svc_alloc_arg()` in `net/sunrpc/svc_xprt.c` | refills `rq_respages` up to the old `rq_next_page`, then sets `rq_next_page = rq_respages`, `rq_page_end = &rq_respages[rq_maxpages]`, and stores NULL at `rq_page_end[0]` |
| `svc_rdma_recvfrom()` | sets `rq_next_page = rq_respages` |
| `svc_process()` | sets `rq_next_page = &rq_respages[1]` |
| `svc_rqst_release_pages()` | releases and NULLs the slots from `rq_respages` up to `rq_next_page`; leaves `rq_next_page` unchanged |

- `net/sunrpc/svcsock.c` assigns neither `rq_respages` nor `rq_next_page`.
- `svc_alloc_arg()` does not scan the whole array for NULL slots: the value
  it finds in `rq_next_page` bounds its refill of `rq_respages`, and a NULL
  slot at or above it is not refilled.
- `rq_pages` refill: `svc_alloc_arg()` refills only the first
  `rq_pages_nfree` entries, which a transport sets when it takes call pages
  out of the array.
- `svc_rqst_replace_page()` bounds `rq_next_page` by `rq_respages` and
  `rq_page_end`, not by `rq_pages`.

**RPC dispatch**

- Decode failure: `nfsd_dispatch()` writes `rpc_garbage_args` through
  `rq_accept_statp` and returns 1; it does not write `rq_auth_stat`.
- Cache type: `ntli->ntli_cachetype`, set from `pc_cachetype` before
  `pc_decode`; `nfsd_cache_lookup()` reads it from `rq_private` itself, so a
  value the decoder stored is the one the lookup uses.
- Encode failure and `RQ_DROPME`: both call
  `nfsd_cache_update(rqstp, rp, RC_NOCACHE, NULL)`; the NULL status pointer
  makes `nfsd_cache_update()` free the entry.
- `rp` stays NULL after `RC_DOIT` unless `nfsd_cache_lookup()` inserted a new
  entry, for example when the type is `RC_NOCACHE` or the entry allocation
  failed; `nfsd_cache_update()` then returns at once.
- Return 1 with an accept status other than `rpc_success`:
  `svc_process_common()` truncates away everything encoded after
  authentication and sends the reply.
- `nfsd_status_counter_set_idle()`: called on every return path after the
  store that makes `rq_status_counter` odd, including both drop paths; the
  decode-failure path returns before that store.

**Per-version status filtering**

- `nfsd_map_status()` in `fs/nfsd/nfsproc.c` differs from `nfsd3_map_status()`:

| Status | NFSv2 result | NFSv3 result |
|---|---|---|
| `nfserr_nofilehandle` | `nfserr_stale` | `nfserr_badhandle` |
| `nfserr_badhandle` | `nfserr_stale` | unchanged |
| `nfserr_xdev` | `nfserr_acces` | unchanged |
| `nfserr_symlink`, `nfserr_wrong_type` | `nfserr_io` | `nfserr_inval` |

- `nfsd_map_status()` and `nfsd3_map_status()` are `static` and are called by
  the procedure itself, on `resp->status`; neither has a caller outside its own
  file, and neither dispatch nor the encoders apply them.
- NFSv4: `nfsd4_map_status()` in `fs/nfsd/nfs4xdr.c`, a switch on the status
  with the minor version as argument; there is no per-minor table.
- `nfsd4_map_status()` has one call site, at the `status:` label of
  `nfsd4_encode_operation()`, and it overwrites `op->status`.
- COMPOUND status: `nfsd4_proc_compound()` copies it from `op->status` after
  `nfsd4_encode_operation()` returns, so it is already mapped.
- `nfserr_wrong_type` is a protocol value, `cpu_to_be32(NFS4ERR_WRONG_TYPE)`;
  `nfsd4_map_status()` changes it to `nfserr_inval` for minor version 0 only.
- Dropping a reply: NFSD procedures return `rpc_success` and set `RQ_DROPME`,
  as `nfsd_proc_read()` does on `nfserr_jukebox`.
- `rpc_drop_reply` is not used in `fs/nfsd`; after `pc_func` returns,
  `nfsd_dispatch()` tests only `RQ_DROPME`.

**Errno to NFS status**

- `nfserrno()` is defined in `fs/nfsd/vfs.c`.
- `-EBADF` maps to `nfserr_stale`.
- `-ETIMEDOUT` maps to `nfserr_jukebox`.

**Status and errno types**

- **Potentially unsafe usage**: passing the return value of a VFS call
  straight to `nfserrno()`.
  - Unsafe: when the callee can return an errno with no entry in `nfs_errtbl`,
    for example `-ENODATA` or `-ERANGE`; `nfserrno()` warns once and the client
    gets `nfserr_io`.
  - Safe: when those values are translated first, as `nfsd_xattr_errno()` in
    `fs/nfsd/vfs.c` does before it falls back to `nfserrno()`.
- **Unsafe usage**: returning an NFS status from a `pc_func`.
  - Unsafe: sparse does not flag it, because the RPC accept status is `__be32`
    too; `svc_process_common()` then truncates the reply and sends the value as
    the accept status.
  - Safe: store the status in `resp->status` and return `rpc_success`, as
    `nfsd3_proc_getattr()` does.
  - Safe: for NFSv4, store it in `cstate->status`, as `nfsd4_proc_compound()`
    does.
- Internal status codes: `nfserr_eof`, `nfserr_replay_me`,
  `nfserr_replay_cache` and `nfserr_symlink_not_dir`, in the enum that starts
  at `NFSERR_EOF` in `fs/nfsd/nfsd.h`; there is no nfserr_dropit.
- Code that keeps an `int host_err` apart from the `__be32` status and
  converts once with `nfserrno()`: `nfsd_lookup_dentry()`, `nfsd_setattr()`,
  `nfsd_create_locked()` and `nfsd_vfs_write()` in `fs/nfsd/vfs.c`.
- `nfsd_lookup()` holds only a `__be32`.
- `nfserrno(-EINVAL)` on a constant: see `nfsd4_clone_file_range()`;
  `nfsd_setattr()` has no such call.

**Reply page accounting**

- NFSv4 resync: the `release:` label at the end of `nfsd4_encode_operation()`
  in `fs/nfsd/nfs4xdr.c` sets `rq_next_page = xdr->page_ptr + 1`.
- That resync runs for every operation that reaches
  `nfsd4_encode_operation()`, including the early exits that jump to
  `release:`.
- `nfs4svc_encode_compoundres()` does not touch `rq_next_page`.
- `svcxdr_init_encode()` starts `xdr->page_ptr` at `rq_res.pages - 1`, which is
  `&rq_respages[0]`.
- NFSv2 and NFSv3 encoders, and `nfsd4_encode_splice_read()`, sync in the
  other direction: `svcxdr_encode_opaque_pages()` in
  `include/linux/sunrpc/svc.h` sets `xdr->page_ptr = rq_next_page - 1`.
- There is no common NFSv2/v3 resync; the procedure must have moved
  `rq_next_page` past the payload pages before `pc_encode` runs.
- `nfsd3_proc_read()` records `resp->pages` and lets `nfsd_read()` advance
  `rq_next_page`.
- **Potentially unsafe usage**: leaving `rq_next_page` anywhere but one past
  the last page the reply uses.
  - Unsafe: when a slot the reply uses is at or above `rq_next_page`;
    `svc_rqst_release_pages()` and `svc_alloc_arg()` skip it, so the next
    request writes into a page that may still be queued for sending.
  - Safe: when `rq_next_page` is above the last page used, as
    `nfsd_iter_read()` leaves it after a short read;
    `svc_rqst_release_pages()` releases every slot below `rq_next_page` and
    `svc_alloc_arg()` refills them.
  - Safe: `nfsd3_init_dirlist_pages()` advances over the whole buffer, and
    `nfsd3_proc_readdir()` then sets `rq_next_page = resp->xdr.page_ptr + 1`
    only to avoid recycling unused pages.

## NFSv4 compounds and XDR

**Compound processing checks**

- Before the loop, once: `nfsd_minorversion()` (failure encodes no op at
  all), `nfs41_check_op_ordering()`, `check_if_stalefh_allowed()`. The loop
  itself makes no opnum range test and no SEQUENCE-first test;
  `nfsd4_decode_compound()` did the range test.
- Per-op order in `nfsd4_proc_compound()` in `fs/nfsd/nfs4proc.c`:
  1. `resp->opcnt == NFSD_MAX_OPS_PER_COMPOUND`, minor version 0, client
     sent more ops: `nfserr_resource`.
  2. `op->status` already set: handler skipped; `OP_OPEN` goes through
     `nfsd4_open_omfg()`.
  3. `fh_dentry` NULL: `nfserr_nofilehandle` unless `ALLOWED_WITHOUT_FH`.
  4. Else export has `ex_fslocs.migrated`: `nfserr_moved` unless
     `ALLOWED_ON_ABSENT_FS`.
  5. `fh_clear_pre_post_attrs()`.
  6. `OP_MODIFIES_SOMETHING`: `op_rsize_bop` then
     `nfsd4_check_resp_size()`.
  7. `op_get_currentstateid` if set, then `op_func`.
- `NFSD4_FH_FOREIGN` with `fh_dentry` NULL: the op gets `nfserr_stale`
  unless it is `OP_SAVEFH` or has `ALLOWED_WITHOUT_FH`; so `nfsd4_savefh()`
  can run with no dentry.
- `op_release`: called by the loop, not by `nfsd4_encode_operation()`.
  It runs after the op is encoded, on both the `nfsd4_encode_operation()`
  and the `nfsd4_encode_replay()` path, and also when the handler was
  skipped or failed.
- `op_release` is not called for ops that were decoded but lie after the op
  that ended the loop, nor on the `nfserr_replay_cache` jump.
- `nfsd4_map_status()`: called by `nfsd4_encode_operation()` in
  `fs/nfsd/nfs4xdr.c`, just before it writes the status word; it rewrites
  `op->status`, so the loop sees the mapped value.
- `nfsd4_encode_replay()` path: no `nfsd4_map_status()`; the status is the
  cached `rp_status`.
- Loop end: `status = op->status` is read after encoding, so a handler error,
  a wrongsec failure, or an encode or size failure all end the loop.
- `nfserr_replay_me`: does not end the loop by itself; the loop continues
  when the cached `rp_status` is zero.
- `cstate->status == nfserr_replay_cache` (set by `nfsd4_sequence()`):
  jumps to `out` at once, skipping encode, `op_release` and both `fh_put()`
  calls.
- There is no nfserr_dropit in this tree; `RQ_USEDEFERRAL` is cleared in
  `nfs4svc_decode_compoundargs()` and again in `nfsd4_proc_compound()`, so a
  compound is not deferred once decoding has started.

**Operation flags**

- `OP_MODIFIES_SOMETHING`: does not cache anything. It makes the loop call
  `op_rsize_bop` (unchecked for NULL) and `nfsd4_check_resp_size()` before
  the handler, and makes `warn_on_nonidempotent_op()` complain if the reply
  is later truncated.
- `OP_CACHEME`: selects the xid-based DRC, not the session slot.
  `nfsd4_decode_compound()` sets `ntli_cachetype` in
  `struct nfsd_thread_local_info` to `RC_REPLBUFF` if any op has the flag,
  and forces `RC_NOCACHE` when the minor version is non-zero.
- Session slot caching: decided by the client's `cachethis` in
  `nfsd4_sequence()` (`NFSD4_SLOT_CACHETHIS`), by no flag in
  `enum nfsd4_op_flags`.
- `OP_NONTRIVIAL_ERROR_ENCODE`: `nfsd4_encode_operation()` calls the encoder
  although `op->status` is set. In `nfsd4_ops` it is on LOCK, LOCKT, SETATTR
  and SETCLIENTID.
- `ALLOWED_WITHOUT_FH` does not imply `ALLOWED_ON_ABSENT_FS`: with a current
  filehandle on a migrated export, an op with only `ALLOWED_WITHOUT_FH` gets
  `nfserr_moved`.
- **Potentially unsafe usage**: `ALLOWED_WITHOUT_FH` on an op whose handler
  uses `cstate->current_fh`.
  - Unsafe: when the handler dereferences `fh_dentry` or `fh_export`
    without a test; the loop lets it run with both NULL.
  - Safe: the handler tests `fh_dentry` first, as `nfsd4_reclaim_complete()`
    does.
  - Safe: the handler replaces the filehandle, as `nfsd4_putrootfh()` does
    with `fh_put()` and `exp_pseudoroot()`.
- **Unsafe usage**: `OP_NONTRIVIAL_ERROR_ENCODE` with an encoder that
  encodes result fields without looking at its `nfserr` argument, or that
  returns `nfs_ok` when `nfserr` was set.
  - Unsafe: the encoder runs when the handler was skipped (decode error, no
    filehandle, size check), so result fields are unset; its return value
    replaces `op->status`.
  - Safe: switch on `nfserr` and return it, as `nfsd4_encode_lock()` and
    `nfsd4_encode_setattr()` do.

**Decoder and encoder conventions**

- Every entry of `nfsd4_dec_ops` returns `__be32`; none returns bool.
  `nfsd4_decode_compound()`, its caller `nfs4svc_decode_compoundargs()` and
  the xdrgen functions return bool.
- `nfsd4_decode_compound()` returns false (`nfsd_dispatch()` then answers
  `rpc_garbage_args`) only when the tag, minor version, op count or an
  opnum cannot be read, the tag exceeds `NFSD4_MAX_TAGLEN`, or an
  allocation fails (`svcxdr_savemem()` of the tag, `vcalloc()` of
  `argp->ops`). A failing op decoder never makes it return false.
- `svcxdr_tmpalloc()` memory: freed by `nfsd4_release_compoundargs()` in
  `fs/nfsd/nfs4xdr.c`, the `pc_release` of COMPOUND. `svc_process()` calls
  it through `svc_release_rqst()` after `svc_send()`, and also when the
  request is dropped.
- `args->ops`, when not the inline `iops`: freed there with
  `kvfree_rcu_mightsleep()`, not `vfree()`.
- Encoder return value: `nfsd4_encode_operation()` stores it in
  `op->status`. The function returns void; the loop reads `op->status`
  afterwards.

**Large payloads in decoders**

- `nfsd4_write()` passes `wr_payload` to `nfsd_vfs_write()` in
  `fs/nfsd/vfs.c`, which calls `xdr_buf_to_bvec()` into `rqstp->rq_bvec`.
  There is no svc_fill_write_vector() in this tree.
- `nfsd4_decode_setxattr()`: `nfsd4_vbuf_from_vector()` copies into
  `svcxdr_tmpalloc()` memory only when the value is larger than the head of
  the subsegment; otherwise `setxa_buf` points into the receive buffer.
- `svcxdr_savemem()`: returns the `xdr_inline_decode()` pointer unchanged
  unless it is the stream's scratch buffer; names, opaques and the tag from
  it normally point into the receive buffer too.
- Lifetime: decoder output, in place or from `svcxdr_tmpalloc()`, may be
  used by the handler, the encoder and `op_release`, all of which run in the
  nfsd thread before `nfsd4_release_compoundargs()`.
- **Unsafe usage**: keeping a pointer the decoder produced in an object that
  outlives the RPC.
  - Safe: copy it into separately allocated memory before the handler
    returns, as `nfsd4_copy()` does for `cp_src` with `dup_copy_fields()`.

**Reply size checks**

- `op_rsize_bop` returns bytes, not words; the in-tree estimates other than
  `nfsd4_getattr_rsize()` include `op_encode_hdr_size` (opnum and status)
  and multiply by `sizeof(__be32)`.
- `nfsd4_check_resp_size()` knows no session limit of its own; it compares
  against `rq_res.buflen`. `nfsd4_sequence()` lowered that with
  `xdr_restrict_buflen()` to at most `maxresp_cached` or `maxresp_sz`, less
  `rq_auth_slack`.
- `nfsd4_sequence()` fails with `nfserr_rep_too_big` or
  `nfserr_rep_too_big_to_cache` when `xdr_restrict_buflen()` fails, before
  any later op runs.
- Encoder failure after the handler ran: `nfsd4_encode_operation()` turns
  `nfserr_resource` into `nfserr_rep_too_big_to_cache` or
  `nfserr_rep_too_big` when there is a session, truncates the op to opnum
  plus status, and the compound ends. The operation's effect is not undone.
- `op_rsize_bop` is called from `nfsd4_max_reply()` during decode, before
  any handler has run, and also for an op whose decoder failed. The in-tree
  estimates use only decoded arguments and `nfsd4_max_payload()`.
- **Unsafe usage**: an `OP_MODIFIES_SOMETHING` op whose encoder can emit
  more bytes than `op_rsize_bop` returned.
  - Safe: a fixed worst case that covers every field the encoder writes, as
    `nfsd4_write_rsize()` does for `nfsd4_encode_write()`.

**Client-supplied lengths and counts**

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

**Generated XDR code**

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

**Adding an NFSv4 operation**

- Run time, per unset member; there is no NULL test that turns a missing
  entry into `nfserr_notsupp` or `nfserr_op_illegal`:

| Unset | Result |
|---|---|
| `nfsd4_dec_ops` entry | called unchecked in `nfsd4_decode_compound()` |
| `op_rsize_bop` | `BUG_ON()` in `nfsd4_max_reply()` during decode |
| `op_func` | called unchecked in the loop |
| `nfsd4_enc_ops` entry | `BUG_ON()` in `nfsd4_encode_operation()` |

- `nfsd4_enc_ops` `BUG_ON()`: reached only when the encoder would run, that
  is on success or with `OP_NONTRIVIAL_ERROR_ENCODE`.
- `nfsd4_max_reply()` exempts only `OP_ILLEGAL` and `nfserr_notsupp`. The
  all-zero `nfsd4_ops` entries in this tree (for example `OP_DELEGPURGE`)
  survive because their decoder is `nfsd4_decode_notsupp()`.
- Array bounds: `nfsd4_encode_operation()` tests the opnum against
  `ARRAY_SIZE()` of `nfsd4_enc_ops`; the decode and dispatch paths make no
  such test. `nfsd4_dec_ops` and `nfsd4_ops` are indexed by any opnum that
  `nfsd4_opnum_in_range()` accepts, so raising `LAST_NFS42_OP` without an
  entry at that index in both reads past the array.
- The three tables are shared by all minor versions.
  `nfsd4_opnum_in_range()` has only an upper bound per minor version, so a
  v4.0 opnum is accepted in v4.1 and v4.2. A version restriction goes in
  the decoder, as in `nfsd4_decode_release_lockowner()`.
- `op->u` in the inline `iops` is not zeroed between requests: `pc_argzero`
  of COMPOUND stops at `iops` in `struct nfsd4_compoundargs`.
- **Unsafe usage**: an `op_release`, encoder or `op_rsize_bop` that reads a
  field of `op->u` the decoder does not set on every return path.
  - Safe: the decoder clears the struct first; `nfsd4_decode_read()` does
    `memset()` and `nfsd4_read_release()` tests `rd_nf`.
- **Unsafe usage**: a decoder that takes memory or a reference outside
  `argp->to_free` and relies on `op_release` to drop it.
  - Unsafe: `op_release` runs only for ops the loop reached; an op decoded
    after the one that ended the compound never gets it.
  - Safe: allocate with `svcxdr_tmpalloc()`, which
    `nfsd4_release_compoundargs()` frees for every decoded op, as
    `nfsd4_decode_acl()` does.

## File handles, exports and credentials

**In-core file handle**

- `fh_no_wcc`, `fh_no_atomic_attr`, `fh_use_wgather`, `fh_64bit_cookies`: set
  in `nfsd_set_fh_dentry()`, by a switch on `fh_maxsize`; the last three are
  set nowhere else, so only on the first `fh_verify()` of a wire handle.
- `fh_compose()`: of those four it sets only `fh_no_wcc`, copied from `ref_fh`
  or false; the others keep what the structure held before.
- `fh_put()` does not reset `fh_handle`, `fh_maxsize`, `fh_flags`,
  `fh_no_atomic_attr`, `fh_use_wgather` or `fh_64bit_cookies`.
- `fh_put()` calls `fh_clear_pre_post_attrs()` only when `fh_dentry` was set.
- NFSv2/v3 `pc_release` callbacks put only the handles in `rq_resp`; there is
  no nfsd_release_fhandle here.
- Handlers that verify the argument handle in place put it themselves before
  returning, for example `nfsd3_proc_fsstat()`, `nfsd3_proc_fsinfo()`,
  `nfsd3_proc_pathconf()` and `nfsd_proc_statfs()`.
- FSSTAT, FSINFO and PATHCONF in `nfsd_procedures3` have no `pc_release`; a
  handle left referenced by their handler is never put.
- `nfsd4_proc_compound()`: calls `fh_put()` on `current_fh` and `save_fh`
  directly after the operation loop, not through
  `nfsd4_cstate_clear_replay()`.
- `nfsd4_release_compoundargs()`, the COMPOUND `pc_release`: frees decode
  buffers only, puts no handle.

**Copying a file handle**

- `fh_copy()` in `fs/nfsd/nfsfh.h`: plain structure assignment; takes no
  reference and does not put the destination.
- `fh_copy()`: its `WARN_ON()` tests `src->fh_dentry`, not the destination.
- `fh_dup2()`: `static inline` in `fs/nfsd/nfs4proc.c`; code in other files
  cannot call it.
- `fh_dup2()` with a source whose `fh_dentry` is NULL: allowed; `dget(NULL)`
  does nothing and `exp_get()` is guarded.
- `fh_dup2()` copies the whole structure after taking the references,
  including `fh_want_write`, `fh_pre_saved`, `fh_post_saved` and `fh_flags`.
- Saved pre/post attributes on the source are harmless for `current_fh`:
  `nfsd4_proc_compound()` calls `fh_clear_pre_post_attrs()` before each
  handler it runs.
- **Unsafe usage**: `fh_copy()` from a source whose `fh_dentry` is set; both
  structures then share one dentry and one export reference, and two
  `fh_put()` calls drop them twice.
  - Safe: copy the decoded handle first, then `fh_verify()` the destination,
    as `nfsd3_proc_getattr()` does.
- **Unsafe usage**: `fh_copy()` into a destination that holds references;
  they leak.
  - Safe: a destination in `rq_resp`, which `svc_generic_init_request()`
    zeroes before the procedure runs, as in `nfsd3_proc_getattr()`.
- **Unsafe usage**: `fh_dup2()` from a source with `fh_want_write` set; both
  handles then call `mnt_drop_write()` in `fh_drop_write()`.
  - Safe: `nfsd4_create()`; `nfsd_create()` takes write access on
    `current_fh`, the destination, which `fh_put()` inside `fh_dup2()`
    drops, and `resfh`, from `fh_init()` and `fh_compose()`, has
    `fh_want_write` clear.

**File handle verification steps**

- First call, `nfsd_set_fh_dentry()`, in order:
  1. `fh_size == 0` gives `nfserr_nofilehandle`; bad version, auth type,
     fsid type or length gives `nfserr_badhandle`.
  2. `rqst_exp_find()`: `-ENOENT` gives `nfserr_stale`, other errors go
     through `nfserrno()`.
  3. Credentials: with `NFSEXP_NOSUBTREECHECK` it only raises the nfsd
     capabilities on a copy of the current credentials; otherwise it calls
     `nfsd_setuser_and_check_port()`.
  4. `FILEID_ROOT` takes the export root; otherwise the MAC check (see
     "Signed file handles") and then `exportfs_decode_fh_raw()`.
  5. An NFSv2 or NFSv3 handle on an `NFSEXP_V4ROOT` export:
     `nfserr_badhandle`.
- Every call then runs, in `__fh_verify()`: `check_pseudo_root()`,
  `nfsd_setuser_and_check_port()`, `nfsd_mode_check()`,
  `check_xprtsec_policy()`, `check_security_flavor()`, `nfsd_permission()`.
- Later calls skip only `nfsd_set_fh_dentry()`.
- `__fh_verify()` does not call `check_nfsd_access()`; it calls the two
  helpers so that each can be skipped separately.
- `nfsd_mode_check()` on a mismatch, first match wins:

| Object | Requested | Status |
|---|---|---|
| symlink | `S_IFDIR` | `nfserr_symlink_not_dir` |
| symlink | other | `nfserr_symlink` |
| any other | `S_IFDIR` | `nfserr_notdir` |
| directory | other | `nfserr_isdir` |
| any other | other | `nfserr_wrong_type` |

- `nfsd_mode_check()` with a matching `S_IFDIR`: still `nfserr_notdir` when
  `d_can_lookup()` fails.
- `nfserr_inval` is not returned by `nfsd_mode_check()`; it is what
  `nfsd3_map_status()` makes of `nfserr_wrong_type` and `nfserr_symlink`.
- The type argument is `umode_t`; no negative value is handled, whatever the
  comment above `fh_verify()` says.
- `NFSD_MAY_NLM`: always skips `check_xprtsec_policy()`; the flavor check
  still runs.
- `NFSD_MAY_NLM` on an export with `NFSEXP_NOAUTHNLM`: also skips
  `check_security_flavor()` and `nfsd_permission()`.
- `fh_verify_local()` (`rqstp` is NULL): skips the port check, both security
  checks and `svc_xprt_set_valid()`; `nfsd_setuser()`, the type check and
  `nfsd_permission()` still run.

**NFSD_MAY access flags**

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

**Export security policy**

- Both transport security and flavor are checked on both paths.
- `__fh_verify()`: calls `check_xprtsec_policy()` then
  `check_security_flavor()` on every call that has an `rqstp`, except where
  `NFSD_MAY_NLM` skips them (see "File handle verification steps").
- `check_nfsd_access()` has exactly three callers, all passing
  `may_bypass_gss` false: `nfsd_lookup()`, `nfsd4_encode_entry4_fattr()` and
  `nfsd4_proc_compound()`.
- `nfsd_cross_mnt()`, `nfsd4_lookup()` and `nfsd4_do_lookupp()` do not call it
  themselves; there is no nfsd4_encode_dirent here.
- `nfsd4_proc_compound()` calls it only after a successful operation flagged
  `OP_IS_PUTFH_LIKE`, when another operation follows and that one lacks
  `OP_HANDLES_WRONGSEC`; see `need_wrongsec_check()`.
- `compose_entry_fh()` (NFSv3 READDIRPLUS) needs no check: it returns no
  handle for a `d_mountpoint()` entry.
- `check_xprtsec_policy()` failure: `nfserr_wrongsec`, the same as the flavor
  check.
- Transport policy: `may_bypass_gss` and `nfsd4_spo_must_allow()` do not
  relax it; only `NFSD_MAY_NLM` and a NULL `rqstp` skip it.
- Flavor check: passes early for `exp->ex_client == rqstp->rq_gssclient` and
  for `nfsd4_spo_must_allow()`; the bypass flags are in "NFSD_MAY access
  flags".

**Request credentials**

- `nfsd_setuser()` installs the credentials itself with `override_creds()`;
  callers do nothing more.
- `nfsd_setuser()` has one caller, `nfsd_setuser_and_check_port()`; it runs
  on every `__fh_verify()` that gets past `check_pseudo_root()` and the port
  check, and once more inside `nfsd_set_fh_dentry()` for an export without
  `NFSEXP_NOSUBTREECHECK`.
- Squash flags come from `nfsexp_flags()`: the flags of the `ex_flavors`
  entry that matches `cr_flavor`, else `ex_flags`.
- `NFSEXP_ROOTSQUASH`: supplementary groups are kept; only entries equal to
  `GLOBAL_ROOT_GID` are replaced by `ex_anon_gid`.
- `NFSEXP_ALLSQUASH`: the only case that replaces the request's group list
  with an empty one.
- Capabilities: `CAP_NFSD_SET` in `include/linux/capability.h` is dropped
  from `cap_effective` for a non-root fsuid, and raised, limited by
  `cap_permitted`, for root.
- Before the first `fh_verify()` of a request: nothing at dispatch sets or
  clears credentials, so the thread carries the override left by an earlier
  request, or its own if there was none.
- `nfsd_set_fh_dentry()` with `NFSEXP_NOSUBTREECHECK`: decodes with the
  credentials the thread carries at that point plus raised nfsd
  capabilities.

**User namespace for ids**

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

**Signed file handles**

- This tree signs file handles.
- Enabled per export by `NFSEXP_SIGN_FH` (`sign_fh` in `expflags[]`), plus a
  per-net key in `fh_key` of `struct nfsd_net`.
- Key: 16 bytes in netlink attribute `NFSD_A_SERVER_FH_KEY`, stored by
  `nfsd_nl_fh_key_set()`; `nfsd_nl_threads_set_doit()` returns `-EBUSY` if
  threads are running. Nothing else sets it.
- MAC: 8-byte little-endian SipHash of all handle bytes before it, appended
  by `fh_append_mac()`.
- Signing sites: `_fh_update()`, reached from `fh_compose()` and
  `fh_update()`, and `setup_notify_fhandle()` in `fs/nfsd/nfs4xdr.c`.
- Check: `fh_verify_mac()` in `nfsd_set_fh_dentry()`, after the export lookup
  and credential setup, before `exportfs_decode_fh_raw()`, which is given the
  length without the MAC.
- Exempt: handles with `fh_fileid_type` `FILEID_ROOT`, in both directions,
  and handles of exports without the flag.
- The flag is read from `ex_flags`; it is not in `NFSEXP_SECINFO_FLAGS`, so it
  cannot vary by flavor.
- No key, or no room below `fh_maxsize`: `fh_append_mac()` fails,
  `_fh_update()` sets `FILEID_INVALID`, and `fh_compose()` or `fh_update()`
  returns `nfserr_stale`.
- No key at verification: every signed handle fails.

**Bad file handle signature**

- `nfserr_stale`, from `nfsd_set_fh_dentry()`, also when the key is not set.
- `trace_nfsd_set_fh_dentry_badmac()` records it; `__fh_verify()` counts it
  with `nfsd_stats_fh_stale_inc()`.
- `nfsd4_putfh()` with `no_verify` set (`CONFIG_NFSD_V4_2_INTER_SSC`): turns
  any `nfserr_stale`, a bad signature included, into success with
  `NFSD4_FH_FOREIGN`.

**Re-exporting NFS**

- `nfs_export_ops` in `fs/nfs/export.c` sets `EXPORT_OP_NOWCC`,
  `EXPORT_OP_NOSUBTREECHK`, `EXPORT_OP_CLOSE_BEFORE_UNLINK`,
  `EXPORT_OP_REMOTE_FS`, `EXPORT_OP_NOATOMIC_ATTR`,
  `EXPORT_OP_FLUSH_ON_CLOSE` and `EXPORT_OP_NOLOCKS`.
- There is no EXPORT_OP_ASYNC_LOCK here.
- Tests that are easy to miss:

| Flag | Tested in |
|---|---|
| `EXPORT_OP_REMOTE_FS` | `nfsd_vfs_write()`: no `PF_LOCAL_THROTTLE` |
| `EXPORT_OP_CLOSE_BEFORE_UNLINK` | `nfsd_unlink()` and `nfsd_rename()` |
| `EXPORT_OP_FLUSH_ON_CLOSE` | `nfsd_file_check_writeback()` |
| `EXPORT_OP_NOSUBTREECHK` | `check_export()`: `-EINVAL` without `NFSEXP_NOSUBTREECHECK` |
| `EXPORT_OP_NOLOCKS` | through `exportfs_cannot_lock()` |

- `exportfs_cannot_lock()`: `nfsd4_lock()` and `nfsd4_locku()` return
  `nfserr_notsupp`; `nfs4_set_delegation()` returns `-EOPNOTSUPP`; lockd
  tests it through `nlmsvc_file_cannot_lock()`. `nlm_fopen()` does not.
- fsid: `check_export()` returns `-EINVAL` unless the filesystem has
  `FS_REQUIRES_DEV`, or the export has `NFSEXP_FSID` or a uuid; `nfs_fs_type`
  and `nfs4_fs_type` lack `FS_REQUIRES_DEV`.
- `Documentation/filesystems/nfs/reexport.rst` lists exactly four
  limitations:
  - `fsid=` is required and `crossmnt` does not propagate it; each NFS mount
    below needs its own export and `fsid=`.
  - Reboot recovery does not work; clients cannot get locks or delegations at
    all, attempts fail with operation not supported.
  - Handle size: an X-byte original handle becomes X+22 bytes rounded up to a
    multiple of four, and must fit 32, 64 or 128 bytes.
  - OPEN deny bits are not passed to the original server.
- The document does not list WCC, cache coherency or unlink of open files.

**Unverified and composed handles**

- After a failed `fh_verify()`: `fh_dentry` and `fh_export` may be set, from
  an earlier call or because a check after the lookup failed; test the
  status, not the pointers.
- `fh_compose()` makes no permission, flavor or credential check; a later
  `fh_verify()` on the handle skips only the lookup.
- `nfsd_lookup()` across a mount: runs `check_nfsd_access()` on the new
  export but not `nfsd_setuser()`; credentials stay those of the parent's
  export until the next `fh_verify()`.
- `fh_compose()` failure: returns `nfserr_stale` after its own `fh_put()`, so
  the handle holds no references.
- `nfsd_lookup()` on a negative dentry: composes the result handle, then
  returns `nfserr_noent`; the handle still needs `fh_put()`.
- `fh_verify()` on an empty handle (`fh_size` 0, no dentry): returns
  `nfserr_nofilehandle`; a handler that reaches the handle only through
  `fh_verify()` needs no test of its own.
- `nfsd4_proc_compound()` gates only `current_fh`; `save_fh` may be empty for
  any operation.
- There is no `fh_verify()` in `nfs4_check_fh()`; it only compares
  `fh_handle` with the stateid's `fi_fhandle`.
- **Potentially unsafe usage**: reading `fh_dentry` or `fh_export` of
  `save_fh`.
  - Unsafe: with no test and no `fh_verify()`; no SAVEFH may have run, or it
    saved a foreign handle.
  - Safe: after testing `save_fh.fh_dentry`, as `nfsd4_restorefh()` and
    `nfsd4_verify_copy()` do.
  - Safe: through `fh_verify()`, as `nfsd4_rename()` does by passing it to
    `nfsd_rename()`.
  - Safe: reading only `fh_handle`, as `nfsd4_setup_inter_ssc()` does.

## Stateids

**State objects**

- `s2s_cp_stateids` in `struct nfsd_net`: holds only copy-notify stateids,
  `struct nfs4_cpntf_state`; its `copy_stateid_t` is not a
  `struct nfs4_stid`.
- `sc_cp_list`: a list head in the parent stid for its copy-notify states
  (linked through `cp_list`), not a list the stid sits on.
- `find_stateid_locked()`: matches `si_opaque.so_id` only; the clientid half,
  `so_clid`, is compared by `set_client()` in `nfsd4_lookup_stateid()`.
- Type names: `SC_TYPE_COPY` is a fifth bit beside the four known ones;
  `NFS4_COPYNOTIFY_STID` is still the `cs_type` of a `copy_stateid_t`.

**Stateid type and status**

| Bit | Kinds that carry it | Set by |
|---|---|---|
| `SC_STATUS_CLOSED` | open, lock, delegation, layout | `nfsd4_close()`, `release_open_stateid()`; `unhash_lock_stateid()`; `unhash_delegation_locked()`, `nfsd4_free_stateid()`; `nfsd4_return_file_layouts()` |
| `SC_STATUS_REVOKED` | delegation of a v4.1+ client | `unhash_delegation_locked()` called from `nfs4_laundromat()` |
| `SC_STATUS_ADMIN_REVOKED` | open, lock, delegation, layout | `revoke_ol_stid()`, `revoke_one_stid()`, `unhash_delegation_locked()` |
| `SC_STATUS_FREEABLE` | delegation | `revoke_delegation()`, when it puts the delegation on `cl_revoked` |
| `SC_STATUS_FREED` | delegation | `nfsd4_free_stateid()` (revoked), `nfsd4_drop_revoked_stid()` (admin-revoked) |

- `SC_TYPE_COPY` stateid: no code sets a status bit on it.
- `sc_type` for open, lock, delegation and layout: set in the same `cl_lock`
  hold that hashes the stateid, in `init_open_stateid()`,
  `init_lock_stateid()`, `hash_delegation_locked()` and
  `nfsd4_alloc_layout_stateid()`.
- `SC_TYPE_COPY`: set by `nfs4_alloc_copy_stid()` straight after
  `nfs4_alloc_stid()` returns, without `cl_lock`.
- Lookup by id in between: `find_stateid_locked()` returns NULL while
  `sc_type` is 0, so `nfsd4_lookup_stateid()`, `nfsd4_validate_stateid()`
  and `nfsd4_free_stateid()` all give `nfserr_bad_stateid` with no test of
  their own.
- Walk of `cl_stateids` in between (`find_one_sb_stid()`, `states_show()`):
  sees the entry. `nfs4_alloc_stid()` fills `sc_client`, `sc_free`,
  `sc_stateid` and `sc_count` after it drops `cl_lock`, and `sc_file` is set
  later still.
- **Potentially unsafe usage**: reading a field of a stid found by walking
  `cl_stateids`.
  - Unsafe: dereferencing a pointer field such as `sc_file` before testing
    `sc_type`; the entry may still be untyped with the pointer NULL.
  - Safe: under `cl_lock`, test `sc_type` against a type mask and
    `sc_status == 0` first, as `find_one_sb_stid()` does before it reads
    `sc_file`; `move_to_close_lru()` sets `sc_file` to NULL on a closed open
    stateid.
  - Safe: testing a bit of `sc_status` first, as
    `nfs40_clean_admin_revoked()` does; `nfs4_alloc_stid()` zero-allocates
    and every writer of `sc_status` acts on a typed stid.

**Finding a stateid**

- `nfsd4_lookup_stateid()`: adds `SC_STATUS_ADMIN_REVOKED` and
  `SC_STATUS_FREEABLE` to the status mask on every call.
- `SC_STATUS_REVOKED`: added to the mask when the type mask has
  `SC_TYPE_DELEG`.
- `SC_STATUS_REVOKED` found, caller's mask lacked it: `nfserr_deleg_revoked`.
  This test comes first.
- `SC_STATUS_ADMIN_REVOKED` found: `nfserr_admin_revoked`, even when the
  caller's mask had the bit; such a stateid is never returned.
- `SC_STATUS_FREEABLE`: maps to no error; it is let through so that a revoked
  delegation on `cl_revoked` reaches the two tests above.
- `SC_STATUS_CLOSED` and `SC_STATUS_FREED`: never forced; a stateid with
  either gives `nfserr_bad_stateid` unless the caller's mask has the bit.
- In-tree masks: `nfsd4_close()` passes `SC_STATUS_CLOSED`, through
  `nfs4_preprocess_seqid_op()`; `nfsd4_delegreturn()` passes
  `SC_STATUS_REVOKED`; every other caller passes 0.
- Never returned: a stateid for which `ZERO_STATEID()`, `ONE_STATEID()` or
  `CLOSE_STATEID()` is true; a stid of type `SC_TYPE_COPY`.
- `so_clid` differs from `cstate->clp`: `set_client()` fails, giving
  `nfserr_bad_stateid` with a session and `nfserr_stale_stateid` without.
- v4.0 client not found by `set_client()`: `nfserr_expired`, passed through.
- `find_stateid_by_type()`: takes the reference with `refcount_inc()` under
  `cl_lock`; it does not call `refcount_inc_not_zero()`.

**Stateid checks before I/O**

- `find_cpntf_state()`: tried by `nfs4_preprocess_stateid_op()` whenever
  `nfsd4_lookup_stateid()` returns `nfserr_bad_stateid`, whatever the caller
  passed. The stid it yields is the parent of the copy-notify state, looked
  up in the client named by `cp_p_clid`, which need not be `cstate->clp`.
- `nfsd4_stid_check_stateid_generation()`: also rechecks `sc_status` through
  `nfsd4_verify_open_stid()`, so a stateid closed or revoked since the lookup
  fails here.
- `*cstid`: receives the referenced stid on success when `cstid` is non-NULL;
  otherwise `nfs4_preprocess_stateid_op()` puts the reference itself.
- Special stateid: `*cstid` is not written. The caller initialises it to NULL
  and tests it; `nfsd4_copy_notify()` returns `nfserr_bad_stateid` for NULL.
- `*nfp`: filled by `nfs4_check_file()` only when `nfp` is non-NULL; set to
  NULL on entry.
- There is no nfs4_validate_open_stateid() in this tree, and
  `nfsd4_release_lockowner()` takes no stateid.

| Operation | Lookup | Checked for it | Checks itself |
|---|---|---|---|
| CLOSE, OPEN_CONFIRM, LOCKU, LOCK with a lock stateid | `nfs4_preprocess_seqid_op()` | seqid, `st_mutex` and status, generation, `nfs4_check_fh()` | open mode and confirmation are not checked by the helper |
| OPEN_DOWNGRADE, LOCK with an open stateid | `nfs4_preprocess_confirmed_seqid_op()` | the above plus `NFS4_OO_CONFIRMED` | `nfsd4_lock()` calls `nfs4_check_openmode()` and `same_clid()` |
| DELEGRETURN | `nfsd4_lookup_stateid()` | type and status | `fh_verify()`, `nfsd4_stid_check_stateid_generation()`, `nfs4_check_fh()` |
| OPEN claiming a delegation | `find_deleg_stateid()` in `nfs4_check_deleg()` | type; any status bit other than `SC_STATUS_REVOKED` fails the lookup | `SC_STATUS_REVOKED`, `nfs4_check_delegmode()`; no generation check; `nfsd4_process_open2()` compares `sc_file` |
| TEST_STATEID, FREE_STATEID | `find_stateid_locked()` under `cl_lock` | nothing | status and type; generation in TEST_STATEID, and in FREE_STATEID only for an open or lock stateid without `SC_STATUS_ADMIN_REVOKED` |
| LAYOUTGET, LAYOUTCOMMIT, LAYOUTRETURN | `nfsd4_preprocess_layout_stateid()` | `fh_match()`, takes `ls_mutex`; for an existing layout stateid also the layout type, and rejects only a generation newer than the server's | no further stateid check |
| OFFLOAD_STATUS, OFFLOAD_CANCEL | `find_async_copy_locked()` | whole-stateid match on `async_copies` | OFFLOAD_CANCEL falls back to `manage_cpntf_state()` |

- TEST_STATEID and FREE_STATEID: take no reference on the stid, except that
  `nfsd4_free_stateid()` takes one on a lock stateid before it drops
  `cl_lock`; they match on `so_id` alone in the session's client.

**Stateid references**

| Kind | Count after creation | Holders |
|---|---|---|
| open, lock, delegation | 2: `nfs4_alloc_stid()` sets 1, the hash function does `refcount_inc()` | the creating operation puts one at its end; the caller for which the unhash helper returned true puts the other |
| layout | 1 | the creating operation; then one per `struct nfs4_layout` on `ls_layouts` |
| copy offload | 1 | the copy itself; `nfs4_put_copy()` puts it when the copy's own `refcount` reaches 0 |

- Stid allocated but never hashed: one put frees it, as
  `nfsd4_cleanup_open_state()` does for `op_stp`.
- `st_openstp`: a bare pointer; a lock stateid holds no reference on its open
  stateid.
- Layout lists `ls_perclnt` and `ls_perfile`, and the layout lease: hold no
  reference. `nfs4_put_stid()` does not unlink them;
  `nfsd4_free_layout_stateid()` does, after the count reached 0, so a list
  member can have a count of 0.
- v4.0 open stateid after CLOSE: the hash reference becomes the
  `oo_last_closed_stid` reference in `move_to_close_lru()`.
- `nfs4_put_stid()` on the final put, in order:
  1. `refcount_dec_and_lock()` takes `cl_lock`
  2. `idr_remove()` from `cl_stateids`
  3. decrement `cl_admin_revoked` if `SC_STATUS_ADMIN_REVOKED` is set
  4. read `sc_export`
  5. `nfs4_free_cpntf_statelist()`, which takes `s2s_cp_lock`
  6. unlock `cl_lock`
  7. `sc_free()`
  8. `exp_put()` on the export, if any
  9. `put_nfs4_file()` on the `sc_file` read at entry, if any
- `put_ol_stateid_locked()`: a second final-put path for open and lock
  stateids, entered with `cl_lock` held. It does steps 2 and 3, then queues
  the stid; `free_ol_stateid_reaplist()` does steps 7 to 9 after the unlock.
- `nfsd4_run_cb_notify()`: gives up, queueing nothing, when its
  `refcount_inc_not_zero()` fails.
- **Unsafe usage**: calling `nfs4_put_stid()` with `cl_lock` held; the final
  put takes `cl_lock`.
  - Safe: `put_ol_stateid_locked()` under the lock, then
    `free_ol_stateid_reaplist()` after unlocking, as `release_openowner()`
    does.
- **Potentially unsafe usage**: `refcount_inc()` on `sc_count` of a stid
  reached through a pointer or list.
  - Unsafe: when nothing held at that point keeps the count above 0; the
    final put may already have run and `sc_free()` follows.
  - Safe: under `cl_lock` on an entry just found in `cl_stateids`, as
    `find_stateid_by_type()` does; both final-put paths remove the entry
    under `cl_lock`.
  - Safe: under `fi_lock` on a member of `fi_stateids`, as
    `nfsd4_find_existing_open()` does; `unhash_ol_stateid()` unlinks
    `st_perfile` under `fi_lock` before the hash reference is put.
  - Safe: under `cl_lock` on a member of `st_locks` of a hashed open
    stateid, as `find_lock_stateid()` does; `unhash_lock_stateid()` unlinks
    `st_locks` under `cl_lock` before the hash reference is put.
  - Safe: under `deleg_lock` on a hashed delegation, as `nfs4_laundromat()`
    does; `unhash_delegation_locked()` asserts that lock.
  - Safe: under `flc_lock` on the `flc_owner` of a delegation lease still on
    `flc_lease`, as `nfsd4_deleg_getattr_conflict()` does;
    `destroy_unhashed_deleg()` removes the lease before its put.
  - Safe: under `ls_lock` with `ls_layouts` not empty, as
    `nfsd4_recall_file_layout()` does; `nfsd4_insert_layout()` takes one
    reference per entry.
  - Safe: when the caller already holds a reference, as `revoke_one_stid()`
    does with the one from `find_one_sb_stid()`.
  - Safe: `refcount_inc_not_zero()` under `ls_lock` where the pointer comes
    from the layout lease, as `nfsd4_layout_lm_breaker_timedout()` does;
    `nfsd4_free_layout_stateid()` removes the lease before it frees.

**Locks for stateid status**

- There is no nfs4_unhash_stid() in this tree.

| Kind | Bit | Lock held by the writer |
|---|---|---|
| open, lock | every bit | `cl_lock` |
| open | `SC_STATUS_CLOSED` in `nfsd4_close()` | `st_mutex` as well |
| open, lock | `SC_STATUS_ADMIN_REVOKED` | `st_mutex` as well |
| delegation | the bit passed to `unhash_delegation_locked()` | `deleg_lock`, not `cl_lock` |
| delegation | `SC_STATUS_FREEABLE`, `SC_STATUS_FREED`, and `SC_STATUS_CLOSED` set by `nfsd4_free_stateid()` | `cl_lock`, not `deleg_lock` |
| layout | `SC_STATUS_CLOSED` | `ls_lock` |
| layout | `SC_STATUS_ADMIN_REVOKED` | `cl_lock` |

- `release_open_stateid()`: sets `SC_STATUS_CLOSED` under `cl_lock` only; it
  does not take `st_mutex`.
- Admin revocation: the test and set are in `revoke_ol_stid()` and
  `revoke_one_stid()`, not in `nfsd4_revoke_states()`.
- Teardown of open and lock stateids: gated on the return value of
  `unhash_ol_stateid()`, `unhash_lock_stateid()` or `unhash_open_stateid()`
  under `cl_lock`, not on `sc_status`. A true return is what entitles the
  caller to put the hash reference, as in `release_lock_stateid()`.
- `SC_STATUS_FREEABLE` against `SC_STATUS_FREED`: `revoke_delegation()` and
  `nfsd4_free_stateid()` each test the other's bit under `cl_lock`; whichever
  runs second leaves the delegation off `cl_revoked`.
- **Unsafe usage**: testing `sc_status`, dropping the lock, then setting a
  bit or releasing access on the strength of the test.
  - Safe: test `sc_status == 0` and set the bit in one `cl_lock` hold with
    `st_mutex` held throughout, as `revoke_ol_stid()` does; it asserts
    `st_mutex`.
  - Safe: for an open or lock stateid, put the hash reference only when the
    unhash helper returned true under `cl_lock`, as `release_lock_stateid()`
    does.
  - Safe: for a delegation, act only when `unhash_delegation_locked()`
    returned true under `deleg_lock`, as `destroy_delegation()` does.
- **Unsafe usage**: setting `SC_STATUS_ADMIN_REVOKED` without incrementing
  `cl_admin_revoked`; the final put decrements it when the bit is set.
  - Safe: increment in the same critical section, as `revoke_ol_stid()` does.

**Stateid mutex after lookup**

- `nfsd4_lock_ol_stateid()`: tests `sc_status` only, through
  `nfsd4_verify_open_stid()`. It tests neither `sc_type` nor whether the
  stateid is still hashed.
- Return values: `nfserr_admin_revoked` for `SC_STATUS_ADMIN_REVOKED`,
  `nfserr_deleg_revoked` for `SC_STATUS_REVOKED`, `nfserr_bad_stateid` for
  `SC_STATUS_CLOSED`, tested in that order.
- Open stateid unhashed by `release_openowner()`: no `SC_STATUS_CLOSED` is
  set on it, so `nfsd4_lock_ol_stateid()` returns `nfs_ok`.
- Lock stateid: `unhash_lock_stateid()` sets `SC_STATUS_CLOSED` under
  `cl_lock` without that stateid's `st_mutex` (from
  `release_open_stateid_locks()` when the open stateid is closed), so holding
  `st_mutex` does not freeze a lock stateid's status.
- Lookup that allowed `SC_STATUS_CLOSED`, as `nfsd4_close()` does:
  `nfsd4_lock_ol_stateid()` still returns `nfserr_bad_stateid`, so
  `nfs4_seqid_op_checks()` never returns `nfs_ok` for a closed stateid; the
  mask only lets a v4.0 replay reach `nfserr_replay_me` from
  `nfsd4_check_seqid()`, before the mutex is taken.
- Lockdep subclass: `nfsd4_lock_ol_stateid()` always uses
  `LOCK_STATEID_MUTEX`, for open and lock stateids alike. A newly allocated
  stateid is locked with `OPEN_STATEID_MUTEX` in both `init_open_stateid()`
  and `init_lock_stateid()`.
- **Potentially unsafe usage**: linking state to a stateid once
  `nfsd4_lock_ol_stateid()` has returned `nfs_ok`.
  - Unsafe: when hashing was not rechecked; the stateid may be unhashed with
    `sc_status` still 0, and its `st_locks` is then not valid.
  - Safe: recheck `nfs4_ol_stateid_unhashed()` under `cl_lock` before
    linking, as `init_lock_stateid()` does for the open stateid.

## Clients and state locks

**Client creation and destruction**

- `force_expire_client()`: zeroes `cl_time` itself under `client_lock`, while
  the client is still hashed, then sleeps until `cl_rpc_users` is 0. It does
  not call `mark_client_expired_locked()`, so nothing refuses it.
- `client_has_state()`: also counts `cl_sessions` and running async copies
  (`nfsd4_has_active_async_copies()`).
- `client_has_state()` as a refusal: on its own only in
  `nfsd4_destroy_clientid()`. `nfsd4_exchange_id()` and
  `nfsd4_setclientid_confirm()` refuse with `nfserr_clid_inuse` only when the
  credentials also differ; `nfsd4_setclientid()` also when
  `clp_used_exchangeid()` is true.
- EXCHANGE_ID with a new verifier and the same credentials: leaves the
  confirmed client alone, with or without state. The CREATE_SESSION that
  confirms the new record replaces it with no `client_has_state()` test;
  `mark_client_expired_locked()` can still refuse.
- `__destroy_client()` precondition: the client is already unhashed; both
  callers run `unhash_client()` first.
- `__destroy_client()` order:
  1. under `deleg_lock` of `struct nfsd_net`: `unhash_delegation_locked()` on
     every entry of `cl_delegations`;
  2. `destroy_unhashed_deleg()` on each, lock dropped;
  3. `nfs4_put_stid()` on every entry of `cl_revoked`;
  4. `release_openowner()` on every entry of `cl_openowners`;
  5. each lockowner left in `cl_ownerstr_hashtbl`:
     `unhash_lockowner_locked()`, `remove_blocked_locks()`,
     `nfs4_put_stateowner()`;
  6. `nfsd4_return_all_client_layouts()`;
  7. `nfsd4_shutdown_copy()`;
  8. `nfsd4_shutdown_callback()`;
  9. put `cl_cb_conn.cb_xprt`, decrement `nn->nfs4_client_count` and the
     courtesy count; under `CONFIG_NFSD_SCSILAYOUT`, `xa_destroy()` of
     `cl_dev_fences`;
  10. `free_client()`: frees sessions, removes the nfsdfs directory, calls
      `nfsd4_put_client()`;
  11. `wake_up_all(&expiry_wq)`.
- `nfsd4_async_copy_reaper()`: called from `nfs4_laundromat()`, not from
  `__destroy_client()`.

**Client reference counters**

| Counter | Prevents | Who waits |
|---|---|---|
| `cl_rpc_users` | `mark_client_expired_locked()` succeeding | `force_expire_client()`, on `expiry_wq` |
| `cl_ref` in `cl_nfsdfs` | `__free_client()` freeing the memory; nothing else | nobody |
| `cl_cb_inflight` | `__destroy_client()` getting past `nfsd4_shutdown_callback()` | `nfsd4_shutdown_callback()` |

- `cl_rpc_users`: does not hold off `force_expire_client()` once its wait has
  passed. Server-side walks that pin test `is_client_expired()` under
  `client_lock` first, as `nfsd4_revoke_states()` does.
- `cl_ref` helpers: `nfsd4_put_client()` puts. There is no get helper that
  takes a `struct nfs4_client`; takers call `kref_get()` on
  `cl_nfsdfs.cl_ref`, or `get_nfsdfs_client()` on an nfsdfs inode.
  drop_client(), get_nfs4_client() and put_nfs4_client() are not in this tree.
- `cl_cb_inflight`: raised by `nfsd4_run_cb()` for every callback; for one
  that was queued and has `cb_ops`, dropped by `nfsd41_destroy_cb()` after
  the `release` op returns.
- A callback: gets `cl_cb_inflight` from `nfsd4_run_cb()` and holds a
  reference that keeps alive the object that embeds its
  `struct nfsd4_callback`, for example `sc_count` for CB_RECALL. `cl_cb_null`
  holds none.
- A callback also takes `cl_ref` by hand in two cases: CB_RECALL_ANY in
  `deleg_reaper()`, and CB_OFFLOAD in `nfsd4_send_cb_offload()`. The `release`
  op puts it.
- A running async copy: holds no client counter. `cp_clp` is a bare pointer.
- What keeps `cp_clp` valid: the copy is on `clp->async_copies`, and
  `nfsd4_shutdown_copy()` joins its kthread before `free_client()`.
- **Potentially unsafe usage**: taking a copy off `clp->async_copies` and
  then using its client.
  - Unsafe: when nothing pins the client, because `nfsd4_shutdown_copy()` can
    no longer find the copy and `__destroy_client()` proceeds; the last
    `nfs4_put_copy()` then locks `cl_lock` of a freed client in
    `nfs4_put_stid()`.
  - Safe: take `cl_ref` under `async_lock` before unlinking, as
    `nfsd4_cancel_copy_by_sb()` does; `__free_client()` runs only at the last
    `nfsd4_put_client()`.
  - Safe: from the client's own compound, as `nfsd4_offload_cancel()` does;
    `cstate->clp` holds `cl_rpc_users`.
  - Safe: inside `__destroy_client()`, as `nfsd4_shutdown_copy()` does before
    `free_client()`.

**Client put helpers**

- `put_client_no_renew()` and `put_client_no_renew_locked()`: defined in
  `fs/nfsd/nfs4state.c`, next to `put_client_renew()`.
- Difference: on the last put of a client that is not expired,
  `put_client_renew()` calls `renew_client_locked()`; `put_client_no_renew()`
  does nothing.
- On an expired client: the last put of either form only wakes `expiry_wq`.
- Callers of the no-renew form: work the server starts itself.
  `nfsd4_revoke_states()`, `nfsd4_revoke_export_states()`,
  `nfs40_clean_admin_revoked()`, and three loops in `nfs4_laundromat()`
  (timed-out delegations, `close_lru`, blocked locks).
- The matching pin: `atomic_inc()` of `cl_rpc_users` under `client_lock`,
  after `is_client_expired()` returned false. Not `get_client_locked()`, which
  sets `NFSD4_ACTIVE`.
- **Unsafe usage**: pinning a client for server-initiated work with
  `get_client_locked()`, or releasing that pin with `put_client_renew()`.
  - Unsafe: `get_client_locked()` makes a courtesy client `NFSD4_ACTIVE`; the
    last `put_client_renew()` does the same and renews the lease.
  - Safe: bare `atomic_inc()` then `put_client_no_renew()`, as
    `nfs4_laundromat()` does.
  - Safe: `put_client_renew()` at the end of the client's own request, as
    `nfsd4_sequence_done()` does.

**Courtesy clients**

- `NFSD4_ACTIVE` to `NFSD4_COURTESY`: `nfs4_get_client_reaplist()` does it for
  every client whose lease has run out and whose `cl_rpc_users` is 0. No other
  condition.
- What happens next in the same pass: the client is expired at once if it has
  no state, if `nfs4_anylock_blockers()` is true, or if the client count is
  at `nn->nfs4_max_clients` and fewer than `NFSD_CLIENT_MAX_TRIM_PER_RUN`
  were reaped. Otherwise it stays `NFSD4_COURTESY`.
- `nfs4_anylock_blockers()`: also true when `cl_delegs_in_recall` is
  non-zero.
- `NFSD4_EXPIRABLE`: tested before the lease test; the client goes straight
  to `mark_client_expired_locked()`, past the state and blocker tests.
- `NFSD_COURTESY_CLIENT_TIMEOUT`: defined in `fs/nfsd/nfsd.h`, used nowhere.
  No code limits how long a client stays `NFSD4_COURTESY`.
- Back to `NFSD4_ACTIVE`: `get_client_locked()` and `renew_client_locked()`
  both set it, from either state, while `cl_time` is not 0.
- Who reaches those two, for example: SEQUENCE through
  `nfsd4_get_session_locked()`; any clientid lookup through
  `find_client_in_id_table()`; the last `put_client_renew()`.
- `nfsd4_client_record_check()`: does not change `cl_state`.
- Counter: `nn->nfsd_courtesy_clients`. nfs4_courtesy_client_count is not in
  this tree.
- Lock manager callbacks: `nfsd4_lm_lock_expirable()` and
  `nfsd4_lm_expire_lock()`, in `nfsd_posix_mng_ops`.
- Callers of the lock manager callbacks: `posix_lock_inode()` and
  `posix_test_lock()` in `fs/locks.c`.
- `nfsd4_lm_lock_expirable()`: runs under `flc_lock`, so it must not sleep.
  `nfsd4_lm_expire_lock()` runs after `flc_lock` is dropped and flushes
  `laundry_wq`.

**Administrative revocation**

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

**Cleanup after administrative revocation**

- Async copies, superblock path: `nfsd4_cancel_copy_by_sb()` in
  `fs/nfsd/nfs4proc.c` runs before `nfsd4_revoke_states()`. It matches on
  `nf_src` or `nf_dst`, stops the kthread and puts both files.
- A cancelled copy that was still running: its CB_OFFLOAD is still sent, with
  `nfserr_admin_revoked`. `cp_clp` is left set for that reason.
- Async copies, export path: `nfsd_nl_unlock_export_doit()` cancels none.
- Cached files, superblock path: no file-cache purge. Only the references
  that the revoked state and the cancelled copies hold are put.
- Cached files, export path: `nfsd_file_close_export()` in
  `fs/nfsd/filecache.c` runs before the revoke. It closes `NFSD_FILE_GC`
  entries on the same superblock and under the export's dentry.
- `drop_stid_export()`: revocation also puts `sc_export`, so the export is
  not pinned until the stateid is freed.
- NFSv4.0, on next use: `nfsd40_drop_revoked_stid()` frees the stateid as
  `nfserr_admin_revoked` is returned. The next use gets `nfserr_bad_stateid`.
- NFSv4.0, never used again: `nfs40_clean_admin_revoked()` runs from
  `nfs4_laundromat()` one lease period after `nn->nfs40_last_revoke`.
- `cl_admin_revoked`: decremented by the last put, in `nfs4_put_stid()` or
  `put_ol_stateid_locked()`, not by `nfs40_clean_admin_revoked()`.

**Resource limits**

| Object | Bound | Counter | At the bound |
|---|---|---|---|
| Clients | `nn->nfs4_max_clients` | `nn->nfs4_client_count` | no error; see below |
| Delegations | `max_delegations` | `num_delegations` | no delegation granted |
| Running async copies | `sp_nrthreads` of the request's pool | `nn->pending_async_copies` | `nfserr_jukebox` |
| Slots per session | `NFSD_MAX_SLOTS_PER_SESSION` | `se_fchannel.maxreqs` | fewer slots granted |
| Ops per compound, v4.0 | `NFSD_MAX_OPS_PER_COMPOUND` | none | `nfserr_resource` |
| Ops per compound, sessions | `se_fchannel.maxops` | none | `nfserr_too_many_ops` |

- Clients: `alloc_client()` never refuses on the count. At the bound, and
  only if `nn->nfsd_courtesy_clients` is non-zero, it kicks the laundromat.
- `nfserr_jukebox` from EXCHANGE_ID or SETCLIENTID: never means that a limit
  was hit; for example `create_client()` failed to allocate.
- nfsd_drc_max_mem, nfsd_drc_mem_used and nfs4_courtesy_client_count are not
  in this tree. There is no session memory budget.
- Slots: `alloc_session()` needs only slot 0; CREATE_SESSION returns
  `nfserr_jukebox` if that fails. `nfsd4_sequence()` grows the table, capped
  by `svc_serv_maxthreads()`. `nfsd_slot_shrinker_scan()` lowers
  `se_target_maxslots`; `nfsd4_sequence()` then frees the slots.
- Delegation test: in `__alloc_init_deleg()`, so directory delegations from
  `alloc_init_dir_deleg()` count too. Both counters are global, not per net
  namespace.
- `nfs4_alloc_stid()`: returns NULL on failure; each caller picks the status.

**Lock nesting**

- `deleg_lock`: a spinlock in `struct nfsd_net`. `fs/nfsd` has no lock named
  `state_lock`.
- `se_lock`: a spinlock in `struct nfsd4_session`, taken only in
  `fs/nfsd/nfs4callback.c`. It nests with none of the listed locks.

| Outer | Inner | Function |
|---|---|---|
| `deleg_lock` | `client_lock` | `nfs4_laundromat()` |
| `deleg_lock` | `cl_lock`, then `fi_lock` | `nfs4_set_delegation()`, `nfsd_get_dir_deleg()` |
| `client_lock` | `async_lock` | `nfsd4_async_copy_reaper()`, `nfsd4_cancel_copy_by_sb()` |
| `client_lock` | `cl_lock`, then `flc_lock` | `nfs4_get_client_reaplist()` via `nfs4_anylock_blockers()` |
| `cl_lock` | `sc_lock` | `nfsd4_free_stateid()` |
| `cl_lock` | `s2s_cp_lock` | `nfs4_put_stid()` |
| `cl_lock` | `ls_lock` | `nfsd4_return_all_client_layouts()` |
| `cl_lock` | `fi_lock`, then `flc_lock` | `nfsd4_release_lockowner()` via `check_for_locks()` |
| `fi_lock` | `ls_lock` | `nfsd4_insert_layout()` |
| `ls_lock` | `sc_lock` | `nfsd4_insert_layout()` |
| `flc_lock` | `ls_lock` | `nfsd4_layout_lm_break()` |
| `st_mutex` | `cl_lock`, then `fi_lock` | `nfsd4_close()` via `nfsd4_close_open_stateid()` |
| `st_mutex` | `sc_lock` | `nfsd4_open_downgrade()` |
| `st_mutex` | `s2s_cp_lock` | `nfsd4_close()` via `nfsd4_close_open_stateid()` |
| `st_mutex` | `flc_lock` | `nfsd4_lock()` via `vfs_lock_file()` |
| `ls_mutex` | `fi_lock`, then `ls_lock`, then `sc_lock` | `nfsd4_layoutget()` via `nfsd4_insert_layout()` |
| `nfsd_mutex` | `client_lock` | `nfsd4_revoke_states()` |
| `nfsd_mutex` | `st_mutex`, `deleg_lock` | `nfsd4_revoke_states()` via `revoke_one_stid()` |
| `nfsd_mutex` | `nfsd_ssc_lock` | `nfsd_destroy_serv()` via `nfsd4_ssc_shutdown_umount()` |

- `deleg_lock` is outside `client_lock`, `cl_lock` and `fi_lock`; no code
  takes it while holding one of them.
- `nfs4_put_stid()`: its `refcount_dec_and_lock()` is on `cl_lock`, not
  `fi_lock`.
- Two `st_mutex` at once: only in `init_open_stateid()` and
  `init_lock_stateid()`. The outer one belongs to the new stateid, which is
  not hashed yet.
- `nfsd4_lock()`: unlocks the open stateid's `st_mutex` before it locks the
  lock stateid's.
- `nfsd4_process_open2()`: unlocks `st_mutex` before
  `nfs4_open_delegation()`, so `deleg_lock` is not taken under it there.
- `nfsd_break_deleg_cb()` and `nfsd4_lm_lock_expirable()`: run under
  `flc_lock` and take none of the listed locks.
- `nfsd_ssc_lock`: initialised and taken only under
  `CONFIG_NFSD_V4_2_INTER_SSC`; dropped around every `mntput()`.

## Delegations

**Delegation kinds**

- `dl_type`: holds `OPEN_DELEGATE_READ`, `OPEN_DELEGATE_WRITE`,
  `OPEN_DELEGATE_READ_ATTRS_DELEG` or `OPEN_DELEGATE_WRITE_ATTRS_DELEG`; it
  never holds a NONE value.
- Classifiers: `deleg_is_read()`, `deleg_is_write()` and
  `deleg_attrs_deleg()` in `fs/nfsd/state.h`; the first two count the
  ATTRS_DELEG forms.
- Directory delegation: a fifth kind, made by `alloc_init_dir_deleg()` with
  `dl_type` `NFS4_OPEN_DELEGATE_READ`, so `deleg_is_read()` is true for it.
- `dl_type` does not tell a directory delegation from a file read
  delegation; the directory one has `sc_free` set to `nfs4_free_dir_deleg()`.
- `dl_cb_fattr` and `dl_cb_notify`: share an anonymous union; touching the
  wrong one for the kind corrupts the other.

| Member | Valid for | Easy to miss |
|---|---|---|
| `dl_cb_fattr` | file delegations | `alloc_init_deleg()` initialises it for read kinds too; `nfsd4_deleg_getattr_conflict()` uses it only for an `F_WRLCK` lease |
| `ncf_initial_cinfo` | write-access grant | set in `nfs4_open_delegation()` |
| `ncf_cur_fsize` | write kinds | set in `nfsd4_deleg_getattr_conflict()`, not at grant |
| `dl_cb_notify`, `dl_notify_mask`, `dl_child_attrs`, `dl_dir_attrs` | directory delegations | `dl_cb_notify` is set up in `alloc_init_dir_deleg()`, the other three in `nfsd_get_dir_deleg()` |
| `dl_atime`, `dl_mtime`, `dl_ctime` | read only when `deleg_attrs_deleg()` | set only at grant; SETATTR never updates them |
| `dl_written` | `OPEN_DELEGATE_WRITE_ATTRS_DELEG` | `nfsd4_file_mark_deleg_written()` tests that exact value |
| `dl_setattr` | ATTRS_DELEG kinds | set by `vet_deleg_attrs()` when a `FATTR4_WORD2_TIME_DELEG_MODIFY` update is accepted |
| `dl_clnt_odstate` | file delegations | NULL for a directory delegation, and for a file delegation whose open stateid has no `st_clnt_odstate` |

- `dl_atime`, `dl_mtime`, `dl_ctime`: a write-access grant sets all three;
  `nfsd4_vet_deleg_time()` takes them as its `orig` baseline.
- `dl_written` and `dl_setattr`: read only by
  `nfsd4_finalize_deleg_timestamps()`, and only when the file has
  `FMODE_NOCMTIME`.

**Granting a delegation**

- Locks at hashing: `nn->deleg_lock`, then `clp->cl_lock`, then
  `fp->fi_lock`; `hash_delegation_locked()` asserts all three.
- Early check: `nfs4_delegation_exists()` and the `fi_delegees` update run
  under `nn->deleg_lock` and `fp->fi_lock` only.
- Callback channel: `nfsd4_cb_channel_good()` accepts `NFSD4_CB_UP`, and also
  `NFSD4_CB_UNKNOWN` when `cl_minorversion` is not 0.
- `NFS4_OPEN_CLAIM_PREVIOUS` in `nfs4_open_delegation()`: always goes on to
  `nfs4_set_delegation()`; the grace, callback-up and `NFS4_OO_CONFIRMED`
  tests are not applied to it.
- `op_delegate_type` from the request: `nfs4_open_delegation()` never reads
  it.
- `NFS4_OPEN_CLAIM_NULL` and `NFS4_OPEN_CLAIM_FH`: an open with
  `NFS4_SHARE_ACCESS_WRITE` from a `cl_minorversion` 0 client gets no
  delegation.
- Kind: `OPEN_DELEGATE_WRITE` when `op_share_access` has
  `NFS4_SHARE_ACCESS_WRITE` and `find_writeable_file()` finds a file;
  otherwise `OPEN_DELEGATE_READ` when it has `NFS4_SHARE_ACCESS_READ`.
- ATTRS_DELEG forms: `OPEN_DELEGATE_WRITE_ATTRS_DELEG` or
  `OPEN_DELEGATE_READ_ATTRS_DELEG` replaces the plain kind in `dl_type` when
  `nfsd4_want_deleg_timestamps()` is true.
- `nfsd4_want_deleg_timestamps()`: needs `nfsd_delegts_enabled` and
  `OPEN4_SHARE_ACCESS_WANT_DELEG_TIMESTAMPS`.
- Want flags: `OPEN4_SHARE_ACCESS_WANT_READ_DELEG` and
  `OPEN4_SHARE_ACCESS_WANT_WRITE_DELEG` do not choose the kind.
- Other openers: there is no credential test and no "sole opener" test;
  `nfsd4_check_conflicting_opens()` rejects only other writers, for both
  kinds.
- Other leases: `generic_add_lease()` returns `-EAGAIN` for `F_WRLCK` when
  any other lease is on the file, so a write delegation is not granted while
  another client's delegation is on the file.
- Lease call: `kernel_setlease()`, not `vfs_setlease()`.
- Global switch: there is no NFSD delegation-enable variable;
  `leases_enable` in `fs/locks.c`, when 0, makes `generic_add_lease()`
  return `-EINVAL`.

**Delegation references**

| Reference | Taken | Dropped |
|---|---|---|
| Recall | `nfsd_break_one_deleg()`, with `refcount_inc_not_zero()` | `nfsd4_cb_recall_release()` |
| CB_GETATTR | `nfs4_cb_getattr()`, bare `refcount_inc()` | `nfsd4_cb_getattr_release()` |
| CB_NOTIFY | `nfsd4_run_cb_notify()`, with `refcount_inc_not_zero()` | `nfsd4_cb_notify_release()` |
| GETATTR conflict | `nfsd4_deleg_getattr_conflict()`, under `flc_lock` | itself, or its caller in `fs/nfsd/nfs4xdr.c` when `*pdp` is set |
| On `cl_revoked` | caller of `revoke_delegation()`, before unhash | `nfsd4_free_stateid()`, `nfsd4_drop_revoked_stid()`, `__destroy_client()` |

- `revoke_delegation()`: takes no reference; it consumes one through
  `destroy_unhashed_deleg()`, and the one left keeps the delegation on
  `cl_revoked`.
- Callers of `revoke_delegation()`: `nfs4_laundromat()` and
  `revoke_one_stid()` each do `refcount_inc()` before
  `unhash_delegation_locked()`.
- `sc_file`: the `struct nfs4_file` reference from `__alloc_init_deleg()`
  is put by the final `nfs4_put_stid()`, not by `destroy_unhashed_deleg()`.
- `fi_deleg_file`: counted separately by `fi_delegees`; `put_deleg_file()`
  releases the `struct nfsd_file` when it reaches 0.
- Lease owner: `nfs4_alloc_init_lease()` stores the delegation in
  `flc_owner` with no reference.
- **Unsafe usage**: dropping the in-force reference while the lease is
  still on `flc_lease`.
  - Unsafe: `nfsd_break_deleg_cb()` and `nfsd4_deleg_getattr_conflict()`
    dereference `flc_owner` under `flc_lock` with nothing else pinning it.
  - Safe: remove the lease, then put, as `destroy_unhashed_deleg()` does
    with `nfs4_unlock_deleg_lease()` before `nfs4_put_stid()`.

**Lease break callback**

- Callers: besides `__break_lease()`, `nfsd_handle_dir_event()` and
  `nfsd_recall_all_dir_delegs()` call `nfsd_break_deleg_cb()` directly,
  under an `flc_lock` they took themselves.
- `__break_lease()`: also holds `file_rwsem` for read around the callback.
- `nfsd_break_deleg_cb()`: sets `fl_break_time` to 0 and
  `fi_had_conflict`, bumps `cl_delegs_in_recall`, and returns false so the
  lease stays.
- `nfsd_break_one_deleg()`: takes the recall reference with
  `refcount_inc_not_zero()`, not a bare `refcount_inc()`.
- Count already zero: `nfsd_break_one_deleg()` clears
  `NFSD4_CALLBACK_RUNNING` and queues nothing.
- Why not a bare increment: `nfsd4_cb_notify_prepare()` and
  `nfsd4_cb_notify_done()` call `nfsd_break_one_deleg()` with no `flc_lock`
  held.
- Queue failure: undone with `refcount_dec()`, not `nfs4_put_stid()`.
- `nfsd4_cb_recall_prepare()`: the lock it takes is `nn->deleg_lock`.
- Courtesy client: `try_to_expire_client()` moves `cl_state` from
  `NFSD4_COURTESY` to `NFSD4_EXPIRABLE`; there is no
  NFSD4_CLIENT_EXPIRABLE flag.
- Courtesy client recall: the callback still calls
  `nfsd_break_one_deleg()`, after `try_to_expire_client()` has made the
  state `NFSD4_EXPIRABLE`; `nfsd4_run_cb_work()` decides whether CB_RECALL
  is sent.
- `nfsd4_run_cb_work()`: gives up before `prepare` when `cl_cb_client` is
  NULL or `cl_state` is `NFSD4_COURTESY`, so the delegation is not put on
  `del_recall_lru`.
- Expiry: `nfs4_get_client_reaplist()` takes an `NFSD4_EXPIRABLE` client
  only if `mark_client_expired_locked()` finds `cl_rpc_users` at 0.
- After expiry: `__destroy_client()` unhashes the client's delegations with
  `SC_STATUS_CLOSED` and removes the leases.

**Breaker's own delegation**

- `nfsd_breaker_owns_lease()`: tests
  `fl->fl_lmops != &nfsd_lease_mng_ops` itself, before it dereferences
  `flc_owner`.
- Why it tests: `should_notify_deleg()` calls it directly for each lease on
  a directory, not through `fl_lmops`.
- NULL breaker: `nfsd_breaker_owns_lease()` has no test for a NULL
  `ntli_lease_breaker`; its only other test is `nfsd_v4client()` on
  `nfsd_current_rqst()`.
- `nfsd4_deleg_getattr_conflict()`: compares `dp->dl_recall.cb_clp` with
  `*(ntli->ntli_lease_breaker)`.
- Other clients: `nfsd_open_break_lease()` adds `O_NONBLOCK`; the
  `-EWOULDBLOCK` becomes `nfserr_jukebox` through `nfserrno()`.
- Directory events: `should_notify_deleg()` uses the same test, so a client
  gets no CB_NOTIFY for its own change.

**Recall timeout and revocation**

- Lock: `nfs4_laundromat()` walks `nn->del_recall_lru` under
  `nn->deleg_lock`.
- What the laundromat can see: only delegations that
  `nfsd4_cb_recall_prepare()` put on `del_recall_lru`.
- Expired client: the laundromat skips the entry when `is_client_expired()`
  is true.
- Pinning: the laundromat bumps `cl_rpc_users` directly, not through
  `get_client_locked()`, until `revoke_delegation()` returns.
- `revoke_delegation()`: has no branch on `cl_minorversion`; only its
  `WARN_ON_ONCE()` reads it.
- NFSv4.0 from the laundromat: `unhash_delegation_locked()` stores
  `SC_STATUS_CLOSED` in place of `SC_STATUS_REVOKED`.
- NFSv4.0 in `revoke_delegation()`: the delegation is still added to
  `cl_revoked` with `SC_STATUS_FREEABLE`; the lease is removed and one
  reference remains.
- NFSv4.0 lookup: `find_stateid_by_type()` rejects `SC_STATUS_CLOSED`, so
  the client gets `nfserr_bad_stateid`.
- NFSv4.0 free: that delegation is freed when `__destroy_client()` drains
  `cl_revoked`.
- Comment in `fs/nfsd/state.h`: "destroyed (v4.0)" is not what
  `revoke_delegation()` does.
- NFSv4.0 admin revoke: the status stays `SC_STATUS_ADMIN_REVOKED`;
  `nfsd40_drop_revoked_stid()` drops it at first use,
  `nfs40_clean_admin_revoked()` later.
- `SC_STATUS_FREED`: already set when `nfsd4_free_stateid()` or
  `nfsd4_drop_revoked_stid()` ran first; `revoke_delegation()` then does not
  list the delegation.
- `SC_STATUS_FREEABLE`: tells `nfsd4_free_stateid()` that the delegation is
  on `cl_revoked` and must be unlinked.
- DELEGRETURN of a revoked stateid: `nfsd4_stid_check_stateid_generation()`
  returns `nfserr_deleg_revoked` before `destroy_delegation()` is reached;
  the delegation stays on `cl_revoked`.
- Final free: the last `nfs4_put_stid()` calls `sc_free`, which is
  `nfs4_free_deleg()`, or `nfs4_free_dir_deleg()` for a directory
  delegation.

**Directory delegations**

- Implemented, with CB_NOTIFY: `nfsd4_get_dir_delegation()` calls
  `nfsd_get_dir_deleg()`; `nfsd4_cb_notify_ops` sends the notifications.
- Notifications granted: `requested & SUPPORTED_NOTIFY_MASK`, and only if
  the client set `NOTIFY4_GFLAG_EXTEND` and not `NOTIFY4_CFLAG_ORDER`;
  otherwise the delegation is recall-only.
- Lease: `F_RDLCK` with `FL_DELEG`, plus one `FL_IGN_DIR_CREATE`,
  `FL_IGN_DIR_DELETE` or `FL_IGN_DIR_RENAME` flag per granted add, remove or
  rename notification, from `nfsd_notify_to_ignore()`.
- Hashing: same three locks and same `nfs4_delegation_exists()` test as a
  file delegation.
- Two routes carry a directory change to NFSD:

| Route | Used for | Path |
|---|---|---|
| Lease break | event types not granted | `try_break_deleg()` (`include/linux/filelock.h`), called from `fs/namei.c` with a `LEASE_BREAK_DIR_CREATE`, `LEASE_BREAK_DIR_DELETE` or `LEASE_BREAK_DIR_RENAME` flag, then `nfsd_break_deleg_cb()` |
| fsnotify | event types granted | `nfsd_dir_fsnotify_handle_event()` in `fs/nfsd/filecache.c`, then `nfsd_handle_dir_event()` |

- `ignore_dir_deleg_break()` in `fs/locks.c`: makes `__break_lease()` skip
  a lease whose `FL_IGN_DIR_CREATE`, `FL_IGN_DIR_DELETE` or
  `FL_IGN_DIR_RENAME` flag matches the event.
- `nfsd_fsnotify_recalc_mask()`: rebuilds the fsnotify mark's mask from
  `inode_lease_ignore_mask()`; call it after adding or removing a directory
  lease.
- Without `CONFIG_NFSD_V4`: `nfsd_dir_fsnotify_handle_event()` is a stub
  that returns 0.
- `nfsd_handle_dir_event()`: turns `FS_MOVED_FROM` into `FS_DELETE` and
  `FS_MOVED_TO` into `FS_CREATE`.
- `nfsd_handle_dir_event()`: drops `FS_RENAME` when the dentry's parent is
  not this directory.
- `should_notify_deleg()`: skips a lease that lacks the `FL_IGN_DIR_CREATE`,
  `FL_IGN_DIR_DELETE` or `FL_IGN_DIR_RENAME` flag for the event.
- Queue: `ncn_evt[]` in `struct nfsd4_cb_notify`, one per delegation,
  `NOTIFY4_EVENT_QUEUE_SIZE` (3) entries, under `ncn_lock`.
- Send limit: `nfsd4_cb_notify_prepare()` keeps one slot back when
  `NOTIFY4_CHANGE_DIR_ATTRS` was granted, so 2 events fit.
- Encode buffer: `NOTIFY4_PAGE_ARRAY_SIZE` (1) page.
- In flight: `nfsd4_cb_notify_release()` requeues the callback if events
  arrived meanwhile and `sc_status` is 0.
- A recall replaces the notification when:
  - `alloc_nfsd_notify_event()` fails: `nfsd_recall_all_dir_delegs()`
    recalls every NFSD lease on the directory.
  - `ncn_evt_cnt` has reached `NOTIFY4_EVENT_QUEUE_SIZE` in
    `nfsd_handle_dir_event()`.
  - `nfsd4_cb_notify_prepare()` finds more events than its limit, finds
    `fi_deleg_file` NULL, or fails to encode an event or the directory
    attributes.
  - `nfsd4_cb_notify_done()`, with `sc_status` 0, sees `ncn_encode_err`, or
    a `tk_status` other than 0 or `-NFS4ERR_DELAY`.

## Sessions and callbacks

**Forward channel slots**

- Lock: `client_lock` in `struct nfsd_net` covers lookup, seqid check, growth,
  shrink and `reduce_session_slots()` (which uses `spin_trylock()`); `se_lock`
  is for backchannel slots only.
- Without `client_lock`: `nfsd4_sequence_done()` stores the reply and clears
  `NFSD4_SLOT_INUSE`; from `nfsd4_sequence()` until that clear, only the flag
  keeps other requests off the slot.
- Growth trigger: `seq->slotid == se_fchannel.maxreqs - 1` on an accepted new
  request, and `se_target_maxslots >= se_fchannel.maxreqs`.
- Growth cap: min of `NFSD_MAX_SLOTS_PER_SESSION` and
  `svc_serv_maxthreads(rqstp->rq_server)`; growth also raises
  `se_target_maxslots`.
- Shrinker: `nfsd_slot_shrinker_count()` and `nfsd_slot_shrinker_scan()`; there
  are no nfsd_slot_count() or nfsd_slot_scan(). The scan lowers
  `se_target_maxslots` by at most one per session visited and frees no slot
  itself.
- `free_session_slots()` from `nfsd4_sequence()` needs all of: target below
  `maxreqs`; `slot->sl_generation == se_slot_gen`; `seq->maxslots` at or below
  target; `seq->slotid` below target; `nfsd4_slots_inuse()` false from target
  up.
- Reply field: `target_maxslots` in `struct nfsd4_sequence`, encoded minus one
  by `nfsd4_encode_sequence()`; `sr_target_highest_slotid` is a field of the
  NFS client's `struct nfs4_sequence_res`, not of nfsd.
- Freed slot: only `sl_seqid` survives, as `xa_mk_value()` at the same index.
  Cached reply, `sl_cred` and `NFSD4_SLOT_INITIALIZED` are lost.
- **Potentially unsafe usage**: dereferencing `xa_load()` on `se_slots`.
  - Unsafe: index at or above `se_fchannel.maxreqs`; the entry is NULL or a
    value entry, and `nfsd4_sequence()` has no NULL or `xa_is_value()` test
    after its `nfserr_badslot` check.
  - Safe: index below `maxreqs` under `client_lock`, as `nfsd4_slots_inuse()`
    does; on a hashed session `free_session_slots()` and the growth loop
    change `maxreqs` and the entries under that lock.
  - Safe: index equal to `maxreqs` read only through `xa_is_value()` and
    `xa_to_value()`, never dereferenced, as the growth loop in
    `nfsd4_sequence()` does.

**Slot sequence check**

- `NFSD4_SLOT_INUSE` is tested first in `check_slot_seqid()`: matching seqid
  gives `nfserr_jukebox`, every other seqid (next one included) gives
  `nfserr_seq_misordered`.

| Slot not in use, seqid is (first match wins) | Status |
|---|---|
| slot seqid + 1 | `nfs_ok` |
| 1, with `NFSD4_SLOT_REUSED` | `nfs_ok` |
| slot seqid | `nfserr_replay_cache` (internal) |
| other | `nfserr_seq_misordered` |

- Reused slot, seqid equal to the remembered one and not 1:
  `nfserr_replay_cache` turns into `nfserr_seq_misordered` in
  `nfsd4_sequence()`, because the new slot has no `NFSD4_SLOT_INITIALIZED`.
- `sl_seqid` update: in `nfsd4_sequence()`, only after
  `nfsd4_sequence_check_conn()` and `xdr_restrict_buflen()` also pass; a
  request failing either leaves the slot untouched.
- `NFSD4_SLOT_REUSED`: cleared at that same point.
- `nfsd4_create_session()` passes flags 0 and bumps `cl_cs_slot.sl_seqid`
  right after `nfs_ok`, before the credential checks; later errors are cached
  in the slot, and only the `nfserr_jukebox` path decrements it again.

**Replay from the slot cache**

- Cache decision: `NFSD4_SLOT_CACHETHIS` alone, from `seq->cachethis`; there is
  no nfsd4_cache_this() or nfsd4_is_solo_sequence().
- Nothing stored: `nfsd4_sequence_done()` touches no slot when
  `nfsd4_has_session()` is false (`cstate.slot` is NULL), and
  `nfsd4_store_cache_entry()` returns early when `resp->opcnt == 1` with
  non-zero `cstate.status`; in that second case `sl_seqid` stays advanced.
- Oversize reply: never truncated into the slot; with `cachethis` set
  `nfsd4_sequence()` limits the encode buffer to `maxresp_cached`, so the op
  fails with `nfserr_rep_too_big_to_cache`.
- `nfsd4_store_cache_entry()`: copies `buf->len - data_offset` bytes into
  `sl_data` with no bound check; it relies on that limit and on the size
  chosen in `nfsd4_alloc_slot()`.
- `replay_matches_cache()` fails when: cachethis differs from
  `NFSD4_SLOT_CACHETHIS`; `sl_opcnt < argp->opcnt` with zero `sl_status`;
  `sl_opcnt > argp->opcnt`; `same_creds()` false. No opcode or hash compare.
- Replay encode: `nfsd4_replay_cache_entry()` calls `nfsd4_encode_operation()`
  on `args->ops[0]`; there is no nfsd4_enc_sequence_replay().
- Solo SEQUENCE replay (`args->opcnt == 1`): returns the re-encoded SEQUENCE
  status, before `NFSD4_SLOT_CACHED` is looked at.

**Callback lifecycle**

- `prepare`: returns `bool`; false makes `nfsd4_run_cb_work()` call
  `nfsd41_destroy_cb()`: no RPC, no `done`, no requeue, `release` runs.
- `prepare`: runs in the workqueue, at most once per `nfsd4_run_cb()`; skipped
  on a requeue and not rerun on an RPC restart.
- `done`: returns `int`; 1 finished, 0 restart via
  `rpc_restart_call_prepare()` (never a requeue), other values `BUG()`.
- `done` not called, `release` still called: `prepare` false; no
  `cl_cb_client` or `NFSD4_COURTESY`; on 4.1+ when `nfsd4_cb_sequence_done()`
  returns false with neither a requeue nor an RPC restart, for example on
  `-ESERVERFAULT`.
- `release`: runs after `nfsd41_destroy_cb()` cleared
  `NFSD4_CALLBACK_RUNNING`, so the callback may be re-armed by then;
  `nfsd4_cb_notify_release()` relies on it to requeue itself.
- `cl_cb_null` has NULL `cb_ops`: no op is ever called for it.

| Bit | Set by | Cleared by |
|---|---|---|
| `NFSD4_CALLBACK_RUNNING` | caller, or `nfsd4_try_run_cb()` for it, before `nfsd4_run_cb()`; never for `cl_cb_null` | `nfsd41_destroy_cb()`; the caller when it queued nothing, as `nfsd_break_one_deleg()` does |
| `NFSD4_CALLBACK_WAKE` | queuer `nfs4_cb_getattr()` | only `nfsd4_init_cb()` |
| `NFSD4_CALLBACK_REQUEUE` | `nfsd4_requeue_cb()`; `nfsd4_run_cb_work()` on `rpc_call_async()` failure | `nfsd4_run_cb_work()` |

- `nfsd4_run_cb()`: never writes `cb_flags`, and reads it only in the
  `trace_nfsd_cb_queue()` tracepoint.
- `cb_work`: a `struct work_struct` set with `INIT_WORK()`; there is no
  nfsd4_queue_cb_delayed().
- Requeue: `nfsd4_cb_release()` calls `nfsd4_queue_cb()`, an undelayed
  `queue_work()` on the per-client `cl_callback_wq`.

**Callback channel state**

- Workqueue: per client, `cl_callback_wq` from `alloc_ordered_workqueue()` in
  `alloc_client()`; any callback's work item runs
  `nfsd4_process_cb_update()` when a flag is set, not only `cl_cb_null`.
- `cl_cb_session`: an `__rcu` pointer, set to NULL in `create_client()` and
  after that written with `rcu_assign_pointer()` from the workqueue only;
  sessions are freed with `kfree_rcu()` in `__free_session()`.
- **Unsafe usage**: reading `cl_cb_session` in RPC context without RCU, or
  using the session after `rcu_read_unlock()`; `cl_cb_inflight` does not pin
  the session.
  - Safe: `rcu_read_lock()`, `rcu_dereference()`, NULL test, as
    `nfsd41_cb_get_slot()` and `nfsd4_cb_sequence_done()` do.
  - Safe: `rcu_access_pointer()` for a NULL test only, as `nfsd4_cb_prepare()`
    does.
- `cl_cb_state`: not serialised; a plain `int` written by
  `nfsd4_mark_cb_state()` from nfsd threads, the workqueue and RPC context.
- `nfsd4_mark_cb_down()` and `nfsd4_mark_cb_fault()`: do nothing while
  `NFSD4_CLIENT_CB_UPDATE` is set.
- `NFSD4_CLIENT_CB_UPDATE`: set only in `nfsd4_probe_callback()`.
- `nfsd4_change_callback()`: sets no flag and queues nothing; its caller calls
  `nfsd4_probe_callback()`.
- `nfsd4_mark_cb_fault()`: asks for no rebuild; the state reaches the client
  as `SEQ4_STATUS_BACKCHANNEL_FAULT`.
- `NFSD4_CLIENT_CB_KILL`: `nfsd4_process_cb_update()` drops the RPC client,
  cred and xprt, then returns before clearing UPDATE or writing
  `cl_cb_session`.
- Backchannel slots: `se_cb_slot_avail` and `se_cb_highest_slot` in
  `struct nfsd4_session`, updated under `se_lock`; no cl_cb_slot_avail or
  cl_cb_seq_nr exists.

**Queueing a callback**

- `nfsd4_run_cb()`: takes only `cl_cb_inflight`; no client refcount, no
  `cl_rpc_users`, and there is no nfsd4_get_client().
- `cl_cb_inflight` dropped: at once when `queue_work()` fails; else in
  `nfsd41_destroy_cb()` after `release`; for a CB_NULL probe that is sent, in
  `nfsd4_cb_probe_release()`.
- Return false: `queue_work()` found `cb_work` pending;
  `NFSD4_CALLBACK_RUNNING` is not consulted.
- Before the call: `cb->cb_clp` must be valid; `nfsd4_run_cb()` dereferences
  it before it takes the inflight count.
- Before the call, for a callback with `cb_ops`: own
  `NFSD4_CALLBACK_RUNNING` by `test_and_set_bit()`, and hold whatever
  `release` drops. `nfsd4_try_run_cb()` does the `test_and_set_bit()` itself
  and queues nothing when the bit was set.
- **Potentially unsafe usage**: ignoring the return of `nfsd4_run_cb()`, or
  using `nfsd4_try_run_cb()`, which returns nothing.
  - Unsafe: a reference was taken for `release` and the bit may already be
    set or the work pending; nothing drops that reference.
  - Safe: caller won `NFSD4_CALLBACK_RUNNING`, which `nfsd41_destroy_cb()`
    clears only once the work is no longer pending, as `nfs4_cb_getattr()`
    does.
  - Safe: `cb_flags` is still as `nfsd4_init_cb()` left it, on a callback
    sent once, as in `nfsd4_send_cb_offload()` and `nfsd4_lm_notify()`.
  - Safe: `cl_cb_null` with no reference taken, as `nfsd4_probe_callback()`
    does.
- **Unsafe usage**: calling `nfsd4_init_cb()` on a callback that may be
  queued or in flight; it zeroes `cb_flags` and re-inits `cb_work`.
  - Safe: at send time on a callback never queued before, as
    `nfsd4_send_cb_offload()` does, once per copy.

| Callback | Caller | Queues with | Holds for `release` |
|---|---|---|---|
| CB_RECALL | `nfsd_break_one_deleg()` | `nfsd4_run_cb()` | `dl_stid.sc_count` via `refcount_inc_not_zero()` |
| CB_OFFLOAD | `nfsd4_send_cb_offload()` | `nfsd4_try_run_cb()` | `cl_nfsdfs.cl_ref` and copy `refcount` |
| CB_NOTIFY_LOCK | `nfsd4_lm_notify()` | `nfsd4_try_run_cb()` | nothing new; the list's `nbl_kref` |

- `nfsd4_send_cb_offload()`: takes `struct nfsd4_async_copy`, and sends
  nothing when `cp_clp` is NULL.
- `nfsd4_lm_notify()`: queues only if it unlinked the entry under
  `blocked_locks_lock`; `nfsd4_cb_notify_lock_release()` puts that reference
  with `free_blocked_lock()`.

## Grace period

**Ending grace**

- State: bits in `nn->flags`, an `unsigned long` in `struct nfsd_net`, named by
  `enum nfsd_net_flag` in `fs/nfsd/netns.h`.
- There are no fields grace_ended, grace_end_forced, in_grace,
  somebody_reclaimed, track_reclaim_completes or client_tracking_active, and no
  nfsd4_net_flags word.

| Bit | Meaning |
|---|---|
| `NFSD_NET_GRACE_ENDED` | end-of-grace work has been claimed; reads of `v4_end_grace` report it |
| `NFSD_NET_GRACE_END_FORCED` | an administrator asked for the end; first test in `clients_still_reclaiming()` |
| `NFSD_NET_SOMEBODY_RECLAIMED` | a reclaim succeeded in `nfsd4_open()` or `nfsd4_lock()` since the last `clients_still_reclaiming()` that reached it |
| `NFSD_NET_TRACK_RECLAIM_COMPLETES` | RECLAIM_COMPLETE counting is on; set only by `nfs4_cld_state_init()` |
| `NFSD_NET_IN_GRACE` | legacy recovery-directory tracker only, under `CONFIG_NFSD_LEGACY_CLIENT_TRACKING`; set in `nfsd4_init_recdir()`, cleared in `nfsd4_recdir_purge_old()`; read only by `nfsd4_create_clid_dir()` and `nfsd4_remove_clid_dir()` |

- `nfsd4_end_grace()` has three callers: `nfs4_laundromat()` on the
  workqueue, `inc_reclaim_complete()` in the nfsd thread handling
  RECLAIM_COMPLETE, and `nfs4_state_start_net()` on its `skip_grace` path;
  the laundromat can run concurrently with either of the others.
- `inc_reclaim_complete()`: calls `nfsd4_end_grace()` directly; it does not
  call `mod_delayed_work()`.
- `inc_reclaim_complete()`: counts a client only if
  `NFSD_NET_TRACK_RECLAIM_COMPLETES` is set and
  `nfsd4_find_reclaim_client()` finds its name.
- Trackers whose init does not call `nfs4_cld_state_init()`: neither the
  RECLAIM_COMPLETE early end nor the `skip_grace` path can happen.
- Once-only guarantee: `test_and_set_bit(NFSD_NET_GRACE_ENDED, &nn->flags)` at
  the top of `nfsd4_end_grace()`; no lock serialises the callers.
- "Once" is per server start: `nfs4_state_create_net()` clears
  `NFSD_NET_GRACE_ENDED` and `NFSD_NET_GRACE_END_FORCED`.
- **Potentially unsafe usage**: acting on a plain `test_bit()` of
  `NFSD_NET_GRACE_ENDED`.
  - Unsafe: when the code that follows does end-of-grace work; two callers can
    both see the bit clear and both run `->grace_done`, which in
    `nfsd4_cld_grace_done()` sends `Cld_GraceDone` and empties the reclaim
    table through `nfs4_release_reclaim()`.
  - Safe: when the test only decides whether to ask for the end, as in
    `nfsd4_force_end_grace()`; the work still goes through the
    `test_and_set_bit()` in `nfsd4_end_grace()`.
- `nfsd4_end_grace()`: does not call `nfsd4_client_tracking_exit()`; that is
  in `nfs4_state_shutdown_net()`.
- `nfsd4_record_grace_done()`: does nothing when `nn->client_tracking_ops` is
  `NULL`.
- First laundromat run: queued by `nfs4_state_start_net()` after
  `nn->nfsd4_grace` seconds, not `nn->nfsd4_lease`; only the `skip_grace`
  path queues it after `nn->nfsd4_lease`.
- `nfs4_laundromat()`: has no elapsed-time test; it calls `nfsd4_end_grace()`
  on every run where `clients_still_reclaiming()` is false, and later calls
  return at the `test_and_set_bit()`.
- `clients_still_reclaiming()` returns false at the first of these that holds,
  true otherwise:
  1. `NFSD_NET_GRACE_END_FORCED` is set.
  2. `NFSD_NET_TRACK_RECLAIM_COMPLETES` is set and `nn->nr_reclaim_complete`
     equals `nn->reclaim_str_hashtbl_size`.
  3. `NFSD_NET_SOMEBODY_RECLAIMED` was clear (the test clears it).
  4. `ktime_get_boottime_seconds()` is past `nn->boot_time_bt` plus twice
     `nn->nfsd4_lease`.
- `clients_still_reclaiming()`: does not look at `nn->client_lru` or
  `nn->boot_time`.
- While `clients_still_reclaiming()` is true: `nfs4_laundromat()` skips all its
  other work and reruns after `NFSD_LAUNDROMAT_MINTIMEOUT` seconds.
- Length of the delay: it lasts only while a reclaim succeeds between
  consecutive laundromat runs, and ends at the first run later than two
  leases after `nn->boot_time_bt`.
- Forced end: `write_v4_end_grace()` in `fs/nfsd/nfsctl.c` calls
  `nfsd4_force_end_grace()` in `fs/nfsd/nfs4state.c`, not
  `nfsd4_end_grace()`.
- `nfsd4_force_end_grace()`: sets `NFSD_NET_GRACE_END_FORCED` and calls
  `mod_delayed_work()` on `nn->laundromat_work` with delay 0; the work runs in
  the laundromat, and the write does not wait for it.
- `nfsd4_force_end_grace()`: takes no NFSD lock, `nn->client_lock` included.
- `nfsd4_force_end_grace()` returns `false` when `nn->client_tracking_ops` is
  `NULL` or `NFSD_NET_GRACE_ENDED` is already set; the write then fails with
  `-EBUSY`.

**Operations during grace**

- `opens_in_grace()` and `locks_in_grace()` in `fs/nfs_common/grace.c`: take
  only a `struct net *`; the caller compares the claim type or reclaim flag.
- `opens_in_grace()`: true only while a manager with `block_opens` set is on
  the list; `locks_in_grace()`: true while any manager is, lockd's included.
- There is no nfsd4_in_grace() here.
- `nfsd4_process_open1()` and `nfs4_check_open_reclaim()`: call neither
  helper; the open test is in `nfsd4_open()` in `fs/nfsd/nfs4proc.c`, after
  `nfsd4_process_open1()`.
- `nn->client_lock`: not held at the grace tests in `nfsd4_open()` or
  `nfsd4_lock()`.
- `nfsd4_reclaim_complete()`: calls neither helper, so it is not an example of
  the pattern.
- `nfsd4_open()`, sessions pre-check: a non-`NFS4_OPEN_CLAIM_PREVIOUS` open
  from a client without `NFSD4_CLIENT_RECLAIM_COMPLETE` gets `nfserr_grace`
  whatever `opens_in_grace()` says, so also after grace has ended.
- `NFS4_OPEN_CLAIM_PREVIOUS` during grace: can still fail in
  `nfs4_check_open_reclaim()`, with `nfserr_no_grace` if
  `NFSD4_CLIENT_RECLAIM_COMPLETE` is set, else `nfserr_reclaim_bad` if
  `nfsd4_client_record_check()` fails.
- `nfsd4_client_record_check()`: returns `-EOPNOTSUPP` when
  `nn->client_tracking_ops` is `NULL`, so every reclaim open that reaches it
  then gets `nfserr_reclaim_bad`.
- `nfsd4_lock()` has a third test after the pair: a reclaim lock from a client
  with `NFSD4_CLIENT_RECLAIM_COMPLETE` set gets `nfserr_no_grace` during grace.
- `nfsd4_layoutcommit()` (under `CONFIG_NFSD_PNFS`): a third two-sided
  example, `locks_in_grace()` against `lcp->lc_reclaim`.
- One-sided `nfserr_grace` checks: search `fs/nfsd` for the two helper names;
  members easy to miss are `nfsd4_setxattr()`, `nfsd4_removexattr()` and
  `nfsd4_block_proc_layoutget()`.
- There is no grace_disallows_io() here; `check_special_stateids()` in
  `fs/nfsd/nfs4state.c` does that job with `opens_in_grace()`.
- `check_special_stateids()`: a read with the all-ones stateid
  (`ONE_STATEID()` with `RD_STATE`) returns `nfs_ok` during grace; the other
  special-stateid cases get `nfserr_grace`.
- `nlmsvc_lock()` in `fs/lockd/svclock.c`: returns
  `nlm_lck_denied_grace_period` in both directions, also for a reclaim outside
  grace.
- **Potentially unsafe usage**: testing only the in-grace direction (helper
  true, return `nfserr_grace`).
  - Unsafe: in an NFSv4 operation whose arguments carry a reclaim flag or
    claim type; a reclaim sent after grace is then not refused with
    `nfserr_no_grace`.
  - Safe: in an operation with no reclaim form, as `nfsd4_lockt()`,
    `nfsd4_remove()` and `nfsd4_rename()` do; the paired tests in
    `nfsd4_open()` and `nfsd4_lock()` define the two-sided form.

## Copy offload

**Copy state objects**

- `struct nfsd4_async_copy` (`fs/nfsd/xdr4.h`): the async copy object; it
  embeds `cp_stid` (`struct nfs4_stid`) and `cp_copy` (`struct nfsd4_copy`,
  a snapshot of the request and the result).
- `refcount`, `copy_task`, `copies`, `cp_ttl`, `cp_cb_offload`: fields of
  `struct nfsd4_async_copy`, not of `struct nfsd4_copy`.
- `nfs4_alloc_copy_stid()` in `fs/nfsd/nfs4state.c`: allocates the whole
  object from `async_copy_slab` through `nfs4_alloc_stid()`; it is freed by
  the `sc_free` hook `nfsd4_free_async_copy_stid()`, not by `kfree()`.
- Stateid kind: an ordinary `struct nfs4_stid` with `sc_type` set to
  `SC_TYPE_COPY`; the value sent to the client is `cp_stid.sc_stateid`.
- `so_clid` of that stateid: the client's own `cl_clientid`;
  `si_generation` is fixed at 1.
- Not in this tree: NFS4_COPY_STID, nfs4_init_copy_state(),
  nfs4_free_copy_state(); `struct nfsd4_copy` has no `cp_stateid` field.
- `copy_stateid_t` and `nn->s2s_cp_stateids`: used only for COPY_NOTIFY
  (`struct nfs4_cpntf_state`, `NFS4_COPYNOTIFY_STID`); a copy offload
  stateid is never in that idr.
- Registered in: the client's `cl_stateids` idr, by `nfs4_alloc_stid()`,
  before the cap check and before the kthread exists.
- `find_stateid_locked()`: finds the entry and returns NULL because
  `sc_type == SC_TYPE_COPY`; no clientid comparison is involved.
- TEST_STATEID: `nfsd4_validate_stateid()` returns `nfserr_bad_stateid`,
  which `nfsd4_test_stateid()` stores in `ts_id_status`; the operation
  itself returns `nfs_ok`.
- FREE_STATEID: `nfsd4_free_stateid()` returns `nfserr_bad_stateid`.
- `container_of()` from `cp_stid` to the copy: the supported way to get the
  copy from its stateid, as in `nfsd4_free_async_copy_stid()`.
- **Potentially unsafe usage**: walking `cl_stateids` directly instead of
  going through `find_stateid_locked()`.
  - Unsafe: dereferencing `sc_file` or `sc_export` of an entry before testing
    `sc_type`; both are NULL in a `SC_TYPE_COPY` entry.
  - Safe: test `sc_type` against a mask without `SC_TYPE_COPY` first, as
    `find_one_sb_stid()` does with the mask from `nfsd4_revoke_states()`.

**Async copy lifetime**

- `NFSD4_COPY_F_STOPPED`: set only by `nfsd4_stop_copy()`, before
  `kthread_stop()`; the worker neither sets nor tests it.
- Worker stop test: `kthread_should_stop()` in `_nfsd_copy_file_range()`.
- `NFSD4_COPY_F_STOPPED` reader: only `nfsd4_has_active_async_copies()`.
- `NFSD4_COPY_F_CB_ERROR`: set by `nfsd4_cancel_copy_by_sb()` together with
  `nfserr = nfserr_admin_revoked`; while set, neither the worker nor
  `nfsd4_stop_copy()` overwrites `nfserr`. It does not mean CB_OFFLOAD
  failed.
- `NFSD4_COPY_F_OFFLOAD_DONE`: set by `nfsd4_cb_offload_release()`, and by
  `nfsd4_send_cb_offload()` when `cp_clp` is NULL; only the reaper reads it.
- `refcount` in `struct nfsd4_async_copy` has four kinds of holder:

  | Reference | Taken in | Dropped in |
  |---|---|---|
  | list membership | `nfsd4_copy()`, `refcount_set()` to 1 | by whoever unlinked the copy |
  | kthread | `nfsd4_copy()`, before `wake_up_process()` | end of `nfsd4_do_async_copy()` |
  | callback | `nfsd4_send_cb_offload()` | `nfsd4_cb_offload_release()` |
  | canceller | `find_async_copy()`, `nfsd4_unhash_copy()`, `nfsd4_cancel_copy_by_sb()` | inside `nfsd4_stop_copy()` |

- Last `nfs4_put_copy()`: calls `nfs4_put_stid()` on `cp_stid`; that removes
  the stateid from `cl_stateids` and runs `nfsd4_free_async_copy_stid()`.
- `cp_stid.sc_count`: stays at 1 for the whole life of the copy.
- `cp_copy.cp_clp` and `cp_stid.sc_client`: uncounted pointers; a client
  reference (`cl_nfsdfs.cl_ref`) is held only across CB_OFFLOAD and inside
  `nfsd4_cancel_copy_by_sb()`.
- `nfsd4_copy()` order: `kthread_create()`, `get_task_struct()`, kthread
  reference, `wake_up_process()`, then `list_add()` to `async_copies`; the
  worker can finish before the copy is on the list.
- Worker order in `nfsd4_do_async_copy()`:
  1. store `nfserr` (skipped when `NFSD4_COPY_F_CB_ERROR` is set)
  2. set `NFSD4_COPY_F_COMPLETED`
  3. `atomic_dec()` of `pending_async_copies`
  4. `nfsd4_send_cb_offload()`, which queues the callback and does not wait
  5. drop the kthread reference
- The worker never unlinks the copy from `async_copies`.
- `cp_clp == NULL`: marks a cancelled copy; `nfsd4_send_cb_offload()` then
  sends nothing.
- Four paths make the copy unfindable, each unlinking under `async_lock`:
  - `nfsd4_async_copy_reaper()`, from `nfs4_laundromat()`: only once
    `NFSD4_COPY_F_OFFLOAD_DONE` is set and `cp_ttl` (from
    `NFSD_COPY_INITIAL_TTL`) has counted down to 0.
  - `find_async_copy()`, for OFFLOAD_CANCEL: also clears `cp_clp`.
  - `nfsd4_unhash_copy()`, for `nfsd4_shutdown_copy()`: also clears `cp_clp`.
  - `nfsd4_cancel_copy_by_sb()`, from `fs/nfsd/nfsctl.c`: leaves `cp_clp`
    set, so a worker that is still running sends CB_OFFLOAD with
    `nfserr_admin_revoked`.
- `find_async_copy()`: not a plain lookup; use it only to cancel.
- `nfsd4_offload_status()`: uses `find_async_copy_locked()` with `async_lock`
  held throughout and takes no reference.
- `nfsd4_stop_copy()`: calls `kthread_stop()` unconditionally; this relies on
  the `get_task_struct()` in `nfsd4_copy()`.
- `nfsd4_stop_copy()` and `cleanup_async_copy()`: neither unlinks the copy;
  both call `release_copy_files()` and `nfs4_put_copy()`.
- Over the cap: `nfsd4_copy()` returns `nfserr_jukebox`; there is no fallback
  to a synchronous copy.
- `nfs4_alloc_copy_stid()` or `kthread_create()` failure in `nfsd4_copy()`:
  also `nfserr_jukebox`.
- **Unsafe usage**: calling `nfsd4_stop_copy()` on a copy that is still on
  `async_copies`; the reaper or a second canceller can then run
  `release_copy_files()` on it at the same time, with no lock.
  - Safe: take a reference and unlink under `async_lock`, call
    `nfsd4_stop_copy()`, then call `nfs4_put_copy()` once more for the list
    reference, as `nfsd4_offload_cancel()` and `nfsd4_shutdown_copy()` do.
- **Potentially unsafe usage**: a `nfs4_put_copy()` that may drop the last
  reference.
  - Unsafe: when nothing keeps the `struct nfs4_client` alive;
    `nfs4_put_stid()` locks `sc_client->cl_lock`.
  - Safe: in `nfsd4_shutdown_copy()`, which `__destroy_client()` calls before
    `free_client()`.
  - Safe: in `nfsd4_cb_offload_release()`, when the callback was queued
    before `__destroy_client()` reached `nfsd4_shutdown_callback()`;
    `nfsd41_destroy_cb()` ends `cl_cb_inflight` only after the release hook,
    and `nfsd4_shutdown_callback()` waits for it.
  - Safe: in `nfsd4_cancel_copy_by_sb()`, which holds `cl_nfsdfs.cl_ref`
    until after its last put.

## Data transfer and the open file cache

**Read paths**

- `nfsd_splice_read()`: page-cache pages placed in the reply, no copy.
- `nfsd_iter_read()`: `vfs_iocb_iter_read()` into `rq_bvec` built from reply
  pages; it does not call `vfs_iter_read()`.
- `nfsd_direct_read()`: reached only from inside `nfsd_iter_read()`.
- There is no rq_splice_ok in this tree, and `nfsd_read_splice_ok()` makes no
  transport test.
- `nfsd_read_splice_ok()`: returns false first if `nfsd_disable_splice_read`
  is set, then for `RPC_AUTH_GSS_KRB5I` and `RPC_AUTH_GSS_KRB5P`.
- NFSv4 READ and READ_PLUS splice only when all of these hold:
  - `nfsd_read_splice_ok()` was true in `nfsd4_decode_compound()`;
  - the compound holds one READ or READ_PLUS in total;
  - the estimated non-read reply fits in `PAGE_SIZE` less the auth slack;
  - the read is the last operation: `nfsd4_read()` in `fs/nfsd/nfs4proc.c`
    clears `argp->splice_ok` when `nfsd4_last_compound_op()` is false;
  - `file->f_op->splice_read` is set.
- READ_PLUS: `nfsd4_encode_read_plus_data()` makes the same choice as
  `nfsd4_encode_read()`; `nfsd4_read()` serves both operations.
- `nfsd4_encode_splice_read()` does not fall back to `nfsd4_encode_readv()`:
  it returns `nfserr_serverfault` if `xdr->buf->page_len` is non-zero and
  `nfserr_resource` if the head has no room left.
- Read I/O mode: the switch on `nfsd_io_cache_read` at the top of
  `nfsd_iter_read()`.
- `NFSD_IO_DIRECT` read: used only if `nf->nf_dio_read_offset_align` is
  non-zero and `rqstp->rq_res.page_len` is zero; otherwise the read is done as
  for `NFSD_IO_DONTCACHE`.
- Selecting `NFSD_IO_DONTCACHE` or `NFSD_IO_DIRECT` for reads sets
  `nfsd_disable_splice_read`, so splice stops for all versions and exports;
  see `nfsd_io_cache_read_set()` in `fs/nfsd/debugfs.c`.
- Clearing `nfsd_disable_splice_read` resets `nfsd_io_cache_read` to
  `NFSD_IO_BUFFERED` (`nfsd_dsr_set()`); setting the mode back to buffered
  does not re-enable splice.

**Write path**

- `nfsd_vfs_write()`: takes `stable` as an `int` by value; it cannot change
  the level the caller reports.
- Reply level: `nfsd3_proc_write()` sets `resp->committed` and `nfsd4_write()`
  sets `wr_how_written` from the request before the call, so an `async`
  export still replies with the level the client asked for.
- `sync` export: leaves the client's stable-how unchanged; only
  `!EX_ISSYNC()` alters it, to `NFS_UNSTABLE`.

| `stable` after the export test | kiocb flags |
|---|---|
| `NFS_FILE_SYNC` | `IOCB_DSYNC \| IOCB_SYNC` |
| `NFS_DATA_SYNC` | `IOCB_DSYNC` |
| `NFS_UNSTABLE` | none |

- nfsd sets `IOCB_` flags on a kiocb passed to `vfs_iocb_iter_write()`; it
  passes no `RWF_` flags and does not call `vfs_iter_write()`.
- Payload: `xdr_buf_to_bvec()` fills `rq_bvec`; there is no rq_vec.
- `fh_use_wgather`: set in `nfsd_set_fh_dentry()` in `fs/nfsd/nfsfh.c`, only
  when `fh_maxsize` is `NFS_FHSIZE` (NFSv2) and the export has `EX_WGATHER()`.
- With `fh_use_wgather` no sync flag is set; `wait_for_concurrent_writes()`
  runs afterwards only if `stable` is still non-zero.
- `nfsd_commit()` on an `async` export: no fsync, returns the verifier only.
- New verifier value: `siphash_2u64()` of `ktime_get_raw_ts64()` keyed with
  `nn->siphash_key`, in `fs/nfsd/nfssvc.c`; not the boot time.
- `commit_reset_write_verifier()`: skips the reset for `-EAGAIN` and
  `-ESTALE` only.
- Reset sites besides `nfsd_create_serv()`, `nfsd_vfs_write()` and
  `nfsd_commit()`: `nfsd4_clone_file_range()`, the async COPY path in
  `fs/nfsd/nfs4proc.c`, and `nfsd_file_check_write_error()`.
- `nfsd_file_check_write_error()`: runs on every successful
  `nfsd_file_do_acquire()` as well as in `nfsd_file_free()`; acts only on
  files with `FMODE_WRITE`.
- `nfsd_commit()`: `-EINVAL` from `vfs_fsync_range()` gives `nfserr_notsupp`
  with no reset.
- Verifier in a WRITE reply: `nfsd_vfs_write()` copies it before issuing the
  write, so a reset during or after the write differs from what the client
  holds; `nfsd_commit()` copies it after a successful fsync.
- `f_wb_err` is sampled before the write and checked with
  `filemap_check_wb_err()` after it, for unstable writes too; an error fails
  the WRITE and resets the verifier.
- `NFSD_IO_DIRECT` write: `nfsd_direct_write()` and
  `nfsd_write_dio_iters_init()` in `fs/nfsd/vfs.c`.
- Direct mode does not change stable-how: every segment inherits the sync
  flags above, and an `NFS_UNSTABLE` direct write still needs COMMIT.
- Direct write falls back to one buffered segment when any of these holds:
  - `nf_dio_mem_align` or `nf_dio_offset_align` is zero;
  - the write is shorter than the larger of the two;
  - no offset-aligned middle exists;
  - the middle's first bvec is not memory-aligned.
- Buffered segments of a direct write, including the fallback, get
  `IOCB_DONTCACHE` when the file has `FOP_DONTCACHE`;
  `Documentation/filesystems/nfs/nfsd-io-modes.rst` says they do not.
- `nfsd_io_cache_write_set()` returns `-EINVAL` above `NFSD_IO_DIRECT`; the
  document's values 3 and 4 for WRITE do not exist.
- `nfsd_file_get_dio_attrs()`: runs only when `nfsd_file_do_acquire()` opens
  the file itself.
- An entry built from an already-open file passed to
  `nfsd_file_acquire_opened()`, as NFSv4 OPEN with create does, keeps zero
  alignments; direct reads and writes through it fall back.

**Open file cache entries**

- Table: `nfsd_file_rhltable` in `fs/nfsd/filecache.c`, keyed on `nf_inode`
  alone.
- There is no nfsd_file_rhash_tbl, struct nfsd_file_lookup_key or
  nfsd_file_create() here; `nfsd_file_lookup_locked()` compares the other
  fields and `nfsd_file_do_acquire()` builds entries.
- `nf_may`: must equal the request exactly after masking with
  `NFSD_FILE_MAY_MASK`; a read-write entry does not serve a read request.
- Bits matched in `nf_may`: only `NFSD_MAY_READ` and `NFSD_MAY_WRITE`; why
  the mask's third bit is not is in "NFSD_MAY access flags".
- `nf_cred`: compared against `current_cred()` as set by `fh_verify()` or
  `fh_verify_local()`, not against the request's `rq_cred`.

| Acquire call | Kind | File type |
|---|---|---|
| `nfsd_file_acquire_gc()` | GC | `S_IFREG` |
| `nfsd_file_acquire()` | non-GC | `S_IFREG` |
| `nfsd_file_acquire_opened()` | non-GC | `S_IFREG` |
| `nfsd_file_acquire_local()` | non-GC | `S_IFREG` |
| `nfsd_file_acquire_dir()` | non-GC | `S_IFDIR` |

- Non-GC entry: stays hashed while any holder has a reference, unless
  `__nfsd_file_cache_purge()` unhashes it or it was built on an inode whose
  `i_nlink` is zero, so a later non-GC acquire with the same inode, mode, net
  and cred shares it; `nfsd_file_free()` unhashes it at the last put.
- GC acquire on an inode whose `i_nlink` is zero: the new entry is unhashed
  and not put on the LRU, so it closes at the caller's `nfsd_file_put()`.
- What keeps an idle GC entry: see "Closing cached files".

**Closing cached files**

- The hash table holds no reference.
- LRU reference: `nfsd_file_lru_add()` takes it, and is called once, from
  `nfsd_file_do_acquire()` when a GC entry is constructed.
- `nfsd_file_put()`: for a hashed GC entry sets `NFSD_FILE_REFERENCED` and
  `NFSD_FILE_RECENT`, then only decrements; it never touches the LRU.
- Laundrette: walks with `nfsd_file_gc_cb()`, which clears `NFSD_FILE_RECENT`
  and `NFSD_FILE_REFERENCED` and rotates; an entry is disposed on a later pass
  if it was not used in between.
- Shrinker: walks with `nfsd_file_lru_cb()` directly; it tests
  `NFSD_FILE_REFERENCED` and ignores `NFSD_FILE_RECENT`.
- `EXPORT_OP_FLUSH_ON_CLOSE`: makes `nfsd_file_lru_cb()` skip an entry opened
  for write that has dirty or writeback pages; see
  `nfsd_file_check_writeback()`. It starts no writeback.
- Without that flag, dirty pages do not keep an entry on the LRU.
- `EXPORT_OP_CLOSE_BEFORE_UNLINK`: gates `nfsd_file_close_inode_sync()` in
  `nfsd_unlink()` and `nfsd_rename()`.
- `nfsd_rename()`: acts on the rename target only, and only if
  `nfsd_file_is_cached()` finds a GC entry; it closes after `end_renaming()`
  and then retries the rename.
- `nfsd_file_lease_notifier_call()`: runs when a lease is being set, not when
  one is broken, and acts only for `FL_LEASE`.
- `nfsd_file_queue_for_close()`: skips non-GC entries, so the lease, fsnotify
  and unlink/rename closes never touch NFSv4 state's files.
- `nfsd_file_close_export()`: closes GC entries under an export path, in the
  caller; reached from `nfsd_nl_unlock_export_doit()` in `fs/nfsd/nfsctl.c`.
- No cache entry is closed or purged on unmount, on unlock-filesystem, or to
  evict an entry after a writeback error.
- `__nfsd_file_cache_purge()`: unhashes GC and non-GC entries alike.
- `nfsd_file_cond_queue()`, used by every close above except the LRU walks:
  closes an entry only if dropping the LRU reference leaves none; an entry
  still held is only unhashed and closes at its holder's last put.
- "Sync" therefore means the unreferenced entries are closed on return, not
  that the inode has no open file.
- Queued closes (laundrette, shrinker, lease, fsnotify): moved to
  `nn->fcache_dispose_list`; nfsd threads close them in
  `nfsd_file_net_dispose()`, called from the `nfsd()` thread loop.

## Server configuration and netlink

**Netlink family**

- `nfsd_nl_family`: the family struct in `fs/nfsd/netlink.c`; there is no
  nfsd_genl_family in this tree.
- `Documentation/netlink/specs/nfsd.yaml`: declares `protocol: genetlink`.
- Commands beyond threads, version, listener, pool-mode and rpc-status: cache
  requests, cache-flush, unlock-ip, unlock-filesystem, unlock-export and
  server-stats-get; see `nfsd_nl_ops[]` in `fs/nfsd/netlink.c`.
- Dumps: no entry of `nfsd_nl_ops[]` sets `.start` or `.done`; there is no
  nfsd_nl_rpc_status_get_start(). Each `dumpit` call resumes from `cb->args[]`.
- `NFSD_CMD_CACHE_NOTIFY`: an event, so it has no entry in `nfsd_nl_ops[]` and
  no generated prototype; `nfsd_cache_notify()` in `fs/nfsd/nfsctl.c` sends it
  to group `NFSD_NLGRP_EXPORTD`, reached through the `cache_notify` member of
  `struct cache_detail`.
- Pool-mode commands: `sunrpc_set_pool_mode()` only checks the name against a
  list and stores nothing; `sunrpc_get_pool_mode()` always prints "pernode"
  (`net/sunrpc/svc.c`).
- Neighbouring families, generated the same way: `lockd_nl_family` from
  `Documentation/netlink/specs/lockd.yaml`, handlers in `fs/lockd/svc.c`;
  `sunrpc_nl_family` from `Documentation/netlink/specs/sunrpc_cache.yaml`,
  handlers in `net/sunrpc/svcauth_unix.c`.
- Values are positional: the generator numbers commands, attributes and flag
  bits in spec order, so a new entry goes last in its list.
- **Unsafe usage**: a doit handler reading `info->attrs[X]` where `X` is not
  listed under that operation's `request: attributes:` in the spec.
  - Unsafe: `.maxattr` and the top-level policy are sized by the highest
    listed attribute, not by the attribute set, and
    `genl_family_rcv_msg_attrs_parse()` in `net/netlink/genetlink.c` allocates
    `maxattr + 1` slots; an op with no `.policy` gets `info->attrs == NULL`,
    which `GENL_REQ_ATTR_CHECK()` dereferences.
  - Safe: read only listed attributes, as `nfsd_nl_threads_set_doit()` does;
    adding one to the handler means adding it to the op's request list and
    regenerating.
- Nested attribute sets: handlers parse them again with `nla_parse_nested()`
  into a local `tb[]` whose bound is written by hand. `fs/nfsd/export.c` uses
  the last attribute's name (`NFSD_A_SVC_EXPORT_FSID`, `NFSD_A_EXPKEY_PATH`,
  `NFSD_A_AUTH_FLAVOR_FLAGS`, `NFSD_A_FSLOCATION_PATH`), so appending an
  attribute to one of those sets needs the bound changed too, or the new type
  is rejected with `-EINVAL`.
- `export-flags` and `xprtsec-mode` in the spec: must match, in order and
  count, the export flag bits `NFSEXP_READONLY` through `NFSEXP_PNFS` and the
  bits `NFSEXP_XPRTSEC_NONE`, `NFSEXP_XPRTSEC_TLS` and `NFSEXP_XPRTSEC_MTLS`
  in `include/uapi/linux/nfsd/export.h`.
  `nfsd_nl_parse_one_export()` stores `NFSD_A_SVC_EXPORT_FLAGS` straight into
  `ex_flags`, and the generated `NLA_POLICY_MASK()` value (equal to
  `NFSEXP_ALLFLAGS`) comes from the number of spec entries.

**Server configuration mutex**

- Names not in this tree: nfsd_put(), and the fields nfsd_net_up and
  keep_active. `nfsd_destroy_serv()` tears the server down; `NFSD_NET_UP` and
  `NFSD_NET_LOCKD_UP` are bits of `enum nfsd_net_flag` in `nn->flags`.
- `struct svc_serv`: has no reference count here.
- Pool mode: not protected by `nfsd_mutex`.
- `parallel_ops` is set in `nfsd_nl_family`, so genetlink takes no lock around
  handlers; a handler that needs `nfsd_mutex` takes it itself.
- Three states, told apart under `nfsd_mutex`: `nn->nfsd_serv` NULL;
  `nn->nfsd_serv` set but `NFSD_NET_UP` clear (listeners added, no threads
  yet); `NFSD_NET_UP` set. Only `nfsd_startup_net()`, reached from
  `nfsd_svc()`, sets the bit.
- `nfsd_destroy_serv()`: does not stop threads, and neither does
  `svc_destroy()`. Every caller reaches it with `sv_nrthreads` at 0;
  `nfsd_shutdown_threads()` calls `svc_set_num_threads()` with 0 first.
- `nfsd_destroy_serv()` order: clear `nn->nfsd_serv` under
  `nfsd_notifier_lock`, unregister the notifiers if last user,
  `svc_xprt_destroy_all()`, `nfsd_shutdown_net()`, `svc_destroy()`.
  `nfsd_file_dispose_list_delayed()` in `fs/nfsd/filecache.c` depends on the
  pointer being cleared before the file cache shuts down and freed after.
- `nfsd_shutdown_net()`: waits under the mutex for `nfsd_net_ref` to drain
  (`nfsd_net_free_done`), so a holder of an `nfsd_net_try_get()` reference
  that blocks on `nfsd_mutex` deadlocks shutdown.
- `svc_pool_stats_start()` takes the mutex through `si->mutex` and
  `svc_pool_stats_stop()` drops it; `svc_pool_stats_open()` does not take it.

| Helper | `nfsd_mutex` |
|---|---|
| `nfsd_nrthreads()`, `nfsd_shutdown_threads()` | takes it; deadlocks if the caller holds it |
| `nfsd_nrpools()`, `nfsd_get_nrthreads()` | neither takes nor asserts; caller must hold it |
| `nfsd_svc()`, `nfsd_set_nrthreads()`, `nfsd_destroy_serv()` | `lockdep_assert_held()` |
| `nfsd_create_serv()` | `WARN_ON(!mutex_is_locked())` |

- **Unsafe usage**: calling `nfsd_nrpools()` or `nfsd_get_nrthreads()` without
  `nfsd_mutex`; both dereference `nn->nfsd_serv` unlocked.
  - Safe: inside the locked region, as `write_pool_threads()` and
    `nfsd_nl_threads_get_doit()` do.
- **Potentially unsafe usage**: reading `nn->nfsd_serv` without `nfsd_mutex`.
  - Unsafe: outside an nfsd thread, with no lock that `nfsd_destroy_serv()`
    takes; the pointer is cleared and `svc_destroy()` frees the serv.
  - Safe: in an nfsd thread, because the pointer is cleared only once
    `sv_nrthreads` is 0; `check_forechannel_attrs()` does this.
  - Safe: under `nfsd_notifier_lock`, which `nfsd_create_serv()` and
    `nfsd_destroy_serv()` hold when they write the pointer;
    `nfsd_inetaddr_event()` does this. The lock is static to
    `fs/nfsd/nfssvc.c`.
  - Safe: under `nfsd_gc_lock`, as `nfsd_file_dispose_list_delayed()` does;
    `nfsd_file_cache_shutdown_net()`, reached from `nfsd_destroy_serv()`,
    takes that lock after the pointer is cleared and before `svc_destroy()`.
    The lock is static to `fs/nfsd/filecache.c`.
- **Potentially unsafe usage**: taking `nfsd_mutex` in an nfsd thread.
  - Unsafe: with `mutex_lock()`; `svc_stop_kthreads()` waits for the thread to
    exit while its caller holds the mutex.
  - Safe: with `mutex_trylock()`, as `nfsd()` does to spawn or retire a
    dynamic thread; a retiring thread keeps the mutex across
    `svc_exit_thread()`.
- **Unsafe usage**: calling `nfsd4_revoke_states()`,
  `nfsd4_revoke_export_states()` or `nfsd4_cancel_copy_by_sb()` without first
  testing `NFSD_NET_UP` under `nfsd_mutex`; they assert the mutex only, and
  walk `nn->conf_id_hashtbl`, which exists only between
  `nfs4_state_create_net()` and `nfs4_state_destroy_net()`.
  - Safe: test the bit inside the locked region, as
    `nfsd_nl_unlock_export_doit()` and `write_unlock_fs()` do.

**Netlink privilege and namespaces**

- `GENL_ADMIN_PERM`: `genl_family_rcv_msg()` in `net/netlink/genetlink.c`
  checks it with `netlink_capable()`, which tests `CAP_NET_ADMIN` in
  `init_user_ns`, for doit and dumpit alike. The owner of the socket's netns
  is not consulted.
- Operations without `GENL_ADMIN_PERM`: the four get doits, plus the
  rpc-status-get and server-stats-get dumps. Any process in the netns can read
  them, including client addresses of in-flight RPCs.
- Dumps with `GENL_ADMIN_PERM`: `NFSD_CMD_SVC_EXPORT_GET_REQS` and
  `NFSD_CMD_EXPKEY_GET_REQS`.
- `exportd` multicast group: its entry in `nfsd_nl_mcgrps[]` sets no `flags`
  (for example `GENL_MCAST_CAP_NET_ADMIN`), so joining needs no capability.
  The event carries only the cache type.
- `nfsd_cache_notify()`: has no request socket; it takes the netns from
  `cd->net` and sends with `genlmsg_multicast_netns()`.
- Credentials: netlink handlers pass `current_cred()` to `nfsd_svc()` and
  `svc_xprt_create_from_sa()`; the nfsctl files pass `file->f_cred`.
- Handlers not confined to the socket's netns:
  - `nfsd_nl_unlock_ip_doit()`: `nlmsvc_unlock_all_by_ip()` walks the global
    `nlm_files` table in `fs/lockd/svcsubs.c`; the netns is used only for the
    tracepoint.
  - `nfsd_nl_unlock_filesystem_doit()`: `nlmsvc_unlock_all_by_sb()` is global
    in the same way and runs before the `NFSD_NET_UP` test; only the NFSv4
    revocation is per-net.

## Maintainer conventions

**Coding conventions**

- `Documentation/filesystems/nfs/nfsd-maintainer-entry-profile.rst`: exists, and
  is the `P:` entry of "KERNEL NFSD, SUNRPC, AND LOCKD SERVERS" in
  `MAINTAINERS`.
- Profile wording is mostly preference, not prohibition; the only "must"
  statements in its sections on administrative interfaces, field
  observability and coding style are the BUG and printk bullets under "Field
  observability".
- Administrative interfaces:
  - Interfaces counted: NFSD or SUNRPC module parameters, export options in
    /etc/exports, files under /proc/fs/nfsd/ or /proc/sys/sunrpc/, the NFSD
    netlink protocol.
  - New or modified setting: "a last resort"; the profile does not forbid new
    /proc files, sysctls or module parameters outright.
  - Two destinations offered for a setting that is needed: the NFSD netlink
    protocol first, or /sys/kernel/debug/nfsd/ if it need not be a reliable
    long-term user-space feature.
  - debugfs settings: see `nfsd_debugfs_init()` in `fs/nfsd/debugfs.c`; the
    setters write globals such as `nfsd_disable_splice_read`, so they apply
    to every net namespace.
  - Without `CONFIG_DEBUG_FS`: `nfsd_debugfs_init()` is an empty stub in
    `fs/nfsd/nfsd.h`, so a debugfs setting does not exist.
  - Namespace awareness: not a requirement stated in the profile.
  - User-space support, man pages, backward compatibility: no requirement
    stated in the profile's administrative-interface section.
  - User space: kernel and user-space changes are posted as separate series
    (section "Patch submission").
- Observability:
  - `dprintk()`: not deprecated by the profile, and new call sites are not
    banned; it is called inappropriate for frequent operations like I/O.
  - Static trace points: "favored for use in hot paths"; not mandated for all
    new diagnostics.
  - General rule: "Contributors should select the most appropriate tool"
    among counters, printks, WARNings and static trace points.
  - BUG: "must be avoided if at all possible".
  - WARN: appropriate only when a full stack trace is useful.
  - printk: must not be used on paths a remote user can trigger repeatedly;
    the profile does not name rate limiting as an accepted alternative.
  - Counters: described as always on and low in per-event detail; the profile
    names no file for them.
  - Dynamic tracing (kprobes, eBPF): listed as a mechanism, noted as unusable
    under full kernel lockdown.
  - Tracepoint ABI stability: the profile says nothing.
- Coding style:
  - Exceptions to `Documentation/process/coding-style.rst`: exactly five, the
    local-variable, kdoc and three naming rules below; the "Coding style"
    section has no rule on line length, `scripts/checkpatch.pl`, `%pe`, XDR
    or xdrgen.
  - Local variables: new ones are added in reverse Christmas tree order; the
    definition the profile links to is the `rcs` label in
    `Documentation/process/maintainer-netdev.rst`.
  - Kdoc comments: to be used on non-static functions, static inline
    functions, and static functions that are callbacks or virtual functions.
  - Naming, version-independent: new function names start with `nfsd_`.
  - Naming, per version: `nfsdN_` for NFSv2, NFSv3, or code used by all NFSv4
    minor versions.
  - Naming, per NFSv4 minor version: `nfsd4M_` may be used, for example
    `nfsd41_cb_get_slot()` in `fs/nfsd/nfs4callback.c`.
  - Stand-alone clean-up patches (section "Clean-up patches"): discouraged
    when "not in the context of other work"; the examples given are
    `checkpatch.pl` warnings after merge, local variable ordering, and
    long-standing whitespace damage.
  - Variable order rule: applies to new local variables; a patch that only
    reorders existing declarations is one of the discouraged clean-ups.
  - Spelling and grammar fixes: encouraged.

## Model gaps

### Other mistakes models make

- Models take an NFSv4 request to be deferrable on a cache miss once decoding
  has started. `nfs4svc_decode_compoundargs()` and `nfsd4_proc_compound()`
  clear `RQ_USEDEFERRAL`, and `svc_defer()` returns NULL without it.
- Models take the thread count to be fixed. Here, when `min_threads` in
  `struct nfsd_net` is non-zero, `nfsd()` in `fs/nfsd/nfssvc.c` spawns and
  retires threads. `nfsd_nrthreads()` reports the sum of every pool's ceiling
  `sp_nrthrmax`; `sp_nrthreads` is the running count.
- Models name no lock for the reclaim table. `reclaim_str_hashtbl` and
  `reclaim_str_hashtbl_size` are under the `rw_semaphore`
  `reclaim_str_hashtbl_lock`, not `client_lock`; outside the tracker's set-up
  and teardown, only the start-up read of the size in
  `nfs4_state_start_net()` is made without it.
  `nfsd4_find_reclaim_client()` takes no lock, its callers hold the
  semaphore.
- Models carry size limits from older trees, such as a 1 MB payload. Here
  `RPCSVC_MAXPAYLOAD` (`include/linux/sunrpc/svc.h`) and `NFSSVC_DEFBLKSIZE`
  are 4 MB, and `NFSD_MAX_OPS_PER_COMPOUND` is 200.
- Models take POSIX ACLs to reach clients only through NFSACL. Under
  `CONFIG_NFSD_V4_POSIX_ACLS`, NFSv4.2 also carries
  `FATTR4_WORD2_POSIX_ACCESS_ACL` and `FATTR4_WORD2_POSIX_DEFAULT_ACL`
  (`fs/nfsd/attr4.h`); `nfsd_setattr()` applies `na_pacl` and `na_dpacl`.
- Models know no fencing path for a layout whose lease break times out. Here
  `nfsd4_layout_lm_breaker_timedout()` in `fs/nfsd/nfs4layouts.c` pins the
  stateid and queues `ls_fence_work`; `nfsd4_layout_fence_worker()` retries
  `fence_client` with back-off.
- Models take NFSv2 and the recovery-directory backend to be always built.
  `CONFIG_NFSD_V2` and `CONFIG_NFSD_LEGACY_CLIENT_TRACKING` both default to n
  (`fs/nfsd/Kconfig`); without them `fs/nfsd/nfsproc.c` is not compiled and
  only the nfsdcld backends in `fs/nfsd/nfs4recover.c` remain.
