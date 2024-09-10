from enum import Enum
import sys
import numpy as np

image_path = [".\\2048.obj"]

MEMORY_MAX = 1 << 16
class REGISTERS(Enum):
        R_R0 = 0
        R_R1 = 1
        R_R2 = 2
        R_R3 = 3
        R_R4 = 4
        R_R5 = 5
        R_R6 = 6
        R_R7 = 7
        R_PC = 8
        R_COND = 9
        R_COUNT = 10

class OPCODES(Enum):
    OP_BR = 0
    OP_ADD = 1
    OP_LD = 2
    OP_ST = 3
    OP_JSR = 4 
    OP_AND = 5
    OP_LDR = 6
    OP_STR = 7
    OP_RTI = 8
    OP_NOT = 9
    OP_LDI = 10
    OP_STI = 11
    OP_JMP = 12
    OP_RES = 13
    OP_LEA = 14
    OP_TRAP = 15

class CONDITION_FLAGS(Enum):
    FL_POS = 1 << 0
    FL_ZRO = 1 << 1
    FL_NEG = 1 << 2

class KEYBOARD_REGISTERS(Enum):
    MR_KBSR = 0xFE00
    MR_KBDR = 0xFE02

class TRAPCODES(Enum):
    TRAP_GETC = 0x20
    TRAP_OUT = 0x21
    TRAP_PUTS = 0x22
    TRAP_IN = 0x23
    TRAP_PUTSP = 0x24
    TRAP_HALT = 0x25 

running = 1

def sign_extend(x, bit_count):
    if ((x >> (bit_count - 1)) & 1) :
        x = x | (0xFFFF << bit_count)
    return x

def update_flags(reg, r):
    if (reg[r] == 0):
        reg[REGISTERS.R_COND.value] = CONDITION_FLAGS.FL_ZRO.value
    elif(reg[r] >> 15):
    
        reg[REGISTERS.R_COND.value] = CONDITION_FLAGS.FL_NEG.value
    else:
        reg[REGISTERS.R_COND.value] = CONDITION_FLAGS.FL_POS.value
    




class TRAPFUNC:
    def TRAP_GETC(reg, memory):
        key = input()
        sys.stdout.flush()
        reg[REGISTERS.R_R0.value] = ord(key)
        update_flags(reg, REGISTERS.R_R0.value)

    def TRAP_PUTS(reg, memory):
        i = 1
        c = memory[reg[REGISTERS.R_R0.value]]
        # print(hex(reg[REGISTERS.R_R0.value]))
        while c:
            sys.stdout.write(chr(c))
            c = memory[reg[REGISTERS.R_R0.value] + i]
            i += 1
        sys.stdout.flush()

    def TRAP_OUT(reg, memory):
        sys.stdout.write(chr(reg[REGISTERS.R_R0.value]))
        sys.stdout.flush()

    def TRAP_IN(reg, memory):
        print("Enter a character: ")
        c = sys.stdin.read(1)
        sys.stdout.write(c)
        sys.stdout.flush()
        reg[REGISTERS.R_R0.value] = c
        update_flags(reg, REGISTERS.R_R0.value)

    def TRAP_PUTSP(reg, memory):
        i = 1
        c = memory[reg[REGISTERS.R_R0.value]]
        while c:
            char1 = c & 0xFF
            sys.stdout.write(chr(char1))
            char2 = c >> 8
            if char2:
                sys.stdout.write(chr(char2))
            c = memory[reg[REGISTERS.R_R0.value] + i]
            i += 1
    def TRAP_HALT(reg, memory):
        global running
        sys.stdout.write("HALT")
        sys.stdout.flush()
        running = 0

