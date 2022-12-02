def sign_extend_32(binary_str):
    return binary_str[0]*(32-len(binary_str)) + binary_str
