import os
from utils import sign_safe_binary_conversion, sign_safe_binary_to_int, sign_extend_12
from stage_utils import STAGES
from alu import ALU
from instruction import Instruction, INSTR_TYPES

MemSize = 1000

class State(object):
    def __init__(self):
        self.reset_ID()
        self.reset_IF()
        self.reset_EX()
        self.reset_MEM()
        self.reset_WB()

    def reset_EX(self):
        self.EX = {
            "nop": False,
            "Read_data1": 0, 
            "Read_data2": 0, 
            "Imm": 0, 
            "Rs": 0, "Rt": 0, 
            "Wrt_reg_addr": 0, 
            "is_I_type": False, 
            "rd_mem": 0, 
            "wrt_mem": 0,
            "alu_op": 0,
            "wrt_enable": 0,
            "parsed_instr":None,
            "halted":False
        }
    
    def reset_IF(self):
        self.IF = {"nop": 0, "PC": 0,"halted":False}

    def reset_ID(self):
        self.ID = {
            "nop": False,
            "Instr":None,
            "halted":False
            }

    def reset_MEM(self):
        self.MEM = {
            "nop": False,
            "ALUresult": 0,
            "Store_data": 0,
            "Rs": 0,
            "Rt": 0,
            "Wrt_reg_addr": 0,
            "rd_mem": 0, 
            "wrt_mem": 0,
            "wrt_enable": 0,
            "parsed_instr":None,
            "halted":False
        }

    def reset_WB(self):
        self.WB = {
            "nop": False,
            "Wrt_data": 0,
            "Rs": 0,
            "Rt": 0,
            "Wrt_reg_addr": 0,
            "wrt_enable": 0,
            "parsed_instr":None,
            "halted":False
        }
    


class InsMem(object):
    def __init__(self, name, ioDir):
        self.id = name
        
        with open(os.path.join(ioDir,'imem.txt')) as im:
            self.IMem = [data.replace("\n", "") for data in im.readlines()]

    def readInstr(self, ReadAddress):
        #read instruction memory
        #return 32 bit hex val
        if ReadAddress %4 != 0:
            ReadAddress //= 4 # make sure it is a multiple of 4
        instr_binary = "".join(self.IMem[ReadAddress:ReadAddress+4]) # read Big Endian instruction
        return instr_binary # We choose to work with binary instruction as a string
          
class DataMem(object):
    def __init__(self, name, ioDir):
        self.id = name
        self.ioDir = ioDir
        with open(os.path.join(ioDir,'dmem.txt')) as dm:
            self.DMem = [data.replace("\n", "") for data in dm.readlines()]
        
        while len(self.DMem)<4000:
            self.DMem.append('00000000')

    def readDataMem(self, ReadAddress):
        #read data memory
        #return 32 bit hex val
        if ReadAddress %4 != 0:
            ReadAddress //= 4 # make sure it is a multiple of 4
        data_binary = "".join(self.DMem[ReadAddress:ReadAddress+4]) # read Big Endian instruction
        return data_binary
        
    def writeDataMem(self, Address, WriteData):
        #write data into byte addressable memory
        binary_form = sign_safe_binary_conversion(WriteData)
        for i in range(4):
            self.DMem[Address+i] = binary_form[8*i:8*i+8]
        
                     
    def outputDataMem(self):
        resPath = os.path.join(self.ioDir, self.id + "_DMEMResult.txt")
        with open(resPath, "w") as rp:
            rp.writelines([str(data) + "\n" for data in self.DMem])

class RegisterFile(object):
    def __init__(self, ioDir):
        self.outputFile = ioDir + "RFResult.txt"
        self.Registers = [0x0 for i in range(32)]
    
    def readRF(self, Reg_addr):
        return self.Registers[Reg_addr]
    
    def writeRF(self, Reg_addr, Wrt_reg_data):
        if Reg_addr:
            self.Registers[Reg_addr] = Wrt_reg_data
         
    def outputRF(self, cycle):
        op = ["State of RF after executing cycle:\t" + str(cycle) + "\n"]
        op.extend([str(sign_safe_binary_conversion(val))+"\n" for val in self.Registers])
        if(cycle == 0): perm = "w"
        else: perm = "a"
        with open(self.outputFile, perm) as file:
            file.writelines(op)

class Core(object):
    def __init__(self, ioDir, imem, dmem):
        self.myRF = RegisterFile(ioDir)
        self.cycle = 0
        self.halted = False
        self.ioDir = ioDir
        self.state = State()
        self.ext_imem = imem
        self.ext_dmem = dmem

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