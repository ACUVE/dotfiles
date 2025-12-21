"""Tests for Docker credential storage helper."""

import json
from unittest.mock import MagicMock, patch


from cli.docker_credential_storage import (
    _cmd_erase,
    _cmd_get,
    _cmd_list,
    _cmd_store,
    main,
)
from cli.docker_credential.bitwarden import (
    BitwardenError,
)


class TestCmdGet:
    """Tests for the get command."""

    @patch("cli.docker_credential_storage.check_bw_status")
    @patch("cli.docker_credential_storage.get_all_credentials")
    @patch("builtins.print")
    def test_get_success(
        self, mock_print: MagicMock, mock_get_all: MagicMock, mock_check: MagicMock
    ) -> None:
        """Test successful credential retrieval."""
        mock_get_all.return_value = {
            "https://index.docker.io/v1/": {
                "Username": "testuser",
                "Secret": "testpass",
            }
        }

        _cmd_get("https://index.docker.io/v1/")

        # Verify output
        mock_print.assert_called_once()
        output = json.loads(mock_print.call_args[0][0])
        assert output["ServerURL"] == "https://index.docker.io/v1/"
        assert output["Username"] == "testuser"
        assert output["Secret"] == "testpass"

    @patch("cli.docker_credential_storage.check_bw_status")
    @patch("cli.docker_credential_storage.get_all_credentials")
    @patch("cli.docker_credential_storage.output_error")
    def test_get_not_found(
        self,
        mock_error: MagicMock,
        mock_get_all: MagicMock,
        mock_check: MagicMock,
    ) -> None:
        """Test get when credential not found."""
        mock_get_all.return_value = {}
        _cmd_get("https://index.docker.io/v1/")
        mock_error.assert_called_once_with("credentials not found")

    @patch("cli.docker_credential_storage.check_bw_status")
    @patch("cli.docker_credential_storage.get_all_credentials")
    @patch("cli.docker_credential_storage.output_error")
    def test_get_invalid_format(
        self,
        mock_error: MagicMock,
        mock_get_all: MagicMock,
        mock_check: MagicMock,
    ) -> None:
        """Test get with invalid credential format."""
        mock_get_all.return_value = {
            "https://index.docker.io/v1/": {
                "Username": "testuser",
                # Missing Secret
            }
        }
        _cmd_get("https://index.docker.io/v1/")
        mock_error.assert_called_once_with("invalid credentials format")

    @patch("cli.docker_credential_storage.check_bw_status")
    @patch("cli.docker_credential_storage.output_error")
    def test_get_bitwarden_error(
        self, mock_error: MagicMock, mock_check: MagicMock
    ) -> None:
        """Test get when Bitwarden raises an error."""
        mock_check.side_effect = BitwardenError("Bitwarden is locked")
        _cmd_get("https://index.docker.io/v1/")
        mock_error.assert_called_once_with("Bitwarden is locked")


