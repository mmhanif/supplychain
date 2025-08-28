"""Demo script showcasing the game logic layer."""

import json
from simulation.game import (
    GameController, GameStatus, GameRules, PlayerRole,
    PolicyManager, PolicyType,
    ScenarioManager, ScenarioType, DifficultyLevel
)
from simulation.engine.core import SimulationConfig


def demo_game_controller():
    """Demonstrate the game controller functionality."""
    print("=" * 60)
    print("GAME CONTROLLER DEMO")
    print("=" * 60)
    
    # Create game rules
    rules = GameRules(
        max_weeks=20,
        target_service_level=0.90,
        max_total_cost=5000,
        collaborative_mode=True,
        tutorial_mode=True
    )
    
    # Create game controller
    game = GameController(game_rules=rules)
    
    # Add players
    player1 = game.add_player("Alice", PlayerRole.RETAILER, is_human=True)
    player2 = game.add_player("Bob", PlayerRole.WHOLESALER, is_human=False)
    player3 = game.add_player("Charlie", PlayerRole.DISTRIBUTOR, is_human=False)
    player4 = game.add_player("Diana", PlayerRole.FACTORY, is_human=False)
    
    print(f"Game ID: {game.game_id}")
    print(f"Status: {game.state.status.value}")
    print(f"Players: {len(game.state.players)}")
    
    # Initialize and start game
    game.initialize_game()
    print(f"Status after init: {game.state.status.value}")
    
    # Start the game
    game.start_game()
    print(f"Status after start: {game.state.status.value}")
    
    # Get player view
    player_view = game.get_player_view(player1.id)
    print(f"\nPlayer 1 view:")
    print(f"  Role: {player_view['player']['role']}")
    print(f"  Current Week: {player_view['current_week']}")
    
    # Check win conditions
    win_status = game.check_win_conditions()
    print(f"\nWin Conditions:")
    print(f"  All met: {win_status['all_conditions_met']}")
    print(f"  Game complete: {win_status['game_complete']}")
    
    # Get leaderboard
    leaderboard = game.get_leaderboard()
    print(f"\nLeaderboard:")
    for entry in leaderboard:
        print(f"  {entry['rank']}. {entry['name']} ({entry['role']}): {entry['score']:.0f} points")
    
    return game


def demo_policy_manager():
    """Demonstrate the policy manager functionality."""
    print("\n" + "=" * 60)
    print("POLICY MANAGER DEMO")
    print("=" * 60)
    
    # Create policy manager
    policy_manager = PolicyManager()
    
    # Test different policies
    policies = [
        PolicyType.BASE_STOCK,
        PolicyType.EOQ,
        PolicyType.SS_POLICY,
        PolicyType.FORECAST_BASED
    ]
    
    for policy_type in policies:
        print(f"\n{policy_type.value.upper()} Policy:")
        
        # Get policy info
        info = policy_manager.get_policy_info(policy_type)
        print(f"  Description: {info['description']}")
        print(f"  Parameters: {info['parameters']}")
        
        # Create policy function
        node_context = {
            "inventory": 10,
            "backlog": 2,
            "pending_orders": 5,
            "lead_time": 2
        }
        
        policy_func = policy_manager.create_policy(
            policy_type,
            node_context=node_context
        )
        
        # Test the policy
        order_qty = policy_func(1)  # Week 1
        print(f"  Order quantity (week 1): {order_qty}")
    
    # Test custom policy
    def custom_conservative_policy(week: int) -> int:
        """Custom conservative ordering policy."""
        return 3  # Always order 3 units
    
    policy_manager.register_custom_policy("conservative", custom_conservative_policy)
    print(f"\nCustom Policy Registered: conservative")
    
    # Update demand history for adaptive policies
    for demand in [4, 5, 4, 6, 3, 5]:
        policy_manager.update_demand_history(demand)
    
    avg_demand = policy_manager._estimate_average_demand()
    print(f"\nEstimated average demand: {avg_demand:.1f}")
    
    # Forecast demand
    forecast = policy_manager._forecast_demand(4)
    print(f"4-week demand forecast: {forecast}")
    
    return policy_manager


