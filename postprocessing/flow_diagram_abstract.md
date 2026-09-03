# Cost Propagation — How Energy Costs Are Traced

Every energy flow in the system receives a cost. These costs are built from
**fixed** and **variable** components and propagate forward through the network
from sources to demand.

---

## Cost Components

| Type | What it includes | Example |
|------|-----------------|---------|
| **Fixed cost** | Investment, maintenance — constant over the year | Solar panel amortization |
| **Variable cost** | Fuel, dispatch — changes with how much energy flows | Gas price per kWh |

---

## How Costs Propagate

An outgoing flow's cost = **its own component cost** + **a share of all incoming flow costs**.

This means the cost at the final demand (LCOE / LCOH) includes everything upstream:
fuel, investment, conversion losses, storage — all traced back to their origin.

---

## Energy & Cost Flow

The diagram below shows how energy (and its attached costs) move through the
system. Width = energy volume. Colors = different energy carriers.

```mermaid
sankey-beta

Gas Source,Gas Bus,100,#e74c3c
Gas Bus,Gas Power Plant,100,#e74c3c
Gas Power Plant,Electricity Bus,30,#e74c3c
Gas Power Plant,Heat Bus,50,#e74c3c

Wind Source,Electricity Bus,40,#3498db
PV Source,Electricity Bus,25,#f1c40f

Electricity Bus,Electricity Demand,60,#2ecc71
Electricity Bus,Battery Storage,15,#2ecc71
Battery Storage,Electricity Bus,15,#2ecc71
Electricity Bus,Grid Export,5,#2ecc71
Electricity Bus,Electrolyzer,15,#2ecc71
Electrolyzer,Hydrogen Bus,15,#9b59b6

Heat Bus,Heat Demand,40,#e67e22
Heat Bus,Heat Storage,10,#e67e22
Heat Storage,Heat Bus,10,#e67e22
Heat Bus,Excess,0,#e67e22
```

---

## Key Idea

> **Gas Source → Gas Bus → Power Plant → Electricity Bus → Demand**
>
> The demand's cost is not just the power plant's cost. It includes:
> the gas price, the plant's investment, the conversion efficiency,
> and every other upstream component's fixed and variable costs —
> all proportionally weighted by actual energy usage.
