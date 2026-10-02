- "Must be initialised": not stated as a requirement in
  `include/linux/cleanup.h`, whose DOC comment only recommends defining and
  assigning in one statement, for the unwind-order reason; the requirement is
  the `UNINITIALIZED_PTR_WITH_FREE` error in `scripts/checkpatch.pl`,
  described in `Documentation/dev-tools/checkpatch.rst`.
- `UNINITIALIZED_PTR_WITH_FREE`: matches only a pointer declared with
  `__free()` and no initialiser; `= NULL` at the top of a function passes it.
- `__free(...) = NULL` at the top of a function: present in-tree and correct
  where no later guard or cleanup variable depends on the order, for example
  `kmod_dup_request_exists_wait()` in `kernel/module/dups.c`, whose only lock
  is a `scoped_guard()` and whose `put_kmod_req()` needs no lock.
