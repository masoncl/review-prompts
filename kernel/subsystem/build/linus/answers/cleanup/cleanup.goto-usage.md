- **Unsafe usage**: a `goto` placed before a `__free()` or `guard()`
  declaration that targets a label inside that declaration's scope.
  - Safe: every exit before the declaration is a `return`, and `goto` appears
    only after it, as in `simple_util_parse_tdm_width_map()` in
    `sound/soc/generic/simple-card-utils.c` and
    `ieee80211_rx_mgmt_assoc_resp()` in `net/mac80211/mlme.c`; the comment in
    the former states the requirement.
  - Safe: `guard()` is the first statement and all `goto` follow it, as in
    `posixtimer_send_sigqueue()` in `kernel/signal.c`.
  - Safe: a backward `goto` to a label that follows the declaration, as
    `goto retry` in `futex_unqueue()` in `kernel/futex/core.c`; the guard is
    not re-taken.
  - Safe: the declaration sits in a nested block or is a `scoped_guard()`,
    and the labels are at function level, so a `goto` either skips the whole
    block or leaves it; `gpiochip_add_data_with_key()` in
    `drivers/gpio/gpiolib.c` does both with `scoped_guard()`.
- **Unsafe usage**: an `asm goto` inside a cleanup scope whose target label
  is outside that scope.
  - Safe: route it through a label local to the scope and leave with a plain
    C `goto`, as `unsafe_get_user()`, `unsafe_put_user()` and
    `__get_kernel_nofault()` in `include/linux/uaccess.h` do with
    `__label__ local_label` when the architecture defines
    `arch_unsafe_get_user` or `arch_get_kernel_nofault`; the comment above
    them defines the requirement and says Clang rejects the direct form while
    GCC silently emits buggy code.
  - Safe: a plain C `goto` out of a cleanup scope, which is how those
    wrappers themselves leave (`goto label`); the same comment says it "works
    correctly".
- `__scoped_user_access()` in `include/linux/uaccess.h`: its error label
  "must be placed outside the scope".
- `__free(...) = NULL` at the top of the function: not a requirement; it puts
  the declaration ahead of every `goto`, and `scripts/checkpatch.pl` accepts
  it, but the DOC block in `include/linux/cleanup.h` recommends against it
  because unwind order then follows declaration order, not acquisition order.
- Clang, forward jump over the declaration: the tree records it as a build
  failure, in comments in `simple_util_parse_tdm_width_map()` and
  `audio_graph2_link_c2c()` ("Clang doesn't allow to use "goto end" before
  calling __free(), because it bypasses the initialization").
- GCC, forward jump over the declaration: the tree has no statement that GCC
  rejects it, and no build flag names such a diagnostic; the string
  jump-misses-init appears nowhere in the tree, including
  `scripts/Makefile.warn`.
- Supported compilers and minimum versions: `scripts/min-tool-version.sh`.
