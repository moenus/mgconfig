import pytest
import re
from unittest.mock import patch, MagicMock
import pytest
from unittest.mock import patch
from mgconfig import config_values as cvmod

import mgconfig.config_values 


@pytest.fixture
def mock_cfg_def():
    """Fixture returning a fake ConfigDef object."""
    class DummyCfgDef:
        config_id = "test_id"
        config_type = "str"
        config_default = "default_val"
        config_readonly = False
    return DummyCfgDef()


@pytest.fixture
def mock_cfg_defs(mock_cfg_def):
    """Fixture returning a fake ConfigDefs collection."""
    class DummyCfgDefs(dict):
        def values(self):
            return [mock_cfg_def]
    return DummyCfgDefs({mock_cfg_def.config_id: mock_cfg_def})


# ---------------- ConfigValue Tests ----------------

def test_configvalue_initialize_and_str(mock_cfg_def):
    with patch("mgconfig.config_values.ConfigTypes") as mock_types:
        mock_types.parse_value.return_value = (True, "parsed_val")
        mock_types.display_value.side_effect = lambda v, t: f"display:{v}"
        mock_types.output_value.side_effect = lambda v, t: f"out:{v}"

        cv = mgconfig.config_values.ConfigValue(mock_cfg_def, "raw_val", "env")
        assert str(cv) == "display:parsed_val"
        assert cv.display_current() == "display:parsed_val"
        assert cv.output_current() == "out:parsed_val"


def test_configvalue_invalid_type_raises(mock_cfg_def):
    with patch("mgconfig.config_values.ConfigTypes") as mock_types:
        mock_types.parse_value.return_value = (False, None)
        with pytest.raises(ValueError):
            mgconfig.config_values.ConfigValue(mock_cfg_def, "bad_val")


def test_configvalue_value_new_valid(mock_cfg_def):
    with patch("mgconfig.config_values.ConfigTypes") as mock_types:
        mock_types.parse_value.return_value = (True, "parsed")
        mock_types.output_value.side_effect = lambda v, t: v

        cv = mgconfig.config_values.ConfigValue(mock_cfg_def, "val")
        cv.value_new = "parsed"
        assert cv.value_new == "parsed"


def test_configvalue_value_new_invalid(mock_cfg_def):
    with patch.object(cvmod, "ConfigTypes") as mock_types:
        mock_types.parse_value.side_effect = [
            (True,  "parsed_init"),
            (False, None),
        ]
        mock_types.output_value.side_effect = lambda v, t: v

        cv = cvmod.ConfigValue(mock_cfg_def, "init")
        with pytest.raises(ValueError):
            cv.value_new = "bad"


# ---------------- ConfigValues Tests ----------------

def test_configvalues_add_and_get(mock_cfg_defs):
    with patch("mgconfig.config_values.ValueStores.retrieve_val") as mock_retrieve, \
         patch("mgconfig.config_values.ConfigValue") as mock_cv:
        mock_retrieve.return_value = ("val", "env")
        mock_cv.return_value = "ConfigValueInstance"

        cv_container = mgconfig.config_values.ConfigValues(mock_cfg_defs)
        assert cv_container["test_id"] == "ConfigValueInstance"
        assert "test_id" in cv_container
        assert list(cv_container.keys()) == ["test_id"]


def test_replace_var_basic(mock_cfg_defs):
    cv_container = mgconfig.config_values.ConfigValues.__new__(mgconfig.config_values.ConfigValues)
    cv_container._cfg_vals = {
        "FOO": MagicMock(value_src="bar"),
    }
    result = cv_container._replace_var("prefix-$(FOO)-suffix", cv_container._cfg_vals)
    assert result == "prefix-bar-suffix"


def test_replace_var_nested(mock_cfg_defs):
    cv_container = mgconfig.config_values.ConfigValues.__new__(mgconfig.config_values.ConfigValues)
    cv_container._cfg_vals = {
        "A": MagicMock(value_src="$(B)"),
        "B": MagicMock(value_src="val"),
    }
    result = cv_container._replace_var("$(A)", cv_container._cfg_vals)
    assert result == "val"


def test_replace_var_circular_reference_raises(mock_cfg_defs):
    cv_container = mgconfig.config_values.ConfigValues.__new__(mgconfig.config_values.ConfigValues)
    cv_container._cfg_vals = {
        "A": MagicMock(value_src="$(B)"),
        "B": MagicMock(value_src="$(A)"),
    }
    with pytest.raises(ValueError, match="Circular reference"):
        cv_container._replace_var("$(A)", cv_container._cfg_vals)


def test_save_new_value_secret(mock_cfg_defs, mock_cfg_def):
    mock_cfg_def.config_type = "secret"
    with patch("mgconfig.config_values.ValueStores.save_val") as mock_save, \
         patch("mgconfig.config_values.ConfigValue") as mock_cv, \
         patch("mgconfig.config_values.logger") as mock_logger:

        dummy_cv = MagicMock()
        dummy_cv._cfg_def = mock_cfg_def
        dummy_cv.output_new.return_value = "parsed_secret"
        mock_cv.return_value = dummy_cv

        cv_container = mgconfig.config_values.ConfigValues(mock_cfg_defs)
        cv_container._cfg_vals["test_id"] = dummy_cv

        result = cv_container.save_new_value("test_id", "new_secret", True)
        mock_save.assert_called_once()
        mock_logger.info.assert_called()
        assert result is None  # function has no return


def test_save_new_value_normal(mock_cfg_defs, mock_cfg_def):
    mock_cfg_def.config_type = "string"
    with patch("mgconfig.config_values.ValueStores.save_val") as mock_save, \
         patch("mgconfig.config_values.ConfigValue") as mock_cv, \
         patch("mgconfig.config_values.logger") as mock_logger:

        dummy_cv = MagicMock()
        dummy_cv._cfg_def = mock_cfg_def
        dummy_cv.value = "old"
        dummy_cv.output_new.return_value = "parsed_new"
        mock_cv.return_value = dummy_cv

        cv_container = mgconfig.config_values.ConfigValues(mock_cfg_defs)
        cv_container._cfg_vals["test_id"] = dummy_cv

        cv_container.save_new_value("test_id", "new_value", apply_immediately=True)
        mock_save.assert_called_once()
        mock_logger.info.assert_called()
        dummy_cv.initialize_value.assert_called_once()


def test_save_new_value_readonly_raises(mock_cfg_defs, mock_cfg_def):
    mock_cfg_def.config_readonly = True
    with patch("mgconfig.config_values.ValueStores.save_val"), \
         patch("mgconfig.config_values.ConfigValue") as mock_cv:
        dummy_cv = MagicMock()
        dummy_cv._cfg_def = mock_cfg_def
        mock_cv.return_value = dummy_cv

        cv_container = mgconfig.config_values.ConfigValues(mock_cfg_defs)
        cv_container._cfg_vals["test_id"] = dummy_cv

        with pytest.raises(ValueError):
            cv_container.save_new_value("test_id", "new_val")
