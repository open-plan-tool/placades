import tempfile
import zipfile


def unzip_package(zip_path, ext_path=None):
    """
    Extract a zip file to a temporary directory.

    Returns:
        TemporaryDirectory object (caller must manage cleanup)
    """
    if ext_path is None:
        ext_path = tempfile.TemporaryDirectory()

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(ext_path.name)

    return ext_path
