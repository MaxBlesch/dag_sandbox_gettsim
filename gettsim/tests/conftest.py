import pytest
import yaml

from gettsim.config import ROOT_DIR


@pytest.fixture(scope="session")
def soz_vers_beitr_raw_data():
    return yaml.safe_load(
        (ROOT_DIR / "soz_vers_beitr.yaml").read_text(encoding="utf-8")
    )
