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
        # process new instruction
        if self.state.ID["halted"]:
            return

        self.buffer.ID["Instr"] = self.ext_imem.readInstr(self.state.IF["PC"])

        self.state.IF["PC"] += 4


    def handle_ID(self):
        if self.state.ID["halted"]:
            self.state.EX["halted"] = True
            self.state.ID["nop"] = 1
            return

        self.state.ID["Instr"] = self.buffer.ID["Instr"]
        
        if not self.state.ID["Instr"]:
            return

        parsed_instruction = Instruction(self.buffer.ID["Instr"])

        if parsed_instruction.instr_type == INSTR_TYPES.HALT:
            self.state.ID["halted"] = True
            self.state.EX["halted"] = True
            self.state.ID["nop"] = 1
            return

        if self.check_load_use_data(parsed_instruction):
            return

        # pass the instruction itself to the buffer along with state relevant data
        self.buffer.EX["parsed_instr"] = parsed_instruction
        if not parsed_instruction.rs1 is None:
            self.buffer.EX["Read_data1"] = self.myRF.readRF(parsed_instruction.rs1)
        
        if not parsed_instruction.rs2 is None:
            self.buffer.EX["Read_data2"] = self.myRF.readRF(parsed_instruction.rs2)
        
        if not parsed_instruction.imm is None:
            self.buffer.EX["Imm"] = parsed_instruction.imm
        
        if not parsed_instruction.alu_control is None:
            self.buffer.EX["alu_op"] = parsed_instruction.alu_control.get_operation()
        
        if not parsed_instruction.rd is None:
            self.buffer.EX["Wrt_reg_addr"] = parsed_instruction.rd

        if parsed_instruction.control.Jump == 1:
            self.myRF.writeRF(parsed_instruction.rd,self.state.IF["PC"]+4)
            self.state.IF["PC"] = self.state.IF["PC"] + sign_safe_binary_to_int(sign_extend_12(self.state.EX["Imm"]))
            self.state.EX["nop"] = 1
            return

            

    def check_load_use_data(self,parsed_instruction):
        if self.buffer.EX["parsed_instr"] and self.buffer.EX["parsed_instr"].control.MemRead:
            if (self.buffer.EX["parsed_instr"].rd == parsed_instruction.rs1) or (self.buffer.EX["parsed_instr"].rd == parsed_instruction.rs2):
                self.state.IF["PC"] -= 4
                self.state.EX["nop"] = 1
                
                return True
        return False

    def check_forwarding(self):
        forwardA,forwardB = 0b00,0b00

        if self.buffer.WB["parsed_instr"] and self.buffer.EX["parsed_instr"] and self.buffer.EX["parsed_instr"].control.RegWrite:
            if self.buffer.MEM["parsed_instr"] and self.buffer.MEM["parsed_instr"].rd and self.buffer.MEM["parsed_instr"].rd == self.buffer.EX["parsed_instr"].rs1:
                forwardA = 0b10
            elif self.buffer.WB["parsed_instr"].rd and self.buffer.WB["parsed_instr"].rd == self.buffer.EX["parsed_instr"].rs1:
                forwardA = 0b01
        
            if self.buffer.MEM["parsed_instr"] and self.buffer.MEM["parsed_instr"].rd and self.buffer.MEM["parsed_instr"].rd == self.buffer.EX["parsed_instr"].rs2:
                forwardB = 0b10
            elif self.buffer.WB["parsed_instr"].rd and self.buffer.WB["parsed_instr"].rd == self.buffer.EX["parsed_instr"].rs2:
                forwardB = 0b01
        
        return forwardA,forwardB

    def handle_EX(self):
        
        if self.state.EX["halted"]:
            self.state.MEM["halted"] = True
            self.state.EX["nop"] = 1
            return

        if self.state.EX["nop"] == 1:
            self.buffer.reset_EX()
            self.state.MEM["nop"] = 1
            self.state.EX["nop"] = 0
            return


        forwardA,forwardB = self.check_forwarding()

        self.state.EX["parsed_instr"] = self.buffer.EX["parsed_instr"]

        self.state.EX["Read_data1"] = self.buffer.EX["Read_data1"]

        self.state.EX["Read_data2"] = self.buffer.EX["Read_data2"]
        

        self.state.EX["Imm"] = self.buffer.EX["Imm"]
        self.state.EX["alu_op"] = self.buffer.EX["alu_op"]
        self.state.EX["Wrt_reg_addr"] = self.buffer.EX["Wrt_reg_addr"]

        if forwardA == 0b01:
            self.state.EX["Read_data1"] = self.buffer.WB["Wrt_data"]
        elif forwardA == 0b10:
            self.state.EX["Read_data1"] = self.buffer.MEM["ALUresult"]
            
        if forwardB == 0b01:
            self.state.EX["Read_data2"] = self.buffer.WB["Wrt_data"]
        elif forwardB == 0b10:
            self.state.EX["Read_data2"] = self.buffer.MEM["ALUresult"]

        if self.state.EX["parsed_instr"]:
            self.buffer.MEM["parsed_instr"] = self.state.EX["parsed_instr"]

            if self.state.EX["parsed_instr"].control.Branch == 1:
                rs_equal = (self.state.EX["Read_data1"] == self.state.EX["Read_data2"])
                if (self.state.EX["parsed_instr"].funct3 == '000' and rs_equal) or (self.state.EX["parsed_instr"].funct3 == '001' and not rs_equal):
                    val = self.state.IF["PC"] + sign_safe_binary_to_int(sign_extend_12(self.state.EX["Imm"]))
                    self.state.IF = val

                self.state.MEM["nop"] = 1
                return


            op1 = self.state.EX["Read_data1"]
            if self.state.EX["parsed_instr"].control.AluSrc == 0:
                op2 = self.state.EX["Read_data2"]
            else:
                op2 = sign_safe_binary_to_int(sign_extend_12(self.state.EX["Imm"]))

            self.buffer.MEM["ALUresult"] = ALU[self.state.EX["alu_op"]](op1,op2)

            self.buffer.MEM["Wrt_reg_addr"] = self.state.EX["Wrt_reg_addr"]
            
            self.buffer.MEM["Store_data"] = self.state.EX["Read_data2"]


    def handle_MEM(self):

        if self.state.MEM["halted"]:
            self.state.WB["halted"] = True
            self.state.MEM["nop"] = 1
            return

        if self.state.MEM["nop"] == 1:
            self.buffer.reset_MEM()
            self.state.WB["nop"] = 1
            self.state.MEM["nop"] = 0
            return

        self.state.MEM["parsed_instr"] = self.buffer.MEM["parsed_instr"]
        self.state.MEM["ALUresult"] = self.buffer.MEM["ALUresult"]
        self.state.MEM["Store_data"] = self.buffer.MEM["Store_data"]
        self.state.MEM["Wrt_reg_addr"] = self.buffer.MEM["Wrt_reg_addr"]


        if self.state.MEM["parsed_instr"]:

            self.buffer.WB["parsed_instr"] = self.state.MEM["parsed_instr"]

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

        if self.state.WB["halted"]:
            self.state.WB["nop"] = 1
            return

        if self.state.WB["nop"] == 1:
            self.buffer.reset_WB()
            self.state.WB["nop"] = 0
            return

        self.state.WB["parsed_instr"] = self.buffer.WB["parsed_instr"]
        self.state.WB["Wrt_reg_addr"] = self.buffer.WB["Wrt_reg_addr"]
        self.state.WB["Wrt_data"] = self.buffer.WB["Wrt_data"]
        
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

        
        if self.state.ID["halted"] and self.state.EX["halted"] and self.state.MEM["halted"] and self.state.WB["halted"]:
            self.halted = True
        
        self.myRF.outputRF(self.cycle) # dump RF
        self.printState(self.state, self.cycle) # print states after executing cycle 0, cycle 1, cycle 2 ... 
        
        self.cycle += 1

    def printState(self, state, cycle):
        printstate = [ "State after executing cycle:\t" + str(cycle) + "\n"]
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
    ioDir = '/Users/adityachawla/Desktop/course_work/csa_project/risc-v-simulator/TC2'
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