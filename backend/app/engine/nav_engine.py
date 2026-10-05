from pydantic import BaseModel as PydanticBaseModel, Field, ConfigDict

class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
from typing import List, Dict, Optional, Union

class NAVAsset(BaseModel):
    name: str
    value: float
    type: str # "Real Estate", "Financial", "Resource"
    details: Optional[Dict] = None

class RealEstateNAVInputs(BaseModel):
    noi: float = Field(ge=0) #
    cap_rate: float = Field(gt=0, le=1)
    other_assets: float = Field(ge=0) #
    total_debt: float = Field(ge=0) #
    minority_interest: float = Field(ge=0) #
    preferred_equity: float = Field(ge=0) #
    shares_outstanding: float = Field(gt=0)

class ResourceNAVInputs(BaseModel):
    reserves: float = Field(ge=0) # # e.g. boe or oz
    value_per_unit: float = Field(ge=0) #
    production_cost_per_unit: float = Field(ge=0) #
    exploration_upside: float = Field(ge=0) #
    liabilities: float = Field(ge=0) #
    shares_outstanding: float = Field(gt=0)

class NAVEngine:
    @staticmethod
    def calculate_real_estate(inputs: RealEstateNAVInputs) -> Dict:
        gross_asset_value = (inputs.noi / inputs.cap_rate) + inputs.other_assets
        nav = gross_asset_value - inputs.total_debt - inputs.minority_interest - inputs.preferred_equity
        nav_per_share = nav / inputs.shares_outstanding if inputs.shares_outstanding > 0 else 0

        return {
            "gross_asset_value": gross_asset_value,
            "net_asset_value": nav,
            "nav_per_share": nav_per_share,
            "components": {
                "property_valuation": inputs.noi / inputs.cap_rate,
                "other_assets": inputs.other_assets,
                "debt_deduction": -inputs.total_debt
            }
        }

    @staticmethod
    def calculate_resource(inputs: ResourceNAVInputs) -> Dict:
        # Simplified risked NAV for resources
        reserve_value = inputs.reserves * (inputs.value_per_unit - inputs.production_cost_per_unit)
        nav = reserve_value + inputs.exploration_upside - inputs.liabilities
        nav_per_share = nav / inputs.shares_outstanding if inputs.shares_outstanding > 0 else 0

        return {
            "reserve_value": reserve_value,
            "net_asset_value": nav,
            "nav_per_share": nav_per_share
        }
