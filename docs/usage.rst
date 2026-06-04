=====
Usage
=====

1. Python Script
2. Datapackage

Python Script
=============

Getting started with eesyplan.

Initialisation
--------------

First, a project and an energy system object must be created. The project
serves to define global parameters. These are the project name and economic
parameters in case of an investment optimisation.

The energy system is the container for the system graph. It contains the
time index of the model. In case of an hourly resolved optimisation over a
year, only the year needs to be specified. Further details on deviating
time systems can be found in the class description
:py:class:`~.model.EnergySystem`

.. code-block:: python

    from oemof.eesyplan import Project, EnergySystem
    project = Project(name="test", lifetime=20, tax=0, discount_factor=0)
    energy_system = EnergySystem(2023)

Now the components of the energy system can be defined. Buses can be used
to connect components. An overview of all components can be found at
:ref:`eesyplan-reference-label`.


.. code-block:: python

    from oemof.eesyplan import DsoElectricity, PvPlant, Demand

    bus_elec = CarrierBus(name="electricity")
    energy_system.add(bus_elec)

    # Electricity Provider
    dso = DsoElectricity(
            name="dso",
            bus_electricity=bus_elec,
            energy_price=0.1,
            feedin_tariff=0.04,
        )
    energy_system.add(dso)

    # PV Plant
    pv = PvPlant(
            name="pv",
            bus_out_electricity=bus_elec,
            project_data=project,
            installed_capacity=5.0,
            input_timeseries=normalised_timeseries,
            optimize_cap=False,
        )
    )
    energy_system.add(pv)

    # Electricity demand
    elec_demand = Demand(
            name="demand_electricity",
            bus_in_electricity=bus_elec,
            input_timeseries=data["demand_elec"],
        )
    )
    energy_system.add(elec_demand)



Afterwards, the energy system can be optimised.

.. code-block:: python

    results = optimise(energy_system)

An advanced result handling will be part of eesyplan. Until this is
available, the results have to be processed using the oemof-solph API. Go to
the
`oemof-solph documentation <https://oemof-solph.readthedocs.io/en/stable/reference/oemof.solph.results.html#oemof.solph._results.Results>`__
for further information


Datapackage
===========

It is possible to setup an eesyPlan model and solve it from a datapackage. One can do it via the terminal or via a python script. For example of datapackage please refer to our examples in `examples/simple_datapackage`

To use the terminal interface you need to have oemof-eesyplan installed in your local virtual environment, then in a terminal where the environment is activated you can type

.. code-block:: basic

    solve_dp -f <path to a datapackage folder>

To enquiry about the possible options simply use the `-h` option

.. code-block:: basic

    solve_dp -h

If you prefer to use a python script

.. code-block:: python

    from pathlib import Path
    from oemof.eesyplan.datapackage.energy_system import create_energy_system_from_dp

    path = Path("path/to/your/datapackage")
    energy_system = create_energy_system_from_dp(path)

    results = optimise(energy_system)
