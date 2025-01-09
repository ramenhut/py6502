import random

class Ricoh2A03:
    def __init__(self, memory):
        # Registers
        self.A = 0x00      # Accumulator
        self.X = 0x00      # X Register
        self.Y = 0x00      # Y Register
        self.SP = 0xFD     # Stack Pointer
        self.PC = 0x0000   # Program Counter
        # self.P = 0x24      # Processor Status Register

        # Flags
        self.C = 0         # Carry Flag
        self.Z = 0         # Zero Flag
        self.I = 1         # Interrupt Disable
        self.D = 0         # Decimal Mode (disabled in Ricoh 2A03)
        self.B = 0         # Break Command
        self.U = 1         # Unused, always set to 1
        self.V = 0         # Overflow Flag
        self.N = 0         # Negative Flag

        self.memory = memory  # Memory interface (should be 64KB)

    def reset(self):
        """Resets the CPU to its initial state."""
        self.SP = 0xFD
        self.C = 0         # Carry Flag
        self.Z = 0         # Zero Flag
        self.I = 1         # Interrupt Disable
        self.D = 0         # Decimal Mode (disabled in Ricoh 2A03)
        self.B = 0         # Break Command
        self.U = 1         # Unused, always set to 1
        self.V = 0         # Overflow Flag
        self.N = 0         # Negative Flag
        self.PC = self._read_word(0xFFFC)
        # self.P = 0x24

    def randomize(self):
        """Randomizes the CPU registers for training."""
        self.A = random.randint(0, 255)
        self.X = random.randint(0, 255)
        self.Y = random.randint(0, 255)
        self.SP = random.randint(0, 255)
        self.PC = random.randint(0, 65535)
        self.C = random.randint(0, 1)
        self.Z = random.randint(0, 1)
        self.I = random.randint(0, 1)
        self.D = random.randint(0, 1)
        self.B = random.randint(0, 1)
        self.U = 1
        self.V = random.randint(0, 1)
        self.N = random.randint(0, 1)

    def _read_byte(self, addr):
        """Reads a byte from memory."""
        addr = addr & 0xFFFF
        if 0x2000 <= addr <= 0x3FFF:
            # PPU registers (mirrored every 8 bytes)
            # Return a default value or simulate minimal PPU behavior
            return 0x00
        elif 0x4000 <= addr <= 0x401F:
            # APU and I/O registers
            return 0x00
        else:
            value = self.memory[addr]
            # print (f"Read {value:02X} from {addr:04X}")
            return value

    def _write_byte(self, addr, data):
        """Writes a byte to memory."""
        addr = addr & 0xFFFF
        data = data & 0xFF

        # print (f"Write {data:02X} to {addr:04X}")

        if 0x2000 <= addr <= 0x3FFF:
            # PPU registers (mirrored every 8 bytes)
            pass  # Ignore writes or simulate minimal PPU behavior
        elif 0x4000 <= addr <= 0x401F:
            # APU and I/O registers
            pass  # Ignore writes or simulate minimal APU behavior
        else:
            self.memory[addr] = data

    def _read_word(self, addr):
        """Reads a word (two bytes) from memory with zero page wraparound."""
        lo = self._read_byte(addr)
        hi = self._read_byte((addr + 1) & 0xFFFF)
        return (hi << 8) | lo

    def _push(self, value):
        """Pushes a byte onto the stack."""
        # print (f"Pushing {value:02X} onto stack at {0x0100 + self.SP:04X}")
        self._write_byte(0x0100 + self.SP, value)
        self.SP = (self.SP - 1) & 0xFF
        # print (f"Stack Pointer after push: {self.SP:02X}")

    def _pop(self):
        """Pops a byte from the stack."""
        self.SP = (self.SP + 1) & 0xFF
        return self._read_byte(0x0100 + self.SP)

    def _set_flags(self, value):
        """Sets the Zero and Negative flags based on the value."""
        self.Z = (value == 0)
        self.N = (value & 0x80) != 0   

    def _get_status(self):
        """Constructs the status register byte."""
        return (
            self.C |
            (self.Z << 1) |
            (self.I << 2) |
            (self.D << 3) |  # Always 0 in Ricoh 2A03
            (self.B << 4) |
            (self.U << 5) |
            (self.V << 6) |
            (self.N << 7)
        )

    def _set_status(self, value):
        """Sets the status flags from a byte."""
        self.C = value & 1
        self.Z = (value >> 1) & 1
        self.I = (value >> 2) & 1
        self.D = (value >> 3) & 1  # Ignored in Ricoh 2A03
        # self.B = (value >> 4) & 1
        self.U = 1 # (value >> 5) & 1
        self.V = (value >> 6) & 1
        self.N = (value >> 7) & 1

        # Update our P flag which stores a combined view of our flags.
        # self.P = self._get_status()

    def step(self):
        current_pc = self.PC
        opcode = self._read_byte(current_pc)

        status = self._get_status()
        print(f"About to execute opcode: {opcode:02X} at PC: {current_pc:04X},  A: {self.A:02X},  X: {self.X:02X},  Y: {self.Y:02X}, P: {status:02X}, SP: {self.SP:02X}")

        self.PC += 1  # Prepare PC for the next instruction's address
        instruction = self._decode_opcode(opcode)
        instruction()  # Execute the instruction

    def _decode_opcode(self, opcode):
        """Decodes the opcode to an instruction method."""
        opcode_map = {
            # LDA
            0xA9: self._LDA_immediate,
            0xA5: self._LDA_zero_page,
            0xB5: self._LDA_zero_page_x,
            0xAD: self._LDA_absolute,
            0xBD: self._LDA_absolute_x,
            0xB9: self._LDA_absolute_y,
            0xA1: self._LDA_indirect_x,
            0xB1: self._LDA_indirect_y,
            # STA
            0x85: self._STA_zero_page,
            0x95: self._STA_zero_page_x,
            0x8D: self._STA_absolute,
            0x9D: self._STA_absolute_x,
            0x99: self._STA_absolute_y,
            0x81: self._STA_indirect_x,
            0x91: self._STA_indirect_y,
            # INX
            0xE8: self._INX,
            # DEX
            0xCA: self._DEX,
            # INY
            0xC8: self._INY,
            # DEY
            0x88: self._DEY,
            # JMP
            0x4C: self._JMP_absolute,
            0x6C: self._JMP_indirect,
            # JSR and RTS
            0x20: self._JSR,
            0x60: self._RTS,
            # Branch Instructions
            0x10: self._BPL,
            0x30: self._BMI,
            0x50: self._BVC,
            0x70: self._BVS,
            0x90: self._BCC,
            0xB0: self._BCS,
            0xD0: self._BNE,
            0xF0: self._BEQ,
            # System Functions
            0x00: self._BRK,
            0x40: self._RTI,
            # Flag Instructions
            0x18: self._CLC,
            0x38: self._SEC,
            0x58: self._CLI,
            0x78: self._SEI,
            0xB8: self._CLV,
            # NOP
            0xEA: self._NOP,
            # Add more opcode mappings as needed...
            0xD8: self._CLD,  # Add this line for CLD
            0xA2: self._LDX_immediate,  # LDX Immediate
            0xA6: self._LDX_zero_page,    # LDX Zero Page
            0xB6: self._LDX_zero_page_y,  # LDX Zero Page,Y
            0xAE: self._LDX_absolute,     # LDX Absolute
            0xBE: self._LDX_absolute_y,   # LDX Absolute,Y
            0xA0: self._LDY_immediate,    # LDY Immediate
            0xA4: self._LDY_zero_page,    # LDY Zero Page
            0xB4: self._LDY_zero_page_x,  # LDY Zero Page,X
            0xAC: self._LDY_absolute,     # LDY Absolute
            0xBC: self._LDY_absolute_x,   # LDY Absolute,X
            0xAA: self._TAX,  # TAX
            0x8A: self._TXA,  # TXA
            0xA8: self._TAY,  # TAY
            0x98: self._TYA,  # TYA
            0x29: self._AND_immediate,  # AND Immediate
            0x9A: self._TXS,  # TXS
            0xBA: self._TSX,  # TSX
            0x48: self._PHA,  # PHA
            0x68: self._PLA,  # PLA
            0x86: self._STX_zero_page,  # STX Zero Page
            # Add other variants of STX as needed
            0x96: self._STX_zero_page_y,  # STX Zero Page,Y
            0x8E: self._STX_absolute,     # STX Absolute
            0x24: self._BIT_zero_page,  # BIT Zero Page
            0x2C: self._BIT_absolute,   # BIT Absolute (if you need to implement it)
            0xF8: self._SED,  # SED
            0x08: self._PHP,  # PHP
            0x28: self._PLP,  # PLP
            0x09: self._ORA_immediate,  # ORA Immediate
            0x05: self._ORA_zero_page,  # ORA Zero Page (if needed)
            0x15: self._ORA_zero_page_x,  # ORA Zero Page,X (if needed)
            0x0D: self._ORA_absolute,   # ORA Absolute (if needed)
            0x1D: self._ORA_absolute_x, # ORA Absolute,X (if needed)
            0x19: self._ORA_absolute_y, # ORA Absolute,Y (if needed)
            0x01: self._ORA_indirect_x, # ORA Indexed Indirect (if needed)
            0x11: self._ORA_indirect_y, # ORA Indirect Indexed (if needed)
            0x49: self._EOR_immediate,  # EOR Immediate
            0x45: self._EOR_zero_page,  # EOR Zero Page
            0x55: self._EOR_zero_page_x,  # EOR Zero Page,X
            0x4D: self._EOR_absolute,   # EOR Absolute
            0x5D: self._EOR_absolute_x, # EOR Absolute,X
            0x59: self._EOR_absolute_y, # EOR Absolute,Y
            0x41: self._EOR_indirect_x, # EOR Indexed Indirect (Indirect,X)
            0x51: self._EOR_indirect_y, # EOR Indirect Indexed (Indirect,Y)
            0x69: self._ADC_immediate,  # ADC Immediate
            0x65: self._ADC_zero_page,  # ADC Zero Page
            0x75: self._ADC_zero_page_x,  # ADC Zero Page,X
            0x6D: self._ADC_absolute,   # ADC Absolute
            0x7D: self._ADC_absolute_x, # ADC Absolute,X
            0x79: self._ADC_absolute_y, # ADC Absolute,Y
            0x61: self._ADC_indirect_x, # ADC Indexed Indirect (Indirect,X)
            0x71: self._ADC_indirect_y, # ADC Indirect Indexed (Indirect,Y)
            0xC0: self._CPY_immediate,  # CPY Immediate
            0xC4: self._CPY_zero_page,  # CPY Zero Page
            0xCC: self._CPY_absolute,   # CPY Absolute
            0xE0: self._CPX_immediate,  # CPX Immediate
            0xE4: self._CPX_zero_page,  # CPX Zero Page
            0xEC: self._CPX_absolute,   # CPX Absolute
            0xE9: self._SBC_immediate,  # SBC Immediate
            0xE5: self._SBC_zero_page,  # SBC Zero Page
            0xF5: self._SBC_zero_page_x,  # SBC Zero Page,X
            0xED: self._SBC_absolute,   # SBC Absolute
            0xFD: self._SBC_absolute_x, # SBC Absolute,X
            0xF9: self._SBC_absolute_y, # SBC Absolute,Y
            0xE1: self._SBC_indirect_x, # SBC Indexed Indirect (Indirect,X)
            0xF1: self._SBC_indirect_y, # SBC Indirect Indexed (Indirect,Y)
            0x4A: self._LSR_accumulator,  # LSR Accumulator
            0x46: self._LSR_zero_page,  # LSR Zero Page
            0x56: self._LSR_zero_page_x,  # LSR Zero Page,X
            0x4E: self._LSR_absolute,   # LSR Absolute
            0x5E: self._LSR_absolute_x, # LSR Absolute,X
            0x0A: self._ASL_accumulator,  # ASL Accumulator
            0x06: self._ASL_zero_page,  # ASL Zero Page
            0x16: self._ASL_zero_page_x,  # ASL Zero Page,X
            0x0E: self._ASL_absolute,   # ASL Absolute
            0x1E: self._ASL_absolute_x, # ASL Absolute,X
            0x6A: self._ROR_accumulator,  # ROR Accumulator
            0x66: self._ROR_zero_page,  # ROR Zero Page
            0x76: self._ROR_zero_page_x,  # ROR Zero Page,X
            0x6E: self._ROR_absolute,   # ROR Absolute
            0x7E: self._ROR_absolute_x, # ROR Absolute,X
            0x2A: self._ROL_accumulator,  # ROL Accumulator
            0x26: self._ROL_zero_page,  # ROL Zero Page
            0x36: self._ROL_zero_page_x,  # ROL Zero Page,X
            0x2E: self._ROL_absolute,   # ROL Absolute
            0x3E: self._ROL_absolute_x, # ROL Absolute,X
            0x21: self._AND_indirect_x,  # AND (Indirect,X)
            0x25: self._AND_zero_page,   # AND Zero Page
            0x29: self._AND_immediate,   # AND Immediate
            0x2D: self._AND_absolute,    # AND Absolute
            0x31: self._AND_indirect_y,  # AND (Indirect,Y)
            0x35: self._AND_zero_page_x, # AND Zero Page,X
            0x39: self._AND_absolute_y,  # AND Absolute,Y
            0x3D: self._AND_absolute_x,  # AND Absolute,X
            0xC1: self._CMP_indirect_x,  # CMP (Indirect,X)
            0xC5: self._CMP_zero_page,   # CMP Zero Page
            0xC9: self._CMP_immediate,   # CMP Immediate
            0xCD: self._CMP_absolute,    # CMP Absolute
            0xD1: self._CMP_indirect_y,  # CMP (Indirect,Y)
            0xD5: self._CMP_zero_page_x, # CMP Zero Page,X
            0xD9: self._CMP_absolute_y,  # CMP Absolute,Y
            0xDD: self._CMP_absolute_x,  # CMP Absolute,X
            0x84: self._STY_zero_page,  # STY Zero Page
            0x94: self._STY_zero_page_x,  # STY Zero Page,X
            0x8C: self._STY_absolute,   # STY Absolute
            0xE6: self._INC_zero_page,  # INC Zero Page
            0xF6: self._INC_zero_page_x,  # INC Zero Page,X
            0xEE: self._INC_absolute,   # INC Absolute
            0xFE: self._INC_absolute_x, # INC Absolute,X
            0xC6: self._DEC_zero_page,  # DEC Zero Page
            0xD6: self._DEC_zero_page_x,  # DEC Zero Page,X
            0xCE: self._DEC_absolute,   # DEC Absolute
            0xDE: self._DEC_absolute_x, # DEC Absolute,X
            0xA7: self._LAX_zero_page,   # LAX Zero Page
            0xAF: self._LAX_absolute,    # LAX Absolute
            0xA3: self._LAX_indirect_x,  # LAX (Indirect,X)
            0xB3: self._LAX_indirect_y,  # LAX (Indirect,Y)
            0xB7: self._LAX_zero_page_y,
            0xBF: self._LAX_absolute_y,        
            0x83: self._SAX_indirect_x,  # Map opcode 0x83 to the SAX (Indirect,X) method   
            0x87: self._SAX_zero_page,    # SAX Zero Page
            0x8F: self._SAX_absolute,     # SAX Absolute
            0x97: self._SAX_zero_page_y,  # SAX Zero Page,Y
            0x9F: self._SAX_absolute_y,   # SAX Absolute,Y
            0xEB: self._SBC_immediate_illegal,    # SBC Immediate

            0xC7: self._DCP_zero_page,       # DCP Zero Page
            0xD7: self._DCP_zero_page_x,     # DCP Zero Page,X
            0xCF: self._DCP_absolute,        # DCP Absolute
            0xDF: self._DCP_absolute_x,      # DCP Absolute,X
            0xDB: self._DCP_absolute_y,      # DCP Absolute,Y
            0xC3: self._DCP_indirect_x,      # DCP (Indirect,X)
            0xD3: self._DCP_indirect_y,      # DCP (Indirect,Y)

            0xE3: self._ISC_indirect_x,    # ISC Indirect,X
            0xE7: self._ISC_zero_page,     # ISC Zero Page
            0xEF: self._ISC_absolute,      # ISC Absolute
            0xF3: self._ISC_indirect_y,    # ISC Indirect,Y
            0xF7: self._ISC_zero_page_x,   # ISC Zero Page,X
            0xFB: self._ISC_absolute_y,    # ISC Absolute,Y
            0xFF: self._ISC_absolute_x,    # ISC Absolute,X

            0x07: self._SLO_zero_page,
            0x17: self._SLO_zero_page_x,
            0x0F: self._SLO_absolute,
            0x1F: self._SLO_absolute_x,
            0x1B: self._SLO_absolute_y,
            0x03: self._SLO_indirect_x,  # Already defined in previous message
            0x13: self._SLO_indirect_y,

            0x23: self._RLA_indirect_x,  # RLA (Indirect,X)
            0x27: self._RLA_zero_page,
            0x37: self._RLA_zero_page_x,
            0x2F: self._RLA_absolute,
            0x3F: self._RLA_absolute_x,
            0x3B: self._RLA_absolute_y,
            0x33: self._RLA_indirect_y,

            0x43: self._SRE_indirect_x,
            0x47: self._SRE_zero_page,
            0x57: self._SRE_zero_page_x,
            0x4F: self._SRE_absolute,
            0x5F: self._SRE_absolute_x,
            0x5B: self._SRE_absolute_y,
            0x53: self._SRE_indirect_y,

            0x63: self._RRA_indirect_x,
            0x67: self._RRA_zero_page,
            0x73: self._RRA_indirect_y,
            0x77: self._RRA_zero_page_x,
            0x6F: self._RRA_absolute,
            0x7B: self._RRA_absolute_y,
            0x7F: self._RRA_absolute_x,
        
            0x04: self._NOP_illegal_1x,  # Treat 04 as illegal NOP
            0x44: self._NOP_illegal_1x,  # Handle 44 as an illegal NOP
            0x64: self._NOP_illegal_1x,  # Handle 64 as an illegal NOP
            0x0C: self._NOP_illegal_2x,  # Handle 0C as an illegal NOP
            0x1C: self._NOP_illegal_2x,  # Handle 1C as an illegal NOP
            0x14: self._NOP_illegal_1x,  # Handle 14 as an illegal NOP
            0x34: self._NOP_illegal_1x,  # Handle 34 as an illegal NOP
            0x54: self._NOP_illegal_1x,  # Handle 54 as an illegal NOP
            0x74: self._NOP_illegal_1x,  # Handle 74 as an illegal NOP
            0xD4: self._NOP_illegal_1x,  # Handle D4 as an illegal NOP
            0xF4: self._NOP_illegal_1x,  # Handle F4 as an illegal NOP
            0x1A: self._NOP_illegal_0x,  # Handle 1A as an illegal NOP
            0x3A: self._NOP_illegal_0x,  # Handle 3A as an illegal NOP
            0x5A: self._NOP_illegal_0x,  # Handle 5A as an illegal NOP
            0x7A: self._NOP_illegal_0x,  # Handle 7A as an illegal NOP
            0xDA: self._NOP_illegal_0x,  # Handle DA as an illegal NOP
            0xFA: self._NOP_illegal_0x,  # Handle FA as an illegal NOP
            0x80: self._NOP_illegal_1x,  # Handle 80 as an illegal NOP
            0x3C: self._NOP_illegal_2x,  # Handle 3C as an illegal NOP
            0x5C: self._NOP_illegal_2x,  # Handle 5C as an illegal NOP
            0x7C: self._NOP_illegal_2x,  # Handle 7C as an illegal NOP
            0xDC: self._NOP_illegal_2x,  # Handle DC as an illegal NOP
            0xFC: self._NOP_illegal_2x,  # Handle FC as an illegal NOP
            # 0xA3: self._NOP_illegal_1x,  # Handle A3 as an illegal NOP
        }
        return opcode_map.get(opcode, self._illegal_opcode)

    def _NOP_illegal_0x(self):
        """Handle the illegal opcode 04 as a NOP (No Operation)."""
        pass

    def _NOP_illegal_1x(self):
        """Handle the illegal opcode 04 as a NOP (No Operation)."""
        self.PC += 1  # Increment program counter if necessary, depending on actual behavior.

    def _NOP_illegal_2x(self):
        """Handle the illegal opcode 04 as a NOP (No Operation)."""
        self.PC += 2  # Increment program counter if necessary, depending on actual behavior.

    def _NOP_illegal_3x(self):
        """Handle the illegal opcode 04 as a NOP (No Operation)."""
        self.PC += 3  # Increment program counter if necessary, depending on actual behavior.

    def _illegal_opcode(self):
        """Handle illegal opcodes."""
        self.PC +=1 
        print (f"Illegal opcode {self.memory[self.PC - 1]:02X} at {self.PC - 1:04X}")
        # opcode = self.memory[self.PC - 1]
        # raise NotImplementedError(f"Illegal opcode {opcode:02X} at {self.PC - 1:04X}")

    def _zero_page(self):
        addr = self._read_byte(self.PC)
        self.PC += 1
        return addr

    def _zero_page_x(self):
        addr = (self._read_byte(self.PC) + self.X) & 0xFF
        self.PC += 1
        return addr

    def _zero_page_y(self):
        addr = (self._read_byte(self.PC) + self.Y) & 0xFF
        self.PC += 1
        return addr
    
    def _compare(self, reg, value):
        result = reg - value
        self.C = int(reg >= value)
        self.Z = int(result == 0)
        self.N = (result >> 7) & 1

    def _read_word_zero_page(self, addr):
        """Read a 16-bit address from zero-page, wrapping around the zero-page if necessary."""
        lo = self._read_byte(addr)
        hi = self._read_byte((addr + 1) & 0xFF)  # Wrap around zero-page
        return (hi << 8) | lo


    # Instruction implementations

    def _RRA_indirect_x(self):
        addr = self._indirect_x()  # Get the effective address
        value = self._read_byte(addr)  # Read the value from memory
        # Rotate right through carry
        old_carry = self.C
        self.C = value & 0x01
        value = (value >> 1) | (old_carry << 7)
        self._write_byte(addr, value)  # Write the modified value back to memory
        # Add with carry
        self._adc(value)

    def _RRA_zero_page(self):
        addr = self._zero_page()
        value = self._read_byte(addr)
        old_carry = self.C
        self.C = value & 0x01
        value = (value >> 1) | (old_carry << 7)
        self._write_byte(addr, value)
        self._adc(value)


    def _RRA_zero_page_x(self):
        addr = self._zero_page_x()
        value = self._read_byte(addr)
        old_carry = self.C
        self.C = value & 0x01
        value = (value >> 1) | (old_carry << 7)
        self._write_byte(addr, value)
        self._adc(value)


    def _RRA_absolute(self):
        addr = self._absolute()
        value = self._read_byte(addr)
        old_carry = self.C
        self.C = value & 0x01
        value = (value >> 1) | (old_carry << 7)
        self._write_byte(addr, value)
        self._adc(value)


    def _RRA_absolute_x(self):
        addr = self._absolute_x()
        value = self._read_byte(addr)
        old_carry = self.C
        self.C = value & 0x01
        value = (value >> 1) | (old_carry << 7)
        self._write_byte(addr, value)
        self._adc(value)


    def _RRA_absolute_y(self):
        addr = self._absolute_y()
        value = self._read_byte(addr)
        old_carry = self.C
        self.C = value & 0x01
        value = (value >> 1) | (old_carry << 7)
        self._write_byte(addr, value)
        self._adc(value)


    def _RRA_indirect_y(self):
        addr = self._indirect_y()
        value = self._read_byte(addr)
        old_carry = self.C
        self.C = value & 0x01
        value = (value >> 1) | (old_carry << 7)
        self._write_byte(addr, value)
        self._adc(value)





    def _SRE_indirect_x(self):
        addr = self._indirect_x()
        value = self._read_byte(addr)
        self.C = value & 0x01  # Set carry to the last bit of the value before shift
        value >>= 1
        self._write_byte(addr, value)
        self.A ^= value
        self._set_flags(self.A)

    def _SRE_zero_page(self):
        addr = self._zero_page()
        value = self._read_byte(addr)
        self.C = value & 0x01
        value >>= 1
        self._write_byte(addr, value)
        self.A ^= value
        self._set_flags(self.A)


    def _SRE_zero_page_x(self):
        addr = self._zero_page_x()
        value = self._read_byte(addr)
        self.C = value & 0x01
        value >>= 1
        self._write_byte(addr, value)
        self.A ^= value
        self._set_flags(self.A)


    def _SRE_absolute(self):
        addr = self._absolute()
        value = self._read_byte(addr)
        self.C = value & 0x01
        value >>= 1
        self._write_byte(addr, value)
        self.A ^= value
        self._set_flags(self.A)


    def _SRE_absolute_x(self):
        addr = self._absolute_x()
        value = self._read_byte(addr)
        self.C = value & 0x01
        value >>= 1
        self._write_byte(addr, value)
        self.A ^= value
        self._set_flags(self.A)


    def _SRE_absolute_y(self):
        addr = self._absolute_y()
        value = self._read_byte(addr)
        self.C = value & 0x01
        value >>= 1
        self._write_byte(addr, value)
        self.A ^= value
        self._set_flags(self.A)


    def _SRE_indirect_y(self):
        addr = self._indirect_y()
        value = self._read_byte(addr)
        self.C = value & 0x01
        value >>= 1
        self._write_byte(addr, value)
        self.A ^= value
        self._set_flags(self.A)





    def _RLA_indirect_x(self):
        addr = self._indirect_x()
        value = self._read_byte(addr)
        old_carry = self.C
        self.C = (value >> 7) & 1  # Capture the old bit 7 to carry
        value = ((value << 1) | old_carry) & 0xFF  # Rotate left through carry
        self._write_byte(addr, value)  # Write the rotated value back to memory
        self.A &= value  # AND operation with the accumulator
        self._set_flags(self.A)  # Update the flags based on the new value in the accumulator

    def _RLA_zero_page(self):
        addr = self._zero_page()
        value = self._read_byte(addr)
        old_carry = self.C
        self.C = (value >> 7) & 1
        value = ((value << 1) | old_carry) & 0xFF
        self._write_byte(addr, value)
        self.A &= value
        self._set_flags(self.A)


    def _RLA_zero_page_x(self):
        addr = self._zero_page_x()
        value = self._read_byte(addr)
        old_carry = self.C
        self.C = (value >> 7) & 1
        value = ((value << 1) | old_carry) & 0xFF
        self._write_byte(addr, value)
        self.A &= value
        self._set_flags(self.A)


    def _RLA_absolute(self):
        addr = self._absolute()
        value = self._read_byte(addr)
        old_carry = self.C
        self.C = (value >> 7) & 1
        value = ((value << 1) | old_carry) & 0xFF
        self._write_byte(addr, value)
        self.A &= value
        self._set_flags(self.A)


    def _RLA_absolute_x(self):
        addr = self._absolute_x()
        value = self._read_byte(addr)
        old_carry = self.C
        self.C = (value >> 7) & 1
        value = ((value << 1) | old_carry) & 0xFF
        self._write_byte(addr, value)
        self.A &= value
        self._set_flags(self.A)


    def _RLA_absolute_y(self):
        addr = self._absolute_y()
        value = self._read_byte(addr)
        old_carry = self.C
        self.C = (value >> 7) & 1
        value = ((value << 1) | old_carry) & 0xFF
        self._write_byte(addr, value)
        self.A &= value
        self._set_flags(self.A)


    def _RLA_indirect_y(self):
        addr = self._indirect_y()
        value = self._read_byte(addr)
        old_carry = self.C
        self.C = (value >> 7) & 1
        value = ((value << 1) | old_carry) & 0xFF
        self._write_byte(addr, value)
        self.A &= value
        self._set_flags(self.A)


    def _SLO_zero_page(self):
        addr = self._zero_page()
        value = self._read_byte(addr)
        self.C = (value >> 7) & 1
        value = (value << 1) & 0xFF
        self._write_byte(addr, value)
        self.A |= value
        self._set_flags(self.A)

    def _SLO_zero_page_x(self):
        addr = self._zero_page_x()
        value = self._read_byte(addr)
        self.C = (value >> 7) & 1
        value = (value << 1) & 0xFF
        self._write_byte(addr, value)
        self.A |= value
        self._set_flags(self.A)


    def _SLO_absolute(self):
        addr = self._absolute()
        value = self._read_byte(addr)
        self.C = (value >> 7) & 1
        value = (value << 1) & 0xFF
        self._write_byte(addr, value)
        self.A |= value
        self._set_flags(self.A)


    def _SLO_absolute_x(self):
        addr = self._absolute_x()
        value = self._read_byte(addr)
        self.C = (value >> 7) & 1
        value = (value << 1) & 0xFF
        self._write_byte(addr, value)
        self.A |= value
        self._set_flags(self.A)


    def _SLO_absolute_y(self):
        addr = self._absolute_y()
        value = self._read_byte(addr)
        self.C = (value >> 7) & 1
        value = (value << 1) & 0xFF
        self._write_byte(addr, value)
        self.A |= value
        self._set_flags(self.A)


    def _SLO_indirect_y(self):
        addr = self._indirect_y()
        value = self._read_byte(addr)
        self.C = (value >> 7) & 1
        value = (value << 1) & 0xFF
        self._write_byte(addr, value)
        self.A |= value
        self._set_flags(self.A)

    def _SLO_indirect_x(self):
        addr = self._indirect_x()
        value = self._read_byte(addr)
        self.C = (value >> 7) & 1  # Carry flag is set to the original bit 7
        value = (value << 1) & 0xFF  # Perform the ASL operation
        self._write_byte(addr, value)  # Write the shifted value back to memory
        self.A |= value  # OR the accumulator with the shifted value
        self._set_flags(self.A)  # Set the flags based on the result


    def _ISC_zero_page(self):
        addr = self._zero_page()
        value = (self._read_byte(addr) + 1) & 0xFF
        self._write_byte(addr, value)
        self._sbc(value)

    def _ISC_zero_page_x(self):
        addr = self._zero_page_x()
        value = (self._read_byte(addr) + 1) & 0xFF
        self._write_byte(addr, value)
        self._sbc(value)

    def _ISC_absolute(self):
        addr = self._absolute()
        value = (self._read_byte(addr) + 1) & 0xFF
        self._write_byte(addr, value)
        self._sbc(value)

    def _ISC_absolute_x(self):
        addr = self._absolute_x()
        value = (self._read_byte(addr) + 1) & 0xFF
        self._write_byte(addr, value)
        self._sbc(value)

    def _ISC_absolute_y(self):
        addr = self._absolute_y()
        value = (self._read_byte(addr) + 1) & 0xFF
        self._write_byte(addr, value)
        self._sbc(value)

    def _ISC_indirect_x(self):
        addr = self._indirect_x()
        value = (self._read_byte(addr) + 1) & 0xFF
        self._write_byte(addr, value)
        self._sbc(value)

    def _ISC_indirect_y(self):
        addr = self._indirect_y()
        value = (self._read_byte(addr) + 1) & 0xFF
        self._write_byte(addr, value)
        self._sbc(value)


    def _DCP_zero_page(self):
        addr = self._zero_page()  # Fetch the zero-page address
        value = self._read_byte(addr)  # Read the value from the specified address
        decremented_value = (value - 1) & 0xFF  # Decrement the value and ensure it wraps around 0xFF
        self._write_byte(addr, decremented_value)  # Write the decremented value back to the same address
        self._compare(self.A, decremented_value)  # Compare the accumulator with the decremented value

    def _DCP_zero_page_x(self):
        addr = self._zero_page_x()  # Calculate the zero-page address offset by X
        value = self._read_byte(addr)  # Read the current value from the calculated address
        decremented_value = (value - 1) & 0xFF  # Decrement the value and ensure it wraps around at 0xFF
        self._write_byte(addr, decremented_value)  # Write the decremented value back to memory at the same address
        self._compare(self.A, decremented_value)  # Compare the decremented value with the accumulator

    def _DCP_absolute(self):
        addr = self._absolute()
        value = (self._read_byte(addr) - 1) & 0xFF
        self._write_byte(addr, value & 0xFF)
        self._compare(self.A, value)

    def _DCP_absolute_x(self):
        addr = self._absolute_x()
        value = (self._read_byte(addr) - 1) & 0xFF
        self._write_byte(addr, value & 0xFF)
        self._compare(self.A, value)


    def _DCP_absolute_y(self):
        addr = self._absolute_y()
        value = (self._read_byte(addr) - 1) & 0xFF
        self._write_byte(addr, value & 0xFF)
        self._compare(self.A, value)


    def _DCP_indirect_x(self):
        addr = self._indirect_x()  # Calculate the effective address using indirect indexed addressing
        value = self._read_byte(addr)  # Read the current value from the effective address
        decremented_value = (value - 1) & 0xFF  # Decrement the value and wrap around with 0xFF
        self._write_byte(addr, decremented_value)  # Write the decremented value back to the same address
        self._compare(self.A, decremented_value)  # Compare the decremented value with the accumulator

    def _DCP_indirect_y(self):
        addr = self._indirect_y()
        value = (self._read_byte(addr) - 1) & 0xFF
        self._write_byte(addr, value & 0xFF)
        self._compare(self.A, value)

    def _SAX_absolute_y(self):
        # Fetch the absolute address from the next two bytes
        base = self._read_word(self.PC)
        self.PC += 2  # Advance the program counter past the address bytes

        # Calculate the effective address by adding Y
        addr = (base + self.Y) & 0xFFFF  # Ensure address wraps around memory map

        # Compute the value to store: bitwise AND of A and X
        value_to_store = self.A & self.X

        # Write the value to the computed address
        self._write_byte(addr, value_to_store)

    def _SBC_immediate_illegal(self):
        # Fetch the immediate value (the next byte in the program)
        value = self._read_byte(self.PC)
        self.PC += 1  # Move the program counter past the immediate value

        # Perform the subtraction with carry
        self._sbc(value)
        
    def _SAX_zero_page_y(self):
        # Fetch the zero page address from the next byte after the opcode and add Y to it
        base_addr = self._read_byte(self.PC)
        self.PC += 1  # Increment the program counter to move past the address byte
        
        # Calculate the zero page address, adding Y and wrapping around 0xFF
        addr = (base_addr + self.Y) & 0xFF
        
        # Compute the value to store: the bitwise AND of A and X
        value_to_store = self.A & self.X
        
        # Write the computed value to the calculated zero page address
        self._write_byte(addr, value_to_store)
        
    def _SAX_absolute(self):
        # Fetch the absolute address from the next two bytes in the program counter
        addr = self._read_word(self.PC)
        self.PC += 2  # Increment program counter to move past the two address bytes

        # Compute the value to store: the bitwise AND of A and X
        value_to_store = self.A & self.X

        # Write the computed value to the absolute address
        self._write_byte(addr, value_to_store)
        
    def _SAX_zero_page(self):
        # Fetch the zero-page address from the next byte in the program counter
        addr = self._read_byte(self.PC)
        self.PC += 1  # Increment program counter to move past the address byte

        # Compute the value to store: the bitwise AND of A and X
        value_to_store = self.A & self.X

        # Write the computed value to the zero-page address
        self._write_byte(addr, value_to_store)

    def _SAX_indirect_x(self):
        # Fetch the zero-page address to start from, then add X to it for indirect indexing
        zero_page_address = self._read_byte(self.PC)
        self.PC += 1  # Increment program counter to move past the byte used for addressing
        effective_address = (zero_page_address + self.X) & 0xFF  # Wrap around zero page
        addr = self._read_word_zero_page(effective_address)  # Fetch the address stored at that zero-page location

        # Compute the value to store: the bitwise AND of A and X
        value_to_store = self.A & self.X

        # Write the computed value to the effective address
        self._write_byte(addr, value_to_store)
        
    def _LAX_absolute_y(self):
        # Calculate the absolute address from the next two program bytes and add the Y register
        base_addr = self._read_word(self.PC)
        self.PC += 2  # Move program counter past the two bytes of the address
        addr = (base_addr + self.Y) & 0xFFFF  # Ensure correct wrapping for 16-bit addresses

        value = self._read_byte(addr)  # Read the value from memory at the calculated address

        # Load the fetched value into both the accumulator (A) and the X register
        self.A = value
        self.X = value

        # Update the processor status flags based on the loaded value
        self._set_flags(value)
        
    def _LAX_zero_page_y(self):
        # Fetch zero-page address from next program byte and add Y with zero-page wrapping
        addr = (self._read_byte(self.PC) + self.Y) & 0xFF
        self.PC += 1  # Increment program counter after reading the address
        value = self._read_byte(addr)  # Read the value from the computed address

        # Load the value into both the accumulator (A) and the X register
        self.A = value
        self.X = value

        # Update the processor status flags based on the loaded value
        self._set_flags(value)
        
    def _LAX_indirect_y(self):
        addr = self._indirect_y()  # Calculates the effective address using indirect indexed addressing with Y
        value = self._read_byte(addr)  # Reads the value from the calculated address
        self.A = value  # Loads the value into the Accumulator
        self.X = value  # Also loads the value into the X register
        self._set_flags(value)  # Sets the processor flags based on the loaded value
        
    def _LAX_indirect_x(self):
        addr = self._indirect_x()
        value = self._read_byte(addr)
        self.A = value
        self.X = value
        self._set_flags(value)
        
    def _LAX_zero_page(self):
        addr = self._zero_page()
        value = self._read_byte(addr)
        self.A = value
        self.X = value
        self._set_flags(value)

    def _LAX_absolute(self):
        addr = self._absolute()
        value = self._read_byte(addr)
        self.A = value
        self.X = value
        self._set_flags(value)
        
    def _DEC_zero_page(self):
        """DEC Zero Page - Decrement the value in zero page memory location."""
        addr = self._zero_page()  # Fetch the zero page address
        value = self._read_byte(addr)  # Read the current value from memory
        value = (value - 1) & 0xFF  # Decrement the value and ensure it wraps at 0xFF
        self._write_byte(addr, value)  # Write the decremented value back to memory
        self._set_flags(value)  # Update the zero and negative flags based on the new value

    def _DEC_zero_page_x(self):
        """DEC Zero Page,X - Decrement the value in zero page memory location offset by X."""
        addr = self._zero_page_x()  # Fetch the zero page address offset by X
        value = self._read_byte(addr)  # Read the current value from memory
        value = (value - 1) & 0xFF  # Decrement the value and wrap at 0xFF
        self._write_byte(addr, value)  # Write back the decremented value
        self._set_flags(value)  # Update flags


    def _DEC_absolute(self):
        """DEC Absolute - Decrement the value in an absolute memory location."""
        addr = self._absolute()  # Fetch the absolute address
        value = self._read_byte(addr)  # Read the current value from memory
        value = (value - 1) & 0xFF  # Decrement the value and wrap at 0xFF
        self._write_byte(addr, value)  # Write back the decremented value
        self._set_flags(value)  # Update flags


    def _DEC_absolute_x(self):
        """DEC Absolute,X - Decrement the value in an absolute memory location offset by X."""
        addr = self._absolute_x()  # Fetch the absolute address offset by X
        value = self._read_byte(addr)  # Read the current value from memory
        value = (value - 1) & 0xFF  # Increment and wrap at 0xFF
        self._write_byte(addr, value)  # Write back the decremented value
        self._set_flags(value)  # Update flags

    def _INC_zero_page(self):
        """INC Zero Page - Increment the value in zero page memory location."""
        addr = self._zero_page()  # Fetch the zero page address
        value = self._read_byte(addr)  # Read the current value from memory
        value = (value + 1) & 0xFF  # Increment the value and ensure it wraps at 0xFF
        self._write_byte(addr, value)  # Write the incremented value back to memory
        self._set_flags(value)  # Update the zero and negative flags based on the new value


    def _INC_zero_page_x(self):
        """INC Zero Page,X - Increment the value in zero page memory location offset by X."""
        addr = self._zero_page_x()  # Fetch the zero page address offset by X
        value = self._read_byte(addr)  # Read the current value from memory
        value = (value + 1) & 0xFF  # Increment the value and wrap at 0xFF
        self._write_byte(addr, value)  # Write back the incremented value
        self._set_flags(value)  # Update flags


    def _INC_absolute(self):
        """INC Absolute - Increment the value in an absolute memory location."""
        addr = self._absolute()  # Fetch the absolute address
        value = self._read_byte(addr)  # Read the current value from memory
        value = (value + 1) & 0xFF  # Increment the value and wrap at 0xFF
        self._write_byte(addr, value)  # Write back the incremented value
        self._set_flags(value)  # Update flags


    def _INC_absolute_x(self):
        """INC Absolute,X - Increment the value in an absolute memory location offset by X."""
        addr = self._absolute_x()  # Fetch the absolute address offset by X
        value = self._read_byte(addr)  # Read the current value from memory
        value = (value + 1) & 0xFF  # Increment and wrap at 0xFF
        self._write_byte(addr, value)  # Write back the incremented value
        self._set_flags(value)  # Update flags

    def _STY_zero_page(self):
        """STY Zero Page - Store Y register in zero page memory location."""
        addr = self._zero_page()  # Fetch the zero page address
        self._write_byte(addr, self.Y)  # Write the Y register's value to memory

    def _STY_zero_page_x(self):
        """STY Zero Page,X - Store Y register in zero page memory location offset by X."""
        addr = self._zero_page_x()  # Fetch the zero page address offset by X
        self._write_byte(addr, self.Y)  # Write the Y register's value to memory


    def _STY_absolute(self):
        """STY Absolute - Store Y register in an absolute memory location."""
        addr = self._absolute()  # Fetch the absolute address
        self._write_byte(addr, self.Y)  # Write the Y register's value to memory

    def _CMP_indirect_x(self):
        """CMP (Indirect,X) - Compare memory value with accumulator using indexed indirect addressing."""
        addr = self._indirect_x()
        value = self._read_byte(addr)
        self._compare(self.A, value)

    def _CMP_immediate(self):
        value = self._immediate()
        self._compare(self.A, value)


    def _CMP_zero_page(self):
        addr = self._zero_page()
        value = self._read_byte(addr)
        self._compare(self.A, value)


    def _CMP_zero_page_x(self):
        addr = self._zero_page_x()
        value = self._read_byte(addr)
        self._compare(self.A, value)


    def _CMP_absolute(self):
        addr = self._absolute()
        value = self._read_byte(addr)
        self._compare(self.A, value)


    def _CMP_absolute_x(self):
        addr = self._absolute_x()
        value = self._read_byte(addr)
        self._compare(self.A, value)


    def _CMP_absolute_y(self):
        addr = self._absolute_y()
        value = self._read_byte(addr)
        self._compare(self.A, value)


    def _CMP_indirect_x(self):
        addr = self._indirect_x()
        value = self._read_byte(addr)
        self._compare(self.A, value)


    def _CMP_indirect_y(self):
        addr = self._indirect_y()
        value = self._read_byte(addr)
        self._compare(self.A, value)

    def _AND_indirect_x(self):
        """AND (Indirect,X) - Logical AND between the accumulator and a memory location calculated with (Indirect,X)."""
        addr = self._indirect_x()
        value = self._read_byte(addr)
        self.A &= value
        self._set_flags(self.A)

    def _AND_zero_page(self):
        addr = self._zero_page()
        value = self._read_byte(addr)
        self.A &= value
        self._set_flags(self.A)

    def _AND_zero_page_x(self):
        addr = self._zero_page_x()
        value = self._read_byte(addr)
        self.A &= value
        self._set_flags(self.A)


    def _AND_absolute(self):
        addr = self._absolute()
        value = self._read_byte(addr)
        self.A &= value
        self._set_flags(self.A)


    def _AND_absolute_x(self):
        addr = self._absolute_x()
        value = self._read_byte(addr)
        self.A &= value
        self._set_flags(self.A)

    def _AND_absolute_y(self):
        addr = self._absolute_y()
        value = self._read_byte(addr)
        self.A &= value
        self._set_flags(self.A)

    def _AND_indirect_x(self):
        addr = self._indirect_x()
        value = self._read_byte(addr)
        self.A &= value
        self._set_flags(self.A)

    def _AND_indirect_y(self):
        addr = self._indirect_y()
        value = self._read_byte(addr)
        self.A &= value
        self._set_flags(self.A)

    def _ROL_accumulator(self):
        """ROL Accumulator - Rotate Left the accumulator."""
        old_carry = self.C
        self.C = (self.A >> 7) & 0x01  # Set the carry flag to the old bit 7
        self.A = ((self.A << 1) | old_carry) & 0xFF  # Rotate left through carry
        self._set_flags(self.A)  # Update the zero and negative flags

    def _ROL_zero_page(self):
        addr = self._zero_page()
        value = self._read_byte(addr)
        old_carry = self.C
        self.C = (value >> 7) & 0x01
        value = ((value << 1) | old_carry) & 0xFF
        self._write_byte(addr, value)
        self._set_flags(value)

    def _ROL_zero_page_x(self):
        addr = self._zero_page_x()
        value = self._read_byte(addr)
        old_carry = self.C
        self.C = (value >> 7) & 0x01
        value = ((value << 1) | old_carry) & 0xFF
        self._write_byte(addr, value)
        self._set_flags(value)

    def _ROL_absolute(self):
        addr = self._absolute()
        value = self._read_byte(addr)
        old_carry = self.C
        self.C = (value >> 7) & 0x01
        value = ((value << 1) | old_carry) & 0xFF
        self._write_byte(addr, value)
        self._set_flags(value)

    def _ROL_absolute_x(self):
        addr = self._absolute_x()
        value = self._read_byte(addr)
        old_carry = self.C
        self.C = (value >> 7) & 0x01
        value = ((value << 1) | old_carry) & 0xFF
        self._write_byte(addr, value)
        self._set_flags(value)

    def _ROR_accumulator(self):
        """ROR Accumulator - Rotate Right the accumulator."""
        old_carry = self.C
        self.C = self.A & 0x01  # Set the carry flag to the old bit 0
        self.A = (self.A >> 1) | (old_carry << 7)  # Rotate right through carry
        self._set_flags(self.A)  # Update the zero and negative flags

    def _ROR_zero_page(self):
        addr = self._zero_page()
        value = self._read_byte(addr)
        old_carry = self.C
        self.C = value & 0x01
        value = (value >> 1) | (old_carry << 7)
        self._write_byte(addr, value)
        self._set_flags(value)

    def _ROR_zero_page_x(self):
        addr = self._zero_page_x()
        value = self._read_byte(addr)
        old_carry = self.C
        self.C = value & 0x01
        value = (value >> 1) | (old_carry << 7)
        self._write_byte(addr, value)
        self._set_flags(value)

    def _ROR_absolute(self):
        addr = self._absolute()
        value = self._read_byte(addr)
        old_carry = self.C
        self.C = value & 0x01
        value = (value >> 1) | (old_carry << 7)
        self._write_byte(addr, value)
        self._set_flags(value)

    def _ROR_absolute_x(self):
        addr = self._absolute_x()
        value = self._read_byte(addr)
        old_carry = self.C
        self.C = value & 0x01
        value = (value >> 1) | (old_carry << 7)
        self._write_byte(addr, value)
        self._set_flags(value)


    def _ASL_accumulator(self):
        """ASL Accumulator - Arithmetic Shift Left the accumulator."""
        self.C = (self.A >> 7) & 0x01  # Set the carry flag to the old bit 7
        self.A = (self.A << 1) & 0xFE  # Perform the shift, ensure bit 0 is 0
        self._set_flags(self.A)  # Update the zero and negative flags

    def _ASL_zero_page(self):
        addr = self._zero_page()
        value = self._read_byte(addr)
        self.C = (value >> 7) & 0x01
        value = (value << 1) & 0xFE
        self._write_byte(addr, value)
        self._set_flags(value)

    def _ASL_zero_page_x(self):
        addr = self._zero_page_x()
        value = self._read_byte(addr)
        self.C = (value >> 7) & 0x01
        value = (value << 1) & 0xFE
        self._write_byte(addr, value)
        self._set_flags(value)

    def _ASL_absolute(self):
        addr = self._absolute()
        value = self._read_byte(addr)
        self.C = (value >> 7) & 0x01
        value = (value << 1) & 0xFE
        self._write_byte(addr, value)
        self._set_flags(value)

    def _ASL_absolute_x(self):
        addr = self._absolute_x()
        value = self._read_byte(addr)
        self.C = (value >> 7) & 0x01
        value = (value << 1) & 0xFE
        self._write_byte(addr, value)
        self._set_flags(value)


    def _LSR_accumulator(self):
        """LSR Accumulator - Logical Shift Right the accumulator."""
        self.C = self.A & 0x01  # Set the carry flag to the old bit 0
        self.A >>= 1  # Perform the shift
        self.A &= 0x7F  # Ensure bit 7 is 0
        self._set_flags(self.A)  # Update the zero and negative flags

    def _LSR_zero_page(self):
        addr = self._zero_page()
        value = self._read_byte(addr)
        self.C = value & 0x01
        value >>= 1
        value &= 0x7F
        self._write_byte(addr, value)
        self._set_flags(value)

    def _LSR_zero_page_x(self):
        addr = self._zero_page_x()
        value = self._read_byte(addr)
        self.C = value & 0x01
        value >>= 1
        value &= 0x7F
        self._write_byte(addr, value)
        self._set_flags(value)

    def _LSR_absolute(self):
        addr = self._absolute()
        value = self._read_byte(addr)
        self.C = value & 0x01
        value >>= 1
        value &= 0x7F
        self._write_byte(addr, value)
        self._set_flags(value)

    def _LSR_absolute_x(self):
        addr = self._absolute_x()
        value = self._read_byte(addr)
        self.C = value & 0x01
        value >>= 1
        value &= 0x7F
        self._write_byte(addr, value)
        self._set_flags(value)

    def _SBC_immediate(self):
        """SBC Immediate - Subtract with carry the accumulator with an immediate value."""
        value = self._immediate()  # Fetch the immediate value
        self._sbc(value)

    def _sbc(self, value):
        """Helper function to perform subtraction with carry."""
        # Perform subtraction with carry; invert the bits of value as SBC uses the complement
        value = 0xFF - value
        temp = self.A + value + self.C
        self.C = 1 if temp > 0xFF else 0  # Update carry
        self.V = 1 if (((self.A ^ temp) & 0x80) != 0 and ((self.A ^ value) & 0x80) == 0) else 0  # Set overflow
        self.A = temp & 0xFF  # Keep A within 0-255
        self._set_flags(self.A)  # Update zero and negative flags

    def _SBC_zero_page(self):
        addr = self._zero_page()
        value = self._read_byte(addr)
        self._sbc(value)

    def _SBC_zero_page_x(self):
        addr = self._zero_page_x()
        value = self._read_byte(addr)
        self._sbc(value)

    def _SBC_absolute(self):
        addr = self._absolute()
        value = self._read_byte(addr)
        self._sbc(value)

    def _SBC_absolute_x(self):
        addr = self._absolute_x()
        value = self._read_byte(addr)
        self._sbc(value)

    def _SBC_absolute_y(self):
        addr = self._absolute_y()
        value = self._read_byte(addr)
        self._sbc(value)

    def _SBC_indirect_x(self):
        addr = self._indirect_x()
        value = self._read_byte(addr)
        self._sbc(value)

    def _SBC_indirect_y(self):
        addr = self._indirect_y()
        value = self._read_byte(addr)
        self._sbc(value)


    def _CPX_immediate(self):
        """CPX Immediate - Compare X register with an immediate value."""
        value = self._immediate()  # Fetch the immediate value
        self._compare(self.X, value)

    def _CPX_zero_page(self):
        addr = self._zero_page()
        value = self._read_byte(addr)
        self._compare(self.X, value)

    def _CPX_absolute(self):
        addr = self._absolute()
        value = self._read_byte(addr)
        self._compare(self.X, value)

    def _CPY_immediate(self):
        """CPY Immediate - Compare Y register with an immediate value."""
        value = self._immediate()  # Fetch the immediate value
        self._compare(self.Y, value)

    def _CPY_zero_page(self):
        addr = self._zero_page()
        value = self._read_byte(addr)
        self._compare(self.Y, value)

    def _CPY_absolute(self):
        addr = self._absolute()
        value = self._read_byte(addr)
        self._compare(self.Y, value)

    def _ADC_immediate(self):
        """ADC Immediate - Add with carry the accumulator with an immediate value."""
        value = self._immediate()  # Fetch the immediate value
        self._adc(value)

    def _adc(self, value):
        # Calculate the sum of the accumulator, value, and the carry bit
        sum = self.A + value + self.C
        # Update the carry flag
        self.C = 1 if sum > 0xFF else 0
        # Adjust for overflow between bit 7 and bit 8
        self.V = 1 if ((self.A ^ value) & 0x80 == 0) and ((self.A ^ sum) & 0x80 != 0) else 0
        # Update accumulator
        self.A = sum & 0xFF
        # Update zero and negative flags
        self._set_flags(self.A)

    def _ADC_zero_page(self):
        addr = self._zero_page()
        value = self._read_byte(addr)
        self._adc(value)

    def _ADC_zero_page_x(self):
        addr = self._zero_page_x()
        value = self._read_byte(addr)
        self._adc(value)

    def _ADC_absolute(self):
        addr = self._absolute()
        value = self._read_byte(addr)
        self._adc(value)

    def _ADC_absolute_x(self):
        addr = self._absolute_x()
        value = self._read_byte(addr)
        self._adc(value)

    def _ADC_absolute_y(self):
        addr = self._absolute_y()
        value = self._read_byte(addr)
        self._adc(value)

    def _ADC_indirect_x(self):
        addr = self._indirect_x()
        value = self._read_byte(addr)
        self._adc(value)

    def _ADC_indirect_y(self):
        addr = self._indirect_y()
        value = self._read_byte(addr)
        self._adc(value)

    def _EOR_immediate(self):
        """EOR Immediate - Exclusive OR the accumulator with an immediate value."""
        value = self._immediate()  # Fetch the immediate value
        self.A ^= value  # Perform bitwise XOR on the accumulator
        self._set_flags(self.A)  # Update the flags based on the result

    def _EOR_zero_page(self):
        addr = self._zero_page()
        value = self._read_byte(addr)
        self.A ^= value
        self._set_flags(self.A)

    def _EOR_zero_page_x(self):
        addr = self._zero_page_x()
        value = self._read_byte(addr)
        self.A ^= value
        self._set_flags(self.A)

    def _EOR_absolute(self):
        addr = self._absolute()
        value = self._read_byte(addr)
        self.A ^= value
        self._set_flags(self.A)

    def _EOR_absolute_x(self):
        addr = self._absolute_x()
        value = self._read_byte(addr)
        self.A ^= value
        self._set_flags(self.A)

    def _EOR_absolute_y(self):
        addr = self._absolute_y()
        value = self._read_byte(addr)
        self.A ^= value
        self._set_flags(self.A)

    def _EOR_indirect_x(self):
        addr = self._indirect_x()
        value = self._read_byte(addr)
        self.A ^= value
        self._set_flags(self.A)

    def _EOR_indirect_y(self):
        addr = self._indirect_y()
        value = self._read_byte(addr)
        self.A ^= value
        self._set_flags(self.A)

    def _ORA_zero_page(self):
        """ORA Zero Page - Logical Inclusive OR with the accumulator."""
        addr = self._zero_page()  # Fetch the zero page address
        value = self._read_byte(addr)  # Read the value from memory
        self.A |= value  # Perform bitwise OR
        self._set_flags(self.A)  # Update flags

    def _ORA_immediate(self):
        """ORA Immediate - Logical Inclusive OR with the accumulator."""
        value = self._immediate()  # Fetch the immediate value
        self.A |= value  # Perform bitwise OR on the accumulator
        self._set_flags(self.A)  # Update the flags based on the result

    def _ORA_zero_page_x(self):
        addr = self._zero_page_x()
        value = self._read_byte(addr)
        self.A |= value
        self._set_flags(self.A)

    def _ORA_absolute(self):
        addr = self._absolute()
        value = self._read_byte(addr)
        self.A |= value
        self._set_flags(self.A)

    def _ORA_absolute_x(self):
        addr = self._absolute_x()
        value = self._read_byte(addr)
        self.A |= value
        self._set_flags(self.A)


    def _ORA_absolute_y(self):
        addr = self._absolute_y()
        value = self._read_byte(addr)
        self.A |= value
        self._set_flags(self.A)

    def _ORA_indirect_x(self):
        addr = self._indirect_x()
        value = self._read_byte(addr)
        self.A |= value
        self._set_flags(self.A)

    def _ORA_indirect_y(self):
        addr = self._indirect_y()
        value = self._read_byte(addr)
        self.A |= value
        self._set_flags(self.A)

    def _PLP(self):
        """PLP - Pull Processor Status from Stack."""
        status = self._pop()  # Retrieve the status from the stack
        # Remove the break flag (bit 4) as per the 6502 behavior
        # print (f"PLP: {status:02X}")
        self._set_status(status & ~0x10)  # Set the processor flags from the retrieved status
        
    def _PHP(self):
        """PHP - Push Processor Status onto Stack."""
        status = self._get_status() | 0x10  # Set the break flag before pushing for PHP
        # print (f"PHP: {status:02X}")
        self._push(status)
        
    def _SED(self):
        """SED - Set Decimal Mode Flag."""
        self.D = 1  # Set the Decimal flag

    def _BIT_zero_page(self):
        """BIT Zero Page - Test bits in memory with accumulator."""
        addr = self._zero_page()  # Fetch the zero page address
        value = self._read_byte(addr)  # Read the value from memory
        test = self.A & value  # AND operation with accumulator
        self.Z = (test == 0)  # Set Zero flag
        self.N = (value & 0x80) != 0  # Set Negative flag from bit 7
        self.V = (value & 0x40) != 0  # Set Overflow flag from bit 6

    def _BIT_absolute(self):
        """BIT Absolute - Test bits in memory with accumulator at an absolute address."""
        addr = self._absolute()  # Fetch the absolute address
        value = self._read_byte(addr)  # Read the value from memory
        test = self.A & value  # AND operation with accumulator
        self.Z = (test == 0)  # Set Zero flag
        self.N = (value & 0x80) != 0  # Set Negative flag from bit 7
        self.V = (value & 0x40) != 0  # Set Overflow flag from bit 6

    def _STX_zero_page_y(self):
        """STX Zero Page,Y - Store X register to zero page address offset by Y."""
        addr = (self._read_byte(self.PC) + self.Y) & 0xFF
        self.PC += 1
        self._write_byte(addr, self.X)

    def _STX_absolute(self):
        """STX Absolute - Store X register to an absolute address."""
        addr = self._absolute()
        self._write_byte(addr, self.X)

    def _STX_zero_page(self):
        """STX Zero Page - Store X register to zero page address."""
        addr = self._zero_page()  # Fetch the zero page address
        self._write_byte(addr, self.X)  # Store the value of X register at the address


    def _PLA(self):
        """PLA - Pull Accumulator from Stack."""
        self.A = self._pop()
        self._set_flags(self.A)  # Typically updates Zero and Negative flags
        
    def _PHA(self):
        """PHA - Push Accumulator onto Stack."""
        self._push(self.A)
        
    def _TSX(self):
        """TSX - Transfer Stack Pointer to X Register."""
        self.X = self.SP
        self._set_flags(self.X)  # Typically updates Zero and Negative flags
        
    def _TXS(self):
        """TXS - Transfer X Register to Stack Pointer."""
        self.SP = self.X
        
    def _AND_immediate(self):
        value = self._immediate()
        self.A &= value
        self._set_flags(self.A)
        
    def _CMP_immediate(self):
        value = self._immediate()
        self._compare(self.A, value)

    def _TAX(self):
        self.X = self.A
        self._set_flags(self.X)

    def _TXA(self):
        self.A = self.X
        self._set_flags(self.A)

    def _TAY(self):
        self.Y = self.A
        self._set_flags(self.Y)

    def _TYA(self):
        self.A = self.Y
        self._set_flags(self.A)

    def _LDY_immediate(self):
        value = self._immediate()
        self.Y = value
        self._set_flags(self.Y)

    def _LDY_zero_page(self):
        addr = self._zero_page()
        self.Y = self._read_byte(addr)
        self._set_flags(self.Y)

    def _LDY_zero_page_x(self):
        addr = self._zero_page_x()
        self.Y = self._read_byte(addr)
        self._set_flags(self.Y)

    def _LDY_absolute(self):
        addr = self._absolute()
        self.Y = self._read_byte(addr)
        self._set_flags(self.Y)

    def _LDY_absolute_x(self):
        addr = self._absolute_x()
        self.Y = self._read_byte(addr)
        self._set_flags(self.Y)


    def _LDX_zero_page(self):
        addr = self._zero_page()
        self.X = self._read_byte(addr)
        self._set_flags(self.X)

    def _LDX_zero_page_y(self):
        addr = self._zero_page_y()
        self.X = self._read_byte(addr)
        self._set_flags(self.X)

    def _LDX_absolute(self):
        addr = self._absolute()
        self.X = self._read_byte(addr)
        self._set_flags(self.X)

    def _LDX_absolute_y(self):
        addr = self._absolute_y()
        self.X = self._read_byte(addr)
        self._set_flags(self.X)


    def _CLD(self):
        """CLD - Clear Decimal Mode."""
        self.D = 0  # Clear the Decimal flag

    def _LDX_immediate(self):
        """LDX Immediate - Load X Register with Immediate Value."""
        value = self._immediate()
        self.X = value
        self._set_flags(self.X)

    # Load and Store Instructions
    def _LDA_immediate(self):
        value = self._immediate()
        self.A = value
        self._set_flags(self.A)

    def _LDA_zero_page(self):
        addr = self._zero_page()
        self.A = self._read_byte(addr)
        self._set_flags(self.A)

    def _LDA_zero_page_x(self):
        addr = self._zero_page_x()
        self.A = self._read_byte(addr)
        self._set_flags(self.A)

    def _LDA_absolute(self):
        """LDA Absolute - Load accumulator from absolute address."""
        addr = self._absolute()
        self.A = self._read_byte(addr)
        self._set_flags(self.A)

    def _LDA_absolute_x(self):
        addr = self._absolute_x()
        self.A = self._read_byte(addr)
        self._set_flags(self.A)

    def _LDA_absolute_y(self):
        addr = self._absolute_y()
        self.A = self._read_byte(addr)
        self._set_flags(self.A)

    def _LDA_indirect_x(self):
        addr = self._indirect_x()
        self.A = self._read_byte(addr)
        self._set_flags(self.A)

    def _LDA_indirect_y(self):
        addr = self._indirect_y()
        self.A = self._read_byte(addr)
        self._set_flags(self.A)

    def _STA_zero_page(self):
        addr = self._zero_page()
        self._write_byte(addr, self.A)

    def _STA_zero_page_x(self):
        addr = self._zero_page_x()
        self._write_byte(addr, self.A)

    def _STA_absolute(self):
        addr = self._absolute()
        self._write_byte(addr, self.A)

    def _STA_absolute_x(self):
        addr = self._absolute_x()
        self._write_byte(addr, self.A)

    def _STA_absolute_y(self):
        addr = self._absolute_y()
        self._write_byte(addr, self.A)

    def _STA_indirect_x(self):
        addr = self._indirect_x()
        self._write_byte(addr, self.A)

    def _STA_indirect_y(self):
        addr = self._indirect_y()
        self._write_byte(addr, self.A)

    # Increment and Decrement Instructions
    def _INX(self):
        self.X = (self.X + 1) & 0xFF
        self._set_flags(self.X)

    def _DEX(self):
        self.X = (self.X - 1) & 0xFF
        self._set_flags(self.X)

    def _INY(self):
        self.Y = (self.Y + 1) & 0xFF
        self._set_flags(self.Y)

    def _DEY(self):
        self.Y = (self.Y - 1) & 0xFF
        self._set_flags(self.Y)

    # Jump and Call Instructions
    def _JMP_absolute(self):
        addr = self._absolute()
        self.PC = addr

    def _JMP_indirect(self):
        addr = self._indirect()
        self.PC = addr

    def _JSR(self):
        addr = self._absolute()
        self.PC -= 1
        self._push((self.PC >> 8) & 0xFF)
        self._push(self.PC & 0xFF)
        self.PC = addr

    def _RTS(self):
        lo = self._pop()
        hi = self._pop()
        self.PC = ((hi << 8) | lo) + 1

    # Branch Instructions
    def _BCC(self):
        offset = self._relative()
        if self.C == 0:
            self._branch(offset)

    def _BCS(self):
        offset = self._relative()
        if self.C == 1:
            self._branch(offset)

    def _BEQ(self):
        offset = self._relative()
        if self.Z == 1:
            self._branch(offset)

    def _BNE(self):
        offset = self._relative()
        if self.Z == 0:
            self._branch(offset)

    def _BMI(self):
        offset = self._relative()
        if self.N == 1:
            self._branch(offset)

    def _BPL(self):
        offset = self._relative()
        if self.N == 0:
            self._branch(offset)

    def _BVC(self):
        offset = self._relative()
        if self.V == 0:
            self._branch(offset)

    def _BVS(self):
        offset = self._relative()
        if self.V == 1:
            self._branch(offset)

    def _branch(self, offset):
        self.PC = (self.PC + offset) & 0xFFFF
        # Note: In an accurate emulator, you would account for additional cycles and page crossings.

    # System Functions
    def _BRK(self):
        self.PC += 1
        self._push((self.PC >> 8) & 0xFF)
        self._push(self.PC & 0xFF)
        self.B = 1
        self._push(self._get_status())
        self.I = 1
        self.PC = self._read_word(0xFFFE)

    def _RTI(self):
        self._set_status(self._pop())
        lo = self._pop()
        hi = self._pop()
        self.PC = (hi << 8) | lo

    # Flag Instructions
    def _CLC(self):
        self.C = 0

    def _SEC(self):
        self.C = 1

    def _CLI(self):
        # print("CLI instruction executed")
        self.I = 0

    def _SEI(self):
        # print("SEI instruction executed")
        self.I = 1

    def _CLV(self):
        self.V = 0

    # NOP Instruction
    def _NOP(self):
        pass

    # Addressing Modes
    def _immediate(self):
        value = self._read_byte(self.PC)
        self.PC += 1
        return value

    def _zero_page(self):
        addr = self._read_byte(self.PC)
        self.PC += 1
        return addr

    def _zero_page_x(self):
        addr = (self._read_byte(self.PC) + self.X) & 0xFF
        self.PC += 1
        return addr

    def _zero_page_y(self):
        addr = (self._read_byte(self.PC) + self.Y) & 0xFF
        self.PC += 1
        return addr

    def _absolute(self):
        addr = self._read_word(self.PC)
        self.PC += 2
        return addr

    def _absolute_x(self):
        base = self._read_word(self.PC)
        self.PC += 2
        addr = (base + self.X) & 0xFFFF
        return addr

    def _absolute_y(self):
        base = self._read_word(self.PC)
        self.PC += 2
        addr = (base + self.Y) & 0xFFFF
        return addr

    def _indirect(self):
        ptr = self._read_word(self.PC)
        self.PC += 2
        # Simulate page boundary hardware bug for indirect jumps
        if ptr & 0x00FF == 0x00FF:
            lo = self._read_byte(ptr)
            hi = self._read_byte(ptr & 0xFF00)
        else:
            lo = self._read_byte(ptr)
            hi = self._read_byte(ptr + 1)
        return (hi << 8) | lo

    def _indirect_x(self):
        ptr = (self._read_byte(self.PC) + self.X) & 0xFF
        self.PC += 1
        lo = self._read_byte(ptr)
        hi = self._read_byte((ptr + 1) & 0xFF)
        return (hi << 8) | lo

    def _indirect_y(self):
        ptr = self._read_byte(self.PC)
        self.PC += 1
        lo = self._read_byte(ptr)
        hi = self._read_byte((ptr + 1) & 0xFF)
        addr = ((hi << 8) | lo) + self.Y
        return addr & 0xFFFF

    def _relative(self):
        offset = self._read_byte(self.PC)
        self.PC += 1
        if offset & 0x80:
            offset -= 0x100
        return offset