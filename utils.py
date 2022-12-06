def sign_extend_32(binary_str,prefix=None):
    if prefix is None:
        prefix = binary_str[0]
    return prefix*(32-len(binary_str)) + binary_str

def sign_extend_12(binary_str):
    if len(binary_str) == 12 and binary_str[0] == '1':
        return sign_extend_32(binary_str,'1')
    return sign_extend_32(binary_str,'0')

def sign_safe_int(x):
    if x>2147483647:
        x -= 2*2147483648
    return x

def sign_safe_add(a,b):
    return sign_safe_int(a)+sign_safe_int(b)

def sign_safe_binary_to_int(x):
    x = int(x,2)
    return sign_safe_int(x)

def sign_safe_subtract(a,b):
    return sign_safe_int(a)-sign_safe_int(b)

def sign_safe_binary_conversion(x,prefix=None):
    if x<0:
        x += 2*2147483648
    return sign_extend_32(format(x,'b')[:32],prefix)