import os
import zipfile

import pytest

FILE_CONTENT = "TEST CONTENT"


@pytest.fixture(scope="session")
def dummy_txt_path(tmp_path_factory):
    path = tmp_path_factory.mktemp("data") / "filename_test.txt"
    path.write_text(FILE_CONTENT)

    return path


@pytest.fixture(scope="session")
def dummy_zipfile_path(tmp_path_factory, dummy_txt_path):
    path = tmp_path_factory.mktemp("data") / "filename_test.zip"

    with zipfile.ZipFile(path, "w") as f_zip:
        f_zip.write(dummy_txt_path, os.path.basename(dummy_txt_path))

    return path
