# An ability, as it's named, is defined to describe the
# data fetching ability of an Agent Class.
# An ability instance should not store any data relying on other
# classes (e.g. agent). It should be very independant implementing
# several utility functions for the caller to use.
class AbilityImplementationError(Exception):
    pass

class Ability:
    def __init__(self):
        pass

    def __eq__(a, b):
        return repr(a) == repr(b)

    def __repr__(self):
        raise AbilityImplementationError

    # b in a?
    # with this operator function, a demander asking
    # for ability "b" can use the service of a supplier
    # providing the ability "a"
    def __contains__(a, b):
        raise AbilityImplementationError

    # calls the public interfaces of the supplier and test its ability,
    # returns True when successful
    def validate_supplier(self, supplier):
        raise AbilityImplementationError

class AbilityPool:
    def __init__(self):
        pass

    # register a supplier to have an ability
    def register(self, ability, supplier):
        pass

    # acquire a supplier that owns some ability
    def acquire(self, ability):
        pass

ability_pool = AbilityPool()

class ListAbility:
    def __init__(self, market=('CNSH', 'CNSZ'), target_type=("stock")):
        self.market = market
        self.target_type = target_type

    def __eq__(a, b):
        return set(a.market) == set(b.market) and set(a.target_type) == set(b.target_type)

    def __repr__(self):
        pass

    def validate_supplier(self, supplier):
        data = supplier.list()
        assert type(data) is list
        assert len(data) > 10
        assert 'name' in data[0] and 'code' in data[0]
        return True

