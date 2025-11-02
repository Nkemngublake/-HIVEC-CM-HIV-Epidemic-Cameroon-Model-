"""
HIVEC-CM Scenario Module
Policy scenario framework for Cameroon HIV epidemic modeling
"""

from .scenario_definitions import (
    BaselineScenario,
    OptimisticFundingScenario,
    PessimisticFundingScenario,
    IntensifiedTestingScenario,
    KeyPopulationScenario,
    PMTCTScenario,
    YouthAdolescentScenario,
    PSNAspirationalScenario,
    GeographicPrioritizationScenario,
    SCENARIO_REGISTRY,
    get_scenario,
    list_scenarios
)

__all__ = [
    'BaselineScenario',
    'OptimisticFundingScenario',
    'PessimisticFundingScenario',
    'IntensifiedTestingScenario',
    'KeyPopulationScenario',
    'PMTCTScenario',
    'YouthAdolescentScenario',
    'PSNAspirationalScenario',
    'GeographicPrioritizationScenario',
    'SCENARIO_REGISTRY',
    'get_scenario',
    'list_scenarios'
]
