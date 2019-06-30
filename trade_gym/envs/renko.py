from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


'''NOTE: I DID NOT WRITE ANY OF THIS LOL - HUGH '''

from .metabase import MetaParams

def with_metaclass(meta, *bases):
    """Create a base class with a metaclass."""
    # This requires a bit of explanation: the basic idea is to make a dummy
    # metaclass for one level of class instantiation that replaces itself with
    # the actual metaclass.
    class metaclass(meta):

        def __new__(cls, name, this_bases, d):
            return meta(name, bases, d)
    return type.__new__(metaclass, str('temporary_class'), (), {})
    

class MetaFilter(MetaParams):
    pass

__all__ = ['Renko']


class Filter(with_metaclass(MetaParams, object)):

    _firsttime = True

    def __init__(self, data):
        pass

    def __call__(self, data):
        if self._firsttime:
            self.nextstart(data)
            self._firsttime = False

        self.next(data)

    def nextstart(self, data):
        pass

    def next(self, data):
        pass


class Renko(Filter):
    '''Modify the data stream to draw Renko bars (or bricks)
    Params:
      - ``hilo`` (default: *False*) Use high and low instead of close to decide
        if a new brick is needed
      - ``size`` (default: *None*) The size to consider for each brick
      - ``autosize`` (default: *20.0*) If *size* is *None*, this will be used
        to autocalculate the size of the bricks (simply dividing the current
        price by the given value)
      - ``dynamic`` (default: *False*) If *True* and using *autosize*, the size
        of the bricks will be recalculated when moving to a new brick. This
        will of course eliminate the perfect alignment of Renko bricks.
      - ``align`` (default: *1.0*) Factor use to align the price boundaries of
        the bricks. If the price is for example *3563.25* and *align* is
        *10.0*, the resulting aligned price will be *3560*. The calculation:
          - 3563.25 / 10.0 = 356.325
          - round it and remove the decimals -> 356
          - 356 * 10.0 -> 3560
    See:
      - http://stockcharts.com/school/doku.php?id=chart_school:chart_analysis:renko
    '''

    params = (
        ('hilo', False),
        ('size', None),
        ('autosize', 20.0),
        ('dynamic', False),
        ('align', 1.0),
    )

    def nextstart(self, data):
        o = data.open[0]
        o = round(o / self.p.align, 0) * self.p.align  # aligned
        self._size = self.p.size or float(o // self.p.autosize)
        self._top = int(o) + self._size
        self._bot = int(o) - self._size

    def next(self, data):
        c = data.close[0]
        h = data.high[0]
        l = data.low[0]

        if self.p.hilo:
            hiprice = h
            loprice = l
        else:
            hiprice = loprice = c

        if hiprice >= self._top:
            # deliver a renko brick from top -> top + size
            self._bot = bot = self._top

            if self.p.size is None and self.p.dynamic:
                self._size = float(c // self.p.autosize)
                top = bot + self._size
                top = round(top / self.p.align, 0) * self.p.align  # aligned
            else:
                top = bot + self._size

            self._top = top

            data.open[0] = bot
            data.low[0] = bot
            data.high[0] = top
            data.close[0] = top
            data.volume[0] = 0.0
            data.openinterest[0] = 0.0
            return False  # length of data stream is unaltered

        elif loprice <= self._bot:
            # deliver a renko brick from bot -> bot - size
            self._top = top = self._bot

            if self.p.size is None and self.p.dynamic:
                self._size = float(c // self.p.autosize)
                bot = top - self._size
                bot = round(bot / self.p.align, 0) * self.p.align  # aligned
            else:
                bot = top - self._size

            self._bot = bot

            data.open[0] = top
            data.low[0] = top
            data.high[0] = bot
            data.close[0] = bot
            data.volume[0] = 0.0
            data.openinterest[0] = 0.0
            return False  # length of data stream is unaltered

        data.backwards()
        return True  # length of stream was changed, get new bar