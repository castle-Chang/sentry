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

        # Test 1a: Check constructor signature - should only have is_new and is_regression
        if 'def __init__(self, is_new, is_regression, is_sample)' in content:
            raise Exception("EventState constructor still has is_sample parameter")

        if 'def __init__(self, is_new, is_regression):' not in content:
            raise Exception("EventState constructor signature is incorrect")

        # Test 1b: Check that self.is_sample assignment is removed
        # Look for the EventState class definition and check its __init__ method
        import re

        # Extract the EventState class definition
        class_pattern = r'class EventState\(object\):\s*\n(.*?)(?=\n\n|\nclass|\n[a-zA-Z]|\Z)'
        match = re.search(class_pattern, content, re.DOTALL)

        if not match:
            raise Exception("Test 1 failed: Could not find EventState class definition")

        class_content = match.group(1)

        # Check that is_sample is not assigned in the __init__ method (allow commented out)
        # Look for uncommented self.is_sample assignments
        is_sample_lines = re.findall(r'^.*self\.is_sample.*$', class_content, re.MULTILINE)
        for line in is_sample_lines:
            if not line.strip().startswith('#'):
                raise Exception("Test 1 failed: EventState.__init__ still assigns self.is_sample")

        # Test 1c: Verify is_new and is_regression are still assigned
        if 'self.is_new = is_new' not in class_content:
            raise Exception("Test 1 failed: EventState.__init__ missing self.is_new assignment")

        if 'self.is_regression = is_regression' not in class_content:
            raise Exception("Test 1 failed: EventState.__init__ missing self.is_regression assignment")

        print("Test 1 passed.")

    except Exception as e:
        print("Test 1 failed: " + str(e))

def test_2():
    try:
        # Read the actual RuleProcessor class from the file
        project_root = get_project_root()
        proc_file = os.path.join(project_root, 'src', 'sentry', 'rules', 'processor.py')
        content = read_file_safe(proc_file)

        # Test 2a: Check constructor signature - should only have event, is_new, is_regression
        if 'def __init__(self, event, is_new, is_regression, is_sample)' in content:
            raise Exception("Test 2 failed: RuleProcessor constructor still has is_sample parameter")

        if 'def __init__(self, event, is_new, is_regression):' not in content:
            raise Exception("Test 2 failed: RuleProcessor constructor signature is incorrect")

        # Test 2b: Check that self.is_sample assignment is removed
        import re

        # Extract the RuleProcessor class definition
        class_pattern = r'class RuleProcessor\(object\):(.*?)(?=\nclass|\Z)'
        match = re.search(class_pattern, content, re.DOTALL)

        if not match:
            raise Exception("Test 2 failed: Could not find RuleProcessor class definition")

        class_content = match.group(1)

        # Check that is_sample is not assigned in the __init__ method (allow commented out)
        import re
        # Look for uncommented assignment (not starting with #)
        if re.search(r'^\s*self\.is_sample\s*=\s*is_sample', class_content, re.MULTILINE):
            raise Exception("RuleProcessor.__init__ still assigns self.is_sample")

        # Test 2c: Check that get_state() method doesn't pass is_sample to EventState (allow commented out)
        # Look for uncommented is_sample parameter (check if line doesn't start with #)
        is_sample_lines = re.findall(r'^.*is_sample\s*=\s*self\.is_sample.*$', class_content, re.MULTILINE)
        for line in is_sample_lines:
            if not line.strip().startswith('#'):
                raise Exception("Test 2 failed: RuleProcessor.get_state() still passes is_sample to EventState")

        # Test 2d: Verify required attributes are still assigned
        if 'self.is_new = is_new' not in class_content:
            raise Exception("Test 2 failed: RuleProcessor.__init__ missing self.is_new assignment")

        if 'self.is_regression = is_regression' not in class_content:
            raise Exception("Test 2 failed: RuleProcessor.__init__ missing self.is_regression assignment")

        print("Test 2 passed.")

    except Exception as e:
        print("Test 2 failed: " + str(e))

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
