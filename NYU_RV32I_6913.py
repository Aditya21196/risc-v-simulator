import os
import argparse
from stage_utils import STAGES
from instruction import Instruction, INSTR_TYPES
from utils import sign_safe_binary_conversion, sign_safe_binary_to_int, sign_extend_12
from alu import ALU
from core import Core, SingleStageCore, RegisterFile, InsMem, DataMem, State

MemSize = 1000 # memory size, in reality, the memory size should be 2^32, but for this lab, for the space resaon, we keep it as this large number, but the memory is still 32-bit addressable.

class FiveStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(FiveStageCore, self).__init__(os.path.join(ioDir,"FS_"), imem, dmem)
        self.opFilePath = os.path.join(ioDir,'StateResult_FS.txt')
        self.buffer = State() # reuse state class because it encapsulates everything already

    def handle_IF(self):
        if self.state.IF['nop'] == 1:
            self.state.IF['nop'] = 0
            return

        # process new instruction
        self.buffer.ID["Instr"] = self.ext_imem.readInstr(self.state.IF["PC"])
        self.state.IF["PC"] += 4

    def handle_ID(self):
        # TODO: handle stalling

        self.state.ID["Instr"] = self.buffer.ID["Instr"]

        if self.state.ID["Instr"]:
            parsed_instruction = Instruction(self.buffer.ID["Instr"])

            # TODO: handle forwarding or stalling?
            if parsed_instruction.instr_type == INSTR_TYPES.HALT:
                self.halted = True
                return

            # pass the instruction itself to the buffer along with state relevant data
            self.buffer.EX["parsed_instr"] = parsed_instruction
            if not parsed_instruction.rs1 is None:
                self.buffer.EX["Read_data1"] = self.myRF.readRF(parsed_instruction.rs1)
            
            if not parsed_instruction.rs2 is None:
                self.buffer.EX["Read_data2"] = self.myRF.readRF(self.parsed_instruction.rs2)
            
            if not parsed_instruction.imm is None:
                self.buffer.EX["Imm"] = parsed_instruction.imm
            
            if not parsed_instruction.alu_control is None:
                self.buffer.EX["alu_op"] = parsed_instruction.alu_control.get_operation()
            
            if not parsed_instruction.rd is None:
                self.buffer.EX["Wrt_reg_addr"] = parsed_instruction.rd
            
            # TODO: Handle Jump and Branch
            
            # self.state.ID["Instr"] = None

    
    def handle_EX(self):
        # TODO: handle stalling
        self.state.EX["parsed_instr"] = self.buffer.EX["parsed_instr"]
        self.state.EX["Read_data1"] = self.buffer.EX["Read_data1"]
        self.state.EX["Read_data2"] = self.buffer.EX["Read_data2"]
        self.state.EX["Imm"] = self.buffer.EX["Imm"]
        self.state.EX["alu_op"] = self.buffer.EX["alu_op"]
        self.state.EX["Wrt_reg_addr"] = self.buffer.EX["Wrt_reg_addr"]

        if self.state.EX["parsed_instr"]:
            op1 = self.state.EX["Read_data1"]
            if self.state.EX["parsed_instr"].control.AluSrc == 0:
                op2 = self.state.EX["Read_data2"]
            else:
                op2 = sign_safe_binary_to_int(sign_extend_12(self.state.EX["Imm"]))

            self.buffer.MEM["ALUresult"] = ALU[self.state.EX["alu_op"]](op1,op2)

            self.buffer.MEM["Wrt_reg_addr"] = self.state.EX["Wrt_reg_addr"]
            
            self.buffer.MEM["Store_data"] = self.state.EX["Read_data2"]


        

    def handle_MEM(self):
        # TODO: handle stalling

        self.state.MEM["parsed_instr"] = self.buffer.MEM["parsed_instr"]
        self.state.MEM["ALUresult"] = self.buffer.MEM["ALUresult"]
        self.state.MEM["Store_data"] = self.buffer.MEM["Store_data"]
        self.state.MEM["Wrt_reg_addr"] = self.buffer.MEM["Wrt_reg_addr"]

        if self.state.MEM["parsed_instr"]:
            if self.state.MEM["parsed_instr"].control.MemWrite == 1:
                self.ext_dmem.writeDataMem(self.state.MEM["ALUresult"],self.state.MEM["Store_data"])
            
            if self.state.MEM["parsed_instr"].control.MemtoReg == 1:
                if self.state.MEM["parsed_instr"].control.MemRead == 1:
                    read_addr = self.state.MEM["ALUresult"]
                    read_val = sign_safe_binary_to_int(self.ext_dmem.readDataMem(read_addr))
                    self.buffer.WB["Wrt_data"] = read_val

            elif self.state.MEM["parsed_instr"].control.MemtoReg == 0:
                self.buffer.WB["Wrt_data"] = self.state.MEM["ALUresult"]
            
            self.buffer.WB["Wrt_reg_addr"] = self.state.MEM["Wrt_reg_addr"]

    

    def handle_WB(self):
        # TODO: handle stalling
        if self.state.WB["parsed_instr"]:
            if self.state.WB["parsed_instr"].control.RegWrite:
                self.myRF.writeRF(self.state.WB["Wrt_reg_addr"],self.state.WB["Wrt_data"])

    def step(self):
        # Your implementation
        # --------------------- WB stage ---------------------
        self.handle_WB()
        
        
        # --------------------- MEM stage --------------------
        self.handle_MEM()
        
        
        # --------------------- EX stage ---------------------
        self.handle_EX()
        
        
        # --------------------- ID stage ---------------------
        self.handle_ID()
        
        
        # --------------------- IF stage ---------------------
        self.handle_IF()

        
        if self.state.IF["nop"] and self.state.ID["nop"] and self.state.EX["nop"] and self.state.MEM["nop"] and self.state.WB["nop"]:
            self.halted = True
        
        self.myRF.outputRF(self.cycle) # dump RF
        self.printState(self.state, self.cycle) # print states after executing cycle 0, cycle 1, cycle 2 ... 
        
        self.cycle += 1

    def printState(self, state, cycle):
        printstate = ["-"*70+"\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.extend(["IF." + key + ": " + str(val) + "\n" for key, val in state.IF.items()])
        printstate.extend(["ID." + key + ": " + str(val) + "\n" for key, val in state.ID.items()])
        printstate.extend(["EX." + key + ": " + str(val) + "\n" for key, val in state.EX.items()])
        printstate.extend(["MEM." + key + ": " + str(val) + "\n" for key, val in state.MEM.items()])
        printstate.extend(["WB." + key + ": " + str(val) + "\n" for key, val in state.WB.items()])

        if(cycle == 0): perm = "w"
        else: perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)

if __name__ == "__main__":
     
    #parse arguments for input file location
    parser = argparse.ArgumentParser(description='RV32I processor')
    parser.add_argument('--iodir', default="", type=str, help='Directory containing the input files.')
    args = parser.parse_args()

    # ioDir = os.path.abspath(args.iodir)
    ioDir = '/Users/adityachawla/Desktop/course_work/csa_project/risc-v-simulator/TC1'
    print("IO Directory:", ioDir)

    imem = InsMem("Imem", ioDir)
    dmem_ss = DataMem("SS", ioDir)
    dmem_fs = DataMem("FS", ioDir)
    
    ssCore = SingleStageCore(ioDir, imem, dmem_ss)
    fsCore = FiveStageCore(ioDir, imem, dmem_fs)

    while(True):
        if not ssCore.halted:
            ssCore.step()
        
        if not fsCore.halted:
            fsCore.step()

        if ssCore.halted and fsCore.halted:
            break
    
    # dump SS and FS data mem.
    dmem_ss.outputDataMem()
    dmem_fs.outputDataMem()