"""
Concentration Risk calculations
Per techspec section 1.2 and 2
"""
from dataclasses import dataclass
from typing import List, Dict
from collections import defaultdict


@dataclass
class ConcentrationMetrics:
    """Concentration risk metrics"""
    # Issuer concentration
    largest_issuer_exposure: float
    top_5_issuers_exposure: float
    top_10_issuers_exposure: float
    herfindahl_issuer: float
    
    # Country concentration
    largest_country_exposure: float
    top_5_countries_exposure: float
    herfindahl_country: float
    
    # Sector concentration
    largest_sector_exposure: float
    top_5_sectors_exposure: float
    herfindahl_sector: float
    
    # Counterparty concentration (for derivatives)
    largest_counterparty_ead: float
    top_5_counterparties_ead: float
    herfindahl_counterparty: float


def calc_herfindahl_index(exposures: List[float], total: float) -> float:
    """
    Calculate Herfindahl-Hirschman Index
    HHI = Σ (exposure_i / total)^2
    
    HHI близок к 1 = высокая концентрация
    HHI близок к 0 = низкая концентрация
    """
    if total == 0:
        return 0.0
    
    hhi = sum((exp / total) ** 2 for exp in exposures)
    return hhi


def calc_concentration_metrics(
    issuer_exposures: Dict[int, float],  # issuer_id -> exposure
    country_exposures: Dict[str, float],  # country_code -> exposure
    sector_exposures: Dict[str, float],   # sector -> exposure
    counterparty_eads: Dict[int, float],  # counterparty_id -> EAD
) -> ConcentrationMetrics:
    """
    Calculate concentration risk metrics across dimensions
    Per techspec section 1.2: issuer/country/sector/counterparty
    """
    # Issuer concentration
    issuer_vals = sorted(issuer_exposures.values(), reverse=True)
    total_issuer = sum(issuer_vals) if issuer_vals else 1.0
    
    largest_issuer = issuer_vals[0] if issuer_vals else 0.0
    top_5_issuers = sum(issuer_vals[:5]) if len(issuer_vals) >= 5 else sum(issuer_vals)
    top_10_issuers = sum(issuer_vals[:10]) if len(issuer_vals) >= 10 else sum(issuer_vals)
    hhi_issuer = calc_herfindahl_index(issuer_vals, total_issuer)
    
    # Country concentration
    country_vals = sorted(country_exposures.values(), reverse=True)
    total_country = sum(country_vals) if country_vals else 1.0
    
    largest_country = country_vals[0] if country_vals else 0.0
    top_5_countries = sum(country_vals[:5]) if len(country_vals) >= 5 else sum(country_vals)
    hhi_country = calc_herfindahl_index(country_vals, total_country)
    
    # Sector concentration
    sector_vals = sorted(sector_exposures.values(), reverse=True)
    total_sector = sum(sector_vals) if sector_vals else 1.0
    
    largest_sector = sector_vals[0] if sector_vals else 0.0
    top_5_sectors = sum(sector_vals[:5]) if len(sector_vals) >= 5 else sum(sector_vals)
    hhi_sector = calc_herfindahl_index(sector_vals, total_sector)
    
    # Counterparty concentration
    cpty_vals = sorted(counterparty_eads.values(), reverse=True)
    total_cpty = sum(cpty_vals) if cpty_vals else 1.0
    
    largest_cpty = cpty_vals[0] if cpty_vals else 0.0
    top_5_cpty = sum(cpty_vals[:5]) if len(cpty_vals) >= 5 else sum(cpty_vals)
    hhi_cpty = calc_herfindahl_index(cpty_vals, total_cpty)
    
    return ConcentrationMetrics(
        largest_issuer_exposure=largest_issuer,
        top_5_issuers_exposure=top_5_issuers,
        top_10_issuers_exposure=top_10_issuers,
        herfindahl_issuer=hhi_issuer,
        largest_country_exposure=largest_country,
        top_5_countries_exposure=top_5_countries,
        herfindahl_country=hhi_country,
        largest_sector_exposure=largest_sector,
        top_5_sectors_exposure=top_5_sectors,
        herfindahl_sector=hhi_sector,
        largest_counterparty_ead=largest_cpty,
        top_5_counterparties_ead=top_5_cpty,
        herfindahl_counterparty=hhi_cpty,
    )
