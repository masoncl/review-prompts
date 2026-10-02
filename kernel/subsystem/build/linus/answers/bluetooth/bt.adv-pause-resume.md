- Pause state: `hdev->advertising_paused` and `hdev->advertising_old_state`;
  neither holds `hdev->cur_adv_instance` or `HCI_LE_ADV`.
- `hdev->advertising_old_state`: holds the `HCI_ADVERTISING` bit; pause does
  not clear `HCI_ADVERTISING`, and resume only sets the flag again, so it
  selects no command.
- Extended resume, listed instances: `hci_enable_ext_advertising_sync()` for
  every entry in `hdev->adv_instances`, not
  `hci_schedule_adv_instance_sync()`.
- Extended resume, instance zero: re-enabled with
  `hci_enable_ext_advertising_sync(hdev, 0x00)` if
  `hci_dev_test_and_clear_flag(hdev, HCI_LE_ADV_0)` is true;
  `hdev->cur_adv_instance` is not read.
- `HCI_LE_ADV_0` between pause and resume: does not mean "enabled in the
  controller"; the pause's disable has `num_of_sets` 0 and its reply leaves
  the flag set.
- `HCI_LE_ADV_0` after resume: set again by the enable reply on success; if
  the enable fails it stays clear.
- Legacy resume: `hci_schedule_adv_instance_sync(hdev,
  hdev->cur_adv_instance, true)` returns `-EPERM` when `HCI_ADVERTISING` is
  set and `-ENOENT` when the instance has no entry, before any command; so
  `hci_resume_advertising_sync()` itself sends nothing for instance zero.
- Failed resume, controller: `hci_remove_ext_adv_instance_sync()` sends
  `HCI_OP_LE_REMOVE_ADV_SET` with the instance number, not `adv->handle`.
- Failed resume, list: the sync function frees nothing;
  `hci_cc_le_remove_adv_set()` calls `hci_remove_adv_instance()` and
  `mgmt_advertising_removed()` on success status only.
- Remove command fails: the entry stays in `hdev->adv_instances` with
  `enabled` false; the resume loop ignores the return value.
