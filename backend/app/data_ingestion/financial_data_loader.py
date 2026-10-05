"""
Data Ingestion Module for Historical Financials
Supports: SEC EDGAR, Excel, CSV, PDF
"""
from typing import List, Dict, Optional
from pydantic import BaseModel
import pandas as pd
import requests
from io import StringIO
import logging

logger = logging.getLogger(__name__)

class FinancialStatement(BaseModel):
    """Normalized financial statement data"""
    period: str
    statement_type: str  # "income_statement", "balance_sheet", "cash_flow"
    line_items: Dict[str, float]
    metadata: Dict[str, str] = {}

class HistoricalFinancials(BaseModel):
    """Complete set of historical financials"""
    company_name: str
    ticker: str
    currency: str = "USD"
    accounting_standard: str = "US_GAAP"
    periods: List[FinancialStatement]

class SECEDGARIngestion:
    """
    Fetch financial data from SEC EDGAR
    """
    BASE_URL = "https://data.sec.gov"

    def __init__(self, user_agent: str = "VertigeResearch/1.0"):
        self.headers = {"User-Agent": user_agent}

    def get_company_facts(self, ticker: str) -> Optional[Dict]:
        """
        Fetch company facts from SEC EDGAR API
        Returns structured financial data
        """
        try:
            # Get CIK from ticker (simplified - would need mapping table)
            cik = self._get_cik_from_ticker(ticker)
            if not cik:
                return None

            url = f"{self.BASE_URL}/api/xbrl/companyfacts/CIK{cik:010d}.json"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"SEC EDGAR request failed: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error fetching SEC data: {e}")
            return None

    def _get_cik_from_ticker(self, ticker: str) -> Optional[int]:
        """
        Get CIK number from ticker symbol
        """
        # Simplified - in production would use SEC ticker-CIK mapping
        ticker_cik_map = {
            "AAPL": 320193,
            "MSFT": 789019,
            "GOOGL": 1652044,
            "JPM": 19617,
            "PLD": 1045609,
        }
        return ticker_cik_map.get(ticker.upper())

    def parse_company_facts(self, facts_data: Dict) -> HistoricalFinancials:
        """
        Parse SEC company facts JSON into normalized format
        """
        # Extract company info
        company_name = facts_data.get("entityName", "Unknown")
        cik = facts_data.get("cik", "")

        periods = []

        # Parse US-GAAP facts
        us_gaap = facts_data.get("facts", {}).get("us-gaap", {})

        # Extract key line items
        revenue_data = us_gaap.get("Revenues", {}).get("units", {}).get("USD", [])

        for entry in revenue_data[-8:]:  # Last 8 quarters
            period = {
                "period": entry.get("end", ""),
                "statement_type": "income_statement",
                "line_items": {
                    "revenue": entry.get("val", 0)
                },
                "metadata": {
                    "form": entry.get("form", ""),
                    "filed": entry.get("filed", "")
                }
            }
            periods.append(FinancialStatement(**period))

        return HistoricalFinancials(
            company_name=company_name,
            ticker=f"CIK{cik}",
            currency="USD",
            accounting_standard="US_GAAP",
            periods=periods
        )

class ExcelCSVIngestion:
    """
    Parse financial data from Excel/CSV files
    """

    def parse_excel(self, file_path: str, sheet_name: str = "Financial Statements") -> HistoricalFinancials:
        """
        Parse Excel file with financial statements
        Expected format:
        - Rows: Line items (Revenue, COGS, etc.)
        - Columns: Periods (2020, 2021, 2022, etc.)
        """
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        return self._parse_dataframe(df)

    def parse_csv(self, file_path: str) -> HistoricalFinancials:
        """Parse CSV file with financials"""
        df = pd.read_csv(file_path)
        return self._parse_dataframe(df)

    def _parse_dataframe(self, df: pd.DataFrame) -> HistoricalFinancials:
        """
        Convert DataFrame to normalized financial statements
        """
        # Assume first column is line items, rest are periods
        line_item_col = df.columns[0]
        period_cols = df.columns[1:]

        periods = []

        for period_col in period_cols:
            line_items = {}
            for _, row in df.iterrows():
                line_item_name = str(row[line_item_col]).lower().replace(" ", "_")
                value = row[period_col]
                if pd.notna(value):
                    try:
                        line_items[line_item_name] = float(value)
                    except:
                        continue

            if line_items:
                periods.append(FinancialStatement(
                    period=str(period_col),
                    statement_type="income_statement",  # Default
                    line_items=line_items,
                    metadata={"source": "excel_csv"}
                ))

        return HistoricalFinancials(
            company_name="Uploaded Company",
            ticker="CUSTOM",
            currency="USD",
            periods=periods
        )

