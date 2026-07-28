import numpy as np

try:
    from tespy.components import Compressor
    from tespy.components import CycleCloser
    from tespy.components import SimpleHeatExchanger
    from tespy.components import Valve
    from tespy.connections import Connection
    from tespy.networks import Network
except (ImportError, ModuleNotFoundError):
    Network = None


def calculate_cop_simple(
    temperature_source, temperature_supply, quality_factor
):
    """

    Parameters
    ----------
    temperature_source : float or array-like
    temperature_supply : float or array-like
    quality_factor : float or array-like

    Returns
    -------
    float or array-like

    Examples
    --------
    >>> round(calculate_cop_simple(10.0, 55.0, 0.5), 2)
    3.65

    """
    temperature_source = np.array(temperature_source)
    temperature_supply = np.array(temperature_supply)
    quality_factor = np.array(quality_factor)

    cop = (
        (temperature_supply + 273.15)
        * quality_factor
        / (temperature_supply - temperature_source)
    )
    if isinstance(cop, np.float64):
        return cop.item()

    return cop


def calculate_cop_tespy(
    temperature_source,
    temperature_supply,
    refrigerant="R290",
    capacity=1000,
    pressure_loss_factor_hex=1,
    eta_s=0.55,
):
    """
    Temperature input must have the same length.

    Parameters
    ----------
    temperature_source
    temperature_supply
    capacity
    refrigerant
    pressure_loss_factor_hex
    eta_s

    Returns
    -------

    Examples
    --------
    >>> c = calculate_cop_simple(10.0, [35, 45, 55], 0.5)
    >>> [round(float(val), 2) for val in c]
    [6.16, 4.54, 3.65]
    >>> c = calculate_cop_tespy([10.0] * 3, [35, 45, 55])
    >>> [round(float(val), 2) for val in c]
    [6.33, 4.54, 3.52]
    >>> c = calculate_cop_tespy([10.0] * 3, [35, 45, 55], refrigerant="R134a")
    >>> [round(float(val), 2) for val in c]
    [6.42, 4.62, 3.59]
    >>> round(calculate_cop_simple(10, 40, 0.5), 2)
    5.22
    >>> round(calculate_cop_tespy(10, 40), 2)
    5.29
    """

    if Network is None:
        msg = (
            "TESPy is required to use this function.\n"
            "Please install the tespy package: 'pip install tespy'"
        )
        raise ModuleNotFoundError(msg)

    if isinstance(temperature_source, (float | int)):
        temperature_source = [temperature_source]
        temperature_supply = [temperature_supply]
        length = 1
    else:
        length = len(temperature_source)

    temperature_source = np.array(temperature_source)
    temperature_supply = np.array(temperature_supply)

    # create a network object with R134a as fluid
    my_plant = Network()

    # set the unitsystem for temperatures to °C and for pressure to bar
    my_plant.units.set_defaults(
        temperature="degC",
        pressure="bar",
        pressure_difference="bar",
        enthalpy="kJ/kg",
        heat="kW",
        power="kW",
    )

    cc = CycleCloser("cycle closer")

    # heat sink
    co = SimpleHeatExchanger("condenser")
    # heat source
    ev = SimpleHeatExchanger("evaporator")

    va = Valve("expansion valve")
    cp = Compressor("compressor")

    # connections of heat pump
    c1 = Connection(cc, "out1", ev, "in1", label="1")
    c2 = Connection(ev, "out1", cp, "in1", label="2")
    c3 = Connection(cp, "out1", co, "in1", label="3")
    c4 = Connection(co, "out1", va, "in1", label="4")
    c0 = Connection(va, "out1", cc, "in1", label="0")

    # this line is crutial: you have to add all connections to your network
    my_plant.add_conns(c1, c2, c3, c4, c0)

    co.set_attr(pr=pressure_loss_factor_hex, Q=capacity * -1)
    ev.set_attr(pr=pressure_loss_factor_hex)
    cp.set_attr(eta_s=eta_s)

    def get_cop(c_src, c_sup, n):
        c_src.set_attr(T=temperature_source[n], x=1, fluid={refrigerant: 1})
        c_sup.set_attr(T=temperature_supply[n], x=0)

        my_plant.solve("design", print_results=False)
        return abs(co.Q.val) / cp.P.val

    cops = [get_cop(c2, c4, n) for n in range(length)]

    if len(cops) == 1:
        cops = float(cops[0])
    return cops
