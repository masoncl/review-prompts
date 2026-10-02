- `tools/include/uapi/linux/const.h`: the only copy a script compares; it is
  in the `FILES` list of `tools/perf/check-headers.sh`, which prints a
  warning and does not fail the build.
- `tools/include/linux/align.h`: exists, defines only `ALIGN()`,
  `ALIGN_DOWN()` and `IS_ALIGNED()`, and is in no list of the script.
- `include/vdso/align.h`: has no copy under `tools/include/vdso/`.
- `tools/include/linux/kernel.h`: has `PERF_ALIGN()` and
  `__PERF_ALIGN_MASK()`, not `ALIGN()`.
- Pageblock copies: `tools/testing/memblock/linux/mmzone.h` and
  `tools/testing/vma/linux/mmzone.h`; no script compares them.
- Pageblock copies, contents: `pageblock_order` is fixed to `MAX_PAGE_ORDER`
  (10); they define `pageblock_align()` and `pageblock_start_pfn()` but not
  `pageblock_aligned()` or `pageblock_end_pfn()`.
- `scripts/gdb`: holds no copy of `ALIGN()` or of the pageblock macros;
  `scripts/gdb/linux/mm.py` has `PAGE_SIZE` and `PAGE_MASK`.
- Other private copies: search for `#define ALIGN(` under `tools/` and
  `scripts/`; for example `tools/firmware/ihex2fw.c` and
  `tools/testing/scatterlist/linux/mm.h` copy `__ALIGN_KERNEL()`.
- `tools/hv/vmbus_bufring.c`: its `ALIGN()` rounds down.
- `tools/virtio/ringtest/ptr_ring.c`: its `ALIGN()` divides, so it accepts
  any multiple.
- Rust `page_align()` in `rust/kernel/page.rs`: returns `Option<usize>`; it
  uses `checked_add` and returns `None` where C `PAGE_ALIGN()` returns 0; it
  does not panic under `CONFIG_RUST_OVERFLOW_CHECKS`.
- Rust `Alignable` in `rust/kernel/ptr.rs`: `align_up()` returns
  `Option<Self>` and `None` on overflow; `const_align_up()` does the same
  for `usize`; `align_down()` returns a plain value.
- Rust `align_up()` with an alignment that does not fit the value's type:
  returns `None` unless the value is 0; C `ALIGN()` truncates `a` and
  returns 0.
- Rust `Alignment` in `rust/kernel/ptr.rs`: `Alignment::new()` rejects a
  non-power-of-two at build time and `Alignment::new_checked()` returns
  `None` at run time; the C macros check nothing.
