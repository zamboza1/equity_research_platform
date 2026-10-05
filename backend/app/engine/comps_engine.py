from typing import List, Dict, Optional
import numpy as np
from pydantic import BaseModel

class ComparableScore(BaseModel):
    growth_score: float
    profitability_score: float
    valuation_score: float
    overall_score: float

class AdvancedCompsEngine:
    @staticmethod
    def calculate_composite_scores(companies: List[Dict]) -> List[Dict]:
        """Calculates institutional scores for growth, profitability, and valuation"""
        if not companies:
            return []

        # Extract for normalization
        metrics = {
            'pe': [c.get('pe_ratio', 0) for c in companies],
            'growth': [c.get('revenue_growth', 0) for c in companies],
            'margin': [c.get('profit_margin', 0) for c in companies]
        }

        # Simple Z-score normalization helper
        def normalize(vals, inverse=False):
            if not vals: return [0] * len(vals)
            arr = np.array(vals)
            m, s = np.mean(arr), np.std(arr)
            if s == 0: return [50.0] * len(vals)
            z = (arr - m) / s
            # Scale to 0-100
            res = 50 + (z * 15) # ~100 scale
            res = np.clip(res, 0, 100)
            return (100 - res) if inverse else res

        growth_normalized = normalize(metrics['growth'])
        profit_normalized = normalize(metrics['margin'])
        valuation_normalized = normalize(metrics['pe'], inverse=True) # Low PE is better/higher score

        for i, company in enumerate(companies):
            g = float(growth_normalized[i])
            p = float(profit_normalized[i])
            v = float(valuation_normalized[i])

            company['growth_score'] = g
            company['profitability_score'] = p
            company['valuation_score'] = v
            company['overall_score'] = (g * 0.4 + p * 0.4 + v * 0.2)

        return companies

    @staticmethod
    def identify_nlp_similarity(target_desc: str, peers: List[Dict]) -> List[Dict]:
        """
        Placeholder for NLP similarity ranking.
        In production, use sentence-transformers or TF-IDF.
        """
        # Explicit token overlap, not an NLP probability or financial score.
        import re
        target=set(re.findall(r"[a-z]{3,}",target_desc.lower()))
        for peer in peers:
            tokens=set(re.findall(r"[a-z]{3,}",str(peer.get('description','')).lower()))
            union=target|tokens
            peer['similarity_score']=len(target&tokens)/len(union) if union else None
            peer['similarity_method']='description_token_jaccard'
        return peers
