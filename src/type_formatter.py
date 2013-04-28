#coding: utf-8

"""
Formatter and scanner of method signature
"""

__author__ = 'Toshihiro Kamiya <kamiya@mbj.nifty.com>'
__status__ = 'experimental'

_value_type_table = { 'boolean': 'Z', 'byte': 'B', 'char': 'C',
        'short': 'S', 'int': 'I', 'long': 'J', 'float': 'F', 'double': 'D',
        'void': 'V' }

def format_type(typ):
    """
    Format type with Javap's comment style.
    
    >>> format_type('org.mydomain.myapp.SomeData[]')
    '[Lorg/mydomain/myapp/SomeData;'
    >>> format_type('int')
    'I'
    """

    assert typ # is not None and != ''

    s = typ.replace('.', '/')
    p = s.find('<')
    if p >= 0:
        s = s[:p]

    array_dim = 0
    while s.endswith("[]"):
        array_dim += 1
        s = s[:-2]

    t = _value_type_table.get(s)
    if t:
        s = t
    else:
        s = "L%s;" % s

    return "[" * array_dim + s

def format_sig(name, args, retv):
    """
    Format method signature with Javap's method definition style.
    Arguments are: name of method, list of argument types, and type of return value.
    
    >>> format_sig('getSomeValue', ['int', 'java.lang.String'], 'org.mydomain.myapp.SomeData[]')
    'org.mydomain.myapp.SomeData[] getSomeValue(int, java.lang.String)'
    """

    return '%s %s(%s)' % (retv, name, ', '.join(args))

def format_sig_in_javap_comment_style(claz, name, args, retv):
    """
    Format method signature with Javap's comment style.
    
    >>> format_sig_in_javap_comment_style('org.mydomain.myapp.App', \
            'getSomeValue', ['int', 'java.lang.String'], 'org.mydomain.myapp.SomeData[]')
    'org/mydomain/myapp/App.getSomeValue:(ILjava/lang/String;)[Lorg/mydomain/myapp/SomeData;'
    """

    if claz is not None:
        return '%s.%s:(%s)%s' % (claz.replace('.', '/'), name, 
                ''.join(map(format_type, args)), format_type(retv))
    else:
        return '%s:(%s)%s' % (name, 
                ''.join(map(format_type, args)), format_type(retv))

def scan_in_javap_comment_style(s):
    """
    Scan method signature from Javap's comment.
    
    >>> scan_in_javap_comment_style('org/myapp/AClass$AInnerClass.aMethod:([Lorg/myapp/Data;I)V')
    ('org/myapp/AClass$AInnerClass', 'aMethod:([Lorg/myapp/Data;I)V')
    """

    p = s.find(":(")
    assert p >= 0

    claz_method, args = s[:p], s[p:]
    q = claz_method.rfind('.')
    assert q >= 0

    claz = claz_method[:q]
    method = claz_method[q+1:]

    return claz, method + args

