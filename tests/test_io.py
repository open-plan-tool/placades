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
        # Create a temporary directory for test files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create sample files
            test_file1 = Path(temp_dir) / "file1.txt"
            test_file2 = Path(temp_dir) / "file2.txt"
            test_file1.write_text("Content of file 1")
            test_file2.write_text("Content of file 2")

            # Create a subdirectory with a file
            sub_dir = Path(temp_dir) / "subdir"
            sub_dir.mkdir()
            test_file3 = sub_dir / "file3.txt"
            test_file3.write_text("Content of file 3")

            # Create zip file
            zip_path = Path(temp_dir) / "test.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.write(test_file1, "file1.txt")
                zf.write(test_file2, "file2.txt")
                zf.write(test_file3, "subdir/file3.txt")

            yield zip_path

    def test_unzip_package_success(self, sample_zip):
        """Test successful extraction of a zip file."""
        # Extract the zip
        temp_dir = unzip_package(sample_zip)

        try:
            # Verify the temporary directory exists
            assert Path(temp_dir.name).exists()

            # Verify files were extracted
            extracted_file1 = Path(temp_dir.name) / "file1.txt"
            extracted_file2 = Path(temp_dir.name) / "file2.txt"
            extracted_file3 = Path(temp_dir.name) / "subdir" / "file3.txt"

            assert extracted_file1.exists()
            assert extracted_file2.exists()
            assert extracted_file3.exists()

            # Verify content
            assert extracted_file1.read_text() == "Content of file 1"
            assert extracted_file2.read_text() == "Content of file 2"
            assert extracted_file3.read_text() == "Content of file 3"
        finally:
            # Cleanup
            temp_dir.cleanup()

    def test_unzip_package_returns_temp_directory(self, sample_zip):
        """Test that function returns a TemporaryDirectory object."""
        temp_dir = unzip_package(sample_zip)

        try:
            assert isinstance(temp_dir, tempfile.TemporaryDirectory)
        finally:
            temp_dir.cleanup()

    def test_unzip_package_cleanup(self, sample_zip):
        """Test that cleanup removes the temporary directory."""
        temp_dir = unzip_package(sample_zip)

        # Verify directory exists
        assert Path(temp_dir.name).exists()

        # Cleanup
        temp_dir.cleanup()

        # Verify directory is removed
        assert not Path(temp_dir.name).exists()

    def test_unzip_package_nonexistent_file(self):
        """Test with a non-existent zip file."""
        with pytest.raises(FileNotFoundError):
            unzip_package("/path/to/nonexistent.zip")

    def test_unzip_package_invalid_zip(self):
        """Test with an invalid zip file."""
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            f.write(b"This is not a valid zip file")
            invalid_zip = f.name

        try:
            with pytest.raises(zipfile.BadZipFile):
                unzip_package(invalid_zip)
        finally:
            Path(invalid_zip).unlink()

    def test_unzip_empty_zip(self):
        """Test with an empty zip file."""
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            empty_zip = f.name

        # Create an empty zip
        with zipfile.ZipFile(empty_zip, "w"):
            pass

        try:
            temp_dir = unzip_package(empty_zip)
            try:
                # Should succeed but extract no files
                assert Path(temp_dir.name).exists()
                assert not any(Path(temp_dir.name).iterdir())
            finally:
                temp_dir.cleanup()
        finally:
            Path(empty_zip).unlink()
