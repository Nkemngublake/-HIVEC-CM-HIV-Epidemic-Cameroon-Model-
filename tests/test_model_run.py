
import os
import sys
import pytest

# Add the src directory to the Python path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from hivec_cm.models.parameters import load_parameters
from hivec_cm.models.model import EnhancedHIVModel

@pytest.fixture
def model_parameters():
    """Fixture to load model parameters for tests."""
    # Use a relative path to find the config file from the test file's location
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../config/parameters.json'))
    return load_parameters(config_path)

def test_simulation_runs_successfully(model_parameters):
    """
    Tests that a small-scale simulation runs to completion without errors.
    """
    # GIVEN a small initial population for a quick test run
    model_parameters.initial_population = 100
    
    # WHEN the model is initialized and run for a short period
    model = EnhancedHIVModel(params=model_parameters)
    # Run for 2 years with a large timestep for speed
    results_df = model.run_simulation(years=2, dt=1.0)
    
    # THEN assert that the results are not empty and have the expected columns
    assert not results_df.empty, "The simulation should produce a non-empty DataFrame."
    assert 'year' in results_df.columns, "Results should contain a 'year' column."
    assert 'hiv_prevalence' in results_df.columns, "Results should contain an 'hiv_prevalence' column."
    assert len(results_df) == 3, "The simulation should have run for the specified number of years (initial state + 2 years)."

