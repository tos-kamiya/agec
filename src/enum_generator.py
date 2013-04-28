#coding: utf-8

__author__ = 'Toshihiro Kamiya <kamiya@mbj.nifty.com>'
__status__ = 'experimental'

class EnumGeneratorError(ValueError):
    pass

class EmptyEnumString(EnumGeneratorError):
    pass

class DuplicatedEnumString(EnumGeneratorError):
    pass

class EnumGenerator:
    def __init__(self, strs=None):
        '''
        Generate EnumGenerator object.
        Optional argument 'strs' are used as initial enum string value.
        If 'strs' includes empty strings, raise EmptyEnumString.
        If some of 'strs' are the same string, raise DuplicatedString.
        '''

        self._str2int = { '': 0 }
        self._int2str = ['']
        if strs:
            self.add_strs(strs)

    def _add_name_i(self, s):
        i = len(self._int2str)
        self._int2str.append(s)
        self._str2int[s] = i
        return i
    
    def lookup_str(self, s):
        '''
        Find string value 's' and return its integer value.
        Return -1 when not found. 
        '''

        if not s:
            return -1
        return self._str2int.get(s, -1)
    
    def add_name(self, s):
        '''
        Add string 's' as a new value and return its integer value.
        If the enum object has already included the string value,
        raise DuplicatedString.
        If the string 's' is empty, raise EmptyEnumString.
        '''
        
        if not s:
            raise EmptyEnumString
        i = self._str2int.get(s, -1)
        if i != -1:
            raise DuplicatedEnumString
        
        return self._add_name_i(s)
    
    def to_int(self, s):
        '''
        If string 's' is already a member of the enum object,
        return its integer value.
        If not, add string 's' as a new value and return its integer value.
        If the string 's' is empty, raise EmptyEnumString.
        '''

        if not s:
            raise EmptyEnumString
        i = self._str2int.get(s, -1)
        if i != -1:
            return i

        return self._add_name_i(s)

    def to_str(self, i):
        '''
        Find integer 'i' in the enum object and return its string value.
        If not found, return None.
        '''
        
        if 0 < i < len(self._int2str):
            return self._int2str[i]

        return None

    def get_strs(self):
        '''
        Return a list of all string values in the enum object,
        in the order of integer value of each string value.
        '''
        
        return list(self._int2str)[1:]

    def add_strs(self, strs):
        '''
        Add string values 'strs' to the enum object.
        If 'strs' includes empty strings, raise EmptyEnumString.
        If some of 'strs' are the same string, raise DuplicatedString.
        '''

        assert strs
        for s in strs:
            self.add_name(s)
