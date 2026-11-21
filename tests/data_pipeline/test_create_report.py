import pytest

import configuration as cfg
from data_pipeline import create_report


@pytest.fixture
def fresh_clone(mocker, tmp_path):
    """Points temp/ and reports/ to folders that do not exist yet, like after a clone."""
    mocker.patch.object(cfg, "TEMP_DIR", tmp_path / "temp")
    mocker.patch.object(cfg, "REPORT_DIR", tmp_path / "reports")
    mocker.patch.object(
        create_report, "data_file_path", tmp_path / "temp" / cfg.FILE_STOCK_DATA
    )
    return tmp_path


def test_ensure_directories_creates_missing_folders(fresh_clone):
    create_report.ensure_directories()

    assert (fresh_clone / "temp").is_dir()
    assert (fresh_clone / "reports").is_dir()


def test_main_without_data_asks_to_download_first(fresh_clone):
    with pytest.raises(SystemExit, match="create_report.py -a"):
        create_report.main(cfg.DATA_DIR, "my_name", "", actualize=False)

    # The folders exist anyway, so the next run with -a can save its data
    assert (fresh_clone / "temp").is_dir()
