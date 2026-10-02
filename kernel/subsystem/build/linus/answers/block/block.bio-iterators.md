- There is no bio_last_bvec_all() in this tree.
- `bio_first_bvec_all()`: the only helper in `include/linux/bio.h` that tests
  `BIO_CLONED`.
- Helpers that reach that test through `bio_first_bvec_all()`:
  `bio_first_page_all()`, `bio_first_folio_all()`, `bio_first_folio()`,
  `bio_for_each_folio_all()`, `bio_for_each_bvec_all()`.
- `bio_for_each_segment_all()`: no `BIO_CLONED` test; `bio_next_segment()`
  only compares the index with `bi_vcnt`.
- `bio_first_bvec_all()` on a flagged bio: warns once and still returns
  `bi_io_vec`.
- `bi_vcnt` in a clone from `bio_alloc_clone()` or `bio_init_clone()`: 0, so
  `bio_for_each_segment_all()` on a clone visits nothing and reports nothing.
- `bio_iov_iter_set()` in `block/bio.c` (there is no bio_iov_bvec_set() here):
  points `bi_io_vec` at the caller's `ITER_BVEC` array, sets `BIO_CLONED` and
  does not set `bi_vcnt`, so the submitter of such a bio cannot use the "_all"
  helpers on it either.
- There is no bio_for_each_folio() here; `bio_for_each_folio_all()` is the
  only folio iterator and it is for the owner.
- There is no bi_bvec_done here; the offset into the current bvec is
  `bi_offset` in `struct bvec_iter`.
- There is no __blk_bios_map_sg() here.
- **Potentially unsafe usage**: reading `bi_io_vec` or `bi_vcnt`, or calling
  an "_all" helper.
  - Unsafe: on a bio received through `->submit_bio` or in a request, from
    index 0 or bounded by `bi_vcnt`. The bio may be the remainder that
    `bio_split()` left: `BIO_CLONED` is clear and `bi_vcnt` is unchanged, but
    `bi_iter` was advanced, so the walk covers the pages of the split-off
    front and nothing warns.
  - Safe: on a bio the caller allocated and filled itself, as
    `mpage_read_end_io()` in `fs/mpage.c` does; the comment above
    `bio_for_each_segment_all()` and the test in `bio_first_bvec_all()` state
    the requirement.
  - Safe: reading `bi_io_vec` at the position `bi_iter` gives, with
    `__bvec_iter_bvec(bio->bi_io_vec, bio->bi_iter)` and `bi_iter.bi_offset`,
    as `lo_rw_aio()` in `drivers/block/loop.c` does for a single-bio request.
