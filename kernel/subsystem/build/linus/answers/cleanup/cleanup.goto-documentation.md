- Wording in the DOC block of `include/linux/cleanup.h`: "the expectation is
  that usage of "goto" and cleanup helpers is never mixed in the same
  function"; it is stated as an expectation, not as a preference. The next
  sentence spells it out: for a given routine, convert all resources that need
  a `goto` cleanup to scope-based cleanup, or convert none of them.
- Stated reason: the benefit of the helpers is removal of `goto`, and `goto`
  "can jump between scopes". The text names no consequence (no mention of an
  uninitialised variable or of a destructor running on garbage).
- Reverse-declaration-order text: belongs to the earlier paragraphs, and
  argues against `__free(...) = NULL` at the top of a function; it is not the
  reason given for the `goto` rule.
- In-tree code that mixes both in one function, for example:
  `simple_util_parse_tdm_width_map()` in
  `sound/soc/generic/simple-card-utils.c`,
  `audio_graph2_link_c2c()` in `sound/soc/generic/audio-graph-card2.c`,
  `posixtimer_send_sigqueue()` in `kernel/signal.c`, `futex_unqueue()` in
  `kernel/futex/core.c`, `gpiochip_add_data_with_key()` in
  `drivers/gpio/gpiolib.c`.
- A mix alone is therefore not a defect in this tree; see "Goto and cleanup in
  one function" for which mixes break.
- The header's own macros expand to `goto`: `__scoped_guard()`,
  `__scoped_cond_guard()` and `__scoped_class()`.
- `__scoped_user_access()` in `include/linux/uaccess.h`: takes an error label
  as an argument, so its users combine a cleanup scope and `goto` by design.
- `scripts/checkpatch.pl`: its one cleanup check is
  `UNINITIALIZED_PTR_WITH_FREE` (a `__free()` pointer with no initialiser);
  it has no check for `goto` mixed with the helpers.
