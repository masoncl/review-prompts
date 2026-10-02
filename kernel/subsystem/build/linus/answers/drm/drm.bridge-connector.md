- How `drm_bridge_connector_init()` picks, per op:

  | Op bit | Several bridges set it |
  |---|---|
  | `DRM_BRIDGE_OP_HPD`, `DRM_BRIDGE_OP_DETECT` | last in chain wins |
  | `DRM_BRIDGE_OP_EDID`, `DRM_BRIDGE_OP_MODES` | picked as a pair, see below |
  | `DRM_BRIDGE_OP_HDMI` | second one: `-EBUSY` |
  | `DRM_BRIDGE_OP_HDMI_AUDIO`, `DRM_BRIDGE_OP_DP_AUDIO` | second of either: `-EBUSY` |
  | `DRM_BRIDGE_OP_HDMI_CEC_NOTIFIER`, `DRM_BRIDGE_OP_HDMI_CEC_ADAPTER` | second of either: `-EBUSY` |

- EDID and MODES pair: a later bridge that sets either bit clears both
  earlier picks, so a MODES-only bridge after an EDID bridge leaves no EDID
  bridge.
- CEC: one bridge that sets both CEC bits also gets `-EBUSY`, since both use
  `bridge_hdmi_cec`.
- Connector type: taken from the last bridge in the chain only
  (`drm_bridge_is_last()`); `DRM_MODE_CONNECTOR_Unknown` there returns
  `-EINVAL`.
- `drm_connector_attach_encoder()`: called by `drm_bridge_connector_init()`
  itself.
- `DRM_BRIDGE_OP_HPD`: `hpd_enable` and `hpd_disable` are optional;
  `drm_bridge_hpd_enable()` tests them for NULL.
- `detect`, `edid_read`, `get_modes`: not checked at init and called with no
  NULL test once the op bit is set.
- Infoframes: `struct drm_bridge_funcs` has one write and one clear callback
  per type, for example `hdmi_write_avi_infoframe`.
  - AVI and HDMI pairs: required with `DRM_BRIDGE_OP_HDMI`, else `-EINVAL`.
  - Audio pair: required when the same bridge sets `DRM_BRIDGE_OP_HDMI_AUDIO`.
  - HDR and SPD pairs: required with `DRM_BRIDGE_OP_HDMI_HDR_DRM_INFOFRAME`
    and `DRM_BRIDGE_OP_HDMI_SPD_INFOFRAME`.
- Optional callbacks: `hdmi_tmds_char_rate_valid`, `hdmi_audio_startup`,
  `hdmi_audio_mute_stream`, `hdmi_cec_init` and the `dp_audio_` equivalents.
- Audio ops: `-EINVAL` unless `hdmi_audio_max_i2s_playback_channels` or
  `hdmi_audio_spdif_playback` is set, and unless prepare and shutdown exist.
- `DRM_BRIDGE_OP_HDMI` chain, checked in `drmm_connector_hdmi_init()`:
  - last bridge `type` must be `DRM_MODE_CONNECTOR_HDMIA` or
    `DRM_MODE_CONNECTOR_HDMIB`
  - `vendor` and `product` must be non-NULL and no longer than
    `DRM_CONNECTOR_HDMI_VENDOR_LEN` and `DRM_CONNECTOR_HDMI_PRODUCT_LEN`
  - `supported_formats` must include RGB444; zero is replaced by RGB444 only
  - `connector->ycbcr_420_allowed` must equal the YCbCr 4:2:0 bit of
    `supported_formats`
  - `max_bpc` must be 8, 10 or 12; zero is replaced by 8
- `drm_bridge_add()`: for an HDMI bridge it sets `ycbcr_420_allowed` from
  `supported_formats`, so `ops` and `supported_formats` must be set first.
- EDID with an HDMI bridge: read from `drm_bridge_connector_detect()`, only
  if some bridge sets `DRM_BRIDGE_OP_DETECT`, and from
  `drm_bridge_connector_force()`; `drm_bridge_connector_get_modes()` then
  only adds modes.
- `DRM_BRIDGE_ATTACH_NO_CONNECTOR` absent: bridges that cannot create a
  connector fail attach with `-EINVAL`, for example `anx7625_bridge_attach()`.
