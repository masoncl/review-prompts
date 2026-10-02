- `enum cxl_decoder_state` has three values; `CXL_DECODER_STATE_AUTO_STAGED`
  is the third.

| Transition | Where | When |
|---|---|---|
| to `CXL_DECODER_STATE_AUTO` | `init_hdm_decoder()`, `cxl_setup_hdm_decoder_from_dvsec()` | committed endpoint decoder, after DPA is reserved |
| `CXL_DECODER_STATE_AUTO` to `CXL_DECODER_STATE_AUTO_STAGED` | `cxl_region_attach_auto()` | decoder put in the first free `p->targets[]` slot |
| `CXL_DECODER_STATE_AUTO_STAGED` to `CXL_DECODER_STATE_AUTO` | `cxl_rr_ep_add()` | the endpoint decoder's `cxld->region` is set |
| `CXL_DECODER_STATE_AUTO_STAGED` to `CXL_DECODER_STATE_AUTO` | `cxl_region_remove_target()` | staged decoder unregistered with no `cxld->region` |
| to `CXL_DECODER_STATE_MANUAL` | `cxl_decoder_reset()` | after the hardware reset |

- `cxl_region_sort_targets()`: writes `cxled->pos` and reorders
  `p->targets[]`, never the state.
- `cxl_decoder_reset()`: returns early without `CXL_DECODER_F_ENABLE` or with
  `CXL_DECODER_F_LOCK`, and then leaves the state alone.
- Failed assembly on the last target: `cxl_region_attach()` returns the error,
  targets stay in `p->targets[]`, the region stays
  `CXL_CONFIG_INTERLEAVE_ACTIVE`.
- `discover_region()`: skips decoders without `CXL_DECODER_F_ENABLE` or not in
  `CXL_DECODER_STATE_AUTO`; it has no DPA test.
- Lookup: `cxl_find_region_by_range()`; there is no cxl_region_find() here.
- `match_region_by_range()`: matches through `spa_maps_hpa()`, which adds
  `p->cache_size` to the region start.
- Range, ways and granularity: taken from `struct cxl_region_context`, which
  the root's `translation_setup_root` op may rewrite in
  `get_cxl_root_decoder()`.
- `attach_target()` result in `cxl_add_to_region()`: ignored; the function
  returns 0 when the attach failed.
