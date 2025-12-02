"""
Stress Testing API Endpoints
Per techspec section 11
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
from datetime import date

from app.core.auth import require_risk_or_admin
from app.db.session import get_db
from risk_core.stress import StressScenario, STRESS_SCENARIOS, calc_stress_test

router = APIRouter()


class StressTestRequest(BaseModel):
    """Request for stress test"""
    portfolio_id: int
    scenarios: List[StressScenario]
    as_of_date: Optional[date] = None


class StressTestResponse(BaseModel):
    """Stress test result"""
    scenario: str
    description: str
    pnl_impact: float
    pnl_pct: float
    delta_var: float
    delta_capital_ratio: Optional[float] = None


@router.post("/stress/run")
async def run_stress_test(
    request: StressTestRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_risk_or_admin),
):
    """
    Run stress tests for portfolio
    
    Per techspec section 11
    
    **Required role**: RISK or ADMIN
    
    Returns:
        List of stress test results
    """
    # TODO: Load portfolio metrics and positions from DB
    # For now, mock data
    portfolio_metrics = {
        'portfolio_id': request.portfolio_id,
        'dv01_total': 5000.0,
        'total_market_value': 10000000.0,
        'avg_spread_duration': 3.5,
    }
    
    positions_data = []
    
    results = []
    for scenario in request.scenarios:
        result = calc_stress_test(scenario, portfolio_metrics, positions_data)
        
        shock = STRESS_SCENARIOS.get(scenario)
        
        results.append(StressTestResponse(
            scenario=result.scenario.value,
            description=shock.description if shock else "",
            pnl_impact=result.pnl_impact,
            pnl_pct=result.pnl_pct,
            delta_var=result.delta_var,
            delta_capital_ratio=result.delta_capital_ratio,
        ))
    
    return {
        "portfolio_id": request.portfolio_id,
        "as_of_date": request.as_of_date or date.today(),
        "results": results,
    }


@router.get("/stress/scenarios")
async def list_stress_scenarios(user=Depends(require_risk_or_admin)):
    """
    List available stress scenarios
    
    **Required role**: RISK or ADMIN
    
    Returns:
        List of scenarios with descriptions
    """
    scenarios = []
    for scenario, shock in STRESS_SCENARIOS.items():
        scenarios.append({
            "scenario": scenario.value,
            "description": shock.description,
            "type": scenario.value.split("_")[0],  # IR, CS, FX, VOL, LIQ
        })
    
    return {"scenarios": scenarios}
