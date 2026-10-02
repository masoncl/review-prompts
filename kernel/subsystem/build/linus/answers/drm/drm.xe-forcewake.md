- `domains` argument of `xe_force_wake_get()`: one domain bit or
  `XE_FORCEWAKE_ALL`; the function asserts `is_power_of_2(domains)`.
- `XE_FORCEWAKE_ALL`: a separate bit, `BIT(XE_FW_DOMAIN_ID_COUNT)`, not the
  OR of the domain bits.
- Returned mask: the domains whose refcount this call raised and still
  holds, including domains that were already awake.
- `XE_FORCEWAKE_ALL` bit in the result: set by `xe_force_wake_get()` only
  when the held set equals `fw->initialized_domains`;
  `xe_force_wake_ref_has_domain()` itself is a plain `fw_ref & domain`.
- Single-domain request: a nonzero result means that domain is held, so
  `if (!fw_ref)` is a sufficient test; only an `XE_FORCEWAKE_ALL` request
  can return a partial nonzero mask.
- `xe_force_wake_put()` with 0: returns at once, so it is safe to call on
  any return value.
- **Potentially unsafe usage**: passing a constant instead of the returned
  reference to `xe_force_wake_put()`.
  - Unsafe: `XE_FORCEWAKE_ALL` after a get whose result lacks the
    `XE_FORCEWAKE_ALL` bit; put expands that bit to
    `fw->initialized_domains` and drops references that were never taken
    (`xe_gt_assert(gt, domain->ref)` catches it only under
    `CONFIG_DRM_XE_DEBUG` and only when the count is already 0).
  - Safe: `XE_FORCEWAKE_ALL` when the matching get returned a reference
    with the `XE_FORCEWAKE_ALL` bit, as `forcewake_release()` in
    `xe_debugfs.c` does for GTs that `forcewake_open()` fully woke.
