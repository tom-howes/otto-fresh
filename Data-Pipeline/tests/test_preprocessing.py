"""
Unit tests for EnhancedCodeChunker (data_preprocessing)
"""
import pytest
from unittest.mock import MagicMock, patch
from src.chunking.enhanced_chunker import EnhancedCodeChunker


@pytest.fixture
def chunker():
    with patch("src.chunking.enhanced_chunker.CodeChunker.__init__", return_value=None):
        c = EnhancedCodeChunker.__new__(EnhancedCodeChunker)
        return c


# ==================== Python imports ====================

def test_extract_python_imports_simple(chunker):
    content = "import os\nimport sys\n"
    result = chunker._extract_python_imports_improved(content)
    assert "os" in result
    assert "sys" in result


def test_extract_python_imports_from(chunker):
    content = "from fastapi import FastAPI\nfrom typing import List\n"
    result = chunker._extract_python_imports_improved(content)
    assert "fastapi" in result
    assert "typing" in result


def test_extract_python_imports_multi(chunker):
    content = "import os, sys, json\n"
    result = chunker._extract_python_imports_improved(content)
    assert "os" in result
    assert "sys" in result
    assert "json" in result


def test_extract_python_imports_skips_comments(chunker):
    content = "# import os\nimport json\n"
    result = chunker._extract_python_imports_improved(content)
    assert "json" in result
    assert "os" not in result


def test_extract_python_imports_empty(chunker):
    result = chunker._extract_python_imports_improved("")
    assert result == []


def test_extract_python_imports_no_duplicates(chunker):
    content = "import os\nimport os\n"
    result = chunker._extract_python_imports_improved(content)
    assert result.count("os") == 1


# ==================== Python decorators ====================

def test_extract_python_decorators(chunker):
    content = "@property\ndef foo(self): pass\n@staticmethod\ndef bar(): pass\n"
    result = chunker._extract_python_decorators(content)
    assert "property" in result
    assert "staticmethod" in result


def test_extract_python_decorators_with_args(chunker):
    content = "@router.get('/path')\nasync def endpoint(): pass\n"
    result = chunker._extract_python_decorators(content)
    assert "router.get" in result


def test_extract_python_decorators_empty(chunker):
    result = chunker._extract_python_decorators("def foo(): pass")
    assert result == []


# ==================== Python async ====================

def test_extract_python_async(chunker):
    content = "async def fetch_data(): pass\nasync def save(): pass\n"
    result = chunker._extract_python_async(content)
    assert "fetch_data" in result
    assert "save" in result


def test_extract_python_async_excludes_sync(chunker):
    content = "def sync_func(): pass\nasync def async_func(): pass\n"
    result = chunker._extract_python_async(content)
    assert "async_func" in result
    assert "sync_func" not in result


def test_extract_python_async_empty(chunker):
    result = chunker._extract_python_async("def foo(): pass")
    assert result == []


# ==================== Python exceptions ====================

def test_extract_python_exceptions_raised(chunker):
    content = "raise ValueError('bad')\nraise HTTPException(404)\n"
    result = chunker._extract_python_exceptions(content)
    assert "ValueError" in result["raised"]
    assert "HTTPException" in result["raised"]


def test_extract_python_exceptions_caught(chunker):
    content = "try:\n    pass\nexcept ValueError:\n    pass\nexcept Exception as e:\n    pass\n"
    result = chunker._extract_python_exceptions(content)
    assert "ValueError" in result["caught"]
    assert "Exception" in result["caught"]


def test_extract_python_exceptions_custom(chunker):
    content = "class MyCustomError(Exception): pass\n"
    result = chunker._extract_python_exceptions(content)
    assert "MyCustomError" in result["custom"]


def test_extract_python_exceptions_empty(chunker):
    result = chunker._extract_python_exceptions("x = 1")
    assert result["raised"] == []
    assert result["caught"] == []
    assert result["custom"] == []


