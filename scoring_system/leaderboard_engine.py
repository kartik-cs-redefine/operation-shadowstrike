"""
WAYGROUND 4-ROUND SCORING & FINAL LEADERBOARD ENGINE
Event: OPERATION SHADOWSTRIKE - ALGO CLUB | PSIT KANPUR
Strict Rule: No score fabrication, rigorous tie-breaking by submission time, comprehensive validation.
"""

import os
import sys
import datetime
import re
from typing import Dict, List, Tuple, Any, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ==============================================================================
# UTILITY & NORMALIZATION FUNCTIONS
# ==============================================================================

def clean_str(val: Any) -> str:
    """Normalize strings for matching: strip whitespace, collapse internal spaces."""
    if val is None:
        return ""
    s = str(val).strip()
    return re.sub(r'\s+', ' ', s)

def normalize_key(team: Any, name: Any) -> str:
    """Generate a clean normalized matching key: 'TEAMNAME:::PARTICIPANTNAME'."""
    t = clean_str(team).lower()
    n = clean_str(name).lower()
    return f"{t}:::{n}"

def parse_time_to_seconds(val: Any) -> Optional[float]:
    """
    Parse varied time formats from Wayground:
    - datetime.time(h, m, s, microsecond)
    - datetime.timedelta
    - string 'hh:mm:ss' or 'mm:ss' or 'ss' or '00:03:39'
    - numeric seconds / milliseconds
    Returns total elapsed seconds as float, or None if invalid.
    """
    if val is None:
        return None
    
    if isinstance(val, datetime.time):
        return val.hour * 3600 + val.minute * 60 + val.second + val.microsecond / 1e6
    
    if isinstance(val, datetime.timedelta):
        return val.total_seconds()
    
    if isinstance(val, (int, float)):
        # If huge (> 100000), might be milliseconds
        if val > 100000:
            return float(val) / 1000.0
        return float(val)
    
    s = clean_str(val)
    if not s:
        return None
    
    # Try parsing "hh:mm:ss" or "mm:ss"
    parts = s.split(':')
    try:
        if len(parts) == 3:
            h = float(parts[0])
            m = float(parts[1])
            sec = float(parts[2])
            return h * 3600 + m * 60 + sec
        elif len(parts) == 2:
            m = float(parts[0])
            sec = float(parts[1])
            return m * 60 + sec
        elif len(parts) == 1:
            return float(parts[0])
    except ValueError:
        pass
    
    return None

def format_seconds(seconds: Optional[float]) -> str:
    """Format seconds into readable MM:SS or HH:MM:SS string."""
    if seconds is None:
        return "N/A"
    
    sec_int = int(round(seconds))
    h = sec_int // 3600
    m = (sec_int % 3600) // 60
    s = sec_int % 60
    
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

# ==============================================================================
# WAYGROUND INSPECTION & EXTRACTION
# ==============================================================================

def inspect_excel_file(filepath: str) -> Dict[str, Any]:
    """Inspect sheets and headers of an Excel file."""
    if not os.path.exists(filepath):
        return {"error": f"File not found: {filepath}"}
    
    try:
        wb = openpyxl.load_workbook(filepath, data_only=True, read_only=True)
        sheets_info = {}
        for name in wb.sheetnames:
            ws = wb[name]
            first_rows = []
            for r_idx, row in enumerate(ws.iter_rows(values_only=True)):
                if r_idx < 5:
                    first_rows.append([clean_str(c) for c in row if c is not None])
                else:
                    break
            sheets_info[name] = {
                "max_row": ws.max_row,
                "max_col": ws.max_column,
                "sample_rows": first_rows
            }
        return {"sheets": sheets_info}
    except Exception as e:
        return {"error": str(e)}

