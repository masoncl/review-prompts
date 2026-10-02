- Buffer passed to `report_fixup`: a temporary `kmemdup()` of `bpf_rdesc`,
  not `dev_rdesc`; `hid_open_report()` frees it itself through
  `__free(kfree)`.
- Returned pointer: has to be readable for `*size` bytes only until the
  `kmemdup()` that `hid_open_report()` runs right after the fixup returns.
- `rdesc` holds that second copy, never the pointer the fixup returned.
- Returned pointer other than the passed buffer: the core never frees it.
- NULL return: not tested and no fallback; `hid_open_report()` passes it
  straight to `kmemdup()`, which copies `*size` bytes from it.
- **Unsafe usage**: freeing the passed buffer inside `report_fixup`.
  - Safe: leave it alone and return it or another pointer, as
    `gembird_report_fixup()` in `drivers/hid/hid-gembird.c` does; the
    `__free(kfree)` on `buf` in `hid_open_report()` frees it.