class cpu:
    mem = [0] * MEMORY_MAX
    reg = [0] * REGISTERS.R_COUNT.value
    funcmap = None

    def read_image(self, image_path):
        with open(image_path, "rb") as f:
            o = f.read(2)
            binary = f.read()
            binnparray = np.frombuffer(binary, dtype=np.uint16)
            o = np.frombuffer(o, dtype=np.uint8)
            origin = o[1]  + o[0] * (1 << 8)
            self.mem[origin:origin + binnparray.size - 1] = binnparray[0:]
        self.mem = np.array(self.mem, dtype=np.uint16).byteswap(False)
        return 1

    def mem_write(self, address, val):
        address &= 0xffff
        self.mem[address] = val


    def mem_read(self, address):

        address &= 0xffff
        if (address == KEYBOARD_REGISTERS.MR_KBSR.value):
            key = input()
            sys.stdout.flush()
            # if press_key_all():
            
            self.mem[KEYBOARD_REGISTERS.MR_KBSR.value] = (1 << 15)
            i = ord(key)
            
            # print(i)
            self.mem[KEYBOARD_REGISTERS.MR_KBDR.value] = i
            # else:
            #     self.mem[KEYBOARD_REGISTERS.MR_KBSR.value] = 0
        # return memory[address:address+2]
        return self.mem[address]



    def BR(self, instr):
        pc_offset = sign_extend(instr & 0x1FF, 9)
        cond_flag = (instr >> 9) & 0x7
        if cond_flag & self.reg[REGISTERS.R_COND.value]:
            self.reg[REGISTERS.R_PC.value] += pc_offset
            self.reg[REGISTERS.R_PC.value] &= 0xffff
        

    def ADD(self, instr):
        r0 = (instr >> 9 ) & 0x7
        r1 = (instr >> 6) & 0x7
        imm_flag = (instr >> 5) & 0x1
        # print(r0)
        # print(r1)
        # print(imm_flag)
        # print(self.reg[r0])
        if imm_flag:
            imm5 = sign_extend(instr & 0x1F, 5)
            self.reg[r0] = self.reg[r1] + imm5
        else:
            r2 = instr & 0x7
            self.reg[r0] = self.reg[r1] + self.reg[r2]
        self.reg[r0] &= 0xFFFF
        # print(self.reg[r0])
        update_flags(self.reg, r0)



    def LD(self, instr):
        r0 = (instr >> 9) & 0x7
        pc_offset = sign_extend(instr & 0x1FF, 9)
        self.reg[r0] = self.mem_read(self.reg[REGISTERS.R_PC.value] + pc_offset)
        update_flags(self.reg, r0)

    def ST(self, instr):
        r0 = (instr >> 9) & 0x7
        pc_offset = sign_extend(instr & 0x1FF, 9)
        self.mem_write(self.reg[REGISTERS.R_PC.value] + pc_offset, self.reg[r0])

    def JSR(self, instr):
        long_flag = (instr >> 11) & 1
        self.reg[REGISTERS.R_R7.value] = self.reg[REGISTERS.R_PC.value]
        if long_flag:
            long_pc_offset = sign_extend(instr & 0x7FF, 11)
            self.reg[REGISTERS.R_PC.value] += long_pc_offset
        else:
            r1 = (instr >> 6) & 0x7
            self.reg[REGISTERS.R_PC.value] = self.reg[r1]
        
    def AND(self, instr):
        r0 = (instr >> 9) & 0x7
        r1 = (instr >> 6) & 0x7
        imm_flag = (instr >> 5) & 0x1

        if imm_flag:
            imm5 = sign_extend(instr & 0x1F, 5)
            self.reg[r0] = self.reg[r1] & imm5
        else:
            r2 = instr & 0x7
            self.reg[r0] = self.reg[r1] & self.reg[r2]
        update_flags(self.reg, r0)

    def LDR(self, instr):
        r0 = (instr >> 9) & 0x7
        r1 = (instr >> 6) & 0x7
        offset = sign_extend(instr & 0x3F, 6)
        self.reg[r0] = self.mem_read(self.reg[r1] + offset)
        update_flags(self.reg, r0)

    def STR(self, instr):
        r0 = (instr >> 9) & 0x7
        r1 = (instr >> 6) & 0x7
        offset = sign_extend(instr & 0x3F, 6)
        self.mem_write(self.reg[r1] + offset, self.reg[r0])
        

    def RTI(self, instr):
        return
    def NOT(self, instr):
        r0 = (instr >> 9) & 0x7
        r1 = (instr >> 6) & 0x7
        self.reg[r0] = ~self.reg[r1]
        update_flags(self.reg, r0)

    def LDI(self, instr):
        r0 = (instr >> 9) & 0x7
        pc_offset = sign_extend(instr & 0x1FF, 9)
        # print('ldi read:')
        # print(hex((self.reg[REGISTERS.R_PC.value] + pc_offset) & 0xffff))
        temp = self.mem_read(self.reg[REGISTERS.R_PC.value] + pc_offset)
        # print(hex(temp))
        self.reg[r0] = self.mem_read(temp)
        update_flags(self.reg, r0)

    def STI(self, instr):
        r0 = (instr >> 9) & 0x7
        pc_offset = sign_extend(instr & 0x1FF, 9)
        self.mem_write(self.mem_read(self.reg[REGISTERS.R_PC.value] + pc_offset), self.reg[r0])

    def JMP(self, instr):
        r1 = (instr >> 6) & 0x7
        self.reg[REGISTERS.R_PC.value] = self.reg[r1]

    def RES(self, instr):
        return
    def LEA(self, instr):
        r0 = (instr >> 9) & 0x7
        pc_offset = sign_extend(instr & 0x1FF, 9)
        self.reg[r0] = self.reg[REGISTERS.R_PC.value] + pc_offset
        self.reg[r0] &= 0xffff
        update_flags(self.reg, r0)
    
    def TRAP(self, instr):
        self.reg[REGISTERS.R_R7.value] = self.reg[REGISTERS.R_PC.value]
        # print(self.trapmap[TRAPCODES(instr & 0xFF)])
        self.trapmap[TRAPCODES(instr & 0xFF)](self.reg, self.mem)

    
    
    def __init__(self) -> None:
        self.funcmap = {
            OPCODES.OP_BR: self.BR,
            OPCODES.OP_ADD: self.ADD,
            OPCODES.OP_LD: self.LD,
            OPCODES.OP_ST: self.ST,
            OPCODES.OP_JSR: self.JSR,
            OPCODES.OP_AND: self.AND,
            OPCODES.OP_LDR: self.LDR,
            OPCODES.OP_STR: self.STR,
            OPCODES.OP_RTI: self.RTI,
            OPCODES.OP_NOT: self.NOT,
            OPCODES.OP_LDI: self.LDI,
            OPCODES.OP_STI: self.STI,
            OPCODES.OP_JMP: self.JMP,
            OPCODES.OP_RES: self.RES,
            OPCODES.OP_LEA: self.LEA,
            OPCODES.OP_TRAP: self.TRAP
        }
        self.trapmap = {
            TRAPCODES.TRAP_GETC: TRAPFUNC.TRAP_GETC,
            TRAPCODES.TRAP_OUT: TRAPFUNC.TRAP_OUT,
            TRAPCODES.TRAP_PUTS: TRAPFUNC.TRAP_PUTS,
            TRAPCODES.TRAP_IN: TRAPFUNC.TRAP_IN,
            TRAPCODES.TRAP_PUTSP: TRAPFUNC.TRAP_PUTSP,
            TRAPCODES.TRAP_HALT: TRAPFUNC.TRAP_HALT
        }

    def main(self):
        for path in image_path:
            i = self.read_image(path)
            if not i:
                print("failed to load image: %s\n", path)
                exit()
        print("read image finish") 

        self.reg[REGISTERS.R_COND.value] = CONDITION_FLAGS.FL_ZRO
        PC_START = 0x3000
        self.reg[REGISTERS.R_PC.value] = PC_START
        while running:
            instr = self.mem_read(self.reg[REGISTERS.R_PC.value])
            self.reg[REGISTERS.R_PC.value] += 1
            op = instr >> 12
            # instr = instr[0] * (1 << 8) + instr[1]
            # print(hex(instr))
            # print(self.funcmap[OPCODES(op)])
            # print(self.reg)
            # input()
            try:
                # print(self.funcmap.get(OPCODES(op)))
                self.funcmap[OPCODES(op)](instr)
            except:
                print("instruction Error: %X" % op)
        # restore_input_buffering()


cpu().main()
