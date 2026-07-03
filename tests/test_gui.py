import builtins
import importlib
import sys
from unittest.mock import ANY
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from oemof.eesyplan.gui import select_value


class TestSelectValue:
    """Tests for the select_value function."""

    @patch("oemof.eesyplan.gui.ttk")
    @patch("oemof.eesyplan.gui.tk")
    def test_select_value_with_selection(self, mock_tk, mock_ttk):
        """Test select_value when user makes a selection."""
        mock_root = MagicMock()
        mock_tk.Tk.return_value = mock_root

        mock_combo = MagicMock()
        mock_combo.get.return_value = "Option 2"
        mock_ttk.Combobox.return_value = mock_combo
        mock_ttk.Label.return_value = MagicMock()

        def bind_side_effect(event, callback):
            callback(None)

        mock_combo.bind.side_effect = bind_side_effect

        result = select_value(["Option 1", "Option 2", "Option 3"])

        assert result == "Option 2"
        mock_root.destroy.assert_called_once()

    @patch("oemof.eesyplan.gui.ttk")
    @patch("oemof.eesyplan.gui.tk")
    def test_select_value_no_selection(self, mock_tk, mock_ttk):
        """Test select_value when user closes window without selection."""
        mock_root = MagicMock()
        mock_tk.Tk.return_value = mock_root

        mock_combo = MagicMock()
        mock_ttk.Combobox.return_value = mock_combo
        mock_ttk.Label.return_value = MagicMock()

        result = select_value(["Option 1", "Option 2"])

        assert result == "None"

    @patch("oemof.eesyplan.gui.ttk")
    @patch("oemof.eesyplan.gui.tk")
    def test_select_value_window_properties(self, mock_tk, mock_ttk):
        """Test that window is created with correct properties."""
        mock_root = MagicMock()
        mock_tk.Tk.return_value = mock_root
        mock_ttk.Combobox.return_value = MagicMock()
        mock_ttk.Label.return_value = MagicMock()

        select_value(["Option 1"])

        mock_root.title.assert_called_once_with("Model Selection")
        mock_root.geometry.assert_called_once_with("450x80")
        mock_root.mainloop.assert_called_once()

    @patch("oemof.eesyplan.gui.ttk")
    @patch("oemof.eesyplan.gui.tk")
    def test_select_value_combobox_configuration(self, mock_tk, mock_ttk):
        """Test that combobox is configured correctly."""
        mock_root = MagicMock()
        mock_tk.Tk.return_value = mock_root

        mock_combo = MagicMock()
        mock_ttk.Combobox.return_value = mock_combo
        mock_ttk.Label.return_value = MagicMock()

        choices = ["Model A", "Model B", "Model C"]

        select_value(choices)

        mock_ttk.Combobox.assert_called_once_with(
            mock_root, values=choices, width=50, state="readonly"
        )
        mock_combo.pack.assert_called_once()
        mock_combo.bind.assert_called_once_with("<<ComboboxSelected>>", ANY)

    @patch("oemof.eesyplan.gui.ttk")
    @patch("oemof.eesyplan.gui.tk")
    def test_select_value_empty_choices(self, mock_tk, mock_ttk):
        """Test select_value with empty choices list."""
        mock_root = MagicMock()
        mock_tk.Tk.return_value = mock_root
        mock_ttk.Combobox.return_value = MagicMock()
        mock_ttk.Label.return_value = MagicMock()

        result = select_value([])

        assert result == "None"

    @patch("oemof.eesyplan.gui.ttk")
    @patch("oemof.eesyplan.gui.tk")
    def test_select_value_single_choice(self, mock_tk, mock_ttk):
        """Test select_value with a single choice."""
        mock_root = MagicMock()
        mock_tk.Tk.return_value = mock_root

        mock_combo = MagicMock()
        mock_combo.get.return_value = "Only Option"
        mock_ttk.Combobox.return_value = mock_combo
        mock_ttk.Label.return_value = MagicMock()

        def bind_side_effect(event, callback):
            callback(None)

        mock_combo.bind.side_effect = bind_side_effect

        result = select_value(["Only Option"])

        assert result == "Only Option"

    @patch("oemof.eesyplan.gui.tk", None)
    def test_select_value_raises_import_error_when_tkinter_missing(self):
        """Test select_value raises ImportError if tkinter is unavailable."""
        with pytest.raises(
            ImportError,
            match=r"Tkinter not installed. Try 'pip install tkinter'",
        ):
            select_value(["Option 1"])


def test_gui_module_sets_tk_and_ttk_to_none_when_tkinter_import_fails():
    """Test module import fallback when tkinter import fails."""
    original_import = builtins.__import__
    original_module = sys.modules.get("oemof.eesyplan.gui")

    def mocked_import(name, *args, **kwargs):
        if name == "tkinter":
            raise ImportError("No module named tkinter")
        return original_import(name, *args, **kwargs)

    try:
        sys.modules.pop("oemof.eesyplan.gui", None)

        with patch("builtins.__import__", side_effect=mocked_import):
            gui = importlib.import_module("oemof.eesyplan.gui")

        assert gui.tk is None
        assert gui.ttk is None

        with pytest.raises(
            ImportError,
            match=r"Tkinter not installed. Try 'pip install tkinter'",
        ):
            gui.select_value(["Option 1"])
    finally:
        sys.modules.pop("oemof.eesyplan.gui", None)
        if original_module is not None:
            sys.modules["oemof.eesyplan.gui"] = original_module
