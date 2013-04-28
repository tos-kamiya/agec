#coding: utf-8

"""
Parser of disassembled method defintion
to extract a list of operation from it.
"""

__author__ = 'Toshihiro Kamiya <kamiya@mbj.nifty.com>'
__status__ = 'experimental'

import re

class OpeError(ValueError):
    pass

class InvalidOpe(OpeError):
    pass

def verify_branch_ope(ope_list):
    jump_ops = frozenset([
            "ifeq", "ifnull", "iflt", "ifle", "ifne", "ifnonull", "ifgt", "ifge",
            "if_icmpeq", "if_icmpne", "if_icmplt", "if_icmpgt", "if_icmple", "if_icmpge",
            "goto", "gotow",
            "jsr", "jsr_w",
    ])
    for index, ope in enumerate(ope_list):
        if ope is None:
            continue
        (opecode, operands, comment) = ope
        if opecode in jump_ops:
            dest_index = int(operands[0])
            if not (0 <= dest_index < len(ope_list)):
                raise InvalidOpe("%d: jump to out of range: %d" % (index, dest_index))
            dest_op = ope_list[dest_index]
            if dest_op is None:
                raise InvalidOpe("%d: jump to invalid ope alignment: %d" % (index, dest_index))
        elif opecode in ("tableswitch", "lookupswitch"):
            case_descs = operands
            for case_value, dest_index_str in case_descs:
                dest_index = int(dest_index_str)
                if not (0 <= dest_index < len(ope_list)):
                    raise InvalidOpe("%d: switch to out of range: %d" % (index, dest_index))
                dest_op = ope_list[dest_index]
                if dest_op is None:
                    raise InvalidOpe("%d: switch to invalid ope alignment: %d" % (index, dest_index))

class AsmFileSyntaxError(OpeError):
    pass

def body_text_to_ope_list(body_lines, method_str=None):
    """
    Parse method definition (a list of str) from disassembled file and
    return a list of tuple (opecode, operands, comment).
    """
    if method_str is None:
        method_str = '*unknown*'

    pat_switch_case = re.compile(r'^\s+(-?\d+[lL]?|default): (\d+)$')
    def scan_switch_case_lines(li):
        tbl = []
        while True:
            li += 1
            L = body_lines[li]
            if L.endswith("}"):
                return tbl, li
            else:
                m = pat_switch_case.match(L)
                if m:
                    value, addr = m.group(1), m.group(2)
                    tbl.append((value, addr))
                else:
                    raise AsmFileSyntaxError("%s: invalid switch-case line: %s" % (method_str, L))

    ope_list = []

    last_pos = -1
    li = -1
    while True:
        li += 1
        if not (li < len(body_lines)): break  # while True
        L = body_lines[li]

        comment = None
        p = L.find('//')
        if p >= 0:
            L, comment = L[:p], L[p:]

        fields = L.split()
        fields_len = len(fields)
        if fields_len == 2:
            pos, opecode, operands = fields[0], fields[1], ()
        elif fields_len == 3:
            pos, opecode, operands = fields[0], fields[1], (fields[2],)
        elif fields_len == 4:
            pos, opecode, operands = fields[0], fields[1], (fields[2], fields[3])
            assert operands[0].endswith(',')
            operands = (operands[0][:-1], operands[1])
        else:
            if not len(fields) in (2, 3, 4):
                raise AsmFileSyntaxError("%s: unexpected len(fields)'s value %d: %s" % (method_str, len(fields), L))

        if opecode in ("tableswitch", "lookupswitch"):
            tbl, next_li = scan_switch_case_lines(li)
            operands = tbl
            li = next_li

        if not pos.endswith(':'):
            raise AsmFileSyntaxError("%s: invalid position field: %s" % (method_str, L))
        pos = int(pos[:-1])
        if pos <= last_pos:
            raise AsmFileSyntaxError("%s: invalid position %d: %s" % (method_str, pos, L))
        last_pos = pos

        while len(ope_list) < pos:
            ope_list.append(None)
        assert len(ope_list) == pos
        ope_list.append((opecode, operands, comment))

    return ope_list

class FORMAT_FIELD:
    ADDR = 1
    OPE = 2
    COMMENT = 4

def format_ope_list(ope_list, 
        fields=FORMAT_FIELD.ADDR | FORMAT_FIELD.OPE | FORMAT_FIELD.COMMENT):
    assert fields & FORMAT_FIELD.OPE
    lines = []; l_a = lines.append
    for index, ope in enumerate(ope_list):
        if ope is None:
            continue
        (opecode, operands, comment) = ope
        if comment is None or (fields & FORMAT_FIELD.COMMENT) == 0:
            comment = ''
        addr_str = "%8d: " % index
        if (fields & FORMAT_FIELD.COMMENT) == 0:
            addr_str = ''
        if opecode in ("tableswitch", "lookupswitch"):
            case_descs = operands
            l_a(addr_str + "%-15s %s" % (opecode + '   {', comment))
            addr_fill = ' ' * len(addr_str)
            for val, dst in operands:
                l_a(addr_fill + "%12s: %s" % (val, dst)) 
            l_a(addr_fill + "}")
        else:
            l_a(addr_str + "%-15s %-20s%s" % (opecode, ', '.join(operands), comment))
    return lines

