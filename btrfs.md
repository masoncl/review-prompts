  | Pattern ID | Check | Risk | Details |
  |------------|-------|------|---------|
  | BT-001 | Extent map field usage correctness | Logic error/Over-read | Verify correct field usage:
    - em->len: logical file extent size
    - em->ram_bytes: uncompressed size of underlying physical extent
    - em->disk_num_bytes: compressed size on disk
    When expanding operations based on extent size, ensure the expansion
    respects intended boundaries (file extent vs physical extent) |
