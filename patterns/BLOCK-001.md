# BLOCK-001: Bio operation type safety

**Risk**: NULL pointer dereference or incorrect behavior when handling different bio operation types

**When to check**: Mandatory when code accesses bio data fields (bi_io_vec, bi_vcnt) or calls helpers that access these fields

Place each step defined below into TodoWrite.

**Mandatory bio operation type validation:**
- step 1: Place into TodoWrite all functions that receive bio or request parameters (new or modified)
  - Output: function name, and a random line from anywhere in each definition
    - you must prove you read the function
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

**After analysis:** Issues found: [none OR list]
