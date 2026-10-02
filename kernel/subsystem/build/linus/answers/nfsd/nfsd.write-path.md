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
