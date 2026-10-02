- Three forms exist in `xe_force_wake.h`; there is no `DEFINE_GUARD()` form
  and no scope-specific has-domain helper.

| Form | Use |
|---|---|
| `CLASS(xe_force_wake, fw_ref)(fw, domains)` | get now, put at end of enclosing scope |
| `xe_with_force_wake(fw_ref, fw, domains)` | same, bound to the next statement or block |
| `CLASS(xe_force_wake_release_only, fw_ref)(ref)` | put only; the get happened in another function |

- `CLASS(xe_force_wake_release_only, ...)`: takes a
  `struct xe_force_wake_ref` by value and skips the put when `.fw` is NULL.
- `xe_force_wake_constructor()`: returns the `struct xe_force_wake_ref` to
  hand to the release-only class; see `force_wake_get_any_engine()` in
  `xe_drm_client.c`.
- Check after a single-domain request: in-tree code uses either
  `!fw_ref.domains` or
  `xe_force_wake_ref_has_domain(fw_ref.domains, domain)`; after an
  `XE_FORCEWAKE_ALL` request only the latter, with `XE_FORCEWAKE_ALL`,
  shows that every domain woke.
