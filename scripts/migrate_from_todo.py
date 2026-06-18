#!/usr/bin/env python3
"""One-shot migration script: TODO → Trip Hub"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
from db import migrate_from_todo

if __name__ == '__main__':
    migrate_from_todo()
