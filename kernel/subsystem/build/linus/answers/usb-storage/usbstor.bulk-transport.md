- CSW `Signature`: a value other than `US_BULK_CS_SIGN` is not rejected. The
  first one seen is stored in `us->bcs_signature`; a later CSW that differs
  returns `USB_STOR_TRANSPORT_ERROR`.
- There is no Olympus signature constant in this tree.
- `US_FL_IGNORE_RESIDUE` affects only the residue; `US_FL_BULK32` only the
  CBW length. Neither relaxes the signature check.
- `Tag` mismatch: accepted when `US_FL_BULK_IGNORE_TAG` is set.
- Check order: `Tag` and `Status` first, then `Signature`. A signature is
  learnt only from a CSW that passed the first two.
- `us->bcs_signature`: never cleared, so it survives resets.
- `usb_stor_Bulk_transport()` does no reset itself; see "Recovery after a
  transport error".
- Tolerances and the reason the code gives:

| Deviation | What the code does | Reason given |
|---|---|---|
| odd CSW signature | learns the first one | broken devices report odd signatures |
| zero-length CSW | reads the CSW once more | devices append needless zero-length packets to data |
| data phase skipped, no ZLP | 13-byte short IN treated as the CSW | device went straight to status |
| babble (`USB_STOR_XFER_LONG`) | still reads CSW; fake sense `usb_stor_sense_invalidCDB` if `Status` is `US_BULK_STAT_OK` | spec requires the CSW; retry is pointless |
| bogus residue | sets `US_FL_IGNORE_RESIDUE` | heuristic on full 36-byte `INQUIRY` or 8-byte `READ_CAPACITY` |

- Skipped data phase: the 13 bytes are tested against `US_BULK_CS_SIGN`, not
  against `us->bcs_signature`.
- Skipped data phase: the first `US_BULK_CS_WRAP_LEN` bytes of the command's
  transfer buffer are zeroed so CSW bytes do not leak to the caller; resid is
  set to the full length; the `Tag`, `Status` and `Signature` checks then run
  as usual.