# ==================== Python globals ====================

def test_extract_python_globals_constants(chunker):
    content = "MAX_SIZE = 100\nDEFAULT_TIMEOUT = 30\n"
    result = chunker._extract_python_globals(content)
    assert "MAX_SIZE" in result
    assert "DEFAULT_TIMEOUT" in result


def test_extract_python_globals_constants_first(chunker):
    content = "MAX_SIZE = 100\nlower_var = 'hello'\n"
    result = chunker._extract_python_globals(content)
    # Constants should appear before lowercase vars
    assert result.index("MAX_SIZE") < result.index("lower_var")


def test_extract_python_globals_skips_imports(chunker):
    content = "import os\nfrom sys import path\nMAX = 10\n"
    result = chunker._extract_python_globals(content)
    assert "os" not in result
    assert "MAX" in result


# ==================== TypeScript ====================

def test_extract_ts_interfaces(chunker):
    content = """
interface User {
    id: string;
    name: string;
    email: string;
}
"""
    result = chunker._extract_ts_interfaces(content)
    assert "User" in result
    assert any("id" in prop for prop in result["User"])


def test_extract_ts_types(chunker):
    content = "type UserId = string;\ntype Status = 'active' | 'inactive';\n"
    result = chunker._extract_ts_types(content)
    assert "UserId" in result
    assert "Status" in result


def test_extract_ts_enums(chunker):
    content = """
enum Direction {
    Up,
    Down,
    Left,
    Right
}
"""
    result = chunker._extract_ts_enums(content)
    assert "Direction" in result
    assert "Up" in result["Direction"]


def test_extract_ts_generics(chunker):
    content = "function identity<T>(arg: T): T { return arg; }\nconst pair: Pair<K, V> = {};\n"
    result = chunker._extract_ts_generics(content)
    assert len(result) > 0


# ==================== JavaScript imports ====================

def test_extract_js_imports_from(chunker):
    content = "import React from 'react';\nimport { useState } from 'react';\n"
    result = chunker._extract_js_imports_improved(content)
    assert "react" in result


def test_extract_js_imports_require(chunker):
    content = "const express = require('express');\n"
    result = chunker._extract_js_imports_improved(content)
    assert "express" in result


def test_extract_js_imports_no_duplicates(chunker):
    content = "import React from 'react';\nimport { useState } from 'react';\n"
    result = chunker._extract_js_imports_improved(content)
    assert result.count("react") == 1


def test_extract_js_imports_skips_relative(chunker):
    content = "import foo from './foo';\nimport bar from '../bar';\n"
    result = chunker._extract_js_imports_improved(content)
    assert "." not in result
    assert ".." not in result


# ==================== JavaScript exports ====================

def test_extract_js_exports_named(chunker):
    content = "export const foo = 1;\nexport function bar() {}\n"
    result = chunker._extract_js_exports(content)
    assert "foo" in result["named"]
    assert "bar" in result["named"]


def test_extract_js_exports_default(chunker):
    content = "export default MyComponent;\n"
    result = chunker._extract_js_exports(content)
    assert result["default"] == "MyComponent"


# ==================== Java ====================

def test_extract_java_annotations(chunker):
    content = "@Override\npublic void method() {}\n@Autowired\nprivate Service service;\n"
    result = chunker._extract_java_annotations(content)
    assert "Override" in result
    assert "Autowired" in result


def test_extract_java_interfaces(chunker):
    content = "public interface Serializable {}\ninterface Runnable {}\n"
    result = chunker._extract_java_interfaces(content)
    assert "Serializable" in result
    assert "Runnable" in result


def test_extract_java_access_modifiers(chunker):
    content = "public class Foo {\n    private int x;\n    protected void bar() {}\n}\n"
    result = chunker._extract_java_access_modifiers(content)
    assert result["public"] > 0
    assert result["private"] > 0
    assert result["protected"] > 0
