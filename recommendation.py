"""
Simple recommendation engine stub.

This lightweight implementation provides the minimal API expected by
`app.py` and `main.py`: `RecommendationEngine` with
`cluster_items()` and `calculate_relevance_score()`.

It intentionally avoids heavy deps so the project can start using the
CSV fallback. Replace with a full implementation later if desired.
"""
from typing import List, Dict, Any


class RecommendationEngine:
    def __init__(self, n_clusters: int = 3):
        self.n_clusters = max(1, int(n_clusters))

    def calculate_relevance_score(self, item: Dict[str, Any], slots: Dict[str, Any]) -> float:
        """Simple heuristic score based on keyword matches and budget fit."""
        score = 0.0

        # location match
        loc = str(item.get("location") or item.get("lokasi") or "").lower()
        if slots.get("lokasi") and slots.get("lokasi").lower() in loc:
            score += 2.0

        # tema/name match
        name = str(item.get("name") or item.get("nama") or "").lower()
        if slots.get("tema") and slots.get("tema").lower() in name:
            score += 1.0

        # budget fit (prefer items within min/max if provided)
        price = None
        for k in ("price", "min_price", "harga_min", "harga"):
            if item.get(k) is not None:
                try:
                    price = int(item.get(k))
                    break
                except Exception:
                    continue

        bmin = slots.get("budget_min")
        bmax = slots.get("budget_max")
        if price is not None:
            if bmin and price >= int(bmin):
                score += 0.5
            if bmax and price <= int(bmax):
                score += 0.5

        return score

    def cluster_items(self, items: List[Dict[str, Any]], slots: Dict[str, Any]) -> Dict[str, Any]:
        """Create simple clusters by sorting items by relevance and round-robin assignment.

        Returns a dict with keys: total_items, clusters, recommendations
        """
        if not items:
            return {"total_items": 0, "clusters": [], "recommendations": []}

        # compute relevance scores
        for it in items:
            it["relevance_score"] = self.calculate_relevance_score(it, slots or {})

        # sort by score (and fallback to price if present)
        def sort_key(x):
            price = x.get("price") or x.get("min_price") or x.get("harga_min") or 0
            try:
                price = int(price)
            except Exception:
                price = 0
            return (x.get("relevance_score", 0), -price)

        items_sorted = sorted(items, key=sort_key, reverse=True)

        # split into clusters (round-robin)
        clusters: List[List[Dict[str, Any]]] = [[] for _ in range(self.n_clusters)]
        for idx, it in enumerate(items_sorted):
            clusters[idx % self.n_clusters].append(it)

        recommendations = items_sorted[:10]

        return {"total_items": len(items_sorted), "clusters": clusters, "recommendations": recommendations}
