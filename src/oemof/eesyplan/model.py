import logging

from oemof.solph import EnergySystem as SolphES
from oemof.solph import Model
from oemof.solph import Results as SolphResults
from oemof.solph import create_time_index


class EnergySystem(SolphES):
    def __init__(
        self,
        year=None,
        interval=1,
        number=None,
        start=None,
        **kwargs,
    ):
        """
        Create an energy system with a datetime index for one year.

        It is also possible to specifiy different periods. See the paramter
        description below.

        Notes
        -----
        To create 8760 hourly intervals for a non leap year a datetime index
        with 8761 time points need to be created. So the number of time steps
        is always the number of intervals plus one.

        Parameters
        ----------
        year : int, datetime
            The year of the index.
            Used to automatically set start and number for the specific year.
        interval : float
            The time interval in hours e.g. 0.5 for 30min or 2 for a two hour
            interval (default: 1).
        number : int
            The number of time intervals. By default number is calculated to
            create an index of one year. For a shorter or longer period the
            number of intervals can be set by the user.
        start : datetime.datetime or datetime.date
            Optional start time. If start is not set, 00:00 of the first day of
            the given year is the start time.

        Examples
        --------
        >>> len(EnergySystem(2014).timeindex)
        8761
        >>> len(EnergySystem(2012).timeindex)  # leap year
        8785
        >>> len(EnergySystem(2014, interval=0.5).timeindex)
        17521
        >>> len(EnergySystem(2014, interval=0.5, number=10).timeindex)
        11
        >>> len(EnergySystem(2014, number=10).timeindex)
        11
        >>> str(EnergySystem(2014, interval=0.5, number=10).timeindex[-1])
        '2014-01-01 05:00:00'
        >>> es = EnergySystem(2014, interval=2, number=10)
        >>> str(es.timeindex[-1])
        '2014-01-01 20:00:00'
        >>> str(EnergySystem(timeindex=es.timeindex).timeindex[-1])
        '2014-01-01 20:00:00'
        """
        if kwargs.get("timeindex", None) is None:
            timeindex = create_time_index(
                year=year, interval=interval, number=number, start=start
            )
        else:
            timeindex = kwargs.get("timeindex")

        super().__init__(
            timeindex=timeindex,
            infer_last_interval=False,
            periods=kwargs.get("periods"),
        )


class Results(SolphResults):
    def __init__(self, model):
        super().__init__(model)


def optimise(energy_system, solver="cbc", debug=False):
    """Optimise the energy system."""
    logging.info("Create model")
    optimization_model = Model(energysystem=energy_system)

    # solve problem
    logging.info("Solve model")

    if debug:
        skwargs = {"tee": True, "keepfiles": False}
    else:
        skwargs = {}
    optimization_model.solve(solver=solver, solve_kwargs=skwargs)
    return Results(optimization_model)