class TestCmdStore:
    """Tests for the store command."""

    @patch("cli.docker_credential_storage.check_bw_status")
    @patch("cli.docker_credential_storage.get_all_credentials")
    @patch("cli.docker_credential_storage.save_all_credentials")
    @patch("sys.exit")
    def test_store_success(
        self,
        mock_exit: MagicMock,
        mock_save: MagicMock,
        mock_get_all: MagicMock,
        mock_check: MagicMock,
    ) -> None:
        """Test successful store command."""
        mock_get_all.return_value = {}

        input_data = {
            "ServerURL": "https://index.docker.io/v1/",
            "Username": "testuser",
            "Secret": "testpass",
        }
        _cmd_store(input_data)

        # Verify save was called with updated credentials
        mock_save.assert_called_once()
        saved_creds = mock_save.call_args[0][1]
        assert saved_creds["https://index.docker.io/v1/"]["Username"] == "testuser"
        assert saved_creds["https://index.docker.io/v1/"]["Secret"] == "testpass"
        mock_exit.assert_called_once_with(0)

    @patch("cli.docker_credential_storage.output_error")
    def test_store_invalid_input(self, mock_error: MagicMock) -> None:
        """Test store with invalid input."""
        input_data = {
            "ServerURL": "https://index.docker.io/v1/",
            # Missing Username and Secret
        }
        _cmd_store(input_data)
        mock_error.assert_called_once()
        assert "invalid input" in mock_error.call_args[0][0]

    @patch("cli.docker_credential_storage.check_bw_status")
    @patch("cli.docker_credential_storage.output_error")
    def test_store_check_status_error(
        self, mock_error: MagicMock, mock_check: MagicMock
    ) -> None:
        """Test store when Bitwarden status check fails."""
        mock_check.side_effect = BitwardenError("Bitwarden is locked")
        input_data = {
            "ServerURL": "https://index.docker.io/v1/",
            "Username": "testuser",
            "Secret": "testpass",
        }
        _cmd_store(input_data)
        mock_error.assert_called_once_with("Bitwarden is locked")

    @patch("cli.docker_credential_storage.check_bw_status")
    @patch("cli.docker_credential_storage.get_all_credentials")
    @patch("cli.docker_credential_storage.save_all_credentials")
    @patch("cli.docker_credential_storage.output_error")
    def test_store_save_error(
        self,
        mock_error: MagicMock,
        mock_save: MagicMock,
        mock_get_all: MagicMock,
        mock_check: MagicMock,
    ) -> None:
        """Test store when save fails."""
        mock_get_all.return_value = {}
        mock_save.side_effect = BitwardenError("Failed to save")
        input_data = {
            "ServerURL": "https://index.docker.io/v1/",
            "Username": "testuser",
            "Secret": "testpass",
        }
        _cmd_store(input_data)
        mock_error.assert_called_once_with("Failed to save")


class TestCmdErase:
    """Tests for the erase command."""

    @patch("cli.docker_credential_storage.check_bw_status")
    @patch("cli.docker_credential_storage.get_all_credentials")
    @patch("sys.exit")
    def test_erase_not_exists(
        self,
        mock_exit: MagicMock,
        mock_get_all: MagicMock,
        mock_check: MagicMock,
    ) -> None:
        """Test erase when credential doesn't exist."""
        mock_get_all.return_value = {}
        _cmd_erase("https://index.docker.io/v1/")
        mock_exit.assert_called_once_with(0)

    @patch("cli.docker_credential_storage.check_bw_status")
    @patch("cli.docker_credential_storage.get_all_credentials")
    @patch("cli.docker_credential_storage.save_all_credentials")
    @patch("sys.exit")
    def test_erase_success(
        self,
        mock_exit: MagicMock,
        mock_save: MagicMock,
        mock_get_all: MagicMock,
        mock_check: MagicMock,
    ) -> None:
        """Test successful erase command."""
        mock_get_all.return_value = {
            "https://index.docker.io/v1/": {
                "Username": "testuser",
                "Secret": "testpass",
            }
        }
        _cmd_erase("https://index.docker.io/v1/")

        # Verify save was called with credential removed
        mock_save.assert_called_once()
        saved_creds = mock_save.call_args[0][1]
        assert "https://index.docker.io/v1/" not in saved_creds
        mock_exit.assert_called_once_with(0)

    @patch("cli.docker_credential_storage.check_bw_status")
    @patch("cli.docker_credential_storage.output_error")
    def test_erase_check_status_error(
        self, mock_error: MagicMock, mock_check: MagicMock
    ) -> None:
        """Test erase when Bitwarden status check fails."""
        mock_check.side_effect = BitwardenError("Bitwarden is locked")
        _cmd_erase("https://index.docker.io/v1/")
        mock_error.assert_called_once_with("Bitwarden is locked")

    @patch("cli.docker_credential_storage.check_bw_status")
    @patch("cli.docker_credential_storage.get_all_credentials")
    @patch("cli.docker_credential_storage.save_all_credentials")
    @patch("cli.docker_credential_storage.output_error")
    def test_erase_save_error(
        self,
        mock_error: MagicMock,
        mock_save: MagicMock,
        mock_get_all: MagicMock,
        mock_check: MagicMock,
    ) -> None:
        """Test erase when save fails."""
        mock_get_all.return_value = {
            "https://index.docker.io/v1/": {
                "Username": "testuser",
                "Secret": "testpass",
            }
        }
        mock_save.side_effect = BitwardenError("Failed to save")
        _cmd_erase("https://index.docker.io/v1/")
        mock_error.assert_called_once_with("Failed to save")


