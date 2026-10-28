#!/usr/bin/env python
"""
FoodieGo 2.0 Root Management Utility
Convenience launcher that allows running manage.py commands directly from the workspace root.
"""
import os
import sys

def main():
    proj_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Online_Food_Ordering_System')
    if proj_dir not in sys.path:
        sys.path.insert(0, proj_dir)
    os.chdir(proj_dir)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Foods_Ordering.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
