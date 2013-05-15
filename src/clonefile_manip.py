#coding: utf-8

"""
agec's clone data file manipulation.
"""

__author__ = 'Toshihiro Kamiya <kamiya@mbj.nifty.com>'
__status__ = 'experimental'

import re
import sys

class CloneFileSyntaxError(ValueError):
    pass

# the command-line options that are specified in n-gram generation
CMDLINE_OPTIONS = (
    ("ngram-size", int, lambda: -1),
    ("max-branch", int, lambda: -1),
    ("max-call-depth", int, lambda: -1),
    ("max-method-definition", int, lambda: -1),
    ("exclude", [str], list),
    ("include-ctors", None, lambda: None)
)

class OptionHolder:
    pat_option = re.compile(r'\s*#\s+--([-\w]+)(=.+)$')
    pat_option_wo_param = re.compile(r'\s*#\s+--([-\w]+)$')

    def __eq__(self, other):
        if not isinstance(other, OptionHolder):
            return False
        return self.format() == other.format()

    def __init__(self, option_descs):
        self.option_descs = option_descs
        for rn, _, default_value_gen in self.option_descs:
            n = rn.replace('-', '_')
            setattr(self, n, default_value_gen())
        self.holded_options = [rn for rn, _, _ in self.option_descs]

    def update(self, name, value):
        for rn, typ, _ in self.option_descs:
            if name == rn:
                n = rn.replace('-', '_')
                if typ is None:
                    setattr(self, n, value)
                elif isinstance(typ, list):
                    if not hasattr(self, n):
                        setattr(self, n, [])
                    getattr(self, n).append(typ[0](value))
                else:
                    setattr(self, n, typ(value))
                return
        raise ValueError

    def get(self, name):
        n = name.replace('-', '_')
        return getattr(self, n)
    
    def option_iter(self):
        for rn in self.holded_options:
            n = rn.replace('-', '_')
            yield rn, getattr(self, n)
    
    def delete(self, name):
        deleted_index = None
        for i, rn in enumerate(self.holded_options):
            if name == rn:
                deleted_index = i
                break  # for rn
        if deleted_index is not None:
            self.holded_options = [v for i, v in enumerate(self.holded_options) if i != deleted_index]
    
    def scan_update(self, L):
        m = OptionHolder.pat_option.match(L)
        if m:
            name = m.group(1)
            arg = m.group(2)[1:]
            try:
                self.update(name, arg)
            except ValueError:
                raise CloneFileSyntaxError("unrecognized option")
        else:
            m = OptionHolder.pat_option_wo_param.match(L)
            if m:
                name = m.group(1)
                try:
                    self.update(name, True)
                except ValueError:
                    raise CloneFileSyntaxError("unrecognized option")
    
    def format(self):
        buf = []
        for rn in self.holded_options:
            n = rn.replace('-', '_')
            value = getattr(self, n)
            typ = None
            for r, t, _ in self.option_descs:
                if r == rn:
                    typ = t
                    break  # for r
            else:
                assert False, "option value not found in description"
            
            if isinstance(typ, list):
                for item in value:
                    self._format_i(buf, typ[0], rn, item)
            else:
                self._format_i(buf, typ, rn, value)
        return buf
    
    def _format_i(self, buf, typ, rn, value):
        if typ is int:
            buf.append(u"# --%s=%d" % (rn, value))
        elif typ is str:
            buf.append(u"# --%s=%s" % (rn, value))
        elif typ is None:
            if value:
                buf.append(u"# --%s" % rn)
        else:
            assert False, "invalid type of option"

OPTIONS = 1
OPESEQ_SINGLE = 2  # ope section, w/o following loc section or trace section
OPESEQ_LOCS = 3
OPESEQ_TRACES = 4
METRIC_VALUES = 5