class TestCmdList:
    """Tests for the list command."""

    @patch("cli.docker_credential_storage.check_bw_status")
    @patch("cli.docker_credential_storage.get_all_credentials")
    @patch("builtins.print")
    @patch("sys.exit")
    def test_list_success(
        self,
        mock_exit: MagicMock,
        mock_print: MagicMock,
        mock_get_all: MagicMock,
        mock_check: MagicMock,
    ) -> None:
        """Test successful list command."""
        mock_get_all.return_value = {
            "https://index.docker.io/v1/": {
                "Username": "testuser",
                "Secret": "testpass",
            },
            "https://gcr.io": {
                "Username": "gcr-user",
                "Secret": "gcr-pass",
            },
        }

        _cmd_list()

        # Verify output
        mock_print.assert_called_once()
        output = json.loads(mock_print.call_args[0][0])
        assert output["https://index.docker.io/v1/"] == "testuser"
        assert output["https://gcr.io"] == "gcr-user"
        mock_exit.assert_called_once_with(0)

    @patch("cli.docker_credential_storage.check_bw_status")
    @patch("cli.docker_credential_storage.get_all_credentials")
    @patch("builtins.print")
    @patch("sys.exit")
    def test_list_empty(
        self,
        mock_exit: MagicMock,
        mock_print: MagicMock,
        mock_get_all: MagicMock,
        mock_check: MagicMock,
    ) -> None:
        """Test list when no credentials exist."""
        mock_get_all.return_value = {}

        _cmd_list()

        mock_print.assert_called_once_with("{}")
        mock_exit.assert_called_once_with(0)

    @patch("cli.docker_credential_storage.check_bw_status")
    @patch("cli.docker_credential_storage.output_error")
    def test_list_check_status_error(
        self, mock_error: MagicMock, mock_check: MagicMock
    ) -> None:
        """Test list when Bitwarden status check fails."""
        mock_check.side_effect = BitwardenError("Bitwarden is locked")
        _cmd_list()
        mock_error.assert_called_once_with("Bitwarden is locked")


class TestMainFunction:
    """Tests for the main entry point."""

    @patch("sys.stdin")
    @patch("cli.docker_credential_storage._cmd_get")
    def test_main_get_command(self, mock_cmd: MagicMock, mock_stdin: MagicMock) -> None:
        """Test main function with get command."""
        mock_stdin.read.return_value = "https://index.docker.io/v1/\n"

        main("get")

        mock_cmd.assert_called_once_with("https://index.docker.io/v1/")

    @patch("sys.stdin")
    @patch("cli.docker_credential_storage._cmd_store")
    def test_main_store_command(
        self, mock_cmd: MagicMock, mock_stdin: MagicMock
    ) -> None:
        """Test main function with store command."""
        mock_stdin.read.return_value = '{"ServerURL":"https://index.docker.io/v1/","Username":"user","Secret":"pass"}'

        main("store")

        mock_cmd.assert_called_once()

    @patch("sys.stdin")
    @patch("cli.docker_credential_storage.output_error")
    def test_main_store_invalid_json(
        self, mock_error: MagicMock, mock_stdin: MagicMock
    ) -> None:
        """Test main function with invalid JSON for store command."""
        mock_stdin.read.return_value = "invalid json"

        main("store")

        mock_error.assert_called_once()
        assert "invalid JSON input" in mock_error.call_args[0][0]

    @patch("sys.stdin")
    @patch("cli.docker_credential_storage._cmd_erase")
    def test_main_erase_command(
        self, mock_cmd: MagicMock, mock_stdin: MagicMock
    ) -> None:
        """Test main function with erase command."""
        mock_stdin.read.return_value = "https://index.docker.io/v1/\n"

        main("erase")

        mock_cmd.assert_called_once_with("https://index.docker.io/v1/")

    @patch("cli.docker_credential_storage._cmd_list")
    def test_main_list_command(self, mock_cmd: MagicMock) -> None:
        """Test main function with list command."""
        main("list")

        mock_cmd.assert_called_once()

    @patch("cli.docker_credential_storage.output_error")
    def test_main_unknown_command(self, mock_error: MagicMock) -> None:
        """Test main function with unknown command."""
        main("unknown")

        mock_error.assert_called_once()
        assert "Unknown command" in mock_error.call_args[0][0]
