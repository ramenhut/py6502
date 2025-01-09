import sys

# Import the Ricoh2A03 emulator class
from ricoh2a03 import Ricoh2A03

def load_test_rom(filename):
    """Loads the test ROM into memory."""
    with open(filename, 'rb') as f:
        rom_data = f.read()
    return rom_data

def extract_register_value(register, line):
    # Search line for "register:" and extract its value
    start = line.find(register + ":") + len(register) + 1
    end = line.find(" ", start)
    if end == -1:  # If no space is found, take the rest of the line
        end = len(line)
    return line[start:end].strip()

def load_expected_log(log_filename):
    """Loads expected states from a log file."""
    expected_states = []
    with open(log_filename, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if parts:
                expected_states.append({
                    "PC": parts[0],
                    "OP": parts[1],
                    "A": extract_register_value("A", line),
                    "X": extract_register_value("X", line),
                    "Y": extract_register_value("Y", line),
                    "P": extract_register_value("P", line),
                    "SP": extract_register_value("SP", line),
                    "CYC": "IGNORED",
                })
            else:
                print ("Empty line in log file!")
                return
    return expected_states

def initialize_memory(rom_data):
    """Initializes memory and loads the ROM data."""
    memory = [0x00] * 0x10000  # 64KB of memory

    # NES ROMs have a header of 16 bytes; we'll skip it
    header_size = 16
    prg_rom_size = len(rom_data) - header_size
    prg_rom = rom_data[header_size:]

    # Load PRG ROM into $C000-$FFFF
    memory[0xC000:0xC000+prg_rom_size] = prg_rom

    # Set the reset vector to point to $C004 for automatic mode
    memory[0xFFFC] = 0x00
    memory[0xFFFD] = 0xC0

    return memory

def run_test(cpu, expected_states):
    """Runs the test ROM and checks CPU state against expected log."""

    instructions_executed = 0

    while instructions_executed < len(expected_states):
        pc_hex = f"{cpu.PC:04X}"
        op = cpu.memory[cpu.PC]
        
        actual_state = {
            "PC": pc_hex,
            "OP": f"{op:02X}",
            "A": f"{cpu.A:02X}",
            "X": f"{cpu.X:02X}",
            "Y": f"{cpu.Y:02X}",
            "P": f"{cpu._get_status():02X}",
            "SP": f"{cpu.SP:02X}",
            "CYC": "IGNORED"  # Placeholder if cycle exact timing isn't being tested
        }

        expected_state = expected_states[instructions_executed]

        if actual_state != expected_state:
            print(f"Line {instructions_executed} Mismatch at PC={pc_hex}:\n Expected {expected_state},\n   Actual {actual_state}")
            break

        instructions_executed += 1
        cpu.step()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python test.py path_to_test_rom path_to_log")
        sys.exit(1)

    test_rom_path = sys.argv[1]
    log_path = sys.argv[2]

    # Load the test ROM and log
    rom_data = load_test_rom(test_rom_path)
    expected_log = load_expected_log(log_path)

    # Initialize memory with ROM data
    memory = initialize_memory(rom_data)

    # Create CPU instance and reset to initial state
    cpu = Ricoh2A03(memory)
    cpu.reset()

    # Run the test with comparison to expected log
    run_test(cpu, expected_log)
