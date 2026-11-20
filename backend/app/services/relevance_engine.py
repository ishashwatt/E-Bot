import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from app.services.link_inspector import LinkInspector

def escape_html(text: Any) -> str:
    if text is None:
        return ""
    s = str(text)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class DateTimeExtractor:
    """
    Extracts dates, timings, test slots, and registration deadlines with high precision.
    """

    MONTH_REGEX = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'

    @classmethod
    def extract_dates_and_times(cls, text: str) -> Dict[str, Any]:
        results = {
            "date": "As per schedule",
            "time": "Refer email",
            "deadline": None,
            "formatted_schedule": "Date & Time in email",
            "all_dates": [],
            "all_times": []
        }
        if not text:
            return results

        clean_text = re.sub(r'\s+', ' ', text)

        numeric_dates = re.findall(r'\b([0-3]?[0-9][-\/\.][0-1]?[0-9][-\/\.](?:202[4-9]|2[4-9]))\b', clean_text)
        iso_dates = re.findall(r'\b(202[4-9][-\/\.][0-1]?[0-9][-\/\.][0-3]?[0-9])\b', clean_text)
        text_dates_1 = re.findall(rf'\b([0-3]?[0-9](?:st|nd|rd|th)?\s+{cls.MONTH_REGEX}(?:\s*,?\s*202[4-9])?)\b', clean_text, re.IGNORECASE)
        text_dates_2 = re.findall(rf'\b({cls.MONTH_REGEX}\s+[0-3]?[0-9](?:st|nd|rd|th)?(?:\s*,?\s*202[4-9])?)\b', clean_text, re.IGNORECASE)

        all_dates = []
        for d in numeric_dates + iso_dates + text_dates_1 + text_dates_2:
            d_clean = d.strip()
            if d_clean and d_clean not in all_dates:
                all_dates.append(d_clean)
        results["all_dates"] = all_dates

        time_matches = re.findall(r'\b((?:[0-1]?[0-9]|2[0-3])(?::[0-5][0-9]|\.[0-5][0-9])?\s*(?:AM|PM|am|pm|hrs|hours)?\s*(?:to|-|till)?\s*(?:[0-1]?[0-9]|2[0-3])?(?::[0-5][0-9]|\.[0-5][0-9])?\s*(?:AM|PM|am|pm|hrs|hours))\b', clean_text)
        clean_times = []
        for t in time_matches:
            t_str = t.strip()
            if re.search(r'(am|pm|hrs|hours|:|\.)', t_str, re.IGNORECASE) and len(t_str) >= 4:
                if t_str not in clean_times:
                    clean_times.append(t_str)
        results["all_times"] = clean_times

        # Clean Deadline Extraction
        m_dead = re.search(
            r'(?:last\s*date\s*(?:for\s*registration)?|registration\s*deadline|apply\s*by|apply\s*before|deadline\s*to\s*apply|closes\s*on)\s*[:\-*]?\s*(?:\n\s*)?\*?([0-3]?[0-9](?:st|nd|rd|th)?\s+[A-Za-z]+(?:\s+202[4-9])?(?:\s*[\(\[]?[0-9]{1,2}(?::[0-9]{2}|\.[0-9]{2})?\s*(?:am|pm|hrs)?[\)\]]?)?)',
            text,
            re.IGNORECASE
        )
        if m_dead:
            raw_dead = m_dead.group(1).strip(" *-_:\t|")
            if raw_dead.count("(") > raw_dead.count(")"):
                raw_dead += ")"
            if len(raw_dead) >= 5:
                results["deadline"] = raw_dead

        primary_date = all_dates[0] if all_dates else ""
        primary_time = clean_times[0] if clean_times else ""

        if primary_date:
            results["date"] = primary_date
        if primary_time:
            results["time"] = primary_time

        if primary_date and primary_time:
            results["formatted_schedule"] = f"{primary_date} | {primary_time}"
        elif primary_date:
            results["formatted_schedule"] = primary_date
        elif primary_time:
            results["formatted_schedule"] = f"Time: {primary_time}"

        return results


