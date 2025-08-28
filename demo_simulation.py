"""Demo script to showcase the simulation engine."""

import json
from simulation.engine import SimulationEnvironment
from simulation.engine.core import SimulationConfig


def run_basic_simulation():
    """Run a basic simulation with default settings."""
    print("=" * 60)
    print("Running Basic Beer Distribution Game Simulation")
    print("=" * 60)
    
    # Create default configuration
    config = SimulationConfig(
        weeks=52,
        initial_inventory=12,
        holding_cost_per_unit=0.5,
        backlog_cost_per_unit=1.0,
        demand_type="constant",
        demand_params={"base_demand": 4}
    )
    
    # Create and run simulation
    sim = SimulationEnvironment(config)
    results = sim.run()
    
    # Display summary
    summary = results['summary']
    print(f"\nSimulation ID: {summary['simulation_id']}")
    print(f"Total Weeks: {summary['total_weeks']}")
    print(f"\nCosts:")
    print(f"  Total Cost: ${summary['total_cost']:.2f}")
    print(f"  Holding Cost: ${summary['total_holding_cost']:.2f}")
    print(f"  Backlog Cost: ${summary['total_backlog_cost']:.2f}")
    print(f"  Average Cost/Week: ${summary['average_cost_per_week']:.2f}")
    print(f"\nPerformance:")
    print(f"  Fill Rate: {summary['fill_rate']:.2%}")
    print(f"  Stockout Weeks: {summary['stockout_weeks']}")
    print(f"  Bullwhip Ratio: {summary['bullwhip_ratio']:.2f}")
    
    # Display node summaries
    print("\nNode Summaries:")
    for node_name, node_summary in results['node_summaries'].items():
        print(f"\n  {node_name}:")
        print(f"    Avg Inventory: {node_summary['average_inventory']:.1f}")
        print(f"    Avg Backlog: {node_summary['average_backlog']:.1f}")
        print(f"    Total Cost: ${node_summary['total_cost']:.2f}")
    
    return results


def run_step_demand_simulation():
    """Run a simulation with step change in demand."""
    print("\n" + "=" * 60)
    print("Running Step Demand Simulation")
    print("=" * 60)
    
    # Create configuration with step demand
    config = SimulationConfig(
        weeks=52,
        initial_inventory=12,
        demand_type="step",
        demand_params={
            "base_demand": 4,
            "step_demand": 8,
            "step_week": 5
        }
    )
    
    # Create and run simulation
    sim = SimulationEnvironment(config)
    
    # Add callback to show progress
    def on_week_complete(state):
        if state['current_week'] % 10 == 0:
            print(f"  Week {state['current_week']}: Total cost so far = ${state['metrics']['total_cost']:.2f}")
    
    sim.on_week_complete = on_week_complete
    
    results = sim.run()
    
    # Display results
    summary = results['summary']
    print(f"\nFinal Results:")
    print(f"  Total Cost: ${summary['total_cost']:.2f}")
    print(f"  Bullwhip Ratio: {summary['bullwhip_ratio']:.2f}")
    
    return results


def run_random_demand_simulation():
    """Run a simulation with random demand variation."""
    print("\n" + "=" * 60)
    print("Running Random Demand Simulation")
    print("=" * 60)
    
    # Create configuration with random demand
    config = SimulationConfig(
        weeks=52,
        initial_inventory=12,
        demand_type="random",
        demand_params={
            "base_demand": 4,
            "variation": 2
        }
    )
    
    # Create and run simulation
    sim = SimulationEnvironment(config)
    results = sim.run()
    
    # Display results
    summary = results['summary']
    print(f"\nResults with Random Demand:")
    print(f"  Total Cost: ${summary['total_cost']:.2f}")
    print(f"  Fill Rate: {summary['fill_rate']:.2%}")
    print(f"  Bullwhip Ratio: {summary['bullwhip_ratio']:.2f}")
    
    return results


def compare_scenarios():
    """Compare different scenarios."""
    print("\n" + "=" * 60)
    print("Comparing Different Scenarios")
    print("=" * 60)
    
    scenarios = [
        ("Constant Demand", {"demand_type": "constant", "demand_params": {"base_demand": 4}}),
        ("Step Demand", {"demand_type": "step", "demand_params": {"base_demand": 4, "step_demand": 8, "step_week": 5}}),
        ("Random Demand", {"demand_type": "random", "demand_params": {"base_demand": 4, "variation": 2}}),
    ]
    
    results_comparison = []
    
    for scenario_name, scenario_params in scenarios:
        config = SimulationConfig(weeks=52, **scenario_params)
        sim = SimulationEnvironment(config)
        results = sim.run()
        summary = results['summary']
        
        results_comparison.append({
            'scenario': scenario_name,
            'total_cost': summary['total_cost'],
            'fill_rate': summary['fill_rate'],
            'bullwhip_ratio': summary['bullwhip_ratio']
        })
    
    # Display comparison table
    print("\nScenario Comparison:")
    print(f"{'Scenario':<20} {'Total Cost':>12} {'Fill Rate':>12} {'Bullwhip':>12}")
    print("-" * 60)
    for result in results_comparison:
        print(f"{result['scenario']:<20} ${result['total_cost']:>11.2f} {result['fill_rate']:>11.2%} {result['bullwhip_ratio']:>11.2f}")


def main():
    """Main demo function."""
    print("\n" + "=" * 60)
    print("     BEER DISTRIBUTION GAME SIMULATION ENGINE DEMO")
    print("=" * 60)
    
    # Run different simulation scenarios
    basic_results = run_basic_simulation()
    step_results = run_step_demand_simulation()
    random_results = run_random_demand_simulation()
    
    # Compare scenarios
    compare_scenarios()
    
    # Save results to file
    print("\n" + "=" * 60)
    print("Saving Results")
    print("=" * 60)
    
    with open('simulation_results.json', 'w') as f:
        json.dump({
            'basic': basic_results['summary'],
            'step_demand': step_results['summary'],
            'random_demand': random_results['summary']
        }, f, indent=2)
    
    print("\nResults saved to simulation_results.json")
    print("\nDemo completed successfully!")


if __name__ == "__main__":
    main()
