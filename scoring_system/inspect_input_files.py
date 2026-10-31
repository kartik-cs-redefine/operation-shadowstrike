"""
INSPECTION SCRIPT FOR WAYGROUND EXCEL FILES & PARTICIPANT REGISTRY
Inspects sheet structure, headers, data types, and potential column mappings.
"""

import os
import sys
import openpyxl

def inspect_file(filepath):
    print("\n" + "=" * 80)
    print(f"FILE: {os.path.basename(filepath)}")
    print(f"PATH: {filepath}")
    print("=" * 80)
    
    if not os.path.exists(filepath):
        print("  [ERROR] File does not exist!")
        return
        
    try:
        wb = openpyxl.load_workbook(filepath, data_only=True)
        print(f"Total Sheets: {len(wb.sheetnames)} -> {wb.sheetnames}")
        
        for sname in wb.sheetnames:
            ws = wb[sname]
            print(f"\n--- Sheet: '{sname}' (Rows: {ws.max_row}, Cols: {ws.max_column}) ---")
            
            rows = list(ws.iter_rows(values_only=True, max_row=6))
            if not rows:
                print("    (Sheet is empty)")
                continue
                
            for idx, r in enumerate(rows):
                # Clean row preview
                vals = [str(c).strip() if c is not None else "" for c in r[:12]]
                if any(vals):
                    print(f"    Row {idx:2d}: {vals}")
    except Exception as e:
        print(f"  [ERROR] Failed to read Excel file: {e}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, "input")
    
    files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.endswith(('.xlsx', '.xls'))]
    if not files:
        print(f"No Excel files found in '{input_dir}'.")
        print("Please place the 5 Excel files in this directory:")
        print("  1. participants_list.xlsx")
        print("  2. round_1.xlsx")
        print("  3. round_2.xlsx")
        print("  4. round_3.xlsx")
        print("  5. round_4.xlsx")
    else:
        for f in files:
            inspect_file(f)
