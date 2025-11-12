# BLOCK-001: Bio operation type safety

**Risk**: NULL pointer dereference or incorrect behavior when handling different bio operation types

**When to check**: Mandatory when code accesses bio data fields (bi_io_vec, bi_vcnt) or calls helpers that access these fields

**Pattern-specific TodoWrite fields**:
- Functions accessing bio data: [function] - [field/helper accessed] - [operation types supported]
- Call sites reaching function: [call site] - [operation types possible]

**Mandatory bio operation type validation:**
- step 1: Place into TodoWrite all functions that receive bio or request parameters (new or modified)
- step 2: for each function, place all accesses to bio data fields into TodoWrite:
  - Direct: bio->bi_io_vec, bio->bi_vcnt, bio->bi_iter.bi_bvec_done
  - Indirect: bio_get_first_bvec(), bio_get_last_bvec(), bio_for_each_bvec(), bio_for_each_segment()
- step 3: for each access, determine which bio operation types make that field NULL or invalid:
  - REQ_OP_READ/WRITE: bi_io_vec is valid (non-NULL), has data buffers
  - REQ_OP_DISCARD: bi_io_vec is NULL, no data buffers (sector range only)
  - REQ_OP_FLUSH: bi_io_vec is NULL, no data buffers
  - REQ_OP_WRITE_ZEROES: bi_io_vec is NULL, no data buffers
  - REQ_OP_SECURE_ERASE: bi_io_vec is NULL, no data buffers
  - Assume that ALL types of bios can reach merge paths
- step 4: trace all call paths backward to entry points (submit_bio, blk_mq_submit_bio, merge functions), add each one to TodoWrite
  - All bio operations can pass through bio merging functions
  - read helper functions definitions (bio_get_first/last_bvec(), bio_for_each_bvec() etc)
- step 5: for each call path, identify which operation types can reach the function
- step 6: verify that unsafe accesses are guarded by bio_has_data() or op_is_write()/op_is_discard() checks
  - When bi_io_vec is NULL, bio_has_data() or other guards must be used to prevent crashes

**Mandatory Self-verification gate:**

**Pattern-specific questions**:
  1. How many functions tracked with bio access? [number]
  2. How many bios tracked in TodoWrite? [number]
  3. How many bios of each OP type tracked in TodoWrite? [number per type]
  4. How many bio access sites tracked in TodoWrite? [number]
  5. How many bio access sites would crash without bio_has_data() guards? [number]

If you cannot answer ALL questions with evidence, RESTART BLOCK-001 from the beginning.
