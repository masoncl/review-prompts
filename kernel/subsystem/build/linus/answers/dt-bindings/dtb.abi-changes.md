- Direction that `Documentation/devicetree/bindings/ABI.rst` guarantees: a
  newer kernel does not break on an older device tree; it says nothing of a
  newer device tree on an older kernel.
- DTS change incompatible with old kernels:
  `Documentation/process/maintainer-soc.rst` allows it, applied no earlier than
  the driver change, and pointed out in the patch description and pull request.
- Incompatible binding change, two requirements from two documents:
  - `ABI.rst`: change the compatible string at the same time; the driver can
    bind against both old and new.
  - `Documentation/devicetree/bindings/writing-bindings.rst`: DON'T break the
    ABI without "explicit and detailed rationale" and a statement of impact.
- Other users of the ABI, by document; none names a specific project:

  | Document | Wording |
  |---|---|
  | `writing-bindings.rst` | "other open-source upstream projects" |
  | `Documentation/devicetree/bindings/submitting-patches.rst` | "multiple projects other than the Linux Kernel" |
  | `maintainer-soc.rst` | "bootloaders or other operating systems" |
  | `ABI.rst` | names none |

- Constraints are ABI: `writing-bindings.rst` counts the number of entries,
  the possible values and the order of a property as ABI.
- `deprecated: true`: no `.rst` file under `Documentation/devicetree/` mentions
  it; it is practice in the schemas, not a written requirement.
- **Potentially unsafe usage**: renaming a property of an existing binding
  under the same compatible.
  - Unsafe: when the driver reads only the new name; a device tree written to
    the old binding then breaks, against rule II.3 of `ABI.rst`.
  - Safe: when the driver still reads the old names, as
    `fwnode_get_phy_node()` in `drivers/net/phy/phy_device.c` does for `phy`
    and `phy-device`, which
    `Documentation/devicetree/bindings/net/ethernet-controller.yaml` marks
    `deprecated: true`.
