#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import sys

def get_project_root():
    """Get the project root directory in a cross-platform way."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(current_dir)

def read_file_safe(file_path):
    """Read file content safely with proper encoding handling."""
    try:
        # Try UTF-8 first (most common)
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Fallback to system default encoding
        try:
            with open(file_path, 'r', encoding=sys.getdefaultencoding()) as f:
                return f.read()
        except UnicodeDecodeError:
            # Final fallback to latin-1 (can handle any byte sequence)
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()

def test_1():
    try:
        # Read the actual EventState class from the file
        project_root = get_project_root()
        base_file = os.path.join(project_root, 'src', 'sentry', 'rules', 'base.py')
        content = read_file_safe(base_file)

        # Check if EventState constructor has is_sample parameter
        if 'def __init__(self, is_new, is_regression, is_sample)' in content:
            raise Exception("Test 1 failed for unexpected is_sample parameter")
        elif 'def __init__(self, is_new, is_regression)' in content:
            print("Test 1 passed.")
        else:
            raise Exception("Test 1 failed for unexpected constructor signature")
    except Exception:
        print("Test 1 failed for initialization")

def test_2():
    try:
        # Read the actual RuleProcessor class from the file
        project_root = get_project_root()
        proc_file = os.path.join(project_root, 'src', 'sentry', 'rules', 'processor.py')
        content = read_file_safe(proc_file)

        # Check if RuleProcessor constructor has is_sample parameter
        if 'def __init__(self, event, is_new, is_regression, is_sample)' in content:
            raise Exception("Test 2 failed for unexpected is_sample parameter")
        elif 'def __init__(self, event, is_new, is_regression)' in content:
            print("Test 2 passed.")
        else:
            raise Exception("Test 2 failed for unexpected constructor signature")
    except Exception:
        print("Test 2 failed for initialization")

def test_3():
    try:
        # Read the actual post_process_group function from the file
        project_root = get_project_root()
        pp_file = os.path.join(project_root, 'src', 'sentry', 'tasks', 'post_process.py')
        content = read_file_safe(pp_file)

        # Check if RuleProcessor is called without is_sample parameter
        if 'RuleProcessor(event, is_new, is_regression, is_sample)' in content:
            raise Exception("Test 3 failed for unexpected is_sample in RuleProcessor call")
        elif 'RuleProcessor(event, is_new, is_regression)' in content:
            print("Test 3 passed.")
        else:
            raise Exception("Test 3 failed for unexpected RuleProcessor call")
    except Exception:
        print("Test 3 failed for function inspection")

def test_4():
    try:
        project_root = get_project_root()
        test_file_path = os.path.join(project_root, 'tests', 'sentry', 'rules', 'test_processor.py')
        if os.path.exists(test_file_path):
            content = read_file_safe(test_file_path)
            if 'is_sample=False' in content:
                raise Exception("Test 4 failed for unexpected is_sample parameter")
            print("Test 4 passed.")
        else:
            raise Exception("Test 4 failed for file existence")
    except Exception:
        print("Test 4 failed for file access")

if __name__ == "__main__":
    test_1()
    test_2()
    test_3()
    test_4()