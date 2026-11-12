import os
import tempfile
import unittest
from unittest.mock import patch

from src.tools.west_update import west_update


class WestUpdateTests(unittest.TestCase):
    def test_nxp_selector_uses_board_filter_and_keeps_other_modules(self):
        with tempfile.TemporaryDirectory() as directory:
            open(os.path.join(directory, "west.yml"), "w", encoding="utf-8").close()
            filter_dir = os.path.join(directory, "boards", "nxp")
            os.makedirs(filter_dir)
            with open(
                os.path.join(filter_dir, "west.yaml"), "w", encoding="utf-8"
            ) as stream:
                stream.write("manifest:\n  project-filter: -hal_.*,+hal_nxp\n")

            with patch("src.tools.west_update.check_tools", return_value={"west": True}), \
                 patch(
                     "src.tools.west_update.run_command",
                     return_value={
                         "status": "success",
                         "stdout": "hal_nxp\nhal_st\nzcbor\nmcuboot\nmanifest\n",
                         "stderr": "",
                     },
                 ) as list_command, \
                 patch(
                     "src.tools.west_update._west_update_internal",
                     return_value={"status": "success", "log": [], "error": None},
                 ) as update:
                result = west_update(directory, "nxp")

            self.assertEqual(result["status"], "success")
            self.assertEqual(result["projects"], ["hal_nxp", "zcbor", "mcuboot"])
            list_command.assert_called_once_with(
                ["west", "list", "--all", "--format", "{name}"], cwd=directory
            )
            update.assert_called_once_with(directory, ["hal_nxp", "zcbor", "mcuboot"])

    def test_default_update_keeps_full_workspace_behavior(self):
        with tempfile.TemporaryDirectory() as directory:
            open(os.path.join(directory, "west.yml"), "w", encoding="utf-8").close()
            with patch("src.tools.west_update.check_tools", return_value={"west": True}), \
                 patch(
                     "src.tools.west_update._west_update_internal",
                     return_value={"status": "success", "log": [], "error": None},
                 ) as update:
                result = west_update(directory)

            self.assertEqual(result["status"], "success")
            update.assert_called_once_with(directory, None)


if __name__ == "__main__":
    unittest.main()
