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
