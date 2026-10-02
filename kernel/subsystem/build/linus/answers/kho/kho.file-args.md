- `struct liveupdate_file_op_args` in `include/linux/liveupdate.h`: the
  retrieve result is the member `retrieve_status`; it has no member named
  `retrieved`.
- Writes LUO keeps: `serialized_data` and `private_data` after `preserve`
  returns 0, `serialized_data` after `freeze` returns 0, `file` after
  `retrieve` returns 0; a write in any other callback is discarded.
- `retrieve` returning 0 with `file` unset: `luo_retrieve_file()` calls
  `get_file()` on it without a test.
- `retrieve` input: only `handler` and `serialized_data` are set.
- `serialized_data`: LUO carries only the u64 and passes the same value to
  `can_finish` and `finish`; it never frees or reads what the value names.
- Memory named by `serialized_data`: owned by the handler, and may be gone
  before `finish`; `memfd_luo_retrieve()` in `mm/memfd_luo.c` frees it on
  success and on failure.
- `retrieve_status`: set for `can_finish` and `finish` only, 0 in every other
  callback; the success value is 1.
- `file` in `can_finish` and `finish`: NULL unless `retrieve` succeeded.
