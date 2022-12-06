from control import Control

class INSTR_TYPES_CLASS:
    def __init__(self):
        self.R = 0
        self.I = 1
        self.B = 2
        self.J = 3
        self.S = 4
        self.HALT = 5
        self.LOAD_I = 6

INSTR_TYPES = INSTR_TYPES_CLASS()

OPCODE_TO_INSTR_TYPE = {
    "0110011":INSTR_TYPES.R,
    "0010011":INSTR_TYPES.I,
    "0000011":INSTR_TYPES.LOAD_I,
    "1101111":INSTR_TYPES.J,
    "1100011":INSTR_TYPES.B,
    "0100011":INSTR_TYPES.S,
    "1111111":INSTR_TYPES.HALT
}

INSTR_TYPE_TO_CONTROL = {
    INSTR_TYPES.R: Control(
        AluSrc = 0,
        MemtoReg = 0,
        RegWrite = 1,
        MemRead = 0,
        MemWrite = 0,
        Branch = 0,
        AluOp1 = 1,
        AluOp0 = 0
    ),
    INSTR_TYPES.I: Control(
        AluSrc = 1,
        MemtoReg = 0,
        RegWrite = 1,
        MemRead = 0,
        MemWrite = 0,
        Branch = 0,
        AluOp1 = 0,
        AluOp0 = 0
    ),
    INSTR_TYPES.LOAD_I: Control(
        AluSrc = 1,
        MemtoReg = 1,
        RegWrite = 1,
        MemRead = 1,
        MemWrite = 0,
        Branch = 0,
        AluOp1 = 0,
        AluOp0 = 0
    ),
    INSTR_TYPES.S: Control(
        AluSrc = 1,
        MemtoReg = None,
        RegWrite = 0,
        MemRead = 0,
        MemWrite = 1,
        Branch = 0,
        AluOp1 = 0,
        AluOp0 = 0
    ),
    INSTR_TYPES.B: Control(
        AluSrc = 0,
        MemtoReg = None,
        RegWrite = 0,
        MemRead = 0,
        MemWrite = 0,
        Branch = 1,
        AluOp1 = 0,
        AluOp0 = 1
    )
}