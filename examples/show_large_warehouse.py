#!/usr/bin/env python3
"""
Large Warehouse Statistics and Summary
"""

from physical_layout import load_physical_warehouse
import networkx as nx

print("="*70)
print("LARGE WAREHOUSE CONFIGURATION")
print("="*70)

graph, warehouse = load_physical_warehouse('warehouse_large.json')

# Count different types
racks = [obj for obj in warehouse.objects if obj.type == 'rack']
aisles = [obj for obj in warehouse.objects if obj.type == 'aisle']
docks = [obj for obj in warehouse.objects if obj.type == 'dock']
staging = [obj for obj in warehouse.objects if obj.type == 'staging']
charging = [obj for obj in warehouse.objects if obj.type == 'charging']
packing = [obj for obj in warehouse.objects if obj.type == 'packing']
offices = [obj for obj in warehouse.objects if obj.type == 'office']

# Count nodes by type
pick_points = [n for n in graph.nodes if '-' in n and any(c in n for c in 'ABCDEFGH')]
aisle_waypoints = [n for n in graph.nodes if 'Aisle_' in n or 'Cross_' in n]
corner_waypoints = [n for n in graph.nodes if '_N' in n or '_S' in n]

print("\nWarehouse Composition:")
print(f"  Docks:            {len(docks)} (Receiving: 2, Shipping: 2)")
print(f"  Staging Areas:    {len(staging)}")
print(f"  Charging Stations: {len(charging)}")
print(f"  Packing Stations: {len(packing)}")
print(f"  Offices:          {len(offices)}")
print(f"  Racks:            {len(racks)}")
print(f"  Aisles:           {len(aisles)} (4 cross-aisles, 8 main aisles)")

print("\nGraph Statistics:")
print(f"  Total nodes:      {graph.number_of_nodes()}")
print(f"  Pick points:      {len(pick_points)}")
print(f"  Aisle waypoints:  {len(aisle_waypoints)}")
print(f"  Corner waypoints: {len(corner_waypoints)}")
print(f"  Total edges:      {graph.number_of_edges()}")

components = list(nx.connected_components(graph))
print(f"  Connected:        {'Yes' if len(components) == 1 else f'No ({len(components)} components)'}")

print("\nRack Configuration:")
vertical_racks = [r for r in racks if r.depth > r.width]
horizontal_racks = [r for r in racks if r.width > r.depth]

print(f"  Vertical racks:   {len(vertical_racks)}")
print(f"  Horizontal racks: {len(horizontal_racks)}")

print("\nDetailed Rack List:")
for rack in sorted(racks, key=lambda r: r.id):
    # Count picks for this rack
    rack_prefix = rack.id.split('_')[1].split('1')[0].split('2')[0]
    picks = [n for n in pick_points if n.startswith(rack_prefix) and rack.id.split('_')[1][0] in n]
    
    if rack.width > rack.depth:
        orientation = "Horizontal"
        dim_str = f"{rack.width}×{rack.depth}"
    else:
        orientation = "Vertical  "
        dim_str = f"{rack.width}×{rack.depth}"
    
    print(f"  {rack.id:20s} {orientation}  {dim_str:8s}  @ ({rack.center_x:3.0f}, {rack.center_y:3.0f})  {len(picks):3d} picks")

print("\nWarehouse Dimensions:")
all_x = [obj.center_x for obj in warehouse.objects]
all_y = [obj.center_y for obj in warehouse.objects]
print(f"  Width:  {min(all_x):.0f} to {max(all_x):.0f} units ({max(all_x) - min(all_x):.0f} total)")
print(f"  Depth:  {min(all_y):.0f} to {max(all_y):.0f} units ({max(all_y) - min(all_y):.0f} total)")

print("\nPick Point Distribution:")
rack_picks = {}
for rack in racks:
    rack_name = rack.id.split('_')[1]
    rack_prefix = rack_name[0]
    picks = [n for n in pick_points if n.startswith(rack_prefix) and rack_name[0] in n]
    if rack_prefix not in rack_picks:
        rack_picks[rack_prefix] = 0
    rack_picks[rack_prefix] += len([p for p in picks if rack_name in p or p[0] == rack_prefix])

print(f"  Total pick points: {len(pick_points)}")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"""
This warehouse contains:
  • {len(racks)} racks ({len(vertical_racks)} vertical, {len(horizontal_racks)} horizontal)
  • {len(pick_points)} pick points
  • {len(aisles)} aisles for navigation
  • {graph.number_of_edges()} graph edges
  
Layout:
  • 8 main aisles running north-south
  • 4 cross-aisles running east-west
  • Vertical racks between main aisles (60 units deep)
  • 1 horizontal rack in the center (40 units wide)
  • 2 staging areas (west and east)
  • 2 charging stations (southwest and southeast)
  • 4 packing stations
  • 4 shipping/receiving docks
""")
print("="*70)
