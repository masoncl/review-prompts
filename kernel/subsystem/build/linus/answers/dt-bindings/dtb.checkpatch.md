| Type | Fires when | Reads |
|---|---|---|
| `DT_SPLIT_BINDING_PATCH` | two consecutive files in the patch differ in whether the path starts with `Documentation/devicetree/` or `include/dt-bindings/` | file names from `diff --git` and `+++` lines |
| `DT_SCHEMA_BINDING_PATCH` | `new file mode` line for a `.txt` file anywhere under `Documentation/devicetree/bindings/` | that line and the file name |
| `UNDOCUMENTED_DT_STRING` (string) | `grep -Erq` of the bindings directory finds no match | added line, working tree |
| `UNDOCUMENTED_DT_STRING` (vendor) | `"^vendor,.*":` not in `vendor-prefixes.yaml` | added line, that file |
| `SPDX_LICENSE_TAG` (headers) | file under `include/dt-bindings/` whose tag lacks `GPL-2.0-only OR <anything>` (`GPL-2.0 OR` also passes) | added SPDX line |
| `UNCOMMENTED_RGMII_MODE` | `phy-mode` or `phy-connection-type` set to `"rgmii"`, `"rgmii-rxid"` or `"rgmii-txid"` with no comment | added line of a `.dts`, `.dtsi` or `.dtso` file |

- `DT_SPLIT_BINDING_PATCH` path test: all of `Documentation/devicetree/`, not
  only `Documentation/devicetree/bindings/`.
- `DT_SPLIT_BINDING_PATCH` and `MAINTAINERS`: that file is skipped, so a
  binding patch that also edits `MAINTAINERS` does not warn.
- `DT_SPLIT_BINDING_PATCH` count: one warning per switch between the two kinds,
  in the order the files appear in the patch.
- `UNDOCUMENTED_DT_STRING` files: only `.dts` and `.dtsi` (line starts
  `compatible = "`) and `.c` and `.h` (line contains `.compatible = "`);
  `.dtso` and `.yaml` files are not tested, so binding examples are not.
- `UNDOCUMENTED_DT_STRING` lines: only an added line that itself holds
  `compatible =`; every quoted string on that line is tested, strings on
  continuation lines are not.
- `UNDOCUMENTED_DT_STRING` skips strings that start `pciclass,`, `pci` plus
  2-4 hex digits and a comma, or `usb`/`usbif` plus 1-4 hex digits and a comma.
- `UNDOCUMENTED_DT_STRING` lookup: plain `grep`, not `git grep`; the string is
  used as an unanchored extended regex, so a match inside a longer string in
  any file under the bindings directory silences the warning.
- `UNDOCUMENTED_DT_STRING` with `--no-tree`: skipped unless `--root` is given,
  since the test is `defined $root`.
- `SPDX_LICENSE_TAG` for headers: always `WARN`, and `--fix` does not rewrite
  it; the binding-document variant is `CHK` with `-f` and is rewritten by
  `--fix`.
- Both `SPDX_LICENSE_TAG` licence tests: read only line 1 of the file (line 2
  after a `#!` line), and only when the patch adds that line.
