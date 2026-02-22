"""
Shared pytest configuration and fixtures
"""
import pytest
import sys
import os

# Add ingest-service to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../ingest-service"))
