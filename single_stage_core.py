
import os
from core import Core
from stage_utils import STAGES
from alu import ALU
from instruction import Instruction, INSTR_TYPES
from utils import sign_safe_binary_to_int, sign_extend_12

class SingleStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(SingleStageCore, self).__init__(os.path.join(ioDir,"SS_"), imem, dmem)
        self.opFilePath = os.path.join(ioDir,"StateResult_SS.txt")
        self.stage = STAGES.IF

    def handle_IF(self):
        if self.state.IF['nop'] == 1:
            self.state.IF['nop'] = 0
            return
        self.state.ID["Instr"] = self.ext_imem.readInstr(self.state.IF["PC"])
        self.stage = STAGES.ID
        
    def handle_ID(self):
        self.parsed_instruction = Instruction(self.state.ID["Instr"])
        if self.parsed_instruction.instr_type == INSTR_TYPES.HALT:
            self.state.IF['nop'] = 1
            self.stage = STAGES.IF
            return


        if not self.parsed_instruction.rs1 is None:
            self.state.EX["Read_data1"] = self.myRF.readRF(self.parsed_instruction.rs1)
        
        if not self.parsed_instruction.rs2 is None:
            self.state.EX["Read_data2"] = self.myRF.readRF(self.parsed_instruction.rs2)
        
        if not self.parsed_instruction.imm is None:
            self.state.EX["Imm"] = self.parsed_instruction.imm
        
        if not self.parsed_instruction.alu_control is None:
            self.state.EX["alu_op"] = self.parsed_instruction.alu_control.get_operation()
        
        if not self.parsed_instruction.rd is None:
            self.state.EX["Wrt_reg_addr"] = self.parsed_instruction.rd

        if self.parsed_instruction.control.Jump == 1:
            self.myRF.writeRF(self.state.EX["Wrt_reg_addr"],self.state.IF["PC"]+4)
            self.state.IF["PC"] = self.state.IF["PC"] + sign_safe_binary_to_int(sign_extend_12(self.state.EX["Imm"]))
            self.stage = STAGES.IF
            return

        if self.parsed_instruction.control.Branch == 1:
            rs_equal = (self.state.EX["Read_data1"] == self.state.EX["Read_data2"])
            if (self.parsed_instruction.funct3 == '000' and rs_equal) or (self.parsed_instruction.funct3 == '001' and not rs_equal):
                self.state.IF["PC"] += sign_safe_binary_to_int(sign_extend_12(self.state.EX["Imm"]))
            else:
                self.state.IF["PC"] += 4
            self.stage = STAGES.IF
            return

        self.stage = STAGES.EX

    def handle_EX(self):
        op1 = self.state.EX["Read_data1"]
        if self.parsed_instruction.control.AluSrc == 0:
            op2 = self.state.EX["Read_data2"]
        else:
            op2 = sign_safe_binary_to_int(sign_extend_12(self.state.EX["Imm"]))

        self.state.MEM["ALUresult"] = ALU[self.state.EX["alu_op"]](op1,op2)

        self.state.MEM["Wrt_reg_addr"] = self.state.EX["Wrt_reg_addr"]
        
        self.state.MEM["Store_data"] = self.state.EX["Read_data2"]

        self.stage = STAGES.MEM

    def handle_MEM(self):
        
        if self.parsed_instruction.control.MemWrite == 1:
            self.ext_dmem.writeDataMem(self.state.MEM["ALUresult"],self.state.MEM["Store_data"])
        
        if self.parsed_instruction.control.MemtoReg == 1:
            if self.parsed_instruction.control.MemRead == 1:
                read_addr = self.state.MEM["ALUresult"]
                read_val = sign_safe_binary_to_int(self.ext_dmem.readDataMem(read_addr))
                self.state.WB["Wrt_data"] = read_val

        elif self.parsed_instruction.control.MemtoReg == 0:
            self.state.WB["Wrt_data"] = self.state.MEM["ALUresult"]
        
        self.state.WB["Wrt_reg_addr"] = self.state.MEM["Wrt_reg_addr"]

        self.stage = STAGES.WB

    def handle_WB(self):
        if self.parsed_instruction.control.RegWrite:
            self.myRF.writeRF(self.state.WB["Wrt_reg_addr"],self.state.WB["Wrt_data"])

        self.state.IF["PC"] += 4
        self.stage = STAGES.IF

    def step(self):
        # Your implementation

        if self.state.IF['nop'] == 1:
            self.halted = True
        else:
        # find the stage
            if self.stage == STAGES.IF and self.state.IF['nop'] == 0:
                self.handle_IF()

            if self.stage == STAGES.ID:
                self.handle_ID()

            if self.stage == STAGES.EX:
                self.handle_EX()

            if self.stage == STAGES.MEM:
                self.handle_MEM()

            if self.stage == STAGES.WB:
                self.handle_WB()
        
        
        
        self.myRF.outputRF(self.cycle) # dump RF
        self.printState(self.state, self.cycle) # print states after executing cycle 0, cycle 1, cycle 2 ... 
            
        self.cycle += 1

    def printState(self, state, cycle):
        printstate = ["-"*70+"\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.append("IF.PC: " + str(state.IF["PC"]) + "\n")
        printstate.append("IF.nop: " + str(state.IF["nop"]) + "\n")
        
        if(cycle == 0): perm = "w"
        else: perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)