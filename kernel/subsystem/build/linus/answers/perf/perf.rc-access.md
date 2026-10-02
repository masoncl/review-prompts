- `RC_CHK_ACCESS()` outside the owning file: used in this tree for direct
  field access, for example on a `struct dso` in
  `tools/perf/util/symbol-minimal.c`, and for object identity.
- `struct maps` and `struct comm_str`: opaque outside
  `tools/perf/util/maps.c` and `tools/perf/util/comm.c`, so neither
  `RC_CHK_ACCESS()` nor `RC_CHK_EQUAL()` compiles on them elsewhere under
  checking; compare maps with `maps__equal()`.
- `struct addr_location` has no maps field; the kernel-maps test is
  `maps__equal(thread__maps(al->thread), machine__kernel_maps(machine))`,
  as in `tools/perf/util/callchain.c`.
- `struct evlist`: checked, so `evlist->field` does not compile under
  checking; use the accessors in `tools/perf/util/evlist.h`.
- `RC_CHK_EQUAL()`: accepts NULL on either side.
- Hash and ordering keys: built from `RC_CHK_ACCESS(ptr)`, as
  `remap_addresses__hash()` in `tools/perf/util/aslr.c` does.
- **Potentially unsafe usage**: `RC_CHK_ACCESS(ptr)` used only to obtain
  the object's address.
  - Unsafe: when `ptr` may be NULL; under checking the macro reads
    `ptr->orig`, with checking off it just yields NULL.
  - Safe: test `ptr` for NULL first, as `__hpp__sort_acc()` in
    `tools/perf/ui/hist.c` does, or use `RC_CHK_EQUAL()`.
- **Potentially unsafe usage**: `container_of()` from a member embedded in
  a checked struct.
  - Unsafe: when the result is used as a `struct name *` in code that is
    compiled under checking; there it points at the `RC_STRUCT(name)`
    object, not at a wrapper.
  - Safe: wrap the result with `ADD_RC_CHK()`, take a count, and put it
    when done, as `from_list_start()` and `from_list_end()` in
    `tools/perf/util/evlist.c` do.
  - Safe: keep a counted back-pointer in the member under
    `#ifdef REFCNT_CHECKING`, as `dso__list_add()` and `close_first_dso()`
    in `tools/perf/util/dso.c` do.
- **Potentially unsafe usage**: calling a get and ignoring its return
  value.
  - Unsafe: for a struct declared with `DECLARE_RC_STRUCT`; the new wrapper
    is lost and the later put frees the wrapper of another holder.
  - Safe: for `struct evsel`, which is not checked; `evsel__get()` returns
    its argument.
