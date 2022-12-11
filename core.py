import os
from utils import sign_safe_binary_conversion


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
