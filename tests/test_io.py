import tempfile
import zipfile
from pathlib import Path

import pytest

from oemof.eesyplan.io import unzip_package


class TestUnzipPackage:
    """Tests for the unzip_package function."""

    @pytest.fixture
    def sample_zip(self):
        """Create a temporary zip file with sample content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file1 = Path(temp_dir) / "file1.txt"
            test_file2 = Path(temp_dir) / "file2.txt"
            test_file1.write_text("Content of file 1")
            test_file2.write_text("Content of file 2")

            sub_dir = Path(temp_dir) / "subdir"
            sub_dir.mkdir()
            test_file3 = sub_dir / "file3.txt"
            test_file3.write_text("Content of file 3")

            zip_path = Path(temp_dir) / "test.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.write(test_file1, "file1.txt")
                zf.write(test_file2, "file2.txt")
                zf.write(test_file3, "subdir/file3.txt")

            yield zip_path

    def test_unzip_package_success(self, sample_zip):
        temp_dir = unzip_package(sample_zip)
        try:
            assert Path(temp_dir.name).exists()
            extracted_file1 = Path(temp_dir.name) / "file1.txt"
            extracted_file2 = Path(temp_dir.name) / "file2.txt"
            extracted_file3 = Path(temp_dir.name) / "subdir" / "file3.txt"
            assert extracted_file1.exists()
            assert extracted_file2.exists()
            assert extracted_file3.exists()
            assert extracted_file1.read_text() == "Content of file 1"
            assert extracted_file2.read_text() == "Content of file 2"
            assert extracted_file3.read_text() == "Content of file 3"
        finally:
            temp_dir.cleanup()

    def test_unzip_package_returns_temp_directory(self, sample_zip):
        temp_dir = unzip_package(sample_zip)
        try:
            assert isinstance(temp_dir, tempfile.TemporaryDirectory)
        finally:
            temp_dir.cleanup()

    def test_unzip_package_cleanup(self, sample_zip):
        temp_dir = unzip_package(sample_zip)
        assert Path(temp_dir.name).exists()
        temp_dir.cleanup()
        assert not Path(temp_dir.name).exists()

    def test_unzip_package_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            unzip_package("/path/to/nonexistent.zip")

    def test_unzip_package_invalid_zip(self):
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            f.write(b"This is not a valid zip file")
            invalid_zip = f.name

        try:
            with pytest.raises(zipfile.BadZipFile):
                unzip_package(invalid_zip)
        finally:
            Path(invalid_zip).unlink()

    def test_unzip_empty_zip(self):
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            empty_zip = f.name

        with zipfile.ZipFile(empty_zip, "w"):
            pass

        try:
            temp_dir = unzip_package(empty_zip)
            try:
                assert Path(temp_dir.name).exists()
                assert not any(Path(temp_dir.name).iterdir())
            finally:
                temp_dir.cleanup()
        finally:
            Path(empty_zip).unlink()

    def test_unzip_with_provided_ext_path(self, sample_zip):
        with tempfile.TemporaryDirectory() as target_dir:
            ext_path = tempfile.TemporaryDirectory(dir=target_dir)
            result = unzip_package(sample_zip, ext_path)
            assert result is ext_path
            extracted = Path(ext_path.name) / "file1.txt"
            assert extracted.exists()
            ext_path.cleanup()