def extract_participants_master(filepath: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Extract registered participants from participants_list.xlsx.
    Looks for Team Name, Participant Name (or First/Last Name), Roll No/ID, Email, etc.
    Returns: (list_of_participants, list_of_validation_flags)
    """
    flags = []
    participants = []
    
    wb = openpyxl.load_workbook(filepath, data_only=True)
    ws = wb.active
    
    # Read all rows
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        flags.append({"type": "EMPTY_FILE", "details": "participants_list.xlsx is completely empty."})
        return participants, flags
    
    # Find header row
    header_idx = -1
    team_col = -1
    name_col = -1
    first_name_col = -1
    last_name_col = -1
    extra_cols = {}
    
    for idx, row in enumerate(rows[:10]):
        row_str = [clean_str(c).lower() for c in row if c is not None]
        # Look for keywords
        if any("team" in c for c in row_str) or any("name" in c for c in row_str) or any("participant" in c for c in row_str):
            header_idx = idx
            break
            
    if header_idx == -1:
        # Fallback to row 0
        header_idx = 0
        
    header_row = rows[header_idx]
    for c_idx, col_val in enumerate(header_row):
        if col_val is None:
            continue
        c_clean = clean_str(col_val).lower()
        
        if "team" in c_clean and team_col == -1:
            team_col = c_idx
        elif ("participant" in c_clean or "candidate" in c_clean or "student" in c_clean or c_clean == "name") and name_col == -1:
            name_col = c_idx
        elif "first" in c_clean and "name" in c_clean and first_name_col == -1:
            first_name_col = c_idx
        elif "last" in c_clean and "name" in c_clean and last_name_col == -1:
            last_name_col = c_idx
        else:
            extra_cols[clean_str(col_val)] = c_idx
            
    # If no separate name col but first & last name exist
    has_split_name = (name_col == -1 and first_name_col != -1)
    
    # Process participant rows
    seen_keys = set()
    for r_idx in range(header_idx + 1, len(rows)):
        row = rows[r_idx]
        if not row or all(c is None or clean_str(c) == "" for c in row):
            continue
            
        team_name = clean_str(row[team_col]) if team_col != -1 and team_col < len(row) else ""
        
        if has_split_name:
            fn = clean_str(row[first_name_col]) if first_name_col < len(row) else ""
            ln = clean_str(row[last_name_col]) if (last_name_col != -1 and last_name_col < len(row)) else ""
            part_name = f"{fn} {ln}".strip()
        else:
            part_name = clean_str(row[name_col]) if name_col != -1 and name_col < len(row) else ""
            
        if not team_name and not part_name:
            continue
            
        if not team_name:
            flags.append({
                "type": "MISSING_TEAM_NAME",
                "row": r_idx + 1,
                "participant": part_name,
                "details": f"Participant '{part_name}' registered without Team Name."
            })
            team_name = "UNASSIGNED_TEAM"
            
        if not part_name:
            flags.append({
                "type": "MISSING_PARTICIPANT_NAME",
                "row": r_idx + 1,
                "team": team_name,
                "details": f"Team '{team_name}' has an empty participant entry."
            })
            part_name = "UNNAMED_PARTICIPANT"
            
        m_key = normalize_key(team_name, part_name)
        if m_key in seen_keys:
            flags.append({
                "type": "DUPLICATE_REGISTRATION",
                "row": r_idx + 1,
                "team": team_name,
                "participant": part_name,
                "details": f"Duplicate registration found for '{part_name}' in team '{team_name}'."
            })
        seen_keys.add(m_key)
        
        extras = {}
        for col_name, c_pos in extra_cols.items():
            if c_pos < len(row):
                extras[col_name] = row[c_pos]
                
        participants.append({
            "team_name": team_name,
            "participant_name": part_name,
            "match_key": m_key,
            "original_row": r_idx + 1,
            "extras": extras
        })
        
    return participants, flags

def extract_wayground_round_data(filepath: str, round_num: int) -> Tuple[List[Dict[str, Any]], Dict[str, Any], List[Dict[str, Any]]]:
    """
    Extract scores and submission times from a Wayground round Excel report.
    Supports:
    - Standard Wayground format with sheet 'Participant Data'
    - Single-sheet reports
    - Sheets containing Rank, First Name, Last Name, Player Name, Score, Total Time Taken, Started At.
    Returns: (records, round_meta, flags)
    """
    flags = []
    records = []
    round_meta = {
        "round_num": round_num,
        "filepath": filepath,
        "max_score": 0,
        "total_submissions": 0
    }
    
    if not os.path.exists(filepath):
        flags.append({
            "type": "MISSING_ROUND_FILE",
            "round": round_num,
            "details": f"Report file for Round {round_num} not found at {filepath}."
        })
        return records, round_meta, flags
        
    wb = openpyxl.load_workbook(filepath, data_only=True)
    
    # 1. Check for Quiz Details / Overview to find max possible score
    quiz_sheet = wb['Quiz Details'] if 'Quiz Details' in wb.sheetnames else None
    
    # 2. Identify the active participant data sheet
    target_sheet = None
    if 'Participant Data' in wb.sheetnames:
        target_sheet = wb['Participant Data']
    else:
        # Find sheet with 'Score' or 'Player Name' in row 0 or 1
        for sname in wb.sheetnames:
            ws_check = wb[sname]
            for row in ws_check.iter_rows(values_only=True, max_row=4):
                row_str = [clean_str(c).lower() for c in row if c is not None]
                if "score" in row_str or "player name" in row_str:
                    target_sheet = ws_check
                    break
            if target_sheet:
                break
        if not target_sheet:
            target_sheet = wb.active
            
    # Read rows from target_sheet
    rows = list(target_sheet.iter_rows(values_only=True))
    if not rows:
        flags.append({
            "type": "EMPTY_ROUND_SHEET",
            "round": round_num,
            "details": f"Sheet '{target_sheet.title}' in {filepath} is empty."
        })
        return records, round_meta, flags
        
    # Find column indices
    header_idx = -1
    col_map = {
        "rank": -1,
        "first_name": -1,
        "last_name": -1,
        "player_name": -1,
        "team_name": -1,
        "score": -1,
        "accuracy": -1,
        "time_taken": -1,
        "started_at": -1,
        "questions_attempted": -1
    }
    
    for r_idx, row in enumerate(rows[:10]):
        row_str = [clean_str(c).lower() for c in row if c is not None]
        if "score" in row_str or "player name" in row_str or "first name" in row_str:
            header_idx = r_idx
            break
            
    if header_idx == -1:
        header_idx = 0
        
    header_row = rows[header_idx]
    for c_idx, col_val in enumerate(header_row):
        if col_val is None:
            continue
        c_clean = clean_str(col_val).lower()
        
        if c_clean == "rank":
            col_map["rank"] = c_idx
        elif "first" in c_clean and "name" in c_clean:
            col_map["first_name"] = c_idx
        elif "last" in c_clean and "name" in c_clean:
            col_map["last_name"] = c_idx
        elif "player" in c_clean and "name" in c_clean:
            col_map["player_name"] = c_idx
        elif "team" in c_clean:
            col_map["team_name"] = c_idx
        elif c_clean == "score" or ("earned" in c_clean and "score" in c_clean) or ("points" in c_clean and "total" not in c_clean):
            col_map["score"] = c_idx
        elif "accuracy" in c_clean:
            col_map["accuracy"] = c_idx
        elif "time" in c_clean and ("taken" in c_clean or "spent" in c_clean or "total" in c_clean or "duration" in c_clean):
            col_map["time_taken"] = c_idx
        elif "start" in c_clean:
            col_map["started_at"] = c_idx
        elif "attempted" in c_clean:
            col_map["questions_attempted"] = c_idx
            
    if col_map["score"] == -1:
        flags.append({
            "type": "CRITICAL_SCHEMA_ERROR",
            "round": round_num,
            "details": f"Could not find 'Score' column in Round {round_num} report ({filepath})."
        })
        return records, round_meta, flags
        
    # Process participants
    seen_attempts = {}
    max_score_seen = 0
    
    for r_idx in range(header_idx + 1, len(rows)):
        row = rows[r_idx]
        if not row or all(c is None or clean_str(c) == "" for c in row):
            continue
            
        # Parse names
        first_name = clean_str(row[col_map["first_name"]]) if col_map["first_name"] != -1 and col_map["first_name"] < len(row) else ""
        last_name = clean_str(row[col_map["last_name"]]) if col_map["last_name"] != -1 and col_map["last_name"] < len(row) else ""
        player_name = clean_str(row[col_map["player_name"]]) if col_map["player_name"] != -1 and col_map["player_name"] < len(row) else ""
        team_name = clean_str(row[col_map["team_name"]]) if col_map["team_name"] != -1 and col_map["team_name"] < len(row) else ""
        
        # In Wayground:
        # Often Player Name = Team Name (e.g. 'KARTIK - 01' or 'Team Alpha'),
        # or Player Name = Participant Name, or First Name + Last Name = Participant.
        # Let's preserve all variations.
        full_name = f"{first_name} {last_name}".strip()
        
        # Parse Score
        score_val = row[col_map["score"]] if col_map["score"] < len(row) else 0
        try:
            earned_score = float(score_val) if score_val is not None else 0.0
        except (ValueError, TypeError):
            earned_score = 0.0
            flags.append({
                "type": "INVALID_SCORE_FORMAT",
                "round": round_num,
                "row": r_idx + 1,
                "raw_value": score_val,
                "player": player_name or full_name,
                "details": f"Invalid score value '{score_val}' encountered in Round {round_num}."
            })
            
        if earned_score > max_score_seen:
            max_score_seen = earned_score
            
        # Parse Time
        time_raw = row[col_map["time_taken"]] if col_map["time_taken"] != -1 and col_map["time_taken"] < len(row) else None
        time_sec = parse_time_to_seconds(time_raw)
        
        if time_sec is None and time_raw is not None:
            flags.append({
                "type": "INVALID_TIME_FORMAT",
                "round": round_num,
                "row": r_idx + 1,
                "raw_time": time_raw,
                "player": player_name or full_name,
                "details": f"Could not parse duration '{time_raw}' in Round {round_num}."
            })
            
        # Check duplicate attempt
        identifier_combo = f"{player_name}:::{full_name}"
        if identifier_combo in seen_attempts:
            flags.append({
                "type": "DUPLICATE_WAYGROUND_ATTEMPT",
                "round": round_num,
                "row": r_idx + 1,
                "identifier": identifier_combo,
                "previous_row": seen_attempts[identifier_combo],
                "details": f"Duplicate record for '{identifier_combo}' in Round {round_num}. Requiring manual verification."
            })
        else:
            seen_attempts[identifier_combo] = r_idx + 1
            
        records.append({
            "round": round_num,
            "row_index": r_idx + 1,
            "first_name": first_name,
            "last_name": last_name,
            "full_name": full_name,
            "player_name": player_name,
            "team_name": team_name,
            "earned_score": earned_score,
            "time_raw": time_raw,
            "time_seconds": time_sec,
            "rank_in_round": row[col_map["rank"]] if col_map["rank"] != -1 and col_map["rank"] < len(row) else None
        })
        
    round_meta["max_score"] = max_score_seen
    round_meta["total_submissions"] = len(records)
    return records, round_meta, flags

# ==============================================================================
# PARTICIPANT MATCHING ALGORITHM
# ==============================================================================

def match_participant_record(
    reg: Dict[str, Any],
    round_records: List[Dict[str, Any]],
    round_num: int
) -> Tuple[Optional[Dict[str, Any]], str, List[Dict[str, Any]]]:
    """
    Match registered participant (Team Name + Participant Name) against Wayground round records.
    Returns: (matched_record, match_status, flags)
    Match statuses:
    - 'EXACT': Confident match on Team + Name
    - 'NAME_ONLY_MATCH': Name matches but team string slightly differs
    - 'ABSENT': Not found in round report (0 score)
    - 'AMBIGUOUS': Multiple conflicting matches found (Requires manual verification)
    """
    flags = []
    reg_team = clean_str(reg["team_name"]).lower()
    reg_name = clean_str(reg["participant_name"]).lower()
    
    # Exact candidates
    candidates = []
    
    for r in round_records:
        r_team = clean_str(r["team_name"]).lower()
        r_player = clean_str(r["player_name"]).lower()
        r_full = clean_str(r["full_name"]).lower()
        r_fn = clean_str(r["first_name"]).lower()
        r_ln = clean_str(r["last_name"]).lower()
        
        # Check Condition 1: Player Name has Team, and First/Last has Name
        cond_team = (reg_team and (reg_team in r_team or reg_team in r_player or r_team in reg_team or r_player in reg_team))
        cond_name = (reg_name and (reg_name == r_full or reg_name in r_full or r_full in reg_name or reg_name == r_player))
        
        # Check Condition 2: Exact (Team + Name)
        if cond_team and cond_name:
            candidates.append((r, "EXACT"))
        elif cond_name and not r_team and not r_player:
            candidates.append((r, "NAME_MATCH_NO_TEAM"))
        elif cond_team and not r_full:
            # Only team matched
            pass
            
    if len(candidates) == 1:
        return candidates[0][0], candidates[0][1], flags
    elif len(candidates) > 1:
        # Ambiguous multiple candidates!
        flags.append({
            "type": "AMBIGUOUS_MATCH",
            "round": round_num,
            "team": reg["team_name"],
            "participant": reg["participant_name"],
            "candidate_count": len(candidates),
            "details": f"Multiple potential matches found for '{reg['participant_name']}' ({reg['team_name']}) in Round {round_num}. Flagged for manual review."
        })
        return None, "AMBIGUOUS", flags
        
    # Fallback search: exact name match
    name_matches = []
    for r in round_records:
        r_full = clean_str(r["full_name"]).lower()
        r_player = clean_str(r["player_name"]).lower()
        if reg_name and (reg_name == r_full or reg_name == r_player):
            name_matches.append(r)
            
    if len(name_matches) == 1:
        flags.append({
            "type": "NAME_ONLY_MATCH_WARNING",
            "round": round_num,
            "team": reg["team_name"],
            "participant": reg["participant_name"],
            "found_player": name_matches[0]["player_name"],
            "details": f"Matched on participant name alone in Round {round_num} (Team name did not strictly match)."
        })
        return name_matches[0], "NAME_ONLY_MATCH", flags
    elif len(name_matches) > 1:
        flags.append({
            "type": "AMBIGUOUS_NAME_MATCH",
            "round": round_num,
            "team": reg["team_name"],
            "participant": reg["participant_name"],
            "details": f"Multiple players with name '{reg['participant_name']}' in Round {round_num} without distinct team matches."
        })
        return None, "AMBIGUOUS", flags
        
    # If not found, participant is absent
    return None, "ABSENT", flags

# ==============================================================================
# CONSOLIDATION & RANKING ENGINE
# ==============================================================================

def build_leaderboard(
    participants: List[Dict[str, Any]],
    rounds_data: Dict[int, List[Dict[str, Any]]],
    rounds_meta: Dict[int, Dict[str, Any]],
    initial_flags: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Consolidate all 4 rounds for every registered participant.
    Resolve ties:
    1. Total score (descending)
    2. Combined submission time (ascending)
    Returns: (ranked_leaderboard, master_data, validation_report)
    """
    all_flags = list(initial_flags)
    master_records = []
    
    # Track used round records to identify unregistered submissions
    used_records_per_round = {1: set(), 2: set(), 3: set(), 4: set()}
    
    for reg in participants:
        p_row = {
            "team_name": reg["team_name"],
            "participant_name": reg["participant_name"],
            "scores": {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0},
            "times": {1: None, 2: None, 3: None, 4: None},
            "status": {1: "ABSENT", 2: "ABSENT", 3: "ABSENT", 4: "ABSENT"},
            "raw_records": {1: None, 2: None, 3: None, 4: None},
            "requires_manual_verification": False
        }
        
        for r_num in [1, 2, 3, 4]:
            r_records = rounds_data.get(r_num, [])
            matched_rec, match_status, m_flags = match_participant_record(reg, r_records, r_num)
            all_flags.extend(m_flags)
            
            p_row["status"][r_num] = match_status
            if matched_rec:
                p_row["scores"][r_num] = matched_rec["earned_score"]
                p_row["times"][r_num] = matched_rec["time_seconds"]
                p_row["raw_records"][r_num] = matched_rec
                used_records_per_round[r_num].add(matched_rec["row_index"])
            else:
                p_row["scores"][r_num] = 0.0
                p_row["times"][r_num] = None
                if match_status == "AMBIGUOUS":
                    p_row["requires_manual_verification"] = True
                    
        # Total score: R1 + R2 + R3 + R4
        total_score = sum(p_row["scores"].values())
        p_row["total_score"] = total_score
        
        # Combined submission time
        # Valid only if time values exist for attempted rounds
        valid_times = [t for t in p_row["times"].values() if t is not None]
        if valid_times:
            p_row["combined_time_sec"] = sum(valid_times)
            p_row["combined_time_str"] = format_seconds(p_row["combined_time_sec"])
            p_row["has_missing_times"] = len(valid_times) < sum(1 for s in p_row["status"].values() if s != "ABSENT")
        else:
            p_row["combined_time_sec"] = float('inf')
            p_row["combined_time_str"] = "N/A"
            p_row["has_missing_times"] = False
            
        master_records.append(p_row)
        
    # Check for unregistered participants in Wayground reports
    for r_num in [1, 2, 3, 4]:
        for r_rec in rounds_data.get(r_num, []):
            if r_rec["row_index"] not in used_records_per_round[r_num]:
                all_flags.append({
                    "type": "UNREGISTERED_SUBMISSION",
                    "round": r_num,
                    "row": r_rec["row_index"],
                    "player_name": r_rec["player_name"],
                    "full_name": r_rec["full_name"],
                    "team_name": r_rec["team_name"],
                    "score": r_rec["earned_score"],
                    "details": f"Submission by '{r_rec['player_name'] or r_rec['full_name']}' in Round {r_num} does not match any registered participant in participants_list.xlsx."
                })
                
    # Sort for Final Leaderboard:
    # 1. Total score (descending)
    # 2. Combined submission time (ascending)
    # Note: If time is missing/inf, they rank lower in tie-break
    sorted_leaderboard = sorted(
        master_records,
        key=lambda x: (-x["total_score"], x["combined_time_sec"])
    )
    
    # Assign Ranks (handling exact ties)
    current_rank = 1
    for idx, row in enumerate(sorted_leaderboard):
        if idx > 0:
            prev = sorted_leaderboard[idx - 1]
            # Exact tie if score and time are identical
            if row["total_score"] == prev["total_score"] and row["combined_time_sec"] == prev["combined_time_sec"]:
                row["rank"] = prev["rank"]
            else:
                row["rank"] = idx + 1
        else:
            row["rank"] = 1
            
    summary_stats = {
        "total_registered": len(participants),
        "total_complete_records": sum(1 for r in master_records if all(s != "ABSENT" for s in r["status"].values())),
        "total_absentees_all_rounds": sum(1 for r in master_records if all(s == "ABSENT" for s in r["status"].values())),
        "total_requiring_verification": sum(1 for r in master_records if r["requires_manual_verification"]),
        "total_flags": len(all_flags)
    }
    
    return sorted_leaderboard, master_records, {"flags": all_flags, "stats": summary_stats}

# ==============================================================================
# PROFESSIONAL EXCEL WORKBOOK GENERATOR
# ==============================================================================

def generate_excel_workbook(
    leaderboard: List[Dict[str, Any]],
    master_data: List[Dict[str, Any]],
    rounds_meta: Dict[int, Dict[str, Any]],
    validation_report: Dict[str, Any],
    output_filepath: str
) -> str:
    """
    Generate professional, competition-ready Excel workbook 'FINAL_WAYGROUND_LEADERBOARD.xlsx'.
    Contains 5 Sheets:
    1. FINAL LEADERBOARD
    2. MASTER DATA
    3. ROUND-WISE ANALYSIS
    4. VALIDATION REPORT
    5. TOP PERFORMERS
    """
    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)
    
    # Style definitions
    font_title = Font(name="Segoe UI", size=16, bold=True, color="FFFFFF")
    font_subtitle = Font(name="Segoe UI", size=11, italic=True, color="CBD5E1")
    font_header = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    font_bold = Font(name="Segoe UI", size=11, bold=True)
    font_regular = Font(name="Segoe UI", size=11)
    font_mono = Font(name="Consolas", size=11)
    font_mono_bold = Font(name="Consolas", size=11, bold=True)
    
    fill_header_dark = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid") # Dark Navy
    fill_header_accent = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    fill_subtle_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    
    # Podium Fills
    fill_gold = PatternFill(start_color="FEF08A", end_color="FEF08A", fill_type="solid")     # Rank 1
    fill_silver = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")   # Rank 2
    fill_bronze = PatternFill(start_color="FED7AA", end_color="FED7AA", fill_type="solid")   # Rank 3
    
    border_thin = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0')
    )
    border_bottom_double = Border(
        bottom=Side(style='double', color='0F172A')
    )
    
    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")
    
    # --------------------------------------------------------------------------
    # SHEET 1: FINAL LEADERBOARD
    # --------------------------------------------------------------------------
    ws_lead = wb.create_sheet(title="FINAL LEADERBOARD")
    ws_lead.views.sheetView[0].showGridLines = True
    
    headers_lead = [
        "Rank", "Team Name", "Participant Name", 
        "Round 1 Score", "Round 2 Score", "Round 3 Score", "Round 4 Score", 
        "Total Score", "Combined Submission Time"
    ]
    
    # Header Row
    ws_lead.append(headers_lead)
    for col_num in range(1, len(headers_lead) + 1):
        cell = ws_lead.cell(row=1, column=col_num)
        cell.font = font_header
        cell.fill = fill_header_dark
        cell.alignment = align_center if col_num in [1, 8, 9] else (align_right if col_num in [4, 5, 6, 7] else align_left)
        cell.border = border_thin
    
    # Data Rows
    for r_idx, row in enumerate(leaderboard, start=2):
        rank_val = row["rank"]
        r1_s = row["scores"][1]
        r2_s = row["scores"][2]
        r3_s = row["scores"][3]
        r4_s = row["scores"][4]
        comb_time = row["combined_time_str"]
        
        # We can also put an Excel formula for Total Score: =SUM(D{r_idx}:G{r_idx})
        # But also preserve the exact numerical value
        formula_total = f"=SUM(D{r_idx}:G{r_idx})"
        
        ws_lead.append([
            rank_val,
            row["team_name"],
            row["participant_name"],
            r1_s,
            r2_s,
            r3_s,
            r4_s,
            formula_total,
            comb_time
        ])
        
        # Apply row styles
        is_podium = rank_val in [1, 2, 3]
        podium_fill = fill_gold if rank_val == 1 else (fill_silver if rank_val == 2 else fill_bronze)
        
        for col_num in range(1, 10):
            c = ws_lead.cell(row=r_idx, column=col_num)
            c.font = font_bold if (is_podium or col_num in [1, 8]) else font_regular
            c.border = border_thin
            
            if is_podium and col_num == 1:
                c.fill = podium_fill
            elif r_idx % 2 == 1:
                c.fill = fill_subtle_zebra
                
            if col_num == 1:
                c.alignment = align_center
            elif col_num in [2, 3]:
                c.alignment = align_left
            elif col_num in [4, 5, 6, 7, 8]:
                c.alignment = align_right
                c.number_format = '#,##0.0'
            elif col_num == 9:
                c.alignment = align_center
                c.font = font_mono
                
    ws_lead.freeze_panes = "A2"
    ws_lead.auto_filter.ref = f"A1:I{len(leaderboard) + 1}"
    
    # --------------------------------------------------------------------------
    # SHEET 2: MASTER DATA
    # --------------------------------------------------------------------------
    ws_master = wb.create_sheet(title="MASTER DATA")
    ws_master.views.sheetView[0].showGridLines = True
    
    headers_master = [
        "Team Name", "Participant Name", 
        "R1 Score", "R1 Time", "R1 Status",
        "R2 Score", "R2 Time", "R2 Status",
        "R3 Score", "R3 Time", "R3 Status",
        "R4 Score", "R4 Time", "R4 Status",
        "Total Score", "Combined Time", "Verification Needed"
    ]
    ws_master.append(headers_master)
    for col_num in range(1, len(headers_master) + 1):
        cell = ws_master.cell(row=1, column=col_num)
        cell.font = font_header
        cell.fill = fill_header_accent
        cell.alignment = align_center
        cell.border = border_thin
        
    for r_idx, row in enumerate(master_data, start=2):
        ws_master.append([
            row["team_name"],
            row["participant_name"],
            row["scores"][1], format_seconds(row["times"][1]), row["status"][1],
            row["scores"][2], format_seconds(row["times"][2]), row["status"][2],
            row["scores"][3], format_seconds(row["times"][3]), row["status"][3],
            row["scores"][4], format_seconds(row["times"][4]), row["status"][4],
            row["total_score"],
            row["combined_time_str"],
            "FLAGGED" if row["requires_manual_verification"] else "OK"
        ])
        for col_num in range(1, len(headers_master) + 1):
            c = ws_master.cell(row=r_idx, column=col_num)
            c.font = font_regular
            c.border = border_thin
            if r_idx % 2 == 1:
                c.fill = fill_subtle_zebra
            if col_num in [3, 6, 9, 12, 15]:
                c.alignment = align_right
            elif col_num in [4, 7, 10, 13, 16]:
                c.alignment = align_center
                c.font = font_mono
            elif col_num in [5, 8, 11, 14, 17]:
                c.alignment = align_center
                if c.value == "FLAGGED":
                    c.font = font_bold
                    c.fill = PatternFill(start_color="FEE2E2", fill_type="solid")
            else:
                c.alignment = align_left
                
    ws_master.freeze_panes = "C2"
    ws_master.auto_filter.ref = f"A1:Q{len(master_data) + 1}"
    
    # --------------------------------------------------------------------------
    # SHEET 3: ROUND-WISE ANALYSIS
    # --------------------------------------------------------------------------
    ws_analysis = wb.create_sheet(title="ROUND-WISE ANALYSIS")
    ws_analysis.views.sheetView[0].showGridLines = True
    
    headers_analysis = [
        "Metric", "Round 1", "Round 2", "Round 3", "Round 4", "Consolidated Event"
    ]
    ws_analysis.append(headers_analysis)
    for col_num in range(1, len(headers_analysis) + 1):
        cell = ws_analysis.cell(row=1, column=col_num)
        cell.font = font_header
        cell.fill = fill_header_dark
        cell.alignment = align_center
        cell.border = border_thin
        
    # Calculate Metrics
    total_reg = len(master_data)
    r_subs = [rounds_meta.get(r, {}).get("total_submissions", 0) for r in [1, 2, 3, 4]]
    r_abs = [total_reg - s for s in r_subs]
    r_max_score = [rounds_meta.get(r, {}).get("max_score", 0) for r in [1, 2, 3, 4]]
    
    # Calculate round scores from master data
    r_scores = {r: [row["scores"][r] for row in master_data if row["status"][r] != "ABSENT"] for r in [1, 2, 3, 4]}
    r_avgs = [(sum(r_scores[r]) / len(r_scores[r])) if r_scores[r] else 0.0 for r in [1, 2, 3, 4]]
    r_highs = [max(r_scores[r]) if r_scores[r] else 0.0 for r in [1, 2, 3, 4]]
    r_lows = [min(r_scores[r]) if r_scores[r] else 0.0 for r in [1, 2, 3, 4]]
    
    all_totals = [row["total_score"] for row in master_data]
    cons_avg = (sum(all_totals) / len(all_totals)) if all_totals else 0.0
    cons_high = max(all_totals) if all_totals else 0.0
    cons_low = min(all_totals) if all_totals else 0.0
    
    metrics_rows = [
        ("Total Registered Participants", total_reg, total_reg, total_reg, total_reg, total_reg),
        ("Submissions Count", r_subs[0], r_subs[1], r_subs[2], r_subs[3], sum(r_subs)),
        ("Absentees Count", r_abs[0], r_abs[1], r_abs[2], r_abs[3], f"{total_reg - sum(1 for m in master_data if all(s != 'ABSENT' for s in m['status'].values()))} (Partial/Full)"),
        ("Highest Score Achieved", r_highs[0], r_highs[1], r_highs[2], r_highs[3], cons_high),
        ("Average Score (Attempted)", round(r_avgs[0], 2), round(r_avgs[1], 2), round(r_avgs[2], 2), round(r_avgs[3], 2), round(cons_avg, 2)),
        ("Lowest Score (Attempted)", r_lows[0], r_lows[1], r_lows[2], r_lows[3], cons_low),
        ("Maximum Possible Marks (Reported)", r_max_score[0], r_max_score[1], r_max_score[2], r_max_score[3], sum(r_max_score))
    ]
    
    for r_idx, m_row in enumerate(metrics_rows, start=2):
        ws_analysis.append(list(m_row))
        for col_num in range(1, len(m_row) + 1):
            c = ws_analysis.cell(row=r_idx, column=col_num)
            c.font = font_bold if col_num in [1, 6] else font_regular
            c.border = border_thin
            c.alignment = align_left if col_num == 1 else align_right
            if r_idx % 2 == 1:
                c.fill = fill_subtle_zebra
                
    # --------------------------------------------------------------------------
    # SHEET 4: VALIDATION REPORT
    # --------------------------------------------------------------------------
    ws_val = wb.create_sheet(title="VALIDATION REPORT")
    ws_val.views.sheetView[0].showGridLines = True
    
    headers_val = [
        "Issue ID", "Category / Type", "Round", "Team / Player Affected", "Description / Details", "Severity"
    ]
    ws_val.append(headers_val)
    for col_num in range(1, len(headers_val) + 1):
        cell = ws_val.cell(row=1, column=col_num)
        cell.font = font_header
        cell.fill = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
        cell.alignment = align_center
        cell.border = border_thin
        
    flags = validation_report.get("flags", [])
    if not flags:
        ws_val.append(["V-001", "CLEAN_AUDIT", "ALL", "None", "No data discrepancies, duplicates, or ambiguous matches found.", "INFO"])
        for col_num in range(1, 7):
            c = ws_val.cell(row=2, column=col_num)
            c.font = font_regular
            c.border = border_thin
            c.fill = PatternFill(start_color="DCFCE7", fill_type="solid")
    else:
        for f_idx, f in enumerate(flags, start=1):
            severity = "HIGH" if "AMBIGUOUS" in f["type"] or "CRITICAL" in f["type"] else ("MEDIUM" if "DUPLICATE" in f["type"] or "UNREGISTERED" in f["type"] else "LOW")
            sev_fill = PatternFill(start_color="FEE2E2", fill_type="solid") if severity == "HIGH" else (PatternFill(start_color="FEF3C7", fill_type="solid") if severity == "MEDIUM" else fill_subtle_zebra)
            
            ws_val.append([
                f"V-{f_idx:03d}",
                f.get("type", "FLAG"),
                f"Round {f.get('round')}" if f.get("round") else "GENERAL",
                f.get("team") or f.get("player") or f.get("participant") or "N/A",
                f.get("details", ""),
                severity
            ])
            r_curr = f_idx + 1
            for col_num in range(1, 7):
                c = ws_val.cell(row=r_curr, column=col_num)
                c.font = font_regular
                c.border = border_thin
                if col_num == 6:
                    c.font = font_bold
                    c.fill = sev_fill
                    c.alignment = align_center
                elif col_num in [1, 3]:
                    c.alignment = align_center
                else:
                    c.alignment = align_left
                    
    ws_val.freeze_panes = "A2"
    ws_val.auto_filter.ref = f"A1:F{max(2, len(flags) + 1)}"
    
    # --------------------------------------------------------------------------
    # SHEET 5: TOP PERFORMERS
    # --------------------------------------------------------------------------
    ws_top = wb.create_sheet(title="TOP PERFORMERS")
    ws_top.views.sheetView[0].showGridLines = True
    
    headers_top = [
        "Rank", "Team Name", "Participant Name", "Total Score", "Combined Time", "Award Status"
    ]
    ws_top.append(headers_top)
    for col_num in range(1, len(headers_top) + 1):
        cell = ws_top.cell(row=1, column=col_num)
        cell.font = font_header
        cell.fill = fill_header_dark
        cell.alignment = align_center
        cell.border = border_thin
        
    top_10 = leaderboard[:10]
    for r_idx, row in enumerate(top_10, start=2):
        rank_val = row["rank"]
        award = "🏆 CHAMPION (1st Place)" if rank_val == 1 else (
            "🥈 1st RUNNER UP (2nd Place)" if rank_val == 2 else (
                "🥉 2nd RUNNER UP (3rd Place)" if rank_val == 3 else f"Top 10 Finalist (Rank {rank_val})"
            )
        )
        
        ws_top.append([
            rank_val,
            row["team_name"],
            row["participant_name"],
            row["total_score"],
            row["combined_time_str"],
            award
        ])
        
        podium_fill = fill_gold if rank_val == 1 else (fill_silver if rank_val == 2 else (fill_bronze if rank_val == 3 else (fill_subtle_zebra if r_idx % 2 == 1 else None)))
        
        for col_num in range(1, 7):
            c = ws_top.cell(row=r_idx, column=col_num)
            c.font = font_bold if rank_val <= 3 else font_regular
            c.border = border_thin
            if podium_fill:
                c.fill = podium_fill
                
            if col_num in [1, 5]:
                c.alignment = align_center
            elif col_num in [2, 3, 6]:
                c.alignment = align_left
            elif col_num == 4:
                c.alignment = align_right
                c.number_format = '#,##0.0'
                
    ws_top.freeze_panes = "A2"
    
    # --------------------------------------------------------------------------
    # AUTO-FIT COLUMN WIDTHS ACROSS ALL SHEETS
    # --------------------------------------------------------------------------
    for sheet in wb.worksheets:
        for col in sheet.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val = cell.value
                if val is not None:
                    s_val = str(val)
                    if s_val.startswith('='):
                        s_val = "12345.0"
                    max_len = max(max_len, len(s_val))
            sheet.column_dimensions[col_letter].width = max(max_len + 4, 14)
            
    # Save Workbook
    wb.save(output_filepath)
    return output_filepath