class DataNormalizer:
    """
    Normalize financial data across different sources and standards
    """

    def convert_currency(
        self,
        amount: float,
        from_currency: str,
        to_currency: str = "USD",
        exchange_rate: Optional[float] = None
    ) -> float:
        """Convert between currencies"""
        if from_currency == to_currency:
            return amount

        # Simplified - would use real-time FX rates in production
        if exchange_rate:
            return amount * exchange_rate

        # Default rates (placeholder)
        rates = {
            ("CAD", "USD"): 0.75,
            ("EUR", "USD"): 1.10,
            ("GBP", "USD"): 1.25,
        }

        rate = rates.get((from_currency, to_currency), 1.0)
        return amount * rate

    def translate_gaap_to_ifrs(self, line_item: str, value: float) -> tuple:
        """
        Translate US GAAP line items to IFRS equivalents
        Returns: (ifrs_line_item, adjusted_value)
        """
        # Simplified mapping
        gaap_to_ifrs = {
            "revenue": "revenue",
            "cost_of_goods_sold": "cost_of_sales",
            "selling_general_administrative": "distribution_costs",
            "research_development": "research_development_costs",
        }

        ifrs_item = gaap_to_ifrs.get(line_item, line_item)
        return (ifrs_item, value)

    def align_fiscal_years(
        self,
        periods: List[FinancialStatement],
        target_year_end: str = "12-31"
    ) -> List[FinancialStatement]:
        """
        Align fiscal years to calendar years
        """
        # Simplified - would need complex date logic for partial periods
        return periods

def create_sample_historical_data() -> HistoricalFinancials:
    """
    Generate sample historical data for testing
    """
    periods = []

    for year in range(2020, 2024):
        periods.append(FinancialStatement(
            period=f"{year}-12-31",
            statement_type="income_statement",
            line_items={
                "revenue": 1000000 * (1.1 ** (year - 2020)),
                "cogs": 600000 * (1.08 ** (year - 2020)),
                "operating_expenses": 200000 * (1.05 ** (year - 2020)),
                "depreciation": 20000,
                "interest_expense": 15000,
                "tax_expense": 35000 * (1.1 ** (year - 2020)),
                "net_income": 130000 * (1.15 ** (year - 2020))
            },
            metadata={"source": "sample_data"}
        ))

        periods.append(FinancialStatement(
            period=f"{year}-12-31",
            statement_type="balance_sheet",
            line_items={
                "cash": 150000,
                "accounts_receivable": 200000 * (1.1 ** (year - 2020)),
                "inventory": 180000 * (1.08 ** (year - 2020)),
                "ppe_net": 500000,
                "total_assets": 1030000 * (1.09 ** (year - 2020)),
                "accounts_payable": 120000 * (1.07 ** (year - 2020)),
                "short_term_debt": 80000,
                "long_term_debt": 300000,
                "total_liabilities": 500000,
                "retained_earnings": 400000 * (1.12 ** (year - 2020)),
                "total_equity": 530000 * (1.11 ** (year - 2020))
            },
            metadata={"source": "sample_data"}
        ))

    return HistoricalFinancials(
        company_name="Sample Company Inc.",
        ticker="SAMPLE",
        currency="USD",
        accounting_standard="US_GAAP",
        periods=periods
    )