class CampusTravelDetector:
    """
    Intelligently detects campus designations (VIT Bhopal, VIT Vellore, VIT Chennai, VIT-AP)
    and physical travel requirements, distinguishing between first-round travel and interview-only travel.
    """

    @classmethod
    def detect_campus_and_travel(cls, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        campuses_found = []
        if re.search(r'\b(?:vit\s*)?bhopal\b', text_lower):
            campuses_found.append("VIT Bhopal")
        if re.search(r'\b(?:vit\s*)?vellore\b', text_lower):
            campuses_found.append("VIT Vellore")
        if re.search(r'\b(?:vit\s*)?chennai\b', text_lower):
            campuses_found.append("VIT Chennai")
        if re.search(r'\b(?:vit\s*[-_]?\s*ap|vit\s*amaravati)\b', text_lower):
            campuses_found.append("VIT-AP")

        is_bhopal_excluded = bool(re.search(
            r'\b(?:only\s*(?:for\s*)?(?:vit\s*)?vellore(?:\s*(?:and|&)\s*chennai)?|'
            r'vit\s*vellore\s*(?:and|&)\s*chennai\s*only|'
            r'campus\s*:\s*vellore\s*only|excluding\s*bhopal|except\s*bhopal)\b',
            text_lower
        )) and not bool(re.search(r'\b(?:vit\s*)?bhopal\b', text_lower))

        first_round_vellore = bool(re.search(
            r'(?:online\s*test.*?[\@at]\s*(?:vit\s*)?vellore|'
            r'written\s*test.*?[\@at]\s*(?:vit\s*)?vellore|'
            r'(?:ppt[,\s]+)?test\s*(?:&|and)\s*interview.*?[\@at]\s*(?:vit\s*)?vellore|'
            r'first\s*round.*?[\@at]\s*(?:vit\s*)?vellore|'
            r'assessment.*?[\@at]\s*(?:vit\s*)?vellore)',
            text_lower,
            re.DOTALL
        ))

        interview_only_vellore = bool(re.search(
            r'(?:physical\s*interview.*?[\@at]\s*(?:vit\s*)?vellore|'
            r'interview\s*(?:process)?.*?[\@at]\s*(?:vit\s*)?vellore|'
            r'final\s*round.*?[\@at]\s*(?:vit\s*)?vellore)',
            text_lower,
            re.DOTALL
        )) and not first_round_vellore

        requires_vellore_travel = first_round_vellore or interview_only_vellore or bool(re.search(
            r'(?:travel\s*(?:to|down\s*to)\s*(?:vit\s*)?vellore|'
            r'report\s*(?:at|to)\s*(?:vit\s*)?vellore|'
            r'shortlisted\s*students\s*must\s*(?:travel|report|visit)\s*(?:to\s*)?(?:vit\s*)?vellore)',
            text_lower
        ))

        travel_note = None
        campus_display = "VIT Bhopal (Local / Virtual)"

        if first_round_vellore:
            travel_note = "⚠️ First-Round Travel Alert: Written test / first round itself requires physical travel to VIT Vellore campus (Not recommended as per your travel preference)."
            campus_display = "⚠️ VIT Vellore (First Round Travel Required)"
        elif interview_only_vellore:
            travel_note = "🚆 Interview Travel: Physical interview is at VIT Vellore campus (Online test is local at Bhopal). Travel required only if qualified for interview."
            campus_display = "VIT Bhopal (Test) / VIT Vellore (Interview)"
        elif requires_vellore_travel:
            travel_note = "⚠️ Travel Required: In-person round requires reporting to VIT Vellore campus."
            campus_display = "⚠️ VIT Vellore Campus (Travel Required)"
        elif "VIT Bhopal" in campuses_found:
            campus_display = "VIT Bhopal Campus"
        elif len(campuses_found) > 1:
            campus_display = f"All VIT Campuses ({', '.join(campuses_found)})"

        return {
            "campuses_found": campuses_found,
            "is_bhopal_excluded": is_bhopal_excluded,
            "requires_vellore_travel": requires_vellore_travel,
            "first_round_vellore": first_round_vellore,
            "interview_only_vellore": interview_only_vellore,
            "travel_note": travel_note,
            "campus_display": campus_display
        }


class ExamModeExtractor:
    """
    Identifies test/interview/session mode (Virtual vs Physical), testing platform,
    meeting links, and campus venues.
    """

    @classmethod
    def extract_mode_and_venues(cls, text: str, subject: str = "") -> Dict[str, Any]:
        combined = f"{subject}\n{text}"
        
        platform = None
        virtual_link = None
        meeting_id = None
        passcode = None
        physical_venues = []

        # 1. Virtual Platform & Meeting Link
        teams_match = re.search(r'https?://teams\.microsoft\.com/[^\s<>"]+', combined)
        if teams_match:
            virtual_link = teams_match.group(0).strip(".,;)>*")
            platform = "Microsoft Teams"
            
        gmeet_match = re.search(r'https?://meet\.google\.com/[^\s<>"]+', combined)
        if gmeet_match:
            virtual_link = gmeet_match.group(0).strip(".,;)>*")
            platform = "Google Meet"
            
        zoom_match = re.search(r'https?://[a-zA-Z0-9\.]*zoom\.us/[^\s<>"]+', combined)
        if zoom_match:
            virtual_link = zoom_match.group(0).strip(".,;)>*")
            platform = "Zoom"

        # Meeting ID and Passcode
        m_id = re.search(r'Meeting\s*ID\s*[:\-]?\s*([0-9 ]{9,20})', combined, re.IGNORECASE)
        if m_id:
            meeting_id = m_id.group(1).strip()
            
        p_code = re.search(r'Passcode\s*[:\-]?\s*([A-Za-z0-9]+)', combined, re.IGNORECASE)
        if p_code:
            passcode = p_code.group(1).strip()

        # Check other testing platforms
        if not platform:
            if re.search(r'\b(?:neopat|neo\s*pat)\b', combined, re.IGNORECASE):
                platform = "NeoPAT Portal"
            elif re.search(r'\bhackerearth\b', combined, re.IGNORECASE):
                platform = "HackerEarth"
            elif re.search(r'\bhackerrank\b', combined, re.IGNORECASE):
                platform = "HackerRank"
            elif re.search(r'\bmettl\b', combined, re.IGNORECASE):
                platform = "Mercer Mettl"
            elif re.search(r'\bteams\b', combined, re.IGNORECASE):
                platform = "Microsoft Teams"
            elif re.search(r'\bzoom\b', combined, re.IGNORECASE):
                platform = "Zoom"
            elif re.search(r'\bgoogle\s*meet\b', combined, re.IGNORECASE):
                platform = "Google Meet"

        # Check Physical Venues (Avoid company names matching 'lab')
        if re.search(r'\brespective\s*campus\s*labs?\b', combined, re.IGNORECASE):
            physical_venues.append("Respective campus labs")
        if re.search(r'\bvit\s*vellore\s*campus\b', combined, re.IGNORECASE):
            physical_venues.append("VIT Vellore campus")
        if re.search(r'\bvit\s*bhopal\s*campus\b', combined, re.IGNORECASE):
            physical_venues.append("VIT Bhopal campus")
        if re.search(r'\bvit\s*chennai\s*campus\b', combined, re.IGNORECASE):
            physical_venues.append("VIT Chennai campus")
            
        lab_matches = re.findall(r'\b(?:lab|laboratory)\s*[-–]?\s*(?:[0-9]{1,4}[A-Z]?|[A-Z][0-9]{1,3})\b', combined, re.IGNORECASE)
        for lm in lab_matches:
            if lm not in physical_venues and not lm.lower().startswith("labcorp"):
                physical_venues.append(lm)
                
        for hall in ["auditorium", "technology tower", "anna auditorium"]:
            if re.search(r'\b' + re.escape(hall) + r'\b', combined, re.IGNORECASE) and hall.title() not in physical_venues:
                physical_venues.append(hall.title())

        has_virtual = bool(re.search(r'\b(virtual\s*mode|online\s*mode|online\s*test|online\s*ppt|pre-?placement\s*talk|own\s*location|from\s*home|microsoft\s*teams|zoom|meet)\b', combined, re.IGNORECASE)) or bool(platform)
        has_physical = bool(re.search(r'\b(physical\s*interview|in-person|offline|campus\s*labs?|report\s*at|at\s*vit\s*vellore)\b', combined, re.IGNORECASE)) or bool(physical_venues)

        if has_virtual and has_physical:
            plat_str = f" ({platform})" if platform else ""
            venue_str = f" / Physical: {', '.join(physical_venues)}" if physical_venues else ""
            mode_desc = f"Hybrid (Online Test{plat_str}{venue_str})"
        elif has_virtual:
            mode_desc = f"Virtual on {platform}" if platform else "Virtual (Own location / Online)"
        elif has_physical:
            mode_desc = f"Physical on campus ({', '.join(physical_venues)})" if physical_venues else "Physical / In-Person on Campus"
        else:
            mode_desc = "Refer email / portal"

        return {
            "mode_desc": mode_desc,
            "platform": platform,
            "virtual_link": virtual_link,
            "meeting_id": meeting_id,
            "passcode": passcode,
            "physical_venues": physical_venues
        }


class JobDetailsExtractor:
    """
    Intelligently extracts Job Role/Profile, CTC / Stipend offered,
    Offer Tiers (Super Dream, Dream, Regular), and Stated Criteria from email content.
    """

    @classmethod
    def extract_role(cls, text: str, subject: str = "") -> str:
        combined = f"{subject}\n{text}"
        
        m_label = re.search(
            r'(?:designation|job\s*role|role|position|job\s*profile|job\s*title|hiring\s*for)\s*[:\-*]?\s*([^\n\r,;]{2,50})',
            combined,
            re.IGNORECASE
        )
        if m_label:
            val = m_label.group(1).strip(" *-_:\t|")
            if len(val) >= 2 and not re.search(r'(refer|attached|below|as per|eligible|criteria|students|batch)', val, re.IGNORECASE):
                val_clean = re.sub(r'^(?:role|position|post)\s*[:\-]?\s*', '', val, flags=re.IGNORECASE).strip()
                return val_clean.title() if val_clean.islower() else val_clean

        known_roles = [
            "Software Development Engineer", "Software Engineer", "Associate Software Engineer",
            "Graduate Engineer Trainee", "Graduate Trainee", "Full Stack Developer",
            "Frontend Developer", "Backend Developer", "Data Scientist", "Data Analyst",
            "Machine Learning Engineer", "AI Engineer", "Cloud Engineer", "DevOps Engineer",
            "Cyber Security Analyst", "QA Engineer", "SDET", "System Engineer",
            "Application Developer", "Technical Consultant", "Associate Consultant",
            "Associate Trainee", "Analytics Role", "Analytics", "Software Developer"
        ]
        for role in known_roles:
            if re.search(r'\b' + re.escape(role) + r'\b', combined, re.IGNORECASE):
                return role

        return "Software Engineer / Technical Role"

    @classmethod
    def extract_package(cls, text: str, subject: str = "") -> str:
        combined = f"{subject}\n{text}"

        ctc_val = None
        stipend_val = None

        m_ctc = re.search(r'(?:CTC|Salary|Package|Compensation)\s*[:\-*]?\s*([^\n\r*]{2,70})', combined, re.IGNORECASE)
        if m_ctc:
            cand = m_ctc.group(1).strip(" *-_:\t|,")
            cand = re.sub(r'^CTC\s*[:\-]?\s*', '', cand, flags=re.IGNORECASE).strip(" *-_:\t|,")
            if re.search(r'\d', cand) and not re.search(r'\b(na|nil|none)\b', cand, re.IGNORECASE):
                ctc_val = cand

        m_stipend = re.search(r'(?:Stipend|Monthly\s*Stipend)\s*[:\-*]?\s*([^\n\r*]{2,70})', combined, re.IGNORECASE)
        if m_stipend:
            cand_stip = m_stipend.group(1).strip(" *-_:\t|,")
            cand_stip = re.sub(r'^Stipend\s*[:\-]?\s*', '', cand_stip, flags=re.IGNORECASE).strip(" *-_:\t|,")
            if re.search(r'\d', cand_stip) and not re.search(r'\b(na|nil|none|no\s*stipend)\b', cand_stip, re.IGNORECASE):
                stipend_val = cand_stip if any(sym in cand_stip for sym in ["₹", "Rs", "k", "pm", "per month"]) else f"₹{cand_stip}/month"

        if ctc_val and stipend_val:
            return f"Stipend: {stipend_val} | Full-time CTC: {ctc_val}"
        elif ctc_val:
            return ctc_val
        elif stipend_val:
            return f"Stipend: {stipend_val}"

        m_lpa = re.search(r'\b([0-9]+(?:\.[0-9]+)?\s*(?:LPA|lakhs?|lac)\b(?:\s*(?:to|-|\+)\s*[₹$]?[0-9]+(?:\.[0-9]+)?\s*(?:LPA|lakhs?|lac|Lakh)?)?)', combined, re.IGNORECASE)
        if m_lpa:
            return m_lpa.group(1).strip(" *-_:\t|,")

        if re.search(r'\bsuper\s*dream\b', combined, re.IGNORECASE):
            super_ctc = re.search(r'(?:super\s*dream\s*(?:offer|drive)?\s*[\(\[]?)([₹$]?[0-9]+(?:\.[0-9]+)?\s*(?:lpa|lakhs?|lac)?)', combined, re.IGNORECASE)
            if super_ctc and super_ctc.group(1):
                return f"Super Dream ({super_ctc.group(1).strip()})"
            return "Super Dream Offer (10+ LPA)"
        elif re.search(r'\bdream\s*offer\b', combined, re.IGNORECASE):
            return "Dream Offer (6 - 10 LPA)"
        elif re.search(r'\bregular\s*offer\b', combined, re.IGNORECASE):
            return "Regular Offer (3.5 - 6 LPA)"

        return "Refer Placement Portal / Email"

    @classmethod
    def extract_tier(cls, text: str, subject: str = "", package: str = "") -> str:
        combined = f"{subject}\n{text}".lower()
        if "super dream" in combined:
            return "🌟 Super Dream (10+ LPA) [Top Priority]"
        if any(k in combined for k in ["dream offer", "dream core", "dream internship"]):
            return "⭐ Dream Offer (6 - 10 LPA) [High Priority]"
        if any(k in combined for k in ["regular offer", "regular internship"]):
            return "🔹 Regular Offer (3.5 - 6 LPA) [Standard Priority]"
        
        m_num = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(?:lpa|lakhs?|lac)', package, re.IGNORECASE)
        if m_num:
            val = float(m_num.group(1))
            if val >= 10.0:
                return "🌟 Super Dream (10+ LPA) [Top Priority]"
            elif val >= 6.0:
                return "⭐ Dream Offer (6 - 10 LPA) [High Priority]"
            elif val >= 3.0:
                return "🔹 Regular Offer (3.5 - 6 LPA) [Standard Priority]"
        return "💼 Campus Recruitment Offer"

    @classmethod
    def extract_criteria_asked(cls, text: str, subject: str = "") -> str:
        combined = f"{subject}\n{text}"
        parts = []

        m_x_xii = re.search(r'(?:%\s*in\s*)?(?:X\s*(?:and|&|\/)\s*XII|10th\s*(?:and|&|\/)\s*12th)\s*[:\-–]?\s*([5-9][0-9](?:\.[0-9]+)?)\s*%?', combined, re.IGNORECASE)
        if m_x_xii:
            parts.append(f"{m_x_xii.group(1)}% in 10th & 12th")
        else:
            m_perc_x = re.search(r'([5-9][0-9](?:\.[0-9]+)?)\s*%\s*(?:in|for)?\s*(?:X\s*and\s*XII|10th\s*and\s*12th)', combined, re.IGNORECASE)
            if m_perc_x:
                parts.append(f"{m_perc_x.group(1)}% in 10th & 12th")

        m_deg = re.search(r'(?:in\s*pursuing\s*degree|degree|ug)\s*[:\-–]?\s*(?:[5-9][0-9]%\s*or\s*)?([0-9]\.[0-9]{1,2})\s*(?:CGPA|GPA)?', combined, re.IGNORECASE)
        if m_deg:
            parts.append(f"{m_deg.group(1)} CGPA in Degree")
        else:
            m_cgpa = re.findall(r'(?:cgpa|gpa|grade\s*point)\s*(?:>=|:|of|above|>)?\s*([0-9]\.[0-9]{1,2})', combined, re.IGNORECASE)
            if m_cgpa:
                parts.append(f"CGPA >= {max([float(c) for c in m_cgpa if float(c) <= 10.0])}")

        m_br_line = re.search(r'eligible\s*branches?\s*[:\-*]?\s*([^\n\r]+)', combined, re.IGNORECASE)
        if m_br_line:
            cand_br = m_br_line.group(1).strip(" *-_:\t|Ø")
            if len(cand_br) >= 3:
                parts.append(cand_br)
        elif re.search(r'\b(core\s*cse\s*only|b\.?tech\s*cse\s*\(?core\)?\s*only)\b', combined, re.IGNORECASE):
            parts.append("Core CSE Only")
        elif re.search(r'\b(b\.?tech\s*cse|cse\s*[\/&]\s*it)\b', combined, re.IGNORECASE):
            parts.append("B.Tech CSE / IT Related Branches")

        batch_m = re.search(r'\b(202[4-9])\s*(?:batch|passing|graduating)', combined, re.IGNORECASE)
        if batch_m:
            parts.append(f"{batch_m.group(1)} Batch")

        # History vs Standing Arrears
        if re.search(r'\b(?:no\s*history\s*of\s*arrears?|0\s*history\s*of\s*arrears?|no\s*arrears?\s*throughout)\b', combined, re.IGNORECASE):
            parts.append("No History of Arrears")
        elif re.search(r'\b(no\s*(?:standing|active)?\s*(?:arrears?|backlogs?)|0\s*arrears?)\b', combined, re.IGNORECASE):
            parts.append("No Standing Arrears")

        return " | ".join(parts) if parts else "As per standard campus placement eligibility criteria"

    @classmethod
    def extract_non_cdc_jobs(cls, text: str, subject: str = "") -> Dict[str, Any]:
        unquoted = '\n'.join([re.sub(r'^[ \t>]+', '', l) for l in text.splitlines()])
        paragraphs = [p.strip() for p in unquoted.split('\n\n') if p.strip()]

        jobs = []
        current_job = None

        for p in paragraphs:
            m_role = re.search(r'[*_·\s]*([A-Za-z0-9\s&.\-]{3,60}?(?:-\s*Intern|Intern\s*role|Engineer\s*-\s*Intern|Marketing Operations|Sales\s*-\s*Intern|Junior\s*software\s*developer|Full\s*Stack|developer\s*role|intern\s*role|analyst\s*role))\b', p, re.IGNORECASE)
            if m_role and not any(k in m_role.group(0).lower() for k in ['after the intern', 'duration', 'interested students', 'registered but']):
                title = m_role.group(1).strip(" *-_:\t|·")
                current_job = {
                    "title": title,
                    "stipend": None,
                    "ctc": None,
                    "location": None,
                    "joiner": None,
                    "action": None
                }
                jobs.append(current_job)

            if current_job:
                if "location" in p.lower():
                    m_loc = re.search(r'Location\s*[:\-*]?\s*([^\n\r*]{2,60})', p, re.IGNORECASE)
                    if m_loc and not current_job["location"]:
                        current_job["location"] = m_loc.group(1).strip(" *-_:\t|")
                if "stipend" in p.lower():
                    m_stip = re.search(r'Stipend\s*[:\-*]?\s*([^\n\r*]{2,60})', p, re.IGNORECASE)
                    if m_stip and not current_job["stipend"]:
                        current_job["stipend"] = m_stip.group(1).strip(" *-_:\t|")
                if "package" in p.lower() or "ctc" in p.lower():
                    m_ctc = re.search(r'(?:package\s*will\s*be\s*between|full-time\s*package|package|ctc)\s*(?:will\s*be)?\s*(?:between)?\s*([^\n\r*]{2,50})', p, re.IGNORECASE)
                    if m_ctc and not current_job["ctc"]:
                        current_job["ctc"] = m_ctc.group(1).strip(" *-_:\t|")
                if "start date" in p.lower() or "joiner" in p.lower():
                    m_j = re.search(r'(?:Start\s*Date|Joiner)\s*[:\-*]?\s*([^\n\r*]{2,50})', p, re.IGNORECASE)
                    if m_j and not current_job["joiner"]:
                        current_job["joiner"] = m_j.group(1).strip(" *-_:\t|")
                if any(k in p.lower() for k in ['come at', 'report at', 'meet us', 'fill the form']):
                    m_act = re.search(r'(?:Interested\s*students\s*can\s*come|come\s*at|report\s*at|meet\s*us|fill\s*the\s*form)\s*([^\n\r*]{5,80})', p, re.IGNORECASE)
                    if m_act and not current_job["action"]:
                        current_job["action"] = m_act.group(0).strip(" *-_:\t|")

        if not jobs:
            m_sub_role = re.search(r'(?:role|job|offers?)\s*[:\-]?\s*([^\n\r]{3,40})', subject, re.IGNORECASE)
            if m_sub_role:
                jobs.append({
                    "title": m_sub_role.group(1).strip(" *-_:\t|"),
                    "stipend": None,
                    "ctc": None,
                    "location": None,
                    "joiner": None,
                    "action": None
                })

        forms = re.findall(r'https?://forms\.gle/[A-Za-z0-9_\-]+', unquoted)
        linkedin = re.findall(r'https?://(?:www\.)?lnkd\.in/[A-Za-z0-9_\-]+', unquoted)
        links = list(dict.fromkeys(forms + linkedin))

        return {
            "jobs": jobs,
            "links": links
        }


class PlainEnglishExplainer:
    """
    Provides a concise 2-sentence summary for database storage and dashboard preview.
    """
    @classmethod
    def explain(cls, category: str, company: Optional[str] = None, role: Optional[str] = None, reason: Optional[str] = None) -> str:
        comp = company or "The company"
        if category == "Shortlisted / Action Required":
            return f"Official shortlist announcement for {comp}. Your profile is shortlisted!"
        elif category == "Pre-Placement Talk / Event Update":
            return f"Pre-Placement Talk scheduled for {comp} ({role or 'Open Role'}). Informational session."
        elif category == "Non-CDC / Off-Campus Placement Opportunity":
            return f"Off-campus / Non-CDC recruitment opportunities shared by Placement Office ({comp})."
        elif category == "Eligible Placement Drive":
            return f"{comp} announced a campus recruitment drive. You meet all criteria and are eligible to register."
        elif category == "Ineligible Placement Drive":
            return f"{comp} campus drive announced, but you are not eligible ({reason or 'Criteria mismatch'})."
        elif category == "Not Shortlisted for Test / Round":
            return f"Candidate selection list published for {comp}. Your Roll Number was not included."
        elif category == "Practice / Mock Exam Notice":
            return f"Voluntary practice / mock assessment announced for {comp} to help prepare for upcoming drives."
        elif "Academic" in category:
            return "Academic / University circular regarding courses, exams, or department schedules."
        return f"Campus notification regarding {comp}."


class RelevanceEngine:
    """
    Intelligent Mail Sorting and Placement Eligibility Engine for Shashwat:
    - Student: Shashwat Pratap Singh
    - Roll No: 23BAI11174
    - NeoPAT ID: S4Z5F7U9
    - Campus: VIT Bhopal
    - Degree & Branch: B.Tech CSE (AI & ML)
    - Batch: 2027
    - CGPA: 7.87
    - 10th: 72.6%
    - 12th: 69.0%
    - Standing Arrears: 0
    - History Arrears: True (Past backlogs/suppli)
    """

    PLACEMENT_KEYWORDS = [
        "placement", "campus drive", "recruitment", "hiring", "online test",
        "written test", "assessment", "shortlist", "interview", "hackathon",
        "internship", "job opportunity", "test schedule", "selection process",
        "cdc", "super dream", "dream offer", "regular offer", "test link",
        "mock test", "coding round", "technical interview", "hr round",
        "registration link", "offer letter", "oa link", "preplacement talk", "ppt",
        "non cdc", "restricted offer"
    ]

    NON_PLACEMENT_NOISE = [
        "prayer meeting", "prayer session", "morning devotion",
        "spiritual", "canteen", "hostel mess", "hostel admission", "hostel allotment",
        "gymnasium", "yoga session", "yoga class", "cricket tournament", "sports fest",
        "cultural fest", "advitiya", "rivera", "gravitas", "blood donation",
        "bus schedule", "wifi maintenance", "network outage", "fee payment reminder",
        "tuition fee", "hostel fee", "student council", "music club", "dance club",
        "security alert", "google account", "password reset", "new sign-in", "verification code",
        "dabbawala", "mental health", "happy birthday", "interactive session with vc"
    ]

    @classmethod
    def evaluate_email(
        cls,
        subject: str,
        body: str,
        attachments_data: List[Dict[str, Any]],
        profile_data: Dict[str, Any],
        body_html: Optional[str] = "",
        sender: Optional[str] = "",
        applied_companies: Optional[List[str]] = None,
        previous_thread_messages: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:

        subject_lower = subject.lower().strip()
        sender_lower = (sender or "").lower().strip()

        # 1. Detect trailing email
        is_trailing = bool(re.search(r'^(?:(?:re|fwd|fw|updated)\s*[:\-]?\s*)+', subject, re.IGNORECASE)) or bool(previous_thread_messages and len(previous_thread_messages) > 0)

        # 2. Handle unquoted context vs new update part
        unquoted_full_body = re.sub(r'^[ \t]*>[ \t]?', '', body, flags=re.MULTILINE)
        quote_split = re.split(r'(?i)\bOn\s+.*wrote:\s*', body, maxsplit=1)
        new_update_text = ""
        if len(quote_split) > 1 and is_trailing:
            new_update_text = re.split(r'(?i)(?:warm regards|with regards|director\s*\(?career development)', quote_split[0])[0].strip()
        elif is_trailing:
            new_update_text = re.split(r'(?i)(?:warm regards|with regards|director\s*\(?career development)', body)[0].strip()

        # Clean sanitized body for evaluation
        sanitized_body = re.sub(r'[\w\.-]+@[\w\.-]+', ' ', unquoted_full_body)
        clean_body_parts = re.split(r'(?i)(?:warm regards|with regards|director\s*\(?career development|vellore institute|qs world university|disclaimer:)', sanitized_body)
        clean_body_for_eval = clean_body_parts[0] if clean_body_parts else sanitized_body

        full_text = f"{subject}\n{clean_body_for_eval}"
        full_text_lower = full_text.lower()

        # 3. Extract Schedule, Dates, Times, Deadlines, Campus, Mode, Links
        datetime_info = DateTimeExtractor.extract_dates_and_times(full_text)
        primary_date = datetime_info.get("date", "As per schedule")
        primary_time = datetime_info.get("time", "Refer email")
        deadline_info = datetime_info.get("deadline")

        campus_info = CampusTravelDetector.detect_campus_and_travel(full_text)
        mode_info = ExamModeExtractor.extract_mode_and_venues(full_text, subject)
        link_data = LinkInspector.extract_links_and_venues(full_text, html=body_html or "")

        # 4. Identity matching (Roll No, NeoPAT, Name)
        roll_no = profile_data.get("roll_number", "23BAI11174").strip()
        neopat_id = profile_data.get("neopat_id", "S4Z5F7U9").strip()
        names = profile_data.get("name_variations", ["Shashwat Pratap Singh", "Shashwat Singh", "Shashwat Pratap"])
        user_email = "shashwat.23bai11174@vitbhopal.ac.in"

        sanitized_for_id = re.sub(re.escape(user_email), "RECIPIENT_EMAIL", body, flags=re.IGNORECASE)
        sanitized_sub_for_id = re.sub(re.escape(user_email), "RECIPIENT_EMAIL", subject, flags=re.IGNORECASE)

        is_security_system_mail = bool(re.search(r'(security alert|google account|password|sign-in on|verification)', subject_lower))
        identity_matches = []

        if not is_security_system_mail:
            for src_name, text in [("Subject", sanitized_sub_for_id), ("Email Body", sanitized_for_id)]:
                if not text:
                    continue
                if roll_no and re.search(r'\b' + re.escape(roll_no) + r'\b', text, re.IGNORECASE):
                    identity_matches.append({"type": "Roll Number", "term": roll_no, "source": src_name})
                if neopat_id and re.search(r'\b' + re.escape(neopat_id) + r'\b', text, re.IGNORECASE):
                    identity_matches.append({"type": "NeoPAT ID", "term": neopat_id, "source": src_name})
                for n in names:
                    if n and len(n) > 4 and re.search(r'\b' + re.escape(n) + r'\b', text, re.IGNORECASE):
                        identity_matches.append({"type": "Name", "term": n, "source": src_name})
                        break

            for att in attachments_data:
                filename = att.get("filename", "Attachment")
                for match in att.get("matches", []):
                    identity_matches.append({
                        "type": "Shortlist Attachment Hit",
                        "term": match.get("term", roll_no),
                        "source": filename,
                        "page": match.get("page", match.get("row", 1)),
                        "snippet": match.get("snippet", "")
                    })

            search_terms = [roll_no, neopat_id, profile_data.get("name", "Shashwat Pratap Singh")]
            for gsheet_url in link_data.get("google_sheets", []):
                sheet_res = LinkInspector.scan_online_google_sheet(gsheet_url, search_terms)
                if sheet_res.get("has_match"):
                    for m in sheet_res.get("matches", []):
                        identity_matches.append({
                            "type": "Online Shortlist Sheet Hit",
                            "term": m.get("term", roll_no),
                            "source": "Google Sheet Link in Email",
                            "page": m.get("row", 1),
                            "snippet": m.get("snippet", ""),
                            "venue": m.get("venue"),
                            "slot": m.get("slot")
                        })
                        if m.get("venue") and m.get("venue") not in link_data["venues"]:
                            link_data["venues"].append(m.get("venue"))
                        if m.get("slot") and m.get("slot") not in link_data["slots"]:
                            link_data["slots"].append(m.get("slot"))

            online_files = link_data.get("google_drive", []) + link_data.get("direct_excel_csv", [])
            for file_url in online_files:
                file_res = LinkInspector.scan_online_drive_or_direct_file(file_url, search_terms)
                if file_res.get("has_match"):
                    for m in file_res.get("matches", []):
                        identity_matches.append({
                            "type": "Online Drive/Excel File Hit",
                            "term": m.get("term", roll_no),
                            "source": m.get("source", "Linked File in Email"),
                            "page": m.get("row", 1),
                            "snippet": m.get("snippet", ""),
                            "venue": m.get("venue"),
                            "slot": m.get("slot")
                        })
                        if m.get("venue") and m.get("venue") not in link_data["venues"]:
                            link_data["venues"].append(m.get("venue"))
                        if m.get("slot") and m.get("slot") not in link_data["slots"]:
                            link_data["slots"].append(m.get("slot"))

        # 5. Extract Company Name
        has_placement_kw = any(kw in full_text_lower for kw in cls.PLACEMENT_KEYWORDS)
        detected_company = cls.extract_company_name(subject, clean_body_for_eval, has_placement_kw)

        # 6. Extract Role, Package, Tier, Criteria
        role_offered = JobDetailsExtractor.extract_role(unquoted_full_body, subject)
        package_offered = JobDetailsExtractor.extract_package(unquoted_full_body, subject)
        offer_tier = JobDetailsExtractor.extract_tier(clean_body_for_eval, subject, package_offered)
        criteria_asked = JobDetailsExtractor.extract_criteria_asked(unquoted_full_body, subject)

        # Helper escaped values for safe Telegram HTML
        comp_esc = escape_html(detected_company or 'Campus Recruitment')
        role_esc = escape_html(role_offered)
        pkg_esc = escape_html(package_offered)
        crit_esc = escape_html(criteria_asked)
        sched_esc = escape_html(datetime_info["formatted_schedule"])
        campus_esc = escape_html(campus_info.get('campus_display', 'VIT Bhopal Campus'))
        mode_esc = escape_html(mode_info.get("mode_desc", "Refer email"))
        deadline_str = f"<b>{escape_html(deadline_info)}</b>" if deadline_info else "Refer Portal / Email"

        # Email Classification Flags
        is_pc_sender = bool(re.search(r'(program chair|programme chair|pc\s*cse|pc\s*aiml|pc-|head of department|hod|dean|academic coordinator)', f"{sender_lower} {subject_lower}"))
        is_cdc_sender = bool(re.search(r'(placementoffice@|noreply\.cdcinfo@|director.*career development|samuel rajkumar|placement office|vitlions2027@|pat@)', f"{sender_lower} {full_text_lower[:250]}"))

        is_registration_drive = bool(re.search(
            r'\b(?:registration|register|apply\s*here|apply\s*by|apply\s*before|last\s*date\s*for\s*registration|'
            r'registration\s*link|inviting\s*applications|application\s*link|hiring\s*drive|campus\s*drive|'
            r'recruitment\s*drive|super\s*dream\s*internship\s*registration|internship\s*registration|'
            r'regular\s*internship\s*offer.*registration|dream\s*offer.*registration)\b',
            f"{subject_lower}\n{clean_body_for_eval[:500].lower()}"
        ))

        is_mock_or_practice = (
            bool(re.search(
                r'\b(?:mock\s*test|mock\s*exam|mock\s*interview|practice\s*exam|practice\s*test|'
                r'practice\s*on\s*expert\s*hire|practice\s*coding\s*round|benchmark\s*exam|'
                r'practice\s*exams?|hcl\s*practice\s*exams?)\b',
                f"{subject_lower} {clean_body_for_eval[:500].lower()}"
            ))
            and not identity_matches
        )

        # Check attachment filenames for shortlist/results indicators
        has_shortlist_attachment = False
        for att in attachments_data:
            att_fn = att.get("filename", "").lower()
            if any(kw in att_fn for kw in ["shortlist", "shortlisted", "selected", "selection", "interview", "eligible_list", "students_list"]):
                has_shortlist_attachment = True
                break

        # Check links or body for online sheet shortlist indicators
        has_shortlist_sheet = False
        if link_data.get("google_sheets") or link_data.get("google_drive") or link_data.get("direct_excel_csv"):
            if re.search(r'\b(?:shortlist(?:ed)?|selects?|selected|selection|next\s*round|interview)\b', clean_body_for_eval[:1500], re.IGNORECASE):
                has_shortlist_sheet = True

        shortlist_regex = (
            r'\b(?:shortlist(?:ed)?(?:\s*candidates?|\s*students?|\s*list)?|'
            r'selection\s*list|selected\s*candidates|selected\s*students|'
            r'final\s*selects|results?\s*(?:of|announced|declared)|'
            r'ppo\s*selection\s*list|congratulations.*selection|'
            r'next\s*round\s*(?:of\s*selection(?:\s*process)?)?|'
            r'interview\s*round|interview\s*schedule|interviews?\s*(?:is|are)?\s*scheduled|'
            r'attached\s*(?:students?\s*)?shortlisted\s*list|attached\s*shortlisted\s*students|'
            r'shortlisted\s*students\s*list|shortlist\s*for\s*.*is\s*below|'
            r'find\s*the\s*attached\s*(?:shortlisted|students\s*shortlisted)|'
            r'list\s*of\s*shortlisted|candidates\s*shortlisted|students\s*shortlisted|'
            r'online\s*test\s*is\s*scheduled\s*on.*shortlist)\b'
        )

        is_shortlist_announcement = (
            (
                bool(re.search(shortlist_regex, subject_lower))
                or bool(re.search(shortlist_regex, clean_body_for_eval[:1500].lower()))
                or has_shortlist_attachment
                or has_shortlist_sheet
            )
            and not is_mock_or_practice
        )

        is_ppt = (
            bool(re.search(r'\b(?:pre-?placement\s*talk|ppt\b|orientation\s*session|information\s*session)\b', subject_lower))
            or bool(re.search(r'\b(?:online\s*pre-?placement\s*talk|join\s*the\s*(?:ppt|pre-?placement\s*talk)|pre-?placement\s*talk\s*is\s*scheduled)\b', clean_body_for_eval.lower()))
        ) and not is_registration_drive and not is_shortlist_announcement and not is_mock_or_practice

        is_non_cdc = (
            bool(re.search(r'\b(?:non\s*cdc\s*offers?|restricted\s*offers?|cyber\s*job)\b', subject_lower))
            or (is_cdc_sender and bool(re.search(r'\b(?:non\s*cdc\s*offers?|restricted\s*offers?|in\s*god\s*bless\s*you\s*mails?|unplaced\s*(?:students\s*)?only)\b', clean_body_for_eval.lower())))
        ) and not is_shortlist_announcement and not is_registration_drive and not is_mock_or_practice

        is_academic_notice = bool(re.search(
            r'\b(?:virtual\s*seminar|seminar|webinar|workshop|guest\s*lecture|symposium|conference|'
            r'academic\s*calendar|course\s*registration|cat\s*[-–]?\s*[12]|fat\s*exam|term\s*end\s*exam|'
            r'grade\s*card|timetable|class\s*schedule|curriculum|nptel|swayam|mooc|convocation)\b',
            f"{subject_lower} {full_text_lower[:250]}"
        )) or is_pc_sender

        # Evaluation dictionary template
        evaluation = {
            "priority": "Low",
            "category": "General Circular",
            "is_placement_mail": False,
            "matched_identity": False,
            "matched_identity_details": identity_matches,
            "company_name": detected_company,
            "eligibility_status": "Neutral",
            "eligibility_notes": "",
            "schedule_date_time": datetime_info["formatted_schedule"],
            "schedule_date": primary_date,
            "schedule_time": primary_time,
            "deadline_date_time": deadline_info,
            "venues": link_data.get("venues", []),
            "slots": link_data.get("slots", []),
            "links": link_data.get("all_links", []),
            "campus_info": campus_info,
            "trigger_sound": False,
            "sound_type": "none",
            "telegram_notify": False,
            "telegram_message": "",
            "plain_english_summary": "",
            "reason": "General notice / circular."
        }

        # =========================================================================
        # CASE 1: 🎯 SHORTLISTED (Candidate Match Found)
        # =========================================================================
        if identity_matches:
            hit = identity_matches[0]
            loc_str = f"in {hit['source']}" + (f" (Page/Row {hit.get('page')})" if hit.get('page') else "")
            hit_info = f"Found {hit['type']} (<code>{escape_html(hit['term'])}</code>) {escape_html(loc_str)}"

            evaluation["matched_identity"] = True
            evaluation["priority"] = "Critical"
            evaluation["category"] = "Shortlisted / Action Required"
            evaluation["trigger_sound"] = True
            evaluation["sound_type"] = "critical_alarm"
            evaluation["telegram_notify"] = True
            evaluation["reason"] = f"🎯 SHORTLIST MATCH: Found {hit['type']} ({hit['term']}) {loc_str}!"
            evaluation["plain_english_summary"] = PlainEnglishExplainer.explain("Shortlisted / Action Required", detected_company, role_offered)

            msg_lines = [
                "🎯 <b>SHORTLISTED</b>\n",
                f"• 🏢 <b>Company:</b> <code>{comp_esc}</code>",
                f"• 💼 <b>Role:</b> <b>{role_esc}</b>",
                f"• 🎯 <b>Shortlist Details:</b> {hit_info}",
                f"• 📅 <b>Date & Time:</b> <b>{sched_esc}</b>",
                f"• 🖥️ <b>Exam / Interview Mode:</b> {mode_esc}",
                f"• 🏫 <b>Campus / Venue:</b> <b>{campus_esc}</b>"
            ]
            if campus_info.get("travel_note"):
                msg_lines.append(f"• 🚆 <b>Travel Notice:</b> <b>{campus_info['travel_note']}</b>")
            if deadline_info:
                msg_lines.append(f"• ⏳ <b>Action Deadline:</b> <b>{escape_html(deadline_info)}</b>")
            msg_lines.append("• ⚡ <b>Action Required:</b> Keep your college ID card ready, carry updated resumes, and check the portal for your exact slot.")

            evaluation["telegram_message"] = "\n".join(msg_lines)
            return evaluation

        # =========================================================================
        # CASE 2: 💼 NON-CDC / OFF-CAMPUS OPPORTUNITY (Shared by Placement Office)
        # =========================================================================
        if is_non_cdc:
            non_cdc_data = JobDetailsExtractor.extract_non_cdc_jobs(unquoted_full_body, subject)
            jobs_found = non_cdc_data.get("jobs", [])
            action_links = non_cdc_data.get("links", [])

            evaluation["priority"] = "High"
            evaluation["category"] = "Non-CDC / Off-Campus Placement Opportunity"
            evaluation["trigger_sound"] = True
            evaluation["sound_type"] = "high_priority"
            evaluation["telegram_notify"] = True
            evaluation["is_placement_mail"] = True
            evaluation["reason"] = f"💼 Non-CDC Opportunity: {detected_company or 'Off-Campus Hiring'}"
            evaluation["plain_english_summary"] = PlainEnglishExplainer.explain("Non-CDC / Off-Campus Placement Opportunity", detected_company)

            msg_lines = [
                "💼 <b>NON-CDC OPPORTUNITY / OFF-CAMPUS HIRING</b>\n",
                f"• 🏛️ <b>Shared by:</b> Placement Office (Curated External Opportunities)",
                f"• 🏢 <b>Company / Platform:</b> <code>{comp_esc}</code>"
            ]

            if jobs_found:
                msg_lines.append("\n• 📋 <b>Available Job Roles:</b>")
                for idx, j in enumerate(jobs_found[:3], 1):
                    msg_lines.append(f"  <b>{idx}. {escape_html(j['title'])}</b>")
                    stip_str = escape_html(j['stipend']) if j.get('stipend') else ""
                    ctc_str = escape_html(j['ctc']) if j.get('ctc') else ""
                    if stip_str and ctc_str:
                        msg_lines.append(f"     - 💰 <b>Stipend & CTC:</b> {stip_str} | {ctc_str}")
                    elif stip_str or ctc_str:
                        msg_lines.append(f"     - 💰 <b>Compensation:</b> {stip_str or ctc_str}")
                    if j.get('location'):
                        msg_lines.append(f"     - 📍 <b>Location:</b> {escape_html(j['location'])}")
                    if j.get('joiner'):
                        msg_lines.append(f"     - ⏳ <b>Joining:</b> {escape_html(j['joiner'])}")
                    if j.get('action'):
                        msg_lines.append(f"     - 📝 <b>Reporting / Submission:</b> {escape_html(j['action'])}")

            if action_links:
                msg_lines.append("\n• 🔗 <b>Application Links / Forms:</b>")
                for u in action_links[:3]:
                    msg_lines.append(f"  - {u}")

            msg_lines.append("\n• ⚡ <b>Action Required:</b> Review the role details and submit your CV / form or attend the session if interested. (Restricted to unplaced students).")

            evaluation["telegram_message"] = "\n".join(msg_lines)
            return evaluation

        # =========================================================================
        # CASE 3: 📢 PRE-PLACEMENT TALK (PPT / Orientation / Session)
        # =========================================================================
        if is_ppt:
            evaluation["priority"] = "High"
            evaluation["category"] = "Pre-Placement Talk / Event Update"
            evaluation["trigger_sound"] = True
            evaluation["sound_type"] = "high_priority"
            evaluation["telegram_notify"] = True
            evaluation["is_placement_mail"] = True
            evaluation["reason"] = f"📢 Pre-Placement Talk: {detected_company or 'Company'}"
            evaluation["plain_english_summary"] = PlainEnglishExplainer.explain("Pre-Placement Talk / Event Update", detected_company, role_offered)

            msg_lines = [
                "📢 <b>PRE-PLACEMENT TALK</b>\n",
                f"• 🏢 <b>Company:</b> <code>{comp_esc}</code>",
                f"• 💼 <b>Hiring Role:</b> <b>{role_esc}</b>",
                f"• 💰 <b>Package Offered:</b> <b>{pkg_esc}</b>",
                f"• 🖥️ <b>Session Mode:</b> <b>{mode_esc}</b>",
                f"• 📅 <b>Date & Time:</b> <b>{sched_esc}</b>",
                f"• 🏫 <b>Location:</b> <b>{campus_esc}</b>"
            ]
            if mode_info.get("virtual_link"):
                msg_lines.append(f"• 🔗 <b>Meeting Link:</b> {escape_html(mode_info['virtual_link'])}")
            if mode_info.get("meeting_id") or mode_info.get("passcode"):
                id_part = f"ID: <code>{escape_html(mode_info['meeting_id'])}</code>" if mode_info.get("meeting_id") else ""
                pass_part = f"Passcode: <code>{escape_html(mode_info['passcode'])}</code>" if mode_info.get("passcode") else ""
                msg_lines.append(f"• 🔑 <b>Credentials:</b> {' | '.join(filter(None, [id_part, pass_part]))}")
            msg_lines.append("• ⚡ <b>Action Required:</b> Join the session 5 minutes before scheduled time with microphone muted. (This is an informational PPT, not a test).")

            evaluation["telegram_message"] = "\n".join(msg_lines)
            return evaluation

        # =========================================================================
        # CASE 4: 🏛️ ACADEMIC NOTICE (Department / University / Program Chair)
        # =========================================================================
        if is_academic_notice and not is_cdc_sender:
            evaluation["priority"] = "High"
            evaluation["category"] = "Department / Academic Notice"
            evaluation["trigger_sound"] = True
            evaluation["sound_type"] = "high_priority"
            evaluation["telegram_notify"] = True
            evaluation["reason"] = f"🏛️ Academic / University Notice: {subject[:60]}"
            evaluation["plain_english_summary"] = PlainEnglishExplainer.explain("Department / Academic Notice")

            sender_display = "Program Chair / Academic Department"
            if "provc" in sender_lower:
                sender_display = "Pro Vice Chancellor Office"
            elif "dean" in sender_lower:
                sender_display = "Dean / Academic Directorate"
            elif "hod" in sender_lower:
                sender_display = "Head of Department (HOD)"

            clean_lines = [l.strip(" *-") for l in clean_body_for_eval.splitlines() if len(l.strip()) > 15 and not re.search(r'^(dear|regards|warm regards|director|disclaimer|on\s+.*wrote)', l.strip(), re.IGNORECASE)][:2]
            detail_lines = "\n".join([f"  • {escape_html(cl[:110])}..." if len(cl) > 110 else f"  • {escape_html(cl)}" for cl in clean_lines])

            msg_lines = [
                "🏛️ <b>ACADEMIC NOTICE</b>\n",
                f"• 🏛️ <b>From:</b> {escape_html(sender_display)}",
                f"• 📅 <b>Date & Time:</b> <b>{sched_esc}</b>",
                f"• 🏫 <b>Campus:</b> <b>VIT Bhopal Campus</b>",
                f"• 📋 <b>Key Details:</b>\n{detail_lines}",
                "• ⚡ <b>Action Required:</b> Review your academic calendar/timetable and adhere to instructions given."
            ]
            evaluation["telegram_message"] = "\n".join(msg_lines)
            return evaluation

        # =========================================================================
        # CASE 5: ℹ️ NOT SHORTLISTED (Shortlist Published, Roll No Not Found)
        # =========================================================================
        if is_shortlist_announcement and not identity_matches:
            evaluation["priority"] = "Medium"
            evaluation["category"] = "Not Shortlisted for Test / Round"
            evaluation["trigger_sound"] = False
            evaluation["telegram_notify"] = True
            evaluation["reason"] = f"ℹ️ Shortlist published for {detected_company or 'Drive'}, but Roll No was not found."
            evaluation["plain_english_summary"] = PlainEnglishExplainer.explain("Not Shortlisted for Test / Round", detected_company)

            msg_lines = [
                "ℹ️ <b>NOT SHORTLISTED</b>\n",
                f"• 🏢 <b>Company:</b> <code>{comp_esc}</code>",
                f"• 💼 <b>Role:</b> <b>{role_esc}</b>",
                f"• 📋 <b>Result:</b> Candidate selection / shortlist published for this round, but your Roll No (<code>{escape_html(roll_no)}</code>) was <b>not found</b> in the list.",
                f"• 📅 <b>Published Date:</b> <b>{escape_html(primary_date)}</b>",
                f"• 🏫 <b>Campus:</b> <b>{campus_esc}</b>",
                "• ⚡ <b>Action Required:</b> No action needed. You were not shortlisted for this round. Keep preparing for upcoming opportunities."
            ]
            evaluation["telegram_message"] = "\n".join(msg_lines)
            return evaluation

        # =========================================================================
        # CASE 5B: 📢 PRACTICE / MOCK EXAM NOTICE (Voluntary Practice Session)
        # =========================================================================
        if is_mock_or_practice:
            evaluation["priority"] = "Medium"
            evaluation["category"] = "Practice / Mock Exam Notice"
            evaluation["trigger_sound"] = False
            evaluation["telegram_notify"] = True
            evaluation["reason"] = f"📢 Practice / Mock Session: {detected_company or 'Practice Exam'}"
            evaluation["plain_english_summary"] = PlainEnglishExplainer.explain("Practice / Mock Exam Notice", detected_company)

            msg_lines = [
                "📢 <b>PRACTICE / MOCK EXAM NOTICE</b>\n",
                f"• 🏢 <b>Company / Topic:</b> <code>{comp_esc}</code>",
                f"• 📋 <b>Details:</b> Voluntary practice / mock assessment announced to help students prepare for upcoming recruitment drives.",
                f"• 📅 <b>Date & Time:</b> <b>{sched_esc}</b>",
                f"• 🏫 <b>Venue / Platform:</b> <b>{campus_esc}</b>",
                "• ⚡ <b>Action Required:</b> This is optional practice (not an official selection drive). Attend if you wish to practise."
            ]
            evaluation["telegram_message"] = "\n".join(msg_lines)
            return evaluation

        # =========================================================================
        # CASE 6 & 7: PLACEMENT RECRUITMENT DRIVE / TRAILING UPDATE
        # =========================================================================
        is_placement_drive = is_registration_drive or has_placement_kw or (detected_company and not any(kw in subject_lower for kw in cls.NON_PLACEMENT_NOISE))

        if is_placement_drive or is_trailing:
            evaluation["is_placement_mail"] = True
            eligibility = cls.check_eligibility(unquoted_full_body, subject, profile_data, campus_info)
            evaluation["eligibility_status"] = eligibility["status"]
            evaluation["eligibility_notes"] = eligibility["notes"] if eligibility["is_eligible"] else eligibility["ineligible_reason"]

            # Inspect previous thread messages for ineligibility inheritance
            prior_ineligible = False
            prior_reason = ""
            if previous_thread_messages:
                for pm in previous_thread_messages:
                    if pm.get("eligibility_status") == "Ineligible" or pm.get("category") == "Ineligible Placement Drive":
                        prior_ineligible = True
                        prior_reason = pm.get("eligibility_notes") or pm.get("reason") or "Criteria cutoff mismatch"
                        if "INELIGIBLE DRIVE" in prior_reason:
                            prior_reason = re.sub(r'^.*?:\s*', '', prior_reason)
                        break

            # Handle Trailing Email Update
            if is_trailing:
                update_summary = new_update_text if new_update_text else "Update regarding recruitment drive / process."
                update_summary = re.sub(r'\s+', ' ', update_summary).strip()
                if len(update_summary) > 200:
                    update_summary = update_summary[:197] + "..."

                if prior_ineligible or not eligibility["is_eligible"]:
                    reason_text = prior_reason or eligibility["ineligible_reason"]
                    evaluation["priority"] = "Low"
                    evaluation["category"] = "Ineligible Placement Drive"
                    evaluation["trigger_sound"] = False
                    evaluation["telegram_notify"] = True
                    evaluation["reason"] = f"❌ INELIGIBLE DRIVE UPDATE ({detected_company}): {reason_text}"
                    evaluation["plain_english_summary"] = PlainEnglishExplainer.explain("Ineligible Placement Drive", detected_company, role_offered, reason_text)

                    msg_lines = [
                        "❌ <b>NOT ELIGIBLE (UPDATE)</b>\n",
                        f"• 🏢 <b>Company:</b> <code>{comp_esc}</code>",
                        f"• 💼 <b>Role:</b> <b>{role_esc}</b>",
                        f"• 🏆 <b>Offer Tier:</b> {offer_tier}",
                        f"• ⚠️ <b>Drive Status:</b> You are <b>NOT ELIGIBLE</b> for this drive ({escape_html(reason_text)}).",
                        f"• 📢 <b>Update in this email:</b> {escape_html(update_summary)}",
                        "• ⚡ <b>Action Required:</b> No action needed as you were not eligible to apply for this drive."
                    ]
                    evaluation["telegram_message"] = "\n".join(msg_lines)
                    return evaluation
                else:
                    evaluation["priority"] = "High"
                    evaluation["category"] = "Eligible Placement Drive"
                    evaluation["trigger_sound"] = True
                    evaluation["sound_type"] = "high_priority"
                    evaluation["telegram_notify"] = True
                    evaluation["reason"] = f"✅ ELIGIBLE DRIVE UPDATE ({detected_company})"
                    evaluation["plain_english_summary"] = PlainEnglishExplainer.explain("Eligible Placement Drive", detected_company, role_offered)

                    msg_lines = [
                        "✅ <b>ELIGIBLE (UPDATE)</b>\n",
                        f"• 🏢 <b>Company:</b> <code>{comp_esc}</code>",
                        f"• 💼 <b>Role:</b> <b>{role_esc}</b>",
                        f"• 💰 <b>Package:</b> <b>{pkg_esc}</b>",
                        f"• 🏆 <b>Offer Tier:</b> {offer_tier}",
                        f"• 📢 <b>Update in this email:</b> {escape_html(update_summary)}",
                        f"• 📅 <b>Drive Date / Schedule:</b> <b>{sched_esc}</b>",
                        f"• 🏫 <b>Campus / Venue:</b> <b>{campus_esc}</b>",
                        "• ⚡ <b>Action Required:</b> Review the updated instructions on the placement portal."
                    ]
                    evaluation["telegram_message"] = "\n".join(msg_lines)
                    return evaluation

            # Open New Placement Drive Evaluation
            if eligibility["is_eligible"]:
                evaluation["priority"] = "High"
                evaluation["category"] = "Eligible Placement Drive"
                evaluation["trigger_sound"] = True
                evaluation["sound_type"] = "high_priority"
                evaluation["telegram_notify"] = True
                evaluation["reason"] = f"✅ ELIGIBLE DRIVE ({detected_company or 'Company'}): Meets all criteria."
                evaluation["plain_english_summary"] = PlainEnglishExplainer.explain("Eligible Placement Drive", detected_company, role_offered)

                msg_lines = [
                    "✅ <b>ELIGIBLE</b>\n",
                    f"• 🏢 <b>Company:</b> <code>{comp_esc}</code>",
                    f"• 💼 <b>Role:</b> <b>{role_esc}</b>",
                    f"• 💰 <b>Package / CTC Offered:</b> <b>{pkg_esc}</b>",
                    f"• 🏆 <b>Offer Tier:</b> {offer_tier}",
                    f"• 📋 <b>Criteria Asked:</b> {crit_esc}",
                    f"• 👤 <b>Your Status:</b> Confirmed Eligible (Your CGPA: {profile_data.get('current_cgpa', 7.87)}, 10th: {profile_data.get('tenth_percentage', 72.6)}%, 12th: {profile_data.get('twelfth_percentage', 69.0)}%)",
                    f"• 🖥️ <b>Exam Mode & Platform:</b> {mode_esc}",
                    f"• 📅 <b>Test / Drive Date:</b> <b>{sched_esc}</b>",
                    f"• 🏫 <b>Campus / Venue:</b> <b>{campus_esc}</b>"
                ]
                if campus_info.get("travel_note"):
                    msg_lines.append(f"• 🚆 <b>Travel Note:</b> <b>{campus_info['travel_note']}</b>")
                msg_lines.append(f"• ⏳ <b>Last Date to Apply:</b> {deadline_str}")
                msg_lines.append("• ⚡ <b>Action Required:</b> Complete your registration on the NeoPAT / Placement portal before the deadline.")

                evaluation["telegram_message"] = "\n".join(msg_lines)
                return evaluation
            else:
                evaluation["priority"] = "Medium"
                evaluation["category"] = "Ineligible Placement Drive"
                evaluation["trigger_sound"] = False
                evaluation["telegram_notify"] = True
                evaluation["reason"] = f"❌ INELIGIBLE DRIVE ({detected_company or 'Company'}): {eligibility['ineligible_reason']}"
                evaluation["plain_english_summary"] = PlainEnglishExplainer.explain("Ineligible Placement Drive", detected_company, role_offered, eligibility['ineligible_reason'])

                reason_esc = escape_html(eligibility["ineligible_reason"])
                msg_lines = [
                    "❌ <b>NOT ELIGIBLE</b>\n",
                    f"• 🏢 <b>Company:</b> <code>{comp_esc}</code>",
                    f"• 💼 <b>Role:</b> <b>{role_esc}</b>",
                    f"• 💰 <b>Package Offered:</b> <b>{pkg_esc}</b>",
                    f"• 🏆 <b>Offer Tier:</b> {offer_tier}",
                    f"• 📋 <b>Criteria Asked:</b> {crit_esc}",
                    f"• ⚠️ <b>Reason:</b> <b>{reason_esc}</b>",
                    f"• 📅 <b>Drive Date:</b> {sched_esc}",
                    f"• 🏫 <b>Campus:</b> {campus_esc}"
                ]
                if campus_info.get("travel_note"):
                    msg_lines.append(f"• 🚆 <b>Travel Note:</b> {campus_info['travel_note']}")
                msg_lines.append("• ⚡ <b>Action Required:</b> Do not apply. You do not meet the minimum academic cutoffs for this company.")

                evaluation["telegram_message"] = "\n".join(msg_lines)
                return evaluation

        # =========================================================================
        # CASE 8: CDC / PLACEMENT OFFICE IMPORTANT GENERAL UPDATE
        # =========================================================================
        if is_cdc_sender:
            evaluation["priority"] = "High"
            evaluation["category"] = "CDC / Placement Office Important Update"
            evaluation["trigger_sound"] = True
            evaluation["sound_type"] = "high_priority"
            evaluation["telegram_notify"] = True
            evaluation["reason"] = f"📢 Placement Office Update: {subject[:60]}"
            evaluation["plain_english_summary"] = "Placement Office / CDC notification regarding campus guidelines."

            clean_lines = [l.strip(" *-") for l in clean_body_for_eval.splitlines() if len(l.strip()) > 15 and not re.search(r'^(dear|regards|warm regards|director|disclaimer|on\s+.*wrote)', l.strip(), re.IGNORECASE)][:2]
            detail_lines = "\n".join([f"  • {escape_html(cl[:110])}..." if len(cl) > 110 else f"  • {escape_html(cl)}" for cl in clean_lines])

            msg_lines = [
                "📢 <b>PLACEMENT OFFICE UPDATE</b>\n",
                f"• 🏛️ <b>From:</b> Placement Office / CDC Director",
                f"• 📅 <b>Date & Time:</b> <b>{sched_esc}</b>",
                f"• 🏫 <b>Campus:</b> <b>{campus_esc}</b>",
                f"• 📋 <b>Instructions:</b>\n{detail_lines}",
                "• ⚡ <b>Action Required:</b> Review the instructions and ensure full compliance."
            ]
            evaluation["telegram_message"] = "\n".join(msg_lines)
            return evaluation

        # Fallback General Circular
        return evaluation

    @classmethod
    def check_eligibility(cls, body_text: str, subject: str, profile: Dict[str, Any], campus_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        user_cgpa = float(profile.get("current_cgpa", 7.87))
        user_10th = float(profile.get("tenth_percentage", 72.6))
        user_12th = float(profile.get("twelfth_percentage", 69.0))
        user_batch = int(profile.get("batch_year", 2027))
        user_branch = str(profile.get("branch", "CSE (AI & ML)")).lower()
        user_standing = int(profile.get("standing_arrears", 0))
        user_history = bool(profile.get("history_arrears", True))

        combined_text = f"{subject}\n{body_text}"
        notes = []
        ineligible_reasons = []
        is_eligible = True

        # 1. Campus restriction
        if campus_info and campus_info.get("is_bhopal_excluded"):
            is_eligible = False
            ineligible_reasons.append("Restricted to VIT Vellore/Chennai campus (You are at VIT Bhopal)")

        # 2. 10th / 12th Cutoffs (including Roman numerals X and XII)
        req_10th = None
        req_12th = None

        m_x_xii = re.search(r'(?:%\s*in\s*)?(?:X\s*(?:and|&|\/)\s*XII|10th\s*(?:and|&|\/)\s*12th)\s*[:\-–]?\s*([5-9][0-9](?:\.[0-9]+)?)\s*%?', combined_text, re.IGNORECASE)
        if m_x_xii:
            val = float(m_x_xii.group(1))
            req_10th = val
            req_12th = val

        m_perc_x_xii = re.search(r'([5-9][0-9](?:\.[0-9]+)?)\s*%\s*(?:or\s*[0-9]\.[0-9]+\s*CGPA\s*)?(?:in|throughout|for)?\s*(?:X\s*(?:and|&|\/)\s*XII|10th\s*(?:and|&|\/)\s*12th)', combined_text, re.IGNORECASE)
        if m_perc_x_xii:
            val = float(m_perc_x_xii.group(1))
            req_10th = max(req_10th or 0, val)
            req_12th = max(req_12th or 0, val)

        m_perc_gen = re.findall(r'([5-9][0-9](?:\.[0-9]+)?)\s*%\s*(?:in|throughout|in 10th|and 12th|in 12th|in 10th/12th|academics)', combined_text, re.IGNORECASE)
        for p in m_perc_gen:
            val = float(p)
            req_10th = max(req_10th or 0, val)
            req_12th = max(req_12th or 0, val)

        if req_10th is not None or req_12th is not None:
            cutoff = max(req_10th or 0, req_12th or 0)
            if user_10th < cutoff or user_12th < cutoff:
                is_eligible = False
                reasons = []
                if user_12th < cutoff:
                    reasons.append(f"Requires 12th >= {cutoff}% (You have {user_12th}%)")
                if user_10th < cutoff:
                    reasons.append(f"Requires 10th >= {cutoff}% (You have {user_10th}%)")
                ineligible_reasons.append(" and ".join(reasons))
            else:
                notes.append(f"10th & 12th >= {cutoff}% (You: 10th {user_10th}%, 12th {user_12th}%)")

        # 3. CGPA Cutoffs
        req_cgpa = None
        m_deg_cgpa = re.search(r'(?:in\s*pursuing\s*degree|degree|ug)\s*[:\-–]?\s*(?:[5-9][0-9]%\s*or\s*)?([0-9]\.[0-9]{1,2})\s*(?:CGPA|GPA)?', combined_text, re.IGNORECASE)
        if m_deg_cgpa:
            req_cgpa = float(m_deg_cgpa.group(1))

        m_num_cgpa = re.findall(r'\b([5-9]\.[0-9]{1,2})\s*(?:or\s*above\s*)?(?:CGPA|GPA)\b', combined_text, re.IGNORECASE)
        for c in m_num_cgpa:
            val = float(c)
            if 5.0 <= val <= 10.0:
                req_cgpa = max(req_cgpa or 0, val)

        m_cgpa_num = re.findall(r'(?:CGPA|GPA|grade\s*point)\s*(?:>=|:|of|above|>)?\s*([0-9]\.[0-9]{1,2})', combined_text, re.IGNORECASE)
        for c in m_cgpa_num:
            val = float(c)
            if 5.0 <= val <= 10.0:
                req_cgpa = max(req_cgpa or 0, val)

        if req_cgpa is not None:
            if user_cgpa >= req_cgpa:
                notes.append(f"CGPA >= {req_cgpa} (You: {user_cgpa})")
            else:
                is_eligible = False
                ineligible_reasons.append(f"Requires CGPA >= {req_cgpa} (You have {user_cgpa})")

        # 4. Batch Check
        batch_match = re.search(r'\b(202[4-9])\s*(?:batch|passing|graduating)', combined_text, re.IGNORECASE)
        if batch_match:
            req_batch = int(batch_match.group(1))
            if req_batch == user_batch:
                notes.append(f"Batch: {req_batch}")
            else:
                is_eligible = False
                ineligible_reasons.append(f"Targeting {req_batch} Batch (You are {user_batch} Batch)")

        # 5. Core CSE Only check
        core_cse_only = bool(re.search(
            r'\b(?:computer science and engineering\s*only|core\s*cse\s*only|b\.?tech\s*cse\s*\(?core\)?\s*only|only\s*b\.?tech\s*cse\s*\(?core\)?|cse\s*only\s*\(no specializations?\))\b',
            combined_text,
            re.IGNORECASE
        ))
        if core_cse_only:
            is_eligible = False
            ineligible_reasons.append("Restricted to Core CSE only (You are CSE AI & ML)")

        # 6. Branch Check (Non-CSE vs CSE)
        m_br_line = re.search(r'eligible\s*branches?\s*[:\-*]?\s*([^\n\r]+(?:\n[^\n\r]+){0,3})', combined_text, re.IGNORECASE)
        branch_scope = m_br_line.group(1).lower() if m_br_line else combined_text.lower()

        cse_allowed = bool(re.search(
            r'\b(?:cse\b|computer\s*science|it\b|information\s*technology|ai\b|aiml|artificial\s*intelligence|software|circuital|all\s*branches|all\s*b\.?tech|open\s*to\s*all)\b',
            branch_scope
        ))

        non_cse_branch = re.search(
            r'\b(mechanical|mech|civil|chemical|biotechnology|biotech|biomedical|aerospace|automobile|mba|mca|bca|m\.sc|msc|b\.sc|bsc|m\.tech|law)\b',
            branch_scope
        )
        if non_cse_branch and not cse_allowed:
            is_eligible = False
            ineligible_reasons.append(f"Restricted to {non_cse_branch.group(1).upper()} (You are B.Tech CSE AI&ML)")
        elif re.search(r'\b(?:biotechnology\s*only|civil\s*(?:engineering\s*)?only|mechanical\s*only|mca\s*only|mba\s*only)\b', combined_text, re.IGNORECASE):
            is_eligible = False
            ineligible_reasons.append("Restricted to non-CSE discipline (You are B.Tech CSE AI&ML)")

        # 7. Arrears & Backlogs Check (Standing vs History)
        history_req = bool(re.search(
            r'\b(?:no\s*history\s*of\s*(?:arrears?|backlogs?)|0\s*history\s*of\s*arrears?|'
            r'history\s*of\s*arrears?\s*[:\-–]?\s*0|no\s*arrears?\s*in\s*history|'
            r'no\s*(?:standing\s*or\s*history|history\s*or\s*standing)\s*arrears?|'
            r'no\s*(?:arrears?|backlogs?)\s*throughout\s*(?:academics?|engineering|degree))\b',
            combined_text,
            re.IGNORECASE
        ))
        if history_req and user_history:
            is_eligible = False
            ineligible_reasons.append("Requires No History of Arrears (You have a past backlog/suppli history)")
        elif not history_req:
            # Check standing arrears
            m_stand = re.search(r'(?:standing\s*arrears?|active\s*backlogs?)\s*(?:allowed|<=|:)?\s*([0-9]+)', combined_text, re.IGNORECASE)
            allowed_stand = int(m_stand.group(1)) if m_stand else 0
            if user_standing > allowed_stand:
                is_eligible = False
                ineligible_reasons.append(f"Requires <= {allowed_stand} standing arrears (You have {user_standing})")
            elif re.search(r'\b(?:no\s*standing\s*arrears?|0\s*standing\s*arrears?|no\s*active\s*backlogs?)\b', combined_text, re.IGNORECASE):
                notes.append("No Standing Arrears (You have 0)")

        status = "Eligible" if is_eligible else "Ineligible"
        return {
            "is_eligible": is_eligible,
            "status": status,
            "notes": " | ".join(notes) if notes else "Meets B.Tech CSE (AI & ML) 2027 criteria",
            "ineligible_reason": " | ".join(ineligible_reasons) if ineligible_reasons else "Criteria mismatch"
        }

    @classmethod
    def extract_company_name(cls, subject: str, body: str, has_placement_kw: bool = True) -> Optional[str]:
        clean_sub = re.sub(r'^(?:(?:re|fwd|fw|updated)\b\s*[:\-]?\s*)+', '', subject, flags=re.IGNORECASE).strip()

        # 1. Check explicit "Name of the Company: <Name>" or "Company profile: <Name>" in body
        m_body_comp = re.search(r'(?:name of the company|company profile|company name)\s*[\*:]*\s*[:\-]?\s*[\*:]*\s*([A-Za-z0-9\s&.\-]{2,50})', body, re.IGNORECASE)
        if m_body_comp:
            cand = m_body_comp.group(1).strip(" *-_:\t|")
            if len(cand) >= 2 and cand.lower() not in ["tbd", "na", "refer email", "applicable", "none"]:
                return cand

        # 2. Ignore academic / general university events
        if re.search(r'\b(virtual\s*seminar|seminar|webinar|workshop|symposium|conference|academic\s*calendar|course\s*registration|exam|circular|convocation)\b', clean_sub, re.IGNORECASE):
            return None

        # 3. Known Companies check (Subject first, then Body)
        KNOWN_COMPANIES = [
            "HCLTech", "HCL Tech", "HCL", "Synopsys", "Hitachi", "Salesforce", "Threatcop",
            "Yaanendriya Inc", "Yaanendriya", "Aethrone Aerospace",
            "Deloitte", "Celebal", "HP", "Mobolutions", "Human Resocia", "Schneider Electric",
            "Tresvista", "Embitel", "Alcatel", "Infosys", "Myntra", "Capgemini", "Palo Alto",
            "Citi India", "Masal.ai", "MASAL AI", "LTIMindtree", "Virtusa", "TCS", "Wipro", "Amazon",
            "Microsoft", "Google", "DE Shaw", "L&T", "Larsen & Toubro", "Oracle", "Cisco",
            "Goldman Sachs", "JPMorgan", "Morgan Stanley", "Optum", "BNY Mellon", "Accenture",
            "ContraVault AI", "ContraVault", "Metro Brands", "AB InBev", "WINFra", "WINFra Technical",
            "Mediatek", "Labcorp", "DHL IT Services India", "DHL IT Services", "DHL", "Innovites", "Cognizant"
        ]
        sub_norm = re.sub(r'[\s\xa0]+', ' ', clean_sub)
        for comp in KNOWN_COMPANIES:
            if re.search(r'\b' + re.escape(comp) + r'\b', sub_norm, re.IGNORECASE):
                return comp

        if has_placement_kw:
            # Strip URLs before scanning body to prevent docs.google.com from matching Google
            body_no_urls = re.sub(r'https?://\S+', ' ', body[:3000])
            body_norm = re.sub(r'[\s\xa0]+', ' ', body_no_urls)
            for comp in KNOWN_COMPANIES:
                if re.search(r'\b' + re.escape(comp) + r'\b', body_norm, re.IGNORECASE):
                    return comp

        # 4. Mock Drive check
        m_mock = re.search(r'mock for\s+([A-Za-z0-9\s&.\-]+?)(?:\s+\d|\s+pm|\s+am|$)', clean_sub, re.IGNORECASE)
        if m_mock:
            return f"{m_mock.group(1).strip(' -:_|')} (Mock Drive)"

        # 5. CDC Subject pattern before drive type: e.g. "COMPANY - Super Dream / Dream / Regular"
        m_cdc_sub = re.search(r'^([A-Za-z0-9\s&.\-]{2,40}?)\s*[-:]?\s*(?:Super\s*Dream|Dream\s*offer|Regular\s*Internship|Regular\s*offer|Hiring|Internship\s*Offer|Assessment)', clean_sub, re.IGNORECASE)
        if m_cdc_sub:
            cand = m_cdc_sub.group(1).strip(" *-_:\t|")
            if len(cand) >= 2 and cand.lower() not in ["congratulations", "urgent", "important", "all", "students", "campus"]:
                return cand

        # 6. Selection / Shortlist / Drive pattern matching
        m_prefix = re.search(
            r'(?:selection\s*list\s*(?:of|for)?|selects\s*of|shortlist(?:ed)?\s*(?:for|of|candidates)?|'
            r'results?\s*of|campus\s*drive\s*(?:for|of)?|hiring\s*(?:at|for)?|opportunity\s*at|'
            r'registration\s*(?:for|of)?|recruitment\s*(?:for|of)?)\s+([A-Za-z0-9\s&.\-]{2,30})',
            clean_sub,
            re.IGNORECASE
        )
        if m_prefix:
            c = m_prefix.group(1).strip(" *-_:\t|")
            c_clean = re.sub(r'\b(campus|drive|batch|\d{4}|written|online|test|round|interview|process|announcement)\b', '', c, flags=re.IGNORECASE).strip(" *-_:\t|")
            if c_clean and len(c_clean) >= 2:
                return c_clean

        m = re.search(r'^(?:Campus Drive|Hiring|Recruitment|Assessment|Drive|Placement)?\s*[-:]?\s*([A-Za-z0-9\s&.\-]{2,30}?)\s+(?:written test|online test|next round|recruitment|drive|test link|hiring|shortlist|super dream|dream offer|registration|regular offer|hackathon|interview|selection)', clean_sub, re.IGNORECASE)
        if m:
            c = m.group(1).strip(" *-_:\t|")
            c_clean = re.sub(r'^(congratulations|urgent|important|dear students|all students|notice|regarding|schedule|kind attention)\s*[:!]?\s*', '', c, flags=re.IGNORECASE).strip(" *-_:\t|")
            if c_clean and len(c_clean) >= 2 and c_clean.lower() not in ["god bless", "prayer", "all", "students", "batch", "important", "urgent", "campus", "selection list", "shortlist"]:
                return c_clean

        if has_placement_kw:
            words = clean_sub.split()
            if len(words) >= 2 and words[0].lower() not in ["circular", "notice", "important", "urgent", "meeting", "dear", "all", "students", "schedule", "god", "prayer", "selection", "virtual", "seminar", "webinar", "workshop"]:
                return f"{words[0]} {words[1]}".replace(":", "").replace("-", "").strip(" *-_:\t|")

        return None