def read_clone_iter(line_it):
    args = OptionHolder(CMDLINE_OPTIONS)

    metric_values = []
    opeseq = []
    locs, traces = [], []
    cursec = []
    for li, L in enumerate(line_it):
        if not L:
            continue  # for li, L
        elif L.startswith('#'):
            try:
                args.scan_update(L)
            except CloneFileSyntaxError as e:
                raise CloneFileSyntaxError("%d: %s: %s" % (li + 1, str(e), L))
        else:
            if args is not None:
                yield OPTIONS, args
                args = None
            if L == 'ope:':
                if locs:
                    yield OPESEQ_LOCS, (opeseq, locs)
                elif traces:
                    yield OPESEQ_TRACES, (opeseq, traces)
                else:
                    if opeseq:
                        yield OPESEQ_SINGLE, (opeseq, None)
                opeseq = []
                locs, traces = [], []
                curseq = opeseq

                if metric_values:
                    yield METRIC_VALUES, metric_values
                metric_values = []
            elif L.startswith('metric-'):
                p = L.find('=')
                if p < 0:
                    raise CloneFileSyntaxError("%d: invalid metric-value format: %s" % (li + 1, L))
                m, s = L[:p], L[p+1:].strip()
                v = int(s)
                metric_values.append((m, v))
                curseq = []  # dummy
            elif L == 'loc:':
                if not opeseq:
                    raise CloneFileSyntaxError("%d: missing ope section" % (li + 1))
                if traces:
                    raise CloneFileSyntaxError("%d: unexpected loc section appears after trace section" % (li + 1))
                curseq = locs
            elif L == 'trace:':
                if not opeseq:
                    raise CloneFileSyntaxError("%d: missing ope section" % (li + 1))
                if locs:
                    raise CloneFileSyntaxError("%d: unexpected trace section appears after loc section" % (li + 1))
                traces.append([])
                curseq = traces[-1]
            else:
                if not L.startswith("  "):
                    raise CloneFileSyntaxError("%d: invalid format: %s" % (li + 1, L))
                curseq.append(L[2:])

    if args is not None:
        yield OPTIONS, args
        args = None
    elif locs:
        yield OPESEQ_LOCS, (opeseq, locs)
    elif traces:
        yield OPESEQ_TRACES, (opeseq, traces)
    else:
        yield OPESEQ_SINGLE, (opeseq, None)
    opeseq = []
    locs, traces = [], []

    if metric_values:
        yield METRIC_VALUES, metric_values
    metric_values = []

def read_clone_file_iter(clonefile):
    """
    Read a clone data file and iterate over the contents.
    Yeilded values
      tag: one of OPTIONS, OPESEQ_SINGLE, OPESEQ_LOCS, OPESEQ_TRACES, and METRIC_VALUES
      value: an OptionHoder object when tag == OPTONS
             a taple (opeseq, None) when tag == OPESEQ_SINGLE
             a taple (opeseq, locs) when tag == OPESEQ_LOCS
             a tuple (opeseq, traces) when tag == OPESEQ_TRACES
             a list of a tuple (metricname, metircvalue) when tag == METRIC_VALUES
    """
    
    if clonefile != '-':
        def it():
            with open(clonefile, "rb") as f:
                for L in f:
                    yield L.decode('utf-8').rstrip()
    else:
        def it():
            for L in sys.stdin:
                yield L.decode('utf-8').rstrip()
    for tag, value in read_clone_iter(it()):
        yield tag, value

#def format_ope_tag():
#    return ['ope:']
#
#def format_opeseq(opeseq):
#    buf = []
#    buf.append('ope:')
#    buf.extend('  %s' % ope for ope in opeseq)
#    return buf
#
#def format_loc_tag():
#    return ['loc:']
#
#def format_trace_tag():
#    return ['trace:']
#
#def format_index(loc, depth):
#    return ['  %s >%d\n' % (loc, depth)]
#
#def format_linenum(source_file, linenum, depth, reference):
#    return ['  %s: %d >%d // %s' % (source_file, linenum, depth, reference)]
#
#def format_metric_value(name, value):
#    return ['%s= %s' % (name, value)]
