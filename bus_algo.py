import csv
import networkx as nx

def get_all_neighbors(graph, node):
    """Get all direct and indirect neighbors of a node using graph traversal."""
    all_neighbors = set()
    def dfs(current_node):
        for neighbor in graph.neighbors(current_node):
            if neighbor not in all_neighbors:
                all_neighbors.add(neighbor)
                dfs(neighbor)
    dfs(node)
    return all_neighbors - {node}

def calculate_max_capacity_required(group, sizes, group_graph, groups):
    neighbors = get_all_neighbors(group_graph, group)
    return sizes[groups.index(group)] + sum(sizes[groups.index(neighbor)] for neighbor in neighbors)

def allocate_to_buses(groups, sizes, capacities, group_graph):
    allocated_buses = {bus: [] for bus in range(1, len(capacities) + 1)}
    assigned_groups = set()
    # Combine group names and sizes into tuples
    groups_and_sizes = list(zip(groups, sizes))
    # Sort groups by the maximum capacity they would require in descending order
    sorted_groups = sorted(groups_and_sizes, key=lambda x: calculate_max_capacity_required(x[0], sizes, group_graph, groups), reverse=True)
    for group, group_size in sorted_groups:
        try:
            # Skip the group if it has already been assigned
            if group in assigned_groups:
                continue
            # Find all direct and indirect neighbors of the group
            all_neighbors = get_all_neighbors(group_graph, group)
            # Calculate the combined size of the group and its neighbors
            combined_size = group_size + sum(sizes[groups.index(neighbor)] for neighbor in all_neighbors)
            # Use the combined size to find the bus
            min_capacity_bus = min((bus for bus, cap in enumerate(capacities, start=1) if cap >= combined_size), key=lambda x: capacities[x-1])
            # Check if the bus can fit the group and all its neighbors
            if capacities[min_capacity_bus - 1] < combined_size:
                continue
            # Allocate the group and its neighbors to the bus
            allocated_buses[min_capacity_bus].append((group, group_size))
            assigned_groups.add(group)
            for neighbor in all_neighbors:
                allocated_buses[min_capacity_bus].append((neighbor, sizes[groups.index(neighbor)]))
                assigned_groups.add(neighbor)
            # Deduct the capacities of the bus
            capacities[min_capacity_bus - 1] -= combined_size
        except ValueError:
            # If ValueError is raised, there is no bus with sufficient capacity for the current group
            # Continue to the next iteration
            pass
    return allocated_buses, assigned_groups, capacities

def main_function():
    # Read data from CSV file
    with open('deshu_count.csv', 'r', encoding='utf-8-sig') as file:
        reader = csv.reader(file)
        groups = next(reader)
        sizes = next(reader)
    # Convert sizes to integers
    sizes = list(map(int, sizes))
    # Define bus capacities
    with open('capacities.csv', 'r', encoding='utf-8-sig') as file:
        reader = csv.reader(file)
        bus_names = next(reader)
        bus_capacities = next(reader)
    # Convert sizes to integers
    bus_capacities = list(map(int, bus_capacities))
    # Create a graph to represent group pairings
    group_graph = nx.Graph()
    # Add nodes to the graph
    group_graph.add_nodes_from(groups)
    # Add edges to the graph
    group_graph.add_edges_from([('明','宽'), ('忠','恕'), ('信','忍'), ('博(三)','博(义)'), ('正','义'), ('节','俭')])
    allocations, assigned_groups, remaining_capacities = allocate_to_buses(groups, sizes, list(bus_capacities), group_graph)
    return allocations, assigned_groups, remaining_capacities, bus_names, groups

def print_results(allocations, assigned_groups, remaining_capacities, bus_names, groups):
    # Print the results
    for bus, allocated_groups in allocations.items():
        if allocated_groups:
            name = bus_names[bus-1]
            print(f"{name} - Allocated groups: {allocated_groups}")
        else:
            print(f"{name} - No groups allocated")
    # Calculate unassigned groups
    unassigned_groups = set(groups) - assigned_groups
    print(f"Unassigned groups: {list(unassigned_groups)}")
    # Print remaining capacities
    print(f"Remaining Capacities: {remaining_capacities}")

def streamlit_main(groups, sizes, bus_names, bus_capacities, bus_edges):
    # Convert sizes to integers
    sizes = list(map(int, sizes))
    bus_capacities = list(map(int, bus_capacities))
    # Create a graph to represent group pairings
    group_graph = nx.Graph()
    # Add nodes to the graph
    group_graph.add_nodes_from(groups)
    # Add edges to the graph
    if bus_edges != []:
        group_graph.add_edges_from(bus_edges)
    allocations, assigned_groups, remaining_capacities = allocate_to_buses(groups, sizes, list(bus_capacities), group_graph)
    return allocations, assigned_groups, remaining_capacities, bus_names, groups

if __name__ == "__main__":
    allocations, assigned_groups, remaining_capacities, bus_names, groups = main_function()
    print_results(allocations, assigned_groups, remaining_capacities, bus_names, groups)

