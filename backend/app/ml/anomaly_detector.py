"""
Anomaly Detection for Comparables Analysis
Uses Isolation Forest to identify outliers in peer group metrics.
"""
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class ComparablesAnomalyDetector:
    """
    Machine learning-based outlier detection for comparables.
    Helps identify companies that don't fit the peer group.
    """

    def __init__(self, contamination=0.1):
        """
        Args:
            contamination: Expected proportion of outliers (default 10%)
        """
        self.contamination = contamination
        self.model = None # Defer model creation

    def _initialize_model(self):
        if self.model is not None:
            return

        try:
            from sklearn.ensemble import IsolationForest
            self.model = IsolationForest(
                contamination=self.contamination,
                random_state=42,
                n_estimators=100
            )
        except Exception as e:
            logger.error(f"Failed to initialize IsolationForest: {e}")
            self.model = None

    def detect_outliers(self, companies: List[Dict]) -> List[Dict]:
        """
        Detect outlier companies based on financial metrics.
        """
        if self.model is None:
            self._initialize_model()

        if self.model is None or len(companies) < 3:
            logger.warning("Too few companies or model unavailable for anomaly detection")
            return companies

        import numpy as np
        # Extract numeric features
        feature_keys = ['market_cap', 'pe_ratio', 'pb_ratio', 'revenue_growth', 'profit_margin']
        features = []
        valid_companies = []

        for company in companies:
            company_features = []
            valid = True

            for key in feature_keys:
                value = company.get(key)
                if value is not None and isinstance(value, (int, float)):
                    company_features.append(value)
                else:
                    valid = False
                    break

            if valid and len(company_features) == len(feature_keys):
                features.append(company_features)
                valid_companies.append(company)

        if len(features) < 3:
            logger.warning("Insufficient valid data for anomaly detection")
            return companies

        # Fit and predict
        X = np.array(features)
        predictions = self.model.fit_predict(X)
        scores = self.model.score_samples(X)

        # Annotate companies
        for i, company in enumerate(valid_companies):
            company['is_outlier'] = bool(predictions[i] == -1)
            company['anomaly_score'] = float(scores[i])
            company['outlier_reason'] = self._explain_outlier(company, X[i], X) if predictions[i] == -1 else None

        return valid_companies

    def _explain_outlier(self, company: Dict, features: any, all_features: any) -> str:
        """Generate human-readable explanation for why company is an outlier"""
        import numpy as np
        feature_keys = ['market_cap', 'pe_ratio', 'pb_ratio', 'revenue_growth', 'profit_margin']

        # Find which feature deviates most from median
        medians = np.median(all_features, axis=0)
        stds = np.std(all_features, axis=0)

        z_scores = np.abs((features - medians) / (stds + 1e-10))
        max_idx = np.argmax(z_scores)

        feature_name = feature_keys[max_idx]
        feature_value = features[max_idx]
        median_value = medians[max_idx]

        return f"Unusual {feature_name}: {feature_value:.2f} (peer median: {median_value:.2f})"

# Singleton
_detector = None

def get_anomaly_detector() -> ComparablesAnomalyDetector:
    """Get or create anomaly detector"""
    global _detector
    if _detector is None:
        _detector = ComparablesAnomalyDetector()
    return _detector
