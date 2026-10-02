| Case | Result |
|---|---|
| node has no `syscon` compatible and no entry on `syscon_list`, any lookup except `device_node_to_regmap()` | `ERR_PTR(-EPROBE_DEFER)` |
| `syscon_node_to_regmap()` with a NULL node | `ERR_PTR(-EPROBE_DEFER)` |
| `syscon_regmap_lookup_by_phandle()`, `of_parse_phandle()` returns NULL | `ERR_PTR(-ENODEV)` |
| `syscon_regmap_lookup_by_phandle_args()`, property missing | code of `of_parse_phandle_with_fixed_args()`, `-ENOENT` |
| `reg` missing or `of_iomap()` fails, on creation | `ERR_PTR(-ENOMEM)` |
| `syscon_regmap_lookup_by_phandle_optional()` with `CONFIG_MFD_SYSCON` off | NULL |

- `-EINVAL` is not returned for a node that lacks `syscon`; see
  `device_node_get_regmap()`.
- `syscon_regmap_lookup_by_phandle_optional()`: turns only `-ENODEV` into
  NULL; every other error, `-EPROBE_DEFER` included, comes back as an
  `ERR_PTR()`.
- `-ENODEV` to NULL covers a property that is present but whose phandle does
  not resolve, since `of_parse_phandle()` returns NULL for both.
- **Unsafe usage**: using the result of
  `syscon_regmap_lookup_by_phandle_optional()` after only one of the two
  tests, `IS_ERR()` or NULL; with only `IS_ERR()` a NULL reaches the regmap
  calls, with only a NULL test an `ERR_PTR(-EPROBE_DEFER)` does.
  - Safe: `IS_ERR()` at the lookup with the error returned from probe, and a
    NULL test at each use, as `rockchip_pinctrl_probe()` does for
    `regmap_ioc`.
