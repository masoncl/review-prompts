- Disable, in `disable_outputs()` in `drivers/gpu/drm/drm_atomic_helper.c`:
  1. `drm_atomic_helper_commit_encoder_bridge_disable()`: bridges
     `atomic_disable`, then the encoder disable
  2. `drm_atomic_helper_commit_encoder_bridge_post_disable()`
  3. `drm_atomic_helper_commit_crtc_disable()`
- Enable, in `drm_atomic_helper_commit_modeset_enables()`:
  1. `drm_atomic_helper_commit_crtc_enable()`
  2. `drm_atomic_helper_commit_encoder_bridge_pre_enable()`
  3. `drm_atomic_helper_commit_encoder_bridge_enable()`: the encoder enable,
     then bridges `atomic_enable`
- Each stage loops over every connector in the commit, or every CRTC for the
  two CRTC stages, before the next stage starts; the order is not per
  encoder.
- The stages are exported, and a driver may order them differently:
  `tidss_atomic_commit_tail()` in `drivers/gpu/drm/tidss/tidss_kms.c` runs
  pre_enable before the CRTC enable and post_disable after the CRTC disable.
- A bridge driver therefore cannot assume the CRTC state in
  `atomic_pre_enable` or `atomic_post_disable`.
- `pre_enable_prev_first` on a bridge: the previous bridge's
  `atomic_pre_enable` runs before this bridge's, and this bridge's
  `atomic_post_disable` runs before the previous bridge's.
- Non-atomic callbacks: `struct drm_bridge_funcs` has no `pre_enable`,
  `enable`, `disable` or `post_disable` member; the chain helpers call only
  the `atomic_` ones, with no fallback.
- `mode_fixup` and `mode_set` are the non-atomic members that remain.
- Atomic callback argument: `struct drm_atomic_commit *`.
- State hooks: there is no atomic_reset member; `atomic_create_state` takes
  its place, see `drm_atomic_helper_bridge_create_state()`.
- `drm_atomic_bridge_chain_pre_enable()`, `drm_atomic_bridge_chain_enable()`,
  `drm_atomic_bridge_chain_disable()` and
  `drm_atomic_bridge_chain_post_disable()` hold `encoder->bridge_chain_mutex`
  while they call the callbacks, so a callback must not walk the chain with
  `drm_for_each_bridge_in_chain()` or attach a bridge to that encoder.
