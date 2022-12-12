from utils import sign_safe_add, sign_safe_subtract
from rv32_constants import INSTR_TYPES

ALU = {
    0b0000: lambda a,b: a&b,
    0b0001: lambda a,b: a|b,
    0b010: sign_safe_add,
    0b0110: sign_safe_subtract,
    0b1110: lambda a,b: a^b
}

class AluControl:
    def __init__(self,AluOp0,AluOp1,funct3,funct7,instr_type):
        self.alu_op1 = AluOp1
        self.alu_op0 = AluOp0
        self.funct3 = funct3
        self.funct7 = funct7
        self.instr_type = instr_type

    def choose_i_operand(self):
        if self.funct3 == '000':
            return 0b010
        elif self.funct3 == '100':
            return 0b1110
        elif self.funct3 == '110':
            return 0b0001
        elif self.funct3 == '111':
            return 0b0000
        else:
            raise Exception("Invalid ALU Control Input")
    
    def get_operation(self):
        if self.instr_type == INSTR_TYPES.I:
            return self.choose_i_operand()

        if self.alu_op1 == 0 and self.alu_op0 == 0:
            return 0b0010
        elif self.alu_op0 == 1:
            return 0b0110
        elif self.alu_op1 == 1:
            if self.funct7 == '0000000' and self.funct3 == '000':
                return 0b0010
            elif self.funct7 == '0100000' and self.funct3 == '000':
                return 0b0110
            elif self.funct7 == '0000000' and self.funct3 == '111':
                return 0b0000
            elif self.funct7 == '0000000' and self.funct3 == '110':
                return 0b0001
            elif self.funct7 == '0000000' and self.funct3 == '100':
                return 0b1110
        raise Exception("Invalid ALU Control Input")
