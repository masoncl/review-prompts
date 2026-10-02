- `Documentation/rust/`: does not describe the convention; "invariant" occurs
  nowhere under it. The convention lives only in the code.
- Enforcement: no flag in `rust_common_flags` and no check in
  `scripts/checkpatch.pl` looks at `# Invariants` or `// INVARIANT:`.
- `ARef::from_raw()` in `rust/kernel/sync/aref.rs`: has the `// INVARIANT:`
  comment.
- `rust/kernel/types.rs`: its example is `struct ScopeGuard`.
- `rust/kernel/str.rs`: defines no `CStr` struct; its `# Invariants` sections
  are on `RawFormatter`, `NullTerminatedFormatter` and `CString`.
- `rust/kernel/sync/lock.rs`: has no `# Invariants` section and no
  `// INVARIANT:` comment; use `struct Guard` in `rust/kernel/sync/rcu.rs`.
- `// INVARIANT:` on a pointer cast: also marks a cast that yields a reference
  or `ARef` to such a type with no struct literal, for example
  `File::from_raw_file()` and `LocalFile::assume_no_fdget_pos()` in
  `rust/kernel/fs/file.rs`, and `probe_callback()` in
  `rust/kernel/platform.rs`.
- `// INVARIANT:` and `// SAFETY:`: may share one comment block above one
  `unsafe` expression, as in `LocalFile::fget()`.
- Temporary break: `rust/kernel/alloc/kvec.rs` marks both the statement that
  breaks the invariant and the one that restores it.
- Spelling: `# Invariant` (for example `rust/kernel/io.rs`) and
  `// INVARIANTS:` (for example `rust/kernel/sync/poll.rs`) also occur.
- Field visibility: under `rust/kernel/`, fields under an invariant are not
  `pub`, but `pub(crate)` occurs, for example `struct Task` in
  `rust/kernel/task.rs`.
