__author__ = 'paul'


def and_(*functions):
    def and_f(exp):
        ret = True
        for f in functions:
            ret = ret and f(exp)
        return ret

    return and_f


def or_(*functions):
    def or_f(exp):
        ret = False
        for f in functions:
            ret = ret or f(exp)
        return ret

    return or_f


def not_(function):
    def not_f(exp):
        return not function(exp)
    return not_f
