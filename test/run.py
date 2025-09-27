#!/usr/bin/env python3
"""
简化的运行测试 - 不需要完整的 Sentry 环境

直接读取和执行目标函数，绕过复杂的模块依赖
"""

import os
import sys
import re
import inspect
from unittest.mock import Mock

def test_plugin():
    def extract_preprocess_event_function():
        """直接从文件中提取 preprocess_event 函数代码"""
        # 查找文件
        possible_paths = [
            "src/sentry/lang/javascript/plugin.py"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 查找 preprocess_event 函数
                    if 'def preprocess_event(' in content:
                        return extract_function_code(content, 'preprocess_event'), path
                except Exception as e:
                    print(f"读取 {path} 失败: {e}")
        
        return None, None

    def extract_function_code(content, function_name):
        """从文件内容中提取指定函数的代码"""
        lines = content.split('\n')
        function_lines = []
        in_function = False
        indent_level = None
        
        for line in lines:
            if f'def {function_name}(' in line:
                in_function = True
                indent_level = len(line) - len(line.lstrip())
                function_lines.append(line)
            elif in_function:
                # 检查是否到了函数结尾
                if line.strip() == '':
                    function_lines.append(line)
                elif len(line) - len(line.lstrip()) <= indent_level and line.strip():
                    # 遇到同级或更外层的代码，函数结束
                    break
                else:
                    function_lines.append(line)
        
        return '\n'.join(function_lines)

    def create_mock_environment():
        """创建模拟的运行环境"""
        # Mock Project
        mock_project = Mock()
        mock_project.get_option = Mock(return_value=True)
        
        mock_project_objects = Mock()
        mock_project_objects.get_from_cache = Mock(return_value=mock_project)
        
        # Mock SourceProcessor
        mock_source_processor_instance = Mock()
        mock_source_processor_instance.process = Mock(return_value={'processed': True})
        mock_source_processor = Mock(return_value=mock_source_processor_instance)
        
        # 设置模拟环境
        sys.modules['sentry'] = Mock()
        sys.modules['sentry.models'] = Mock()
        sys.modules['sentry.models'].Project = Mock()
        sys.modules['sentry.models'].Project.objects = mock_project_objects
        sys.modules['sentry.lang'] = Mock()
        sys.modules['sentry.lang.javascript'] = Mock()
        sys.modules['sentry.lang.javascript.processor'] = Mock()
        sys.modules['sentry.lang.javascript.processor'].SourceProcessor = mock_source_processor
        
        return mock_source_processor, mock_project

    def test_if_condition_removed():
        """测试 if not allow_scraping: return 条件是否被删除"""
        function_code, filepath = extract_preprocess_event_function()
        if not function_code:
            return False

        # 检查函数代码中是否还存在 if not allow_scraping: 的条件
        if 'if not allow_scraping:' in function_code:
            return False

        # 检查函数代码中是否还存在孤立的 return 语句（在 if 条件删除后可能遗留）
        lines = function_code.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            # 检查是否有孤立的 return 语句（不在其他控制结构中）
            if stripped == 'return' and i > 0:
                # 检查上一行是否包含 if 条件
                prev_line = lines[i-1].strip()
                if not prev_line.startswith('if') and not prev_line.startswith('elif') and not prev_line.startswith('else'):
                    # 这可能是未删除的 return 语句
                    return False

        return True

    def test_allow_scraping_parameter():
        """测试 allow_scraping 参数传递"""
        function_code, filepath = extract_preprocess_event_function()
        if not function_code:
            return False

        # 创建模拟环境
        mock_source_processor, mock_project = create_mock_environment()

        # 准备执行环境
        namespace = {
            'Project': sys.modules['sentry.models'].Project,
            'SourceProcessor': mock_source_processor,
            '__builtins__': __builtins__
        }

        try:
            # 执行函数定义
            exec(function_code, namespace)
            preprocess_event = namespace['preprocess_event']

            # 测试数据
            test_data_js = {
                'platform': 'javascript',
                'project': 'test-project'
            }

            # 调用函数
            result = preprocess_event(test_data_js)

            # 检查 SourceProcessor 是否被调用且包含 allow_scraping 参数
            if mock_source_processor.called:
                call_args = mock_source_processor.call_args
                if call_args and 'allow_scraping' in call_args.kwargs:
                    return True

            return False

        except Exception as e:
            return False

    def test_no_early_return_when_scraping_disabled():
        """测试当项目配置 allow_scraping=False 时函数不会提前返回"""
        function_code, filepath = extract_preprocess_event_function()
        if not function_code:
            return False

        # 创建模拟环境，设置项目配置为禁用 scraping
        mock_source_processor, mock_project = create_mock_environment()
        mock_project.get_option = Mock(return_value=False)  # 设置 scraping 为 False

        # 准备执行环境
        namespace = {
            'Project': sys.modules['sentry.models'].Project,
            'SourceProcessor': mock_source_processor,
            '__builtins__': __builtins__
        }

        try:
            # 执行函数定义
            exec(function_code, namespace)
            preprocess_event = namespace['preprocess_event']

            # 测试数据
            test_data_js = {
                'platform': 'javascript',
                'project': 'test-project'
            }

            # 调用函数
            result = preprocess_event(test_data_js)

            # 如果函数没有提前返回，SourceProcessor 应该被调用
            # 即使 allow_scraping=False，函数也应该继续执行并创建 SourceProcessor
            if mock_source_processor.called:
                call_args = mock_source_processor.call_args
                if call_args and 'allow_scraping' in call_args.kwargs:
                    # 验证传递的 allow_scraping 值是 False（从项目配置获取）
                    if call_args.kwargs['allow_scraping'] == False:
                        return True

            return False

        except Exception as e:
            return False

    # 运行所有测试
    if_condition_removed = test_if_condition_removed()
    parameter_passed = test_allow_scraping_parameter()
    no_early_return = test_no_early_return_when_scraping_disabled()

    if if_condition_removed and parameter_passed and no_early_return:
        print("Test 4 passed.")
    else:
        error_details = []
        if not if_condition_removed:
            error_details.append("if condition not removed")
        if not parameter_passed:
            error_details.append("allow_scraping parameter not passed")
        if not no_early_return:
            error_details.append("early return still exists")
        print(f"Test 4 failed: {', '.join(error_details)} at where SourceProcessor is called")

def test_fetch_url():
    """测试 fetch_url 函数的 allow_scraping 功能"""
    
    def find_fetch_url_function():
        """查找 fetch_url 函数"""
        possible_paths = [
            'src/sentry/lang/javascript/processor.py'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if 'def fetch_url(' in content:
                        return extract_function_code(content, 'fetch_url')
                except Exception:
                    pass
        return None

    def extract_function_code(content, function_name):
        """提取函数代码"""
        lines = content.split('\n')
        function_lines = []
        in_function = False
        indent_level = None
        
        for line in lines:
            if f'def {function_name}(' in line:
                in_function = True
                indent_level = len(line) - len(line.lstrip())
                function_lines.append(line)
            elif in_function:
                if line.strip() == '':
                    function_lines.append(line)
                elif len(line) - len(line.lstrip()) <= indent_level and line.strip():
                    break
                else:
                    function_lines.append(line)
        
        return '\n'.join(function_lines)

    def create_mock_environment():
        """创建 Mock 环境"""
        from hashlib import md5
        
        # 创建一个包装的 md5 函数，自动处理字符串编码
        def md5_wrapper(data):
            if isinstance(data, str):
                data = data.encode('utf-8')
            return md5(data)
        
        # Mock logger
        mock_logger = Mock()
        mock_logger.debug = Mock()
        mock_logger.warning = Mock()
        mock_logger.exception = Mock()
        
        # Mock CannotFetchSource 异常，记录调用参数
        class MockCannotFetchSource(Exception):
            def __init__(self, error_dict):
                self.error_dict = error_dict
                super().__init__(str(error_dict))
        
        # Mock EventError
        mock_event_error = Mock()
        mock_event_error.JS_MISSING_SOURCE = 'JS_MISSING_SOURCE'
        
        # Mock fetch_release_file
        mock_fetch_release_file = Mock(return_value=None)
        
        return {
            'CannotFetchSource': MockCannotFetchSource,
            'EventError': mock_event_error,
            'fetch_release_file': mock_fetch_release_file,
            'md5': md5_wrapper,
            'logger': mock_logger,
            '__builtins__': __builtins__
        }
    
    function_code = find_fetch_url_function()
    if not function_code:
        print("Failed to find fetch_url function")
        return False
    
    namespace = create_mock_environment()
    
    try:
        # 执行函数定义
        exec(function_code, namespace)
        fetch_url = namespace['fetch_url']
        
        # 测试: allow_scraping=False 应该抛出特定的异常
        try:
            fetch_url('http://example.com', allow_scraping=False)
            # 如果没有抛出异常，说明功能未实现
            print("A: Failed passing allow_scraping to fetch_url")
            return False
        except namespace['CannotFetchSource'] as e:
            # 检查异常的错误字典是否包含正确的类型和URL
            if (hasattr(e, 'error_dict') and 
                e.error_dict.get('type') == 'JS_MISSING_SOURCE' and
                e.error_dict.get('url') == 'http://example.com'):
                print("Test 1 passed.")
                return True
            else:
                print(f"Testing fetch_url() failed: {e}")
                return False
        except Exception as e:
            if str(e) == "fetch_url() got an unexpected keyword argument 'allow_scraping'":
                print("Test 1 failed: when trying to pass argument 'allow_scraping' to fetch_url().")
                return False
            # 抛出了其他类型的异常，功能可能未正确实现
            else:
                print("Test 1 failed: you did not implement the usage of allow_scraping in fetch_url()")
                return False
        
    except Exception as e:
        print(f"Testing fetch_url() failed: {e}")
        return False


def test_fetch_sourcemap():
    """测试 fetch_sourcemap 函数的 allow_scraping 功能"""
    def find_fetch_sourcemap_function():
        """查找 fetch_sourcemap 函数"""
        possible_paths = [
            'src/sentry/lang/javascript/processor.py'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if 'def fetch_sourcemap(' in content:
                        return extract_function_code(content, 'fetch_sourcemap')
                except Exception:
                    pass
        return None

    def extract_function_code(content, function_name):
        """提取函数代码"""
        lines = content.split('\n')
        function_lines = []
        in_function = False
        indent_level = None
        
        for line in lines:
            if f'def {function_name}(' in line:
                in_function = True
                indent_level = len(line) - len(line.lstrip())
                function_lines.append(line)
            elif in_function:
                if line.strip() == '':
                    function_lines.append(line)
                elif len(line) - len(line.lstrip()) <= indent_level and line.strip():
                    break
                else:
                    function_lines.append(line)
        
        return '\n'.join(function_lines)

    def create_mock_environment():
        """创建 Mock 环境"""
        # Mock fetch_url 函数，根据 allow_scraping 参数决定行为
        def mock_fetch_url(url, project=None, release=None, allow_scraping=True):
            # 记录调用参数，特别是 allow_scraping
            mock_fetch_url.last_call_args = {
                'url': url,
                'project': project,
                'release': release,
                'allow_scraping': allow_scraping
            }
            # 模拟返回结果
            return Mock(body='mock_body')
        
        # 定义常量
        BASE64_SOURCEMAP_PREAMBLE = 'data:application/json;base64,'
        BASE64_PREAMBLE_LENGTH = len(BASE64_SOURCEMAP_PREAMBLE)
        
        # 定义 is_data_uri 函数
        def is_data_uri(url):
            return url[:BASE64_PREAMBLE_LENGTH] == BASE64_SOURCEMAP_PREAMBLE
        
        # Mock base64 和相关函数
        mock_base64 = Mock()
        mock_base64.b64decode = Mock(return_value=b'mock_decoded_data')
        
        # Mock sourcemap_to_index 函数
        mock_sourcemap_to_index = Mock(return_value='mock_index_result')
        
        # Mock logger
        mock_logger = Mock()
        mock_logger.warn = Mock()
        
        # Mock UnparseableSourcemap 异常
        class MockUnparseableSourcemap(Exception):
            pass
        
        # Mock unicode 函数 (Python 2/3 兼容)
        def mock_unicode(s):
            return str(s)
        
        return {
            'fetch_url': mock_fetch_url,
            'is_data_uri': is_data_uri,
            'BASE64_PREAMBLE_LENGTH': BASE64_PREAMBLE_LENGTH,
            'BASE64_SOURCEMAP_PREAMBLE': BASE64_SOURCEMAP_PREAMBLE,
            'base64': mock_base64,
            'sourcemap_to_index': mock_sourcemap_to_index,
            'logger': mock_logger,
            'UnparseableSourcemap': MockUnparseableSourcemap,
            'unicode': mock_unicode,
            'JSONDecodeError': ValueError,  # 简化的异常类型
            'ValueError': ValueError,
            'AssertionError': AssertionError,
            '__builtins__': __builtins__
        }
    
    function_code = find_fetch_sourcemap_function()
    if not function_code:
        print("Failed to find fetch_sourcemap function")
        return False
    
    namespace = create_mock_environment()
    
    try:
        # 执行函数定义
        exec(function_code, namespace)
        fetch_sourcemap = namespace['fetch_sourcemap']
        
        # 测试 1: allow_scraping=True 应该传递给 fetch_url
        try:
            fetch_sourcemap('http://example.com/map.js.map', allow_scraping=True)
            
            # 检查 fetch_url 是否被调用且 allow_scraping=True
            if hasattr(namespace['fetch_url'], 'last_call_args'):
                args = namespace['fetch_url'].last_call_args
                if args.get('allow_scraping') == True:
                    # 测试 2: allow_scraping=False 应该传递给 fetch_url
                    fetch_sourcemap('http://example.com/map2.js.map', allow_scraping=False)
                    
                    args2 = namespace['fetch_url'].last_call_args
                    if args2.get('allow_scraping') == False:
                        print("Test 2 passed.")
                        return True
            
            print("Failed passing allow_scraping from fetch_sourcemap to fetch_url")
            return False
                
        except Exception as e:
            if str(e) == "fetch_sourcemap() got an unexpected keyword argument 'allow_scraping'":
                print("Test 2 failed: when trying to pass argument 'allow_scraping' to fetch_sourcemap().")
                return False
            else:
                print(f"Test 2 failed: when trying to pass argument 'allow_scraping' from fetch_sourcemap() to fetch_url().")
                return False
        
    except Exception as e:
        print(f"Testing fetch_sourcemap() failed: {e}")
        return False

def test_SourceProcessor():
    """测试 SourceProcessor 类的 allow_scraping 功能"""
    
    import os
    import sys
    import inspect
    from unittest.mock import Mock
    
    def find_source_processor_class():
        """查找 SourceProcessor 类"""
        possible_paths = [
            'src/sentry/lang/javascript/processor.py'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if 'class SourceProcessor(' in content:
                        return extract_class_code(content, 'SourceProcessor')
                except Exception:
                    pass
        return None

    def extract_class_code(content, class_name):
        """提取类代码"""
        lines = content.split('\n')
        class_lines = []
        in_class = False
        indent_level = None
        
        for line in lines:
            if f'class {class_name}(' in line:
                in_class = True
                indent_level = len(line) - len(line.lstrip())
                class_lines.append(line)
            elif in_class:
                if line.strip() == '':
                    class_lines.append(line)
                elif len(line) - len(line.lstrip()) <= indent_level and line.strip() and not line.lstrip().startswith('#'):
                    # 遇到同级或更外层的代码（非注释），类结束
                    break
                else:
                    class_lines.append(line)
        
        return '\n'.join(class_lines)

    def create_mock_environment():
        """创建 Mock 环境"""
        # Mock fetch_url 函数，返回包含 sourcemap 信息的内容
        def mock_fetch_url(filename, project=None, release=None, allow_scraping=True):
            mock_fetch_url.last_call_args = {
                'filename': filename,
                'project': project,
                'release': release,
                'allow_scraping': allow_scraping
            }
            # 返回包含 sourcemap 引用的 JS 代码
            mock_result = Mock()
            mock_result.body = '//# sourceMappingURL=app.js.map\nconsole.log("test");'
            mock_result.url = filename
            return mock_result
        
        # Mock fetch_sourcemap 函数
        def mock_fetch_sourcemap(sourcemap_url, project=None, release=None, allow_scraping=True):
            mock_fetch_sourcemap.last_call_args = {
                'sourcemap_url': sourcemap_url,
                'project': project,
                'release': release,
                'allow_scraping': allow_scraping
            }
            return 'mock_sourcemap_result'
        
        # Mock logger
        mock_logger = Mock()
        mock_logger.debug = Mock()
        mock_logger.warning = Mock()
        mock_logger.exception = Mock()
        mock_logger.info = Mock()
        
        # Mock 其他依赖
        mock_source_cache = Mock()
        mock_source_cache.get = Mock(return_value=None)  # 缓存中没有，触发获取
        mock_source_cache.add_error = Mock()
        mock_source_cache.add = Mock()
        
        mock_sourcemap_cache = Mock()
        mock_sourcemap_cache.get = Mock(return_value=None)  # sourcemap缓存中也没有，触发获取
        mock_sourcemap_cache.add = Mock()
        mock_sourcemap_cache.link = Mock()
        mock_sourcemap_cache.__contains__ = Mock(return_value=False)  # sourcemap_url not in sourcemaps
        
        # Mock 常量
        MAX_RESOURCE_FETCHES = 10
        
        # Mock 异常
        class MockBadSource(Exception):
            def __init__(self, data):
                self.data = data
                super().__init__(str(data))
        
        # Mock discover_sourcemap function
        def mock_discover_sourcemap(result):
            # 从 fetch_url 的结果中返回 sourcemap URL
            if hasattr(result, 'body') and 'sourceMappingURL=' in result.body:
                return 'http://example.com/app.js.map'
            return None

        return {
            'fetch_url': mock_fetch_url,
            'fetch_sourcemap': mock_fetch_sourcemap,
            'discover_sourcemap': mock_discover_sourcemap,
            'SourceCache': lambda: mock_source_cache,
            'SourceMapCache': lambda: mock_sourcemap_cache,
            'MAX_RESOURCE_FETCHES': MAX_RESOURCE_FETCHES,
            'BadSource': MockBadSource,
            'logger': mock_logger,
            '__builtins__': __builtins__
        }
    
    class_code = find_source_processor_class()
    if not class_code:
        print("Failed to find SourceProcessor class")
        return False
    
    namespace = create_mock_environment()
    
    try:
        # 执行类定义
        exec(class_code, namespace)
        SourceProcessor = namespace['SourceProcessor']
        
        # 测试1: 检查 __init__ 方法是否包含 allow_scraping 参数
        init_signature = inspect.signature(SourceProcessor.__init__)
        if 'allow_scraping' not in init_signature.parameters:
            print("Test 3 failed: SourceProcessor.__init__ missing allow_scraping parameter")
            return False
        
        # 测试2: 创建 SourceProcessor 实例并检查属性
        processor = SourceProcessor(allow_scraping=False)
        if not hasattr(processor, 'allow_scraping'):
            print("Test 3 failed: SourceProcessor instance missing allow_scraping attribute")
            return False
        
        if processor.allow_scraping != False:
            print("Test 3 failed: SourceProcessor.allow_scraping not set correctly")
            return False
        
        # 测试3: 模拟 populate_source_cache 方法调用
        # 创建模拟的 project, frames, release
        mock_project = Mock()
        
        # 创建具有必要属性的 mock frames
        mock_frame1 = Mock()
        mock_frame1.abs_path = 'http://example.com/app.js'
        mock_frame1.filename = 'http://example.com/app.js'
        mock_frame1.colno = 10  # 需要 colno 才能触发 sourcemap 处理

        mock_frame2 = Mock()
        mock_frame2.abs_path = 'http://example.com/lib.js'
        mock_frame2.filename = 'http://example.com/lib.js'
        mock_frame2.colno = 20  # 需要 colno 才能触发 sourcemap 处理
        
        mock_frames = [mock_frame1, mock_frame2]
        mock_release = Mock()
        
        try:
            # 调用 populate_source_cache 方法
            processor.populate_source_cache(mock_project, mock_frames, mock_release)
            
            # 检查 fetch_url 是否被调用且传递了 allow_scraping=False
            fetch_url_ok = False
            if hasattr(namespace['fetch_url'], 'last_call_args'):
                args = namespace['fetch_url'].last_call_args
                if args.get('allow_scraping') == False:
                    print("✓ fetch_url called with allow_scraping=False")
                    fetch_url_ok = True
                else:
                    print("Test 3 failed: fetch_url() not called with correct allow_scraping in SourceProcessor()")
                    return False
            else:
                print("Test 3 failed: fetch_url() not called in SourceProcessor()")
                return False
            
            # 检查 fetch_sourcemap 是否也被调用且传递了 allow_scraping=False
            fetch_sourcemap_ok = False
            if hasattr(namespace['fetch_sourcemap'], 'last_call_args'):
                sourcemap_args = namespace['fetch_sourcemap'].last_call_args
                print(f"DEBUG: fetch_sourcemap called with args: {sourcemap_args}")
                if sourcemap_args.get('allow_scraping') == False:
                    print("✓ fetch_sourcemap called with allow_scraping=False")
                    fetch_sourcemap_ok = True
                else:
                    print("Test 3 failed: fetch_sourcemap() not called with correct allow_scraping in SourceProcessor()")
                    print(f"Test 3 failed: fetch_sourcemap() not called with correct allow_scraping in SourceProcessor() - allow_scraping={sourcemap_args.get('allow_scraping')}")
                    return False
            else:
                print("Test 3 failed: fetch_sourcemap() not called in SourceProcessor()")
                return False
            
            if fetch_url_ok and fetch_sourcemap_ok:
                print("Test 3 passed.")
                return True
            else:
                return False
                
        except Exception:
            # populate_source_cache 可能因为其他依赖而失败，但这不是我们关心的
            # 只要 fetch_url 和 fetch_sourcemap 被正确调用就行
            fetch_url_ok = False
            fetch_sourcemap_ok = False
            
            if hasattr(namespace['fetch_url'], 'last_call_args'):
                args = namespace['fetch_url'].last_call_args
                if args.get('allow_scraping') == False:
                    # print("✓ fetch_url called with allow_scraping=False")
                    fetch_url_ok = True
            
            if hasattr(namespace['fetch_sourcemap'], 'last_call_args'):
                sourcemap_args = namespace['fetch_sourcemap'].last_call_args
                if sourcemap_args.get('allow_scraping') == False:
                    # print("✓ fetch_sourcemap called with allow_scraping=False")
                    fetch_sourcemap_ok = True
            
            # 详细报告
            if hasattr(namespace['fetch_url'], 'last_call_args'):
                url_args = namespace['fetch_url'].last_call_args
                # print(f"✓ fetch_url called with allow_scraping={url_args.get('allow_scraping')}")

            if hasattr(namespace['fetch_sourcemap'], 'last_call_args'):
                sourcemap_args = namespace['fetch_sourcemap'].last_call_args
                # print(f"✓ fetch_sourcemap called with allow_scraping={sourcemap_args.get('allow_scraping')}")

            if fetch_url_ok and fetch_sourcemap_ok:
                print("Test 3 passed.")
                return True
            else:
                print("Test failed: allow_scraping propagation is incorrect")
                return False
        
    except Exception:
        print("Failed: SourceProcessor class definition or execution failed")
        return False



if __name__ == '__main__':
    # Test 1
    test_fetch_url()

    # Test 2
    test_fetch_sourcemap()

    # Test 3
    test_SourceProcessor()

    # Test 4
    test_plugin()