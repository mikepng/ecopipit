import pandas as pd
from ortools.linear_solver import pywraplp

# Data
df = pd.read_excel('./4bed.xlsx')

# Compute total area:
total_area = df.loc[df['Units']=='sqm', 'Quantity'].sum()

# Params
target_price_per_sqm = 25  # £ per sqm
budget = target_price_per_sqm * total_area

#  solver
solver = pywraplp.Solver.CreateSolver('SCIP')
x = {}
for i, row in df.iterrows():
    if pd.notna(row['Eco Rate']):
        x[i] = solver.IntVar(0, 1, f"x_{i}")

# Maximize total carbon offset
obj = solver.Objective()
for i, row in df.iterrows():
    if i in x:
        obj.SetCoefficient(x[i], row['Carbon Offset'])
obj.SetMaximization()


# Constraints
budget_expr = solver.Sum(
    row['Eco Rate'] * x[i] + row['Non Eco Rate'] * (1 - x[i])
    for i, row in df.iterrows() if i in x
)

solver.Add(budget_expr <= budget)

# Solver
status = solver.Solve()
if status == pywraplp.Solver.OPTIMAL:
    # optimal carbon offset
    opt_offset = obj.Value()
    # compute actual total cost under solution
    total_cost = sum(
        row['Eco Rate'] * x[i].solution_value() +
        row['Non Eco Rate'] * (1 - x[i].solution_value())
        for i, row in df.iterrows() if i in x
    )

    # achieved rate per sqm
    new_rate_per_sqm = total_cost / total_area

    baseline_cost = sum(
        row['Non Eco Rate'] * (row['Quantity'] if row['Units']=='sqm' else 1)
        for _, row in df.iterrows() if pd.notna(row.get('Eco Rate'))
    )

    # New optimized cost
    optimized_cost = sum(
        row['Eco Rate'] * x[i].solution_value() * (row['Quantity'] if row['Units']=='sqm' else 1)
        + row['Non Eco Rate'] * (1 - x[i].solution_value()) * (row['Quantity'] if row['Units']=='sqm' else 1)
        for i, row in df.iterrows() if i in x
    )

    # Print results
    print(f"Previous (all non-eco) total cost: £{baseline_cost:,.2f}")
    print(f"New optimized total cost:      £{optimized_cost:,.2f}")

    print(f"Optimal carbon offset: {opt_offset}kg")
    print(f"Achieved build rate: £{new_rate_per_sqm:.2f} per sqm")

    # list which items went eco
    chosen = df.loc[[i for i in x if x[i].solution_value() > 0.5]]
    print("\nSelected eco-options:")
    print(chosen[['Element','Eco Rate','Carbon Offset']])
    
else:
    print("No optimal solution found.")



