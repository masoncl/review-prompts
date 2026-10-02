- Return type: `int`, not `bool`; for a supported log it is the 16-bit
  directory entry, the number of pages in the log.
- `ata_dev_config_cpr()`: uses the value as the number of sectors to allocate
  and read, so the count must be kept.