# ==============================================================================
# PIPELINE ENTRY POINT
# ==============================================================================

def execute_scoring_pipeline(
    participants_file: str,
    round1_file: str,
    round2_file: str,
    round3_file: str,
    round4_file: str,
    output_excel: str
) -> Dict[str, Any]:
    """Execute complete scoring pipeline across all 5 files."""
    print("=" * 80)
    print("STARTING OPERATION SHADOWSTRIKE 4-ROUND SCORING PIPELINE")
    print("=" * 80)
    
    # 1. Extract Master Participants
    print(f"[1/5] Extracting Master Participant Registry from: {participants_file}")
    participants, reg_flags = extract_participants_master(participants_file)
    print(f"      -> Loaded {len(participants)} registered participants. Flags: {len(reg_flags)}")
    
    # 2. Extract Round Reports
    rounds_data = {}
    rounds_meta = {}
    round_flags = list(reg_flags)
    
    r_files = {
        1: round1_file,
        2: round2_file,
        3: round3_file,
        4: round4_file
    }
    
    for r_num, r_path in r_files.items():
        print(f"[2/5] Extracting Round {r_num} Report from: {r_path}")
        recs, meta, flags = extract_wayground_round_data(r_path, r_num)
        rounds_data[r_num] = recs
        rounds_meta[r_num] = meta
        round_flags.extend(flags)
        print(f"      -> Round {r_num}: {len(recs)} records extracted. Max score: {meta['max_score']}. Flags: {len(flags)}")
        
    # 3. Consolidate and Rank
    print("[3/5] Consolidating scores, resolving ties, and ranking participants...")
    leaderboard, master_data, val_report = build_leaderboard(
        participants, rounds_data, rounds_meta, round_flags
    )
    
    # 4. Generate Professional Workbook
    print(f"[4/5] Generating Final Excel Workbook: {output_excel}")
    generate_excel_workbook(leaderboard, master_data, rounds_meta, val_report, output_excel)
    print(f"      -> Successfully created: {output_excel}")
    
    # 5. Output Summary
    print("[5/5] Pipeline execution complete!")
    print("-" * 80)
    stats = val_report["stats"]
    print(f"Total Registered Participants:        {stats['total_registered']}")
    print(f"Total with Complete Records (All R):   {stats['total_complete_records']}")
    print(f"Total Full Absentees:                  {stats['total_absentees_all_rounds']}")
    print(f"Total Requiring Manual Verification:   {stats['total_requiring_verification']}")
    print(f"Total Validation Issues / Flags:       {stats['total_flags']}")
    print("-" * 80)
    print("TOP 10 PARTICIPANTS:")
    for row in leaderboard[:10]:
        print(f"Rank {row['rank']:2d} | Score: {row['total_score']:7.1f} | Time: {row['combined_time_str']:>8} | Team: {row['team_name']:<20} | Name: {row['participant_name']}")
    print("=" * 80)
    
    return {
        "leaderboard": leaderboard,
        "master_data": master_data,
        "rounds_meta": rounds_meta,
        "validation_report": val_report,
        "output_file": output_excel
    }

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, "input")
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    p_file = os.path.join(input_dir, "participants_list.xlsx")
    r1_file = os.path.join(input_dir, "round_1.xlsx")
    r2_file = os.path.join(input_dir, "round_2.xlsx")
    r3_file = os.path.join(input_dir, "round_3.xlsx")
    r4_file = os.path.join(input_dir, "round_4.xlsx")
    out_file = os.path.join(base_dir, "..", "FINAL_WAYGROUND_LEADERBOARD.xlsx")
    
    # Check if files exist
    missing = [f for f in [p_file, r1_file, r2_file, r3_file, r4_file] if not os.path.exists(f)]
    if missing:
        print("Scoring pipeline script ready.")
        print(f"Awaiting input files in '{input_dir}':")
        for m in missing:
            print(f" - Missing: {os.path.basename(m)}")
        sys.exit(0)
    else:
        execute_scoring_pipeline(p_file, r1_file, r2_file, r3_file, r4_file, out_file)
