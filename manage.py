#!/usr/bin/env python
import os
import sys
from pathlib import Path

if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent
    sys.path.insert(0, str(BASE_DIR))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "taskmaster_site.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
