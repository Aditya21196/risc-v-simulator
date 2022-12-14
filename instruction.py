# using a class as a enum
from alu import AluControl
from rv32_constants import OPCODE_TO_INSTR_TYPE, INSTR_TYPES, INSTR_TYPE_TO_CONTROL
class Instruction:
    
    def initialize(self):
        self.rs1 = None
        self.rs2 = None
        self.rd = None
        self.imm = None
        self.funct3 = None
        self.funct7 = None
        self.opcode = None
        self.control = None
        self.alu_control = None


    def __init__(self,instr):
        self.initialize()
        self.instr = instr
        self.opcode = self.index_instr(0,6)[::-1]
        self.instr_type = OPCODE_TO_INSTR_TYPE[self.opcode]

        if self.instr_type == INSTR_TYPES.HALT:
            return

        self.parse_dest_register()
        self.parse_funct_types()
        self.parse_source_registers()
        self.parse_imm()
        self.parse_control()
        

    def __repr__(self):
        return f"""
rs1:{self.rs1},
rs2:{self.rs2},
rd:{self.rd},
funct7:{self.funct7},
funct3:{self.funct3},
opcode:{self.opcode},
imm:{self.imm}
        """

    def index_instr(self,i,j):
        return self.instr[31-j:32-i][::-1]

    def rev_index(self,i):
        return self.instr[31-i]

    def parse_control(self):
        self.control = INSTR_TYPE_TO_CONTROL[self.instr_type]
        self.alu_control = AluControl(self.control.AluOp0,self.control.AluOp1,self.funct3,self.funct7,self.instr_type)
        

    def get_alu_control(self):
        return INSTR_TYPE_TO_CONTROL[self.instr_type]

    def parse_imm(self):
        if self.instr_type in [INSTR_TYPES.I,INSTR_TYPES.LOAD_I]:
            imm = self.index_instr(20,31)
            self.imm = imm[::-1]
        elif self.instr_type == INSTR_TYPES.J:
            imm = '0' + self.index_instr(21,30) + self.rev_index(20) + self.index_instr(12,19) + self.rev_index(31)
            self.imm = imm[::-1]
        elif self.instr_type == INSTR_TYPES.B:
            imm = '0' + self.index_instr(8,11) + self.index_instr(25,30) + self.rev_index(7) + self.rev_index(31)
            self.imm = imm[::-1]
        elif self.instr_type == INSTR_TYPES.S:
            imm = self.index_instr(7,11) + self.index_instr(25,31)
            self.imm = imm[::-1]

    def parse_source_registers(self):
        if self.instr_type != INSTR_TYPES.J:
            rs1 = self.index_instr(15,19)
            self.rs1 = int(rs1[::-1],2)

        if self.instr_type in [INSTR_TYPES.R,INSTR_TYPES.S,INSTR_TYPES.B]:
            rs2 = self.index_instr(20,24)
            self.rs2 = int(rs2[::-1],2)

    def parse_funct_types(self):
        if self.instr_type != INSTR_TYPES.J:
            funct3 = self.index_instr(12,14)
            self.funct3 = funct3[::-1]
        
        if self.instr_type == INSTR_TYPES.R:
            funct7 = self.index_instr(25,31)
            self.funct7 = funct7[::-1]

    def parse_dest_register(self):
        if not self.instr_type in [INSTR_TYPES.S,INSTR_TYPES.B]:
            rd = self.index_instr(7,11)
            self.rd = int(rd[::-1],2)