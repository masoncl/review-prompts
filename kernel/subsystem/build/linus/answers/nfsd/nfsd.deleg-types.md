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
