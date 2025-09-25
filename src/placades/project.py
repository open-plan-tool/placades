class ProjectData:
    def __init__(self, name, lifetime, tax, discount_factor):
        self.name = name
        self.tax = tax
        self.lifetime = lifetime
        self.discount_factor = discount_factor

    def calculate_epc(self, method="mvs"):
        if method == "mvs":
            return calculate_annuity_mvs()
        elif method == "oemof":
            return oemof.tools.annuity()
