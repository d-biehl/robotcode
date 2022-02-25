from __future__ import annotations

import sys
from os import PathLike
from pathlib import Path
from typing import List, Optional, Union


def find_file(
    path: Union[Path, PathLike[str], str],
    basedir: Union[Path, PathLike[str], str] = ".",
    file_type: Optional[str] = None,
) -> str:
    return find_file_ex(path, basedir, None, file_type)


def find_file_ex(
    path: Union[Path, PathLike[str], str],
    basedir: Union[Path, PathLike[str], str] = ".",
    python_path: Optional[List[str]] = None,
    file_type: Optional[str] = None,
) -> str:
    from robot.errors import DataError

    path = Path(path)
    if path.is_absolute():
        ret = _find_absolute_path(path)
    else:
        ret = _find_relative_path(path, basedir, python_path)
    if ret:
        return str(ret)
    default = file_type or "File"

    file_type = (
        {"Library": "Test library", "Variables": "Variable file", "Resource": "Resource file"}.get(file_type, default)
        if file_type
        else default
    )

    raise DataError("%s '%s' does not exist." % (file_type, path))


def _find_absolute_path(path: Union[Path, PathLike[str], str]) -> Optional[str]:
    if _is_valid_file(path):
        return str(path)
    return None


def _find_relative_path(
    path: Union[Path, PathLike[str], str],
    basedir: Union[Path, PathLike[str], str],
    python_path: Optional[List[str]] = None,
) -> Optional[str]:

    for base in [basedir, *(python_path if python_path is not None else sys.path)]:
        if not base:
            continue
        base_path = Path(base)

        if not base_path.is_dir():
            continue

        ret = Path(base, path).absolute()

        if _is_valid_file(ret):
            return str(ret)
    return None


def _is_valid_file(path: Union[Path, PathLike[str], str]) -> bool:
    path = Path(path)
    return path.is_file() or (path.is_dir() and Path(path, "__init__.py").is_fifo())
