"""
Schema & Statistics Generation
Validates chunk structure and data quality after embedding
"""
import json
import logging
from datetime import datetime
from typing import List, Dict

log = logging.getLogger(__name__)

VALID_LANGUAGES = {
    "python", "javascript", "typescript", "java", "go",
    "rust", "cpp", "c", "ruby", "php", "swift", "kotlin",
    "scala", "sql", "markdown", "json", "yaml", "html",
    "css", "scss", "unknown"
}

REQUIRED_FIELDS = [
    "content", "language", "file_path",
    "chunk_index", "start_line", "end_line"
]


class SchemaValidator:

    def validate(self, chunks: List[Dict]) -> Dict:
        """Run all expectations and return report"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "total": len(chunks),
            "expectations": {}
        }

        # Expectation 1: Required fields present
        missing = [
            i for i, c in enumerate(chunks)
            if any(f not in c for f in REQUIRED_FIELDS)
        ]
        results["expectations"]["required_fields_present"] = {
            "passed": len(missing) == 0,
            "failed_count": len(missing),
            "details": f"Required: {REQUIRED_FIELDS}"
        }

        # Expectation 2: Content non-empty
        empty = [i for i, c in enumerate(chunks)
                 if not c.get("content", "").strip()]
        results["expectations"]["content_non_empty"] = {
            "passed": len(empty) == 0,
            "failed_count": len(empty)
        }

        # Expectation 3: Valid language
        invalid_lang = [
            i for i, c in enumerate(chunks)
            if c.get("language", "").lower() not in VALID_LANGUAGES
        ]
        results["expectations"]["language_valid"] = {
            "passed": len(invalid_lang) == 0,
            "failed_count": len(invalid_lang)
        }

        # Expectation 4: chunk_index non-negative
        invalid_idx = [
            i for i, c in enumerate(chunks)
            if not isinstance(c.get("chunk_index"), int)
            or c.get("chunk_index", -1) < 0
        ]
        results["expectations"]["chunk_index_non_negative"] = {
            "passed": len(invalid_idx) == 0,
            "failed_count": len(invalid_idx)
        }

        # Expectation 5: start_line <= end_line
        invalid_lines = [
            i for i, c in enumerate(chunks)
            if c.get("start_line", 0) > c.get("end_line", 0)
        ]
        results["expectations"]["start_lte_end_line"] = {
            "passed": len(invalid_lines) == 0,
            "failed_count": len(invalid_lines)
        }

        # Expectation 6: Embedding dimension 768
        wrong_dim = [
            i for i, c in enumerate(chunks)
            if c.get("embedding") and len(c["embedding"]) != 768
        ]
        results["expectations"]["embedding_dim_768"] = {
            "passed": len(wrong_dim) == 0,
            "failed_count": len(wrong_dim)
        }

        passed = sum(
            1 for e in results["expectations"].values() if e["passed"])
        results["passed"] = passed
        results["failed"] = len(results["expectations"]) - passed
        results["overall_pass"] = results["failed"] == 0
        results["statistics"] = self._generate_statistics(chunks)

        return results

    def _generate_statistics(self, chunks: List[Dict]) -> Dict:
        if not chunks:
            return {}

        languages = {}
        sizes = []
        files = set()

        for c in chunks:
            lang = c.get("language", "unknown")
            languages[lang] = languages.get(lang, 0) + 1
            sizes.append(len(c.get("content", "")))
            if c.get("file_path"):
                files.add(c["file_path"])

        avg = sum(sizes) / len(sizes) if sizes else 0

        return {
            "total_chunks": len(chunks),
            "total_files": len(files),
            "languages": languages,
            "chunk_size": {
                "avg": round(avg, 2),
                "max": max(sizes) if sizes else 0,
                "min": min(sizes) if sizes else 0,
            }
        }
