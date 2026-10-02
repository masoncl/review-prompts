- `pci_read_config_dword()` and its byte, word and write siblings: return
  the bus op's result unconverted; they do not call
  `pcibios_err_to_errno()`.
- Sign of a failure: positive `PCIBIOS_BAD_REGISTER_NUMBER` or
  `PCIBIOS_DEVICE_NOT_FOUND` when the core generates it, whatever the op
  returned otherwise, which can be a negative errno.
- Misaligned offset, device not disconnected: `pci_read_config_dword()`
  returns positive `PCIBIOS_BAD_REGISTER_NUMBER` to its caller, before the
  output is written.
- `pci_user_read_config_dword()` and its byte, word and write siblings: the
  only accessors in `drivers/pci/access.c` that convert; a misaligned offset
  returns `-EINVAL` directly, output unwritten.
- Without `CONFIG_PCI`: the accessors are `_PCI_NOP` stubs in
  `include/linux/pci.h`; they return `PCIBIOS_FUNC_NOT_SUPPORTED` and leave
  the output unwritten.
- `pcibios_err_to_errno()`: a positive value that is not one of the six
  codes in its switch becomes `-ERANGE`.
- **Potentially unsafe usage**: using the value read without testing the
  return value.
  - Unsafe: when the output variable is uninitialised and the offset can be
    misaligned for the width; the `PCI_word_BAD` and `PCI_dword_BAD` tests
    return before the output is written.
  - Safe: with an aligned offset under `CONFIG_PCI`, where every path writes
    the value or all ones, and the caller tests `PCI_POSSIBLE_ERROR()`, as
    `pci_dev_config_accessible()` in `drivers/pci/pci.c` does.
