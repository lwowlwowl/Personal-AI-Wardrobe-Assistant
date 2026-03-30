"""
Resolve paths relative to the AIwardrobe package root.
"""
import os

def get_project_root()-> str:
    """
    Return the AIwardrobe package root directory (parent of ``utils``).
    """

    # This file: .../AIwardrobe/utils/path_tool.py
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    # Package root is parent of utils/
    project_root = os.path.dirname(current_dir)

    return project_root

def get_abs_path(relative_path: str) -> str:
    """
    Join ``relative_path`` to the package root and return an absolute path.
    """
    project_root = get_project_root()
    return os.path.join(project_root,relative_path)


if __name__ == '__main__':
    print(get_abs_path("config/config.txt"))