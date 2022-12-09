class Control:
    def __init__(
        self,
         AluSrc = None, MemtoReg = None, RegWrite = None, 
         MemRead = None, MemWrite = None, Branch = None, 
         AluOp1 = None, AluOp0 = None,Jump=None
        ):
        self.AluSrc = AluSrc
        self.MemtoReg = MemtoReg
        self.RegWrite = RegWrite
        self.MemRead = MemRead
        self.MemWrite = MemWrite
        self.Branch = Branch
        self.AluOp1 = AluOp1
        self.AluOp0 = AluOp0
        self.Jump = Jump