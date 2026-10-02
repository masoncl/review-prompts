- Value compared: `of_property_read_reg(np, 0, &of_node_addr, NULL)` in
  `drivers/of/address.c`, the first `reg` address, untranslated.
- `mfd_match_of_node_to_dev()` does not call `of_translate_address()` or
  `of_address_to_resource()`.
- Without `CONFIG_OF_ADDRESS`: `of_property_read_reg()` is a stub in
  `include/linux/of_address.h` that returns `-ENOSYS`; a `use_of_reg` cell
  then gets `-EAGAIN` for every node.
