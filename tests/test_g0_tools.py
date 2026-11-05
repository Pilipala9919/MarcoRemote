import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parents[1]/"tools"/(name+".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


probe = load("g0_probe")
session = load("g0_session")


class GuardTests(unittest.TestCase):
    def test_key_allowlist(self):
        self.assertEqual(session.key_for("left"), "DPAD_LEFT")
        for forbidden in ("power", "enter", "home", "shell", "text", "DPAD_CENTER"):
            with self.assertRaises(KeyError):
                session.key_for(forbidden)

    def test_refusal_not_success(self):
        with patch.object(probe.socket, "create_connection", side_effect=ConnectionRefusedError(10061, "refused")):
            result = probe.tcp_probe("test", 6467, "source")
        self.assertEqual(result["result"], "ConnectionRefusedError")

    def test_timeout_not_absence(self):
        with patch.object(probe.socket, "create_connection", side_effect=TimeoutError()):
            self.assertEqual(probe.tcp_probe("test", 6467, "source")["result"], "TimeoutError")

    def test_source_bound_and_socket_closed(self):
        sock = MagicMock()
        with patch.object(probe.socket, "create_connection", return_value=sock) as connect:
            self.assertEqual(probe.tcp_probe("test", 6466, "source")["result"], "tcp_open")
        connect.assert_called_once_with(("test", 6466), 3, ("source", 0))
        sock.__exit__.assert_called_once()


if __name__ == "__main__":
    unittest.main()
