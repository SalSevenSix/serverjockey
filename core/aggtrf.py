

def is_aggregator(candidate):
    return candidate is not None \
        and hasattr(candidate, 'aggregate') \
        and callable(candidate.aggregate)


class Noop:

    def aggregate(self, iterable):
        return iterable


class StrJoin:

    def __init__(self, delim=''):
        self.delim = delim

    def aggregate(self, iterable):
        return self.delim.join(iterable)