def demo_scenario_manager():
    """Demonstrate the scenario manager functionality."""
    print("\n" + "=" * 60)
    print("SCENARIO MANAGER DEMO")
    print("=" * 60)
    
    # Create scenario manager
    scenario_manager = ScenarioManager()
    
    # List all scenarios
    all_scenarios = scenario_manager.list_scenarios()
    print(f"\nTotal Available Scenarios: {len(all_scenarios)}")
    
    # List scenarios by difficulty
    for difficulty in DifficultyLevel:
        scenarios = scenario_manager.list_scenarios(difficulty=difficulty)
        print(f"  {difficulty.value.capitalize()}: {len(scenarios)} scenarios")
    
    # Display scenario details
    print("\nScenario Details:")
    for scenario_id in ["classic", "step_change", "seasonal", "tutorial"]:
        scenario = scenario_manager.get_scenario(scenario_id)
        if scenario:
            print(f"\n  {scenario.name}:")
            print(f"    Type: {scenario.type.value}")
            print(f"    Difficulty: {scenario.difficulty.value}")
            print(f"    Duration: {scenario.duration_weeks} weeks")
            print(f"    Tags: {', '.join(scenario.tags)}")
    
    # Get scenario hints
    hints = scenario_manager.get_scenario_hints("step_change", week=3)
    print(f"\nHints for 'step_change' scenario (week 3):")
    for hint in hints:
        print(f"  - {hint}")
    
    # Get difficulty settings
    settings = scenario_manager.get_difficulty_settings(DifficultyLevel.MEDIUM)
    print(f"\nMedium Difficulty Settings:")
    for key, value in settings.items():
        print(f"  {key}: {value}")
    
    # Create custom scenario
    custom_config = {
        "difficulty": "medium",
        "demand_type": "random",
        "demand_params": {"base_demand": 6, "variation": 2},
        "holding_cost": 0.75,
        "backlog_cost": 1.5,
        "duration": 30,
        "tags": ["custom", "test"]
    }
    
    custom_id = scenario_manager.create_custom_scenario(
        "Test Scenario",
        "A custom test scenario",
        custom_config
    )
    print(f"\nCreated custom scenario: {custom_id}")
    
    # Generate random scenario
    random_id = scenario_manager.generate_random_scenario(DifficultyLevel.MEDIUM)
    random_scenario = scenario_manager.get_scenario(random_id)
    print(f"\nGenerated random scenario: {random_scenario.name}")
    
    # Create simulation config from scenario
    config = scenario_manager.create_simulation_config("classic")
    print(f"\nSimulation config created for 'classic' scenario:")
    print(f"  Weeks: {config.weeks}")
    print(f"  Demand type: {config.demand_type}")
    print(f"  Initial inventory: {config.initial_inventory}")
    
    return scenario_manager


