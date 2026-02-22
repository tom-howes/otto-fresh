"""
Bias Detection via Data Slicing
Slices by: language, file type, repo section, chunk size
Detects inconsistent embedding coverage across slices
"""
import logging
import statistics
from datetime import datetime
from typing import List, Dict

log = logging.getLogger(__name__)


class BiasDetector:

    def detect(self, chunks: List[Dict], repo: str = "") -> Dict:
        results = {
            "timestamp": datetime.now().isoformat(),
            "repo": repo,
            "total_chunks": len(chunks),
            "slicing_analyses": {}
        }

        results["slicing_analyses"]["by_language"] = self._analyze_slice(
            self._slice_by_language(chunks), "language"
        )
        results["slicing_analyses"]["by_file_type"] = self._analyze_slice(
            self._slice_by_file_type(chunks), "file_type"
        )
        results["slicing_analyses"]["by_chunk_size"] = self._analyze_slice(
            self._slice_by_chunk_size(chunks), "chunk_size"
        )
        results["slicing_analyses"]["by_repo_section"] = self._analyze_slice(
            self._slice_by_repo_section(chunks), "repo_section"
        )

        any_bias = any(
            a["bias_detected"]
            for a in results["slicing_analyses"].values()
        )
        results["bias_detected"] = any_bias
        results["recommendation"] = (
            "Bias detected — review biased_slices and consider re-embedding"
            if any_bias else
            "No significant bias detected across slices"
        )

        return results

    def _slice_by_language(self, chunks):
        slices = {}
        for c in chunks:
            lang = c.get("language", "unknown")
            slices.setdefault(lang, []).append(c)
        return slices

    def _slice_by_file_type(self, chunks):
        slices = {}
        for c in chunks:
            path = c.get("file_path", "")
            ext = "." + path.split(".")[-1] if "." in path else "unknown"
            slices.setdefault(ext, []).append(c)
        return slices

    def _slice_by_chunk_size(self, chunks):
        slices = {"small": [], "medium": [], "large": []}
        for c in chunks:
            size = len(c.get("content", ""))
            if size < 200:
                slices["small"].append(c)
            elif size < 1000:
                slices["medium"].append(c)
            else:
                slices["large"].append(c)
        return slices

    def _slice_by_repo_section(self, chunks):
        slices = {}
        for c in chunks:
            path = c.get("file_path", "")
            section = path.split("/")[0] if "/" in path else "root"
            slices.setdefault(section, []).append(c)
        return slices

    def _analyze_slice(self, slices: Dict, slice_type: str) -> Dict:
        analyses = {}
        for name, slice_chunks in slices.items():
            if not slice_chunks:
                continue
            with_emb = sum(1 for c in slice_chunks if c.get("embedding"))
            coverage = with_emb / len(slice_chunks)
            sizes = [len(c.get("content", "")) for c in slice_chunks]
            analyses[name] = {
                "count": len(slice_chunks),
                "embedding_coverage": round(coverage, 3),
                "avg_content_size": round(
                    sum(sizes) / len(sizes) if sizes else 0, 1
                ),
                "missing_embeddings": len(slice_chunks) - with_emb,
            }

        # Detect bias — slices > 1 stdev below average coverage
        coverages = [
            a["embedding_coverage"]
            for a in analyses.values()
            if a["count"] > 5
        ]
        if len(coverages) < 2:
            return {
                "slice_type": slice_type,
                "analyses": analyses,
                "bias_detected": False,
                "biased_slices": [],
                "mitigation": "Not enough slices to compare"
            }

        avg = statistics.mean(coverages)
        stdev = statistics.stdev(coverages)

        biased = [
            name for name, a in analyses.items()
            if a["count"] > 5
            and a["embedding_coverage"] < avg - stdev
        ]

        return {
            "slice_type": slice_type,
            "analyses": analyses,
            "avg_embedding_coverage": round(avg, 3),
            "bias_detected": len(biased) > 0,
            "biased_slices": biased,
            "mitigation": (
                f"Slices {biased} have lower embedding coverage. "
                f"Consider force re-embedding these."
                if biased else "No bias detected"
            )
        }