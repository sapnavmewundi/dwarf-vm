#!/usr/bin/env python3
"""
The DWARF Virtual Machine — Paged Out! Article PoC
====================================================
A hidden Turing-complete stack machine lives inside
the DWARF debug info of every ELF/Mach-O binary.

This script implements a minimal DWARF expression evaluator
and runs a hand-crafted bytecode program that computes
Factorial(5) = 120 using only DWARF opcodes.

HOW TO RUN:
  python3 dwarf_vm.py
"""

import struct

# ===== DWARF OPCODE DEFINITIONS =====
# These are REAL opcodes from the DWARF standard (dwarf.h)
DW_OP_lit0  = 0x30  # Push literal 0
DW_OP_lit1  = 0x31  # Push literal 1
DW_OP_lit5  = 0x35  # Push literal 5
DW_OP_over  = 0x14  # Copy 2nd item on stack to top
DW_OP_swap  = 0x16  # Swap top two stack items
DW_OP_minus = 0x1c  # Pop two, push (second - first)
DW_OP_mul   = 0x1e  # Pop two, push (first * second)
DW_OP_eq    = 0x29  # Pop two, push 1 if equal, else 0
DW_OP_bra   = 0x28  # Pop top; if non-zero, jump by signed offset
DW_OP_skip  = 0x2f  # Unconditional jump by signed offset

# Opcode name lookup for pretty printing
OP_NAMES = {
    0x14: "DW_OP_over", 0x16: "DW_OP_swap",
    0x1c: "DW_OP_minus", 0x1e: "DW_OP_mul",
    0x28: "DW_OP_bra", 0x29: "DW_OP_eq", 0x2f: "DW_OP_skip",
}


def execute_dwarf(bytecode, trace=True):
    """Execute DWARF expression bytecode on a stack machine."""
    stack = []
    pc = 0
    step = 0

    if trace:
        print("=" * 55)
        print("  DWARF Virtual Machine — Execution Trace")
        print("=" * 55)

    while pc < len(bytecode):
        op = bytecode[pc]
        pc += 1
        step += 1

        # Decode opcode name
        if DW_OP_lit0 <= op <= 0x4f:
            name = f"DW_OP_lit{op - DW_OP_lit0}"
        else:
            name = OP_NAMES.get(op, f"UNKNOWN(0x{op:02x})")

        # Execute
        if DW_OP_lit0 <= op <= 0x4f:
            stack.append(op - DW_OP_lit0)

        elif op == DW_OP_over:
            stack.append(stack[-2])

        elif op == DW_OP_swap:
            stack[-1], stack[-2] = stack[-2], stack[-1]

        elif op == DW_OP_minus:
            a, b = stack.pop(), stack.pop()
            stack.append(b - a)

        elif op == DW_OP_mul:
            a, b = stack.pop(), stack.pop()
            stack.append(a * b)

        elif op == DW_OP_eq:
            a, b = stack.pop(), stack.pop()
            stack.append(1 if b == a else 0)

        elif op == DW_OP_skip:
            offset = struct.unpack('<h', bytes(bytecode[pc:pc+2]))[0]
            if trace:
                print(f"  [{step:2d}] {name} {offset:+d}  →  JUMP to PC={pc+2+offset}")
            pc += 2 + offset
            continue

        elif op == DW_OP_bra:
            offset = struct.unpack('<h', bytes(bytecode[pc:pc+2]))[0]
            cond = stack.pop()
            pc += 2
            if trace:
                jump = "YES → JUMP" if cond != 0 else "NO  → continue"
                print(f"  [{step:2d}] {name} (cond={cond}) {jump}")
            if cond != 0:
                pc += offset
            continue

        else:
            raise Exception(f"Unknown opcode: 0x{op:02x}")

        if trace:
            print(f"  [{step:2d}] {name:20s}  →  Stack: {stack}")

    return stack


# ===== HAND-CRAFTED DWARF BYTECODE: FACTORIAL(5) =====
#
# Algorithm:
#   N = 5, Acc = 1
#   LOOP:
#     if N == 0: exit
#     Acc = Acc * N
#     N = N - 1
#     goto LOOP
#   Result: Acc = 120
#
factorial_program = [
    DW_OP_lit5,             # [0]  Push N = 5
    DW_OP_lit1,             # [1]  Push Acc = 1
    # --- LOOP START (PC=2) ---
    DW_OP_over,             # [2]  Copy N to top
    DW_OP_lit0,             # [3]  Push 0
    DW_OP_eq,               # [4]  N == 0 ?
    DW_OP_bra, 0x09, 0x00,  # [5]  If yes, jump +9 → exit (PC=17)
    DW_OP_over,             # [8]  Copy N to top
    DW_OP_mul,              # [9]  Acc = Acc * N
    DW_OP_swap,             # [10] Swap: put N on top
    DW_OP_lit1,             # [11] Push 1
    DW_OP_minus,            # [12] N = N - 1
    DW_OP_swap,             # [13] Swap: put Acc on top
    DW_OP_skip, 0xf1, 0xff, # [14] Jump -15 → back to LOOP (PC=2)
    # --- EXIT (PC=17) ---
]


if __name__ == "__main__":
    print()
    print("Computing Factorial(5) using DWARF bytecode...")
    print(f"Bytecode ({len(factorial_program)} bytes): "
          + " ".join(f"0x{b:02x}" for b in factorial_program))
    print()

    result = execute_dwarf(factorial_program, trace=True)

    print()
    print("=" * 55)
    print(f"  RESULT: factorial(5) = {result[-1]}")
    print(f"  Verification: 5 × 4 × 3 × 2 × 1 = {5*4*3*2*1}")
    print(f"  Match: {'✅ CORRECT' if result[-1] == 120 else '❌ WRONG'}")
    print("=" * 55)
    print()