def demo_integrated_game():
    """Demonstrate integrated game logic with scenario and policies."""
    print("\n" + "=" * 60)
    print("INTEGRATED GAME DEMO")
    print("=" * 60)
    
    # Create managers
    scenario_manager = ScenarioManager()
    policy_manager = PolicyManager()
    
    # Select scenario
    scenario_id = "step_change"
    scenario = scenario_manager.get_scenario(scenario_id)
    print(f"Selected Scenario: {scenario.name}")
    print(f"  {scenario.description}")
    
    # Create simulation config from scenario
    sim_config = scenario_manager.create_simulation_config(scenario_id)
    
    # Apply difficulty settings
    difficulty_settings = scenario_manager.get_difficulty_settings(scenario.difficulty)
    
    # Create game rules based on scenario
    rules = GameRules(
        max_weeks=scenario.duration_weeks,
        target_service_level=scenario.target_service_level,
        max_total_cost=scenario.target_cost,
        enable_information_sharing=difficulty_settings["information_sharing"],
        enable_forecasting=difficulty_settings["forecast_enabled"],
        cost_penalty_multiplier=difficulty_settings["cost_multiplier"]
    )
    
    # Create game controller
    game = GameController(game_rules=rules, simulation_config=sim_config)
    
    print(f"\nGame Configuration:")
    print(f"  Duration: {rules.max_weeks} weeks")
    print(f"  Target Service Level: {rules.target_service_level:.0%}")
    print(f"  Information Sharing: {rules.enable_information_sharing}")
    print(f"  Cost Multiplier: {rules.cost_penalty_multiplier}")
    
    # Add players with different policies
    players = [
        ("AI-Retailer", PlayerRole.RETAILER, PolicyType.BASE_STOCK),
        ("AI-Wholesaler", PlayerRole.WHOLESALER, PolicyType.FORECAST_BASED),
        ("AI-Distributor", PlayerRole.DISTRIBUTOR, PolicyType.SS_POLICY),
        ("AI-Factory", PlayerRole.FACTORY, PolicyType.ADAPTIVE)
    ]
    
    for name, role, policy_type in players:
        player = game.add_player(name, role, is_human=False)
        print(f"  Added {name} using {policy_type.value} policy")
    
    # Initialize game
    game.initialize_game()
    
    # Configure AI policies
    if game.simulation:
        # Set up retailer with base stock policy
        retailer_policy = policy_manager.create_policy(
            PolicyType.BASE_STOCK,
            custom_params={"base_stock_level": 25}
        )
        
        # Set up wholesaler with forecast policy
        wholesaler_policy = policy_manager.create_policy(
            PolicyType.FORECAST_BASED,
            custom_params={"forecast_horizon": 6}
        )
        
        # Apply policies
        game.simulation.set_order_policies(
            retailer_policy=retailer_policy,
            wholesaler_policy=wholesaler_policy
        )
    
    print(f"\nGame Status: {game.state.status.value}")
    print("Game initialized with AI players and policies")
    
    # Start game
    print("\nStarting game...")
    game.start_game()
    
    # Display final results
    print(f"\nFinal Results:")
    print(f"  Total Cost: ${game.state.total_cost:.2f}")
    print(f"  Service Level: {game.state.service_level:.2%}")
    print(f"  Bullwhip Ratio: {game.state.bullwhip_ratio:.2f}")
    
    # Check win conditions
    win_status = game.check_win_conditions()
    print(f"\nWin Conditions Met: {win_status['all_conditions_met']}")
    if win_status['conditions']:
        for condition, met in win_status['conditions'].items():
            status = "✓" if met else "✗"
            print(f"  {status} {condition}")
    
    # Final leaderboard
    leaderboard = game.get_leaderboard()
    print(f"\nFinal Leaderboard:")
    for entry in leaderboard[:3]:
        print(f"  {entry['rank']}. {entry['name']}: {entry['score']:.0f} points")
    
    # Save game data
    game.save_game("demo_game_results.json")
    print(f"\nGame data saved to demo_game_results.json")
    
    return game


def main():
    """Main demo function."""
    print("\n" + "=" * 60)
    print("     BEER GAME - GAME LOGIC LAYER DEMONSTRATION")
    print("=" * 60)
    
    # Run demonstrations
    game_controller = demo_game_controller()
    policy_manager = demo_policy_manager()
    scenario_manager = demo_scenario_manager()
    
    # Run integrated demo
    integrated_game = demo_integrated_game()
    
    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)
    
    # Summary statistics
    print("\nSummary:")
    print(f"  Game Controller: Created game with {len(game_controller.state.players)} players")
    print(f"  Policy Manager: Demonstrated {len(PolicyType)} policy types")
    print(f"  Scenario Manager: {len(scenario_manager.scenarios)} predefined scenarios")
    print(f"  Integrated Game: Completed {integrated_game.state.current_week} weeks")


if __name__ == "__main__":
    main()
