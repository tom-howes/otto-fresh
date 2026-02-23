"""
Unit tests for GitHubIngester (data_acquisition)
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from src.ingestion.github_ingester import GitHubIngester


@pytest.fixture
def ingester():
    with patch("src.ingestion.github_ingester.storage.Client"):
        return GitHubIngester(
            project_id="test-project",
            bucket_name="test-bucket",
            github_token="test-token"
        )


# ==================== _parse_repo_url ====================

def test_parse_repo_url_full_url(ingester):
    owner, repo = ingester._parse_repo_url("https://github.com/otto-pm/otto")
    assert owner == "otto-pm"
    assert repo == "otto"


def test_parse_repo_url_git_suffix(ingester):
    owner, repo = ingester._parse_repo_url(
        "https://github.com/otto-pm/otto.git")
    assert owner == "otto-pm"
    assert repo == "otto"


def test_parse_repo_url_short_format(ingester):
    owner, repo = ingester._parse_repo_url("otto-pm/otto")
    assert owner == "otto-pm"
    assert repo == "otto"


def test_parse_repo_url_trailing_slash(ingester):
    owner, repo = ingester._parse_repo_url("https://github.com/otto-pm/otto/")
    assert owner == "otto-pm"
    assert repo == "otto"


# ==================== _detect_language ====================

def test_detect_language_python(ingester):
    assert ingester._detect_language("app/main.py") == "python"


def test_detect_language_typescript(ingester):
    assert ingester._detect_language("frontend/page.tsx") == "typescript"


def test_detect_language_javascript(ingester):
    assert ingester._detect_language("index.js") == "javascript"


def test_detect_language_java(ingester):
    assert ingester._detect_language("Main.java") == "java"


def test_detect_language_unknown(ingester):
    assert ingester._detect_language("Makefile") == "unknown"


def test_detect_language_no_extension(ingester):
    assert ingester._detect_language("README") == "unknown"


# ==================== _filter_code_files ====================

def test_filter_code_files_excludes_node_modules(ingester):
    tree = [{"type": "blob", "path": "node_modules/lodash/index.js"}]
    assert ingester._filter_code_files(tree) == []


def test_filter_code_files_excludes_pycache(ingester):
    tree = [{"type": "blob", "path": "__pycache__/main.cpython-311.pyc"}]
    assert ingester._filter_code_files(tree) == []


def test_filter_code_files_excludes_directories(ingester):
    tree = [{"type": "tree", "path": "src"}]
    assert ingester._filter_code_files(tree) == []


def test_filter_code_files_includes_python(ingester):
    tree = [{"type": "blob", "path": "src/main.py"}]
    result = ingester._filter_code_files(tree)
    assert len(result) == 1
    assert result[0]["path"] == "src/main.py"


def test_filter_code_files_includes_typescript(ingester):
    tree = [{"type": "blob", "path": "frontend/app/page.tsx"}]
    result = ingester._filter_code_files(tree)
    assert len(result) == 1


def test_filter_code_files_excludes_unsupported_extension(ingester):
    tree = [{"type": "blob", "path": "image.png"}]
    assert ingester._filter_code_files(tree) == []


def test_filter_code_files_mixed_tree(ingester):
    tree = [
        {"type": "blob", "path": "src/main.py"},
        {"type": "blob", "path": "node_modules/pkg/index.js"},
        {"type": "blob", "path": "README.md"},
        {"type": "tree", "path": "src"},
        {"type": "blob", "path": "image.png"},
    ]
    result = ingester._filter_code_files(tree)
    paths = [f["path"] for f in result]
    assert "src/main.py" in paths
    assert "README.md" in paths
    assert "node_modules/pkg/index.js" not in paths
    assert "image.png" not in paths


# ==================== _create_retry_session ====================

def test_create_retry_session_returns_session(ingester):
    import requests
    session = ingester._create_retry_session()
    assert isinstance(session, requests.Session)


# ==================== Edge cases ====================

def test_ingester_no_token():
    with patch("src.ingestion.github_ingester.storage.Client"):
        ingester = GitHubIngester(
            project_id="test-project",
            bucket_name="test-bucket"
        )
    assert ingester.github_token is None
    assert "Authorization" not in ingester.headers


def test_ingester_with_token():
    with patch("src.ingestion.github_ingester.storage.Client"):
        ingester = GitHubIngester(
            project_id="test-project",
            bucket_name="test-bucket",
            github_token="ghp_abc123"
        )
    assert ingester.headers["Authorization"] == "token ghp_abc123"
