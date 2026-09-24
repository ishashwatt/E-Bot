import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from app.services.link_inspector import LinkInspector

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

        deadline_match = re.search(r'(?:deadline|last date|register by|closes on|closing date|before|apply by)\s*(?:to\s*apply\s*)?[:\-]?\s*([^.\n\r]{5,45})', clean_text, re.IGNORECASE)
        if deadline_match:
            d_val = deadline_match.group(1).strip()
            d_val = re.sub(r'^(?:to\s*apply|is|by)\s*[:\-]?\s*', '', d_val, flags=re.IGNORECASE).strip()
            results["deadline"] = d_val

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
    and physical travel requirements for shortlisted interviews / tests.
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

        requires_vellore_travel = bool(re.search(
            r'(?:travel\s*(?:to|down\s*to)\s*(?:vit\s*)?vellore|'
            r'report\s*(?:at|to)\s*(?:vit\s*)?vellore|'
            r'shortlisted\s*students\s*must\s*(?:travel|report|visit)\s*(?:to\s*)?(?:vit\s*)?vellore|'
            r'in-person\s*(?:interview|round|assessment)\s*at\s*(?:vit\s*)?vellore|'
            r'offline\s*(?:interview|round|assessment)\s*at\s*(?:vit\s*)?vellore|'
            r'venue\s*:\s*(?:vit\s*)?vellore|'
            r'anna\s*auditorium|technology\s*tower|sjtt\s*vellore|'
            r'travelling\s*students\s*are\s*exempt|ey\s*and\s*vellore\s*or\s*travelling)',
            text_lower
        ))

        travel_note = None
        campus_display = "VIT Bhopal (Local / Virtual)"
        if requires_vellore_travel:
            travel_note = "⚠️ In-Person / Physical reporting required at VIT Vellore campus (Travel required from VIT Bhopal)!"
            campus_display = "⚠️ VIT Vellore Campus (Travel Required)"
        elif "VIT Bhopal" in campuses_found:
            campus_display = "VIT Bhopal Campus"
        elif len(campuses_found) > 1:
            campus_display = f"All VIT Campuses ({', '.join(campuses_found)})"

        return {
            "campuses_found": campuses_found,
            "is_bhopal_excluded": is_bhopal_excluded,
            "requires_vellore_travel": requires_vellore_travel,
            "travel_note": travel_note,
            "campus_display": campus_display
        }

    @classmethod
    def format_clean_bullets(cls, text: str, max_points: int = 4) -> str:
        """
        Splits text into concise, readable bullet points for Telegram messages.
        """
        if not text:
            return ""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        bullets = []
        for l in lines:
            if re.search(r'^(on\s+.*wrote:|dear\s+students|regards|warm regards|director|vellore institute|disclaimer:)', l, re.IGNORECASE):
                continue
            if len(l) > 10:
                clean_l = l if len(l) <= 120 else l[:117] + "..."
                bullets.append(f"  • {clean_l}")
            if len(bullets) >= max_points:
                break
        return "\n".join(bullets) if bullets else f"  • {text[:150]}..."


class JobDetailsExtractor:
    """
    Intelligently extracts Job Role/Profile, CTC / Stipend offered,
    and Stated Criteria from email content.
    """

    @classmethod
    def extract_role(cls, text: str, subject: str = "") -> str:
        combined = f"{subject}\n{text}"
        
        # Explicit labels
        m_label = re.search(
            r'(?:job\s*role|role|position|designation|job\s*profile|job\s*title|hiring\s*for)\s*[:\-]\s*([^\n\r,;]{2,50})',
            combined,
            re.IGNORECASE
        )
        if m_label:
            val = m_label.group(1).strip()
            if len(val) >= 2 and not re.search(r'(refer|attached|below|as per|eligible|criteria|students|batch)', val, re.IGNORECASE):
                return val

        # Common job titles in tech campus drives
        known_roles = [
            "Software Development Engineer", "Software Engineer", "Associate Software Engineer",
            "Graduate Engineer Trainee", "Graduate Trainee", "Full Stack Developer",
            "Frontend Developer", "Backend Developer", "Data Scientist", "Data Analyst",
            "Machine Learning Engineer", "AI Engineer", "Cloud Engineer", "DevOps Engineer",
            "Cyber Security Analyst", "QA Engineer", "SDET", "System Engineer",
            "Application Developer", "Technical Consultant", "Associate Consultant",
            "Member Technical Staff", "SDE-1", "SDE Intern", "Software Developer"
        ]
        for role in known_roles:
            if re.search(r'\b' + re.escape(role) + r'\b', combined, re.IGNORECASE):
                return role

        return "Software Engineer / Technical Role"

    @classmethod
    def extract_package(cls, text: str, subject: str = "") -> str:
        combined = f"{subject}\n{text}"

        # Explicit CTC/Stipend labels with numbers
        m_ctc = re.search(
            r'(?:ctc|package|salary|stipend|compensation|remuneration|offering)\s*[:\-]?\s*([₹$]?[0-9]+(?:\.[0-9]+)?\s*(?:lpa|lakhs?|lac|k|pm|per\s*month|per\s*annum|inr)?(?:\s*(?:to|-)\s*[₹$]?[0-9]+(?:\.[0-9]+)?\s*(?:lpa|lakhs?|lac|k|pm)?)?)',
            combined,
            re.IGNORECASE
        )
        if m_ctc and re.search(r'\d', m_ctc.group(1)):
            val = m_ctc.group(1).strip()
            if len(val) >= 2:
                return val

        # Direct LPA mentions (e.g. 12 LPA, 8.5 LPA, 24 LPA)
        m_lpa = re.search(r'\b([0-9]+(?:\.[0-9]+)?\s*(?:LPA|lakhs?|lac)\b(?:\s*(?:to|-)\s*[0-9]+(?:\.[0-9]+)?\s*(?:LPA|lakhs?|lac))?)', combined, re.IGNORECASE)
        if m_lpa:
            return m_lpa.group(1).strip()

        # Monthly stipend mentions (e.g. 45k/month, 50,000/pm)
        m_stipend = re.search(r'\b([₹$]?[0-9]{2,6}\s*(?:k|\/month|\/pm|per\s*month))\b', combined, re.IGNORECASE)
        if m_stipend:
            return f"Stipend: {m_stipend.group(1).strip()}"

        # Super Dream / Dream labels
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
    def extract_criteria_asked(cls, text: str, subject: str = "") -> str:
        combined = f"{subject}\n{text}"
        criteria_parts = []

        # CGPA
        cgpa_m = re.findall(r'(?:cgpa|gpa|grade\s*point)\s*(?:>=|:|of|above|>)?\s*([0-9]\.[0-9]{1,2})', combined, re.IGNORECASE)
        if cgpa_m:
            req_c = max([float(c) for c in cgpa_m if float(c) <= 10.0])
            criteria_parts.append(f"CGPA >= {req_c}")

        # 10th / 12th Percentage
        perc_m = re.findall(r'([5-9][0-9])%\s*(?:in|throughout|in 10th|and 12th|in 12th|in 10th/12th|academics)', combined, re.IGNORECASE)
        if perc_m:
            req_p = max([float(p) for p in perc_m])
            criteria_parts.append(f"10th & 12th >= {req_p}%")

        # Branches
        if re.search(r'\b(core\s*cse\s*only|b\.?tech\s*cse\s*\(?core\)?\s*only)\b', combined, re.IGNORECASE):
            criteria_parts.append("Core CSE Only")
        elif re.search(r'\b(mechanical|civil|chemical|biotech|mba|b\.com|bba|mca)\b', combined, re.IGNORECASE):
            m_br = re.search(r'\b(mechanical|civil|chemical|biotech|mba|b\.com|bba|mca)\b', combined, re.IGNORECASE)
            criteria_parts.append(f"Targeting: {m_br.group(0).upper()}")
        elif re.search(r'\b(b\.?tech\s*cse|all\s*branches|circuital|engineering)\b', combined, re.IGNORECASE):
            criteria_parts.append("B.Tech CSE / Circuital Branches")

        # Batch
        batch_m = re.search(r'\b(202[4-9])\s*(?:batch|passing|graduating)', combined, re.IGNORECASE)
        if batch_m:
            criteria_parts.append(f"{batch_m.group(1)} Batch")

        # Arrears / Backlogs
        if re.search(r'\b(no\s*(?:standing|active)?\s*(?:arrears?|backlogs?)|0\s*arrears?)\b', combined, re.IGNORECASE):
            criteria_parts.append("No Standing Arrears")

        if criteria_parts:
            return " | ".join(criteria_parts)
        
        # Fallback: check for explicit eligibility line
        elig_line = re.search(r'(?:eligibility|criteria|qualification)\s*[:\-]\s*([^\n\r]{10,80})', combined, re.IGNORECASE)
        if elig_line:
            return elig_line.group(1).strip()

        return "As per standard campus placement eligibility criteria"


class RelevanceEngine:
    """
    Intelligent Mail Sorting and Placement Eligibility Engine for Shashwat:
    - Student: Shashwat Pratap Singh
    - Roll No: 23BAI11174
    - NeoPAT ID: S4Z5F7U9
    - Campus: VIT Bhopal
    - Degree & Branch: B.Tech CSE (AI & ML)
    - Batch: 2027
    - CGPA: 7.85
    - 10th: 72.6%
    - 12th: 69.0%
    """

    PLACEMENT_KEYWORDS = [
        "placement", "campus drive", "recruitment", "hiring", "online test",
        "written test", "assessment", "shortlist", "interview", "hackathon",
        "internship", "job opportunity", "test schedule", "selection process",
        "cdc", "super dream", "dream offer", "regular offer", "test link",
        "mock test", "coding round", "technical interview", "hr round",
        "registration link", "offer letter", "oa link"
    ]

    NON_PLACEMENT_NOISE = [
        "god bless you", "god bless", "prayer meeting", "prayer session", "morning devotion",
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
        
        sanitized_body = re.sub(r'[\w\.-]+@[\w\.-]+', ' ', body)
        clean_body_parts = re.split(r'(?i)(?:warm regards|with regards|director\s*\(?career development|vellore institute|qs world university|disclaimer:)', sanitized_body)
        clean_body_for_eval = clean_body_parts[0] if clean_body_parts else sanitized_body

        full_text = f"{subject}\n{clean_body_for_eval}"
        full_text_lower = full_text.lower()
        
        datetime_info = DateTimeExtractor.extract_dates_and_times(full_text)
        primary_date = datetime_info.get("date", "Refer email")
        primary_time = datetime_info.get("time", "Refer email")
        deadline_info = datetime_info.get("deadline")

        link_data = LinkInspector.extract_links_and_venues(full_text, html=body_html or "")
        
        campus_info = CampusTravelDetector.detect_campus_and_travel(full_text)

        thread_context_str = ""
        if previous_thread_messages and len(previous_thread_messages) > 0:
            earlier_sub = previous_thread_messages[0].get("subject", "")
            earlier_body = previous_thread_messages[0].get("body", "")[:120].strip()
            thread_context_str = (
                f"\n• 🧵 <b>Thread History:</b>\n"
                f"  - <i>Previous:</i> {earlier_sub}\n"
                f"  - <i>Context:</i> {earlier_body}...\n"
            )

        evaluation = {
            "priority": "Low",
            "category": "General Notice",
            "is_placement_mail": False,
            "matched_identity": False,
            "matched_identity_details": [],
            "company_name": None,
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
            "reason": "General notice / circular."
        }

        is_pc_sender = bool(re.search(r'(program chair|programme chair|pc\s*cse|pc\s*aiml|pc-|head of department|hod|dean|academic coordinator)', f"{sender_lower} {subject_lower} {full_text_lower[:200]}"))
        is_cdc_sender = bool(re.search(r'(placementoffice@|noreply\.cdcinfo@|director.*career development|samuel rajkumar|placement office|vitlions2027@|pat@)', f"{sender_lower} {full_text_lower[:250]}"))
        is_biometric_mail = bool(re.search(r'(biometric|biometrics|attendance verification|exam slot|bench marking)', full_text_lower))

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

        venue_slot_points = []
        if link_data.get("venues"):
            venue_slot_points.append(f"• 📍 <b>Venue / Classroom / Lab:</b> <code>{', '.join(link_data['venues'])}</code>")
        if link_data.get("slots"):
            venue_slot_points.append(f"• ⏰ <b>Slot Timings:</b> {', '.join(link_data['slots'])}")
        if campus_info.get("travel_note"):
            venue_slot_points.append(f"• 🚆 <b>Travel Notice:</b> <b>{campus_info['travel_note']}</b>")
        if link_data.get("google_sheets") or link_data.get("action_links") or link_data.get("google_drive") or link_data.get("linkedin_links"):
            top_links = (link_data.get("google_sheets") + link_data.get("google_drive") + link_data.get("action_links") + link_data.get("linkedin_links"))[:2]
            venue_slot_points.append("• 🔗 <b>Action Links / Registration:</b>\n" + "\n".join([f"  - {u}" for u in top_links]))
        
        venue_slot_block = ("\n" + "\n".join(venue_slot_points)) if venue_slot_points else ""

        has_placement_kw = any(kw in full_text_lower for kw in cls.PLACEMENT_KEYWORDS)
        is_subject_noise = any(kw in subject_lower for kw in cls.NON_PLACEMENT_NOISE)

        detected_company = cls.extract_company_name(subject, clean_body_for_eval, has_placement_kw)
        evaluation["company_name"] = detected_company

        # Comprehensive detection for selection / shortlist / result announcements
        has_shortlist_att = any(
            any(k in a.get('filename', '').lower() for k in ['shortlist', 'selected', 'select', 'result', 'placed', 'final_list', 'offer'])
            for a in attachments_data
        )

        has_shortlist_phrase = bool(re.search(
            r'(?:shortlist(?:ed)?\s*(?:students?|candidates?|list)?|'
            r'selection\s*list|selected\s*(?:students?|candidates?|names)|'
            r'congratulations\s*(?:to|all)?\s*(?:the)?\s*(?:following|selected|placed)?|'
            r'final\s*select(?:s|ed)?|placed\s*students?|offers?\s*(?:released|rolled\s*out)|'
            r'result\s*of\s*(?:round|online\s*assessment|test|interview)|'
            r'candidates?\s*(?:moving|selected)\s*(?:for|to)\s*(?:next\s*round|interview|final)|'
            r'find\s*(?:the)?\s*(?:below|attached)\s*(?:shortlist|candidates|selection|results?)|'
            r'list\s*of\s*(?:shortlisted|selected|placed)\s*students?|'
            r'excel\s*sheet\s*containing\s*the\s*list\s*of\s*(?:shortlisted|selected)|'
            r'neo\s*id\s*\n\s*[a-z0-9]{8})',
            full_text_lower
        ))

        # Check if email is an open registration drive vs a result/shortlist announcement
        is_open_registration = bool(re.search(r'\b(registration\s*link|register\s*by|apply\s*here|apply\s*link|fill\s*the\s*google\s*form\s*to\s*register)\b', full_text_lower)) and not has_shortlist_att and not bool(re.search(r'\b(selection\s*list|congratulations\s*to\s*selected|final\s*selects)\b', subject_lower))

        is_shortlist_announcement = (has_shortlist_att or has_shortlist_phrase) and not is_open_registration

        # =========================================================================
        # CASE 1: USER IS SHORTLISTED / SELECTED (Direct Match Found)
        # =========================================================================
        if identity_matches:
            hit = identity_matches[0]
            loc_str = f"in {hit['source']}" + (f" (Page/Row {hit.get('page')})" if hit.get('page') else "")
            
            evaluation["matched_identity"] = True
            evaluation["matched_identity_details"] = identity_matches
            evaluation["priority"] = "Critical"
            evaluation["category"] = "Shortlisted / Action Required"
            evaluation["trigger_sound"] = True
            evaluation["sound_type"] = "critical_alarm"
            evaluation["telegram_notify"] = True
            evaluation["reason"] = f"🎯 SHORTLIST MATCH: Found {hit['type']} ({hit['term']}) {loc_str}!"

            deadline_str = f"\n• ⏳ <b>Action By / Deadline:</b> <b>{deadline_info}</b>" if deadline_info else ""
            evaluation["telegram_message"] = (
                f"🎉 <b>YOU HAVE BEEN SHORTLISTED / SELECTED!</b>\n\n"
                f"• 🏢 <b>Company:</b> <code>{detected_company or 'Campus Placement Drive'}</code>\n"
                f"• 🎯 <b>Shortlisted Info:</b> Found <b>{hit['type']}</b> (<code>{hit['term']}</code>) {loc_str}\n"
                f"• 📅 <b>Date & Time:</b> <b>{primary_date} | {primary_time}</b>\n"
                f"• 🏫 <b>Campus / Venue:</b> <b>{campus_info['campus_display']}</b>"
                f"{deadline_str}"
                f"{venue_slot_block}\n"
                f"• 📝 <b>Subject:</b> {subject}\n"
                f"• 👤 <b>Student:</b> {profile_data.get('name', 'Shashwat Pratap Singh')} (<code>{roll_no}</code>)"
                f"{thread_context_str}"
            )
            return evaluation

        # =========================================================================
        # CASE 2: PROGRAM CHAIR (PC) / ACADEMIC NOTICE
        # =========================================================================
        if is_pc_sender:
            evaluation["priority"] = "High"
            evaluation["category"] = "Program Chair / Academic Notice"
            evaluation["trigger_sound"] = True
            evaluation["sound_type"] = "high_priority"
            evaluation["telegram_notify"] = True
            evaluation["reason"] = f"🏛️ Academic notice from Program Chair (PC) / Department: {subject[:60]}"

            clean_points = CampusTravelDetector.format_clean_bullets(clean_body_for_eval, max_points=3)
            evaluation["telegram_message"] = (
                f"📢 <b>PLACEMENT OFFICE / ACADEMIC UPDATE</b>\n\n"
                f"• 🏛️ <b>From:</b> Program Chair / Academic Department\n"
                f"• 📅 <b>Date & Time:</b> <b>{primary_date} | {primary_time}</b>\n"
                f"• 🏫 <b>Campus:</b> <b>VIT Bhopal Campus</b>"
                f"{venue_slot_block}\n"
                f"• 📝 <b>Subject:</b> {subject}\n"
                f"• 💬 <b>Key Instructions:</b>\n{clean_points}"
                f"{thread_context_str}"
            )
            return evaluation

        # =========================================================================
        # CASE 3: CDC / PLACEMENT OFFICE UPDATE (Non-drive instructions)
        # =========================================================================
        if is_cdc_sender and ("god bless" in subject_lower or "blessing" in subject_lower or is_biometric_mail or "capgemini" in full_text_lower):
            evaluation["priority"] = "High"
            evaluation["category"] = "CDC / Placement Office Important Update"
            evaluation["trigger_sound"] = True
            evaluation["sound_type"] = "high_priority"
            evaluation["telegram_notify"] = True
            evaluation["reason"] = f"📢 Important Placement Office update from CDC: {subject}"

            clean_points = CampusTravelDetector.format_clean_bullets(clean_body_for_eval, max_points=3)
            evaluation["telegram_message"] = (
                f"📢 <b>PLACEMENT OFFICE / ACADEMIC UPDATE</b>\n\n"
                f"• 🏛️ <b>From:</b> Placement Office / CDC Director\n"
                f"• 📅 <b>Date & Time:</b> <b>{primary_date} | {primary_time}</b>\n"
                f"• 🏫 <b>Campus:</b> <b>{campus_info['campus_display']}</b>"
                f"{venue_slot_block}\n"
                f"• 📝 <b>Subject:</b> {subject}\n"
                f"• 💬 <b>Key Instructions:</b>\n{clean_points}"
                f"{thread_context_str}"
            )
            return evaluation

        # =========================================================================
        # CASE 4: SELECTION / SHORTLIST PUBLISHED (USER NOT IN LIST)
        # =========================================================================
        if is_shortlist_announcement and not identity_matches:
            evaluation["priority"] = "Medium"
            evaluation["category"] = "Not Shortlisted for Test / Round"
            evaluation["trigger_sound"] = False
            evaluation["telegram_notify"] = True
            evaluation["reason"] = f"ℹ️ Shortlist / Selection list published for {detected_company or 'Drive'}, but Roll No ({roll_no}) / NeoPAT ID ({neopat_id}) was NOT found."

            evaluation["telegram_message"] = (
                f"ℹ️ <b>SELECTION / SHORTLIST PUBLISHED (NOT SHORTLISTED)</b>\n\n"
                f"• 🏢 <b>Company:</b> <code>{detected_company or 'Campus Recruitment'}</code>\n"
                f"• 📢 <b>Update:</b> Candidate selection list / test shortlist announced, but your Roll No (<code>{roll_no}</code>) / NeoPAT ID (<code>{neopat_id}</code>) was <b>not in the list</b>.\n"
                f"• 📅 <b>Date:</b> <b>{primary_date}</b>\n"
                f"• 🏫 <b>Campus:</b> <b>{campus_info['campus_display']}</b>\n"
                f"• 📝 <b>Subject:</b> {subject}"
                f"{thread_context_str}"
            )
            return evaluation

        # =========================================================================
        # CASE 5: PLACEMENT RECRUITMENT DRIVE (ELIGIBILITY EVALUATION)
        # =========================================================================
        if has_placement_kw or (detected_company and not is_subject_noise):
            evaluation["is_placement_mail"] = True
            eligibility = cls.check_eligibility(clean_body_for_eval, subject, profile_data, campus_info)
            evaluation["eligibility_status"] = eligibility["status"]
            evaluation["eligibility_notes"] = eligibility["notes"]
            
            role_offered = JobDetailsExtractor.extract_role(clean_body_for_eval, subject)
            package_offered = JobDetailsExtractor.extract_package(clean_body_for_eval, subject)
            criteria_asked = JobDetailsExtractor.extract_criteria_asked(clean_body_for_eval, subject)

            deadline_str = f"<b>{deadline_info}</b>" if deadline_info else "Refer Portal / Email"

            if eligibility["is_eligible"]:
                evaluation["priority"] = "High"
                evaluation["category"] = "Eligible Placement Drive"
                evaluation["trigger_sound"] = True
                evaluation["sound_type"] = "high_priority"
                evaluation["telegram_notify"] = True
                evaluation["reason"] = f"✅ ELIGIBLE DRIVE ({detected_company or 'Company'}): Meets all criteria ({eligibility['notes']})."

                evaluation["telegram_message"] = (
                    f"🎯 <b>YOU ARE ELIGIBLE FOR THIS DRIVE!</b>\n\n"
                    f"• 🏢 <b>Company:</b> <code>{detected_company or 'Campus Recruitment'}</code>\n"
                    f"• 💼 <b>Role / Position:</b> <b>{role_offered}</b>\n"
                    f"• 💰 <b>Package / CTC Offered:</b> <b>{package_offered}</b>\n"
                    f"• 📋 <b>Criteria Asked:</b> {criteria_asked}\n"
                    f"• ⏳ <b>Last Date to Apply:</b> {deadline_str}\n"
                    f"• 📅 <b>Drive Date / Schedule:</b> <b>{primary_date} | {primary_time}</b>\n"
                    f"• 🏫 <b>Campus:</b> <b>{campus_info['campus_display']}</b>"
                    f"{venue_slot_block}\n"
                    f"• 📝 <b>Subject:</b> {subject}"
                    f"{thread_context_str}"
                )
            else:
                evaluation["priority"] = "Medium"
                evaluation["category"] = "Ineligible Placement Drive"
                evaluation["trigger_sound"] = False
                evaluation["telegram_notify"] = True
                evaluation["reason"] = f"❌ INELIGIBLE DRIVE ({detected_company or 'Company'}): {eligibility['ineligible_reason']}"

                evaluation["telegram_message"] = (
                    f"❌ <b>NOT ELIGIBLE FOR THIS DRIVE</b>\n\n"
                    f"• 🏢 <b>Company:</b> <code>{detected_company or 'Campus Recruitment'}</code>\n"
                    f"• 📋 <b>Criteria Asked:</b> {criteria_asked}\n"
                    f"• ⚠️ <b>Reason for Ineligibility:</b> <b>{eligibility['ineligible_reason']}</b>\n"
                    f"• 📝 <b>Subject:</b> {subject}"
                    f"{thread_context_str}"
                )
            return evaluation

        # Default fallback
        evaluation["priority"] = "Low"
        evaluation["category"] = "General Circular"
        evaluation["trigger_sound"] = False
        evaluation["telegram_notify"] = False
        evaluation["reason"] = "General college circular / notice. Stored silently in background."
        return evaluation

    @classmethod
    def extract_company_name(cls, subject: str, body: str, has_placement_kw: bool = True) -> Optional[str]:
        clean_sub = re.sub(r'^(Re|RE|Fwd|FWD):\s*', '', subject, flags=re.IGNORECASE).strip()
        
        # 1. Known Companies check across clean subject and body
        KNOWN_COMPANIES = [
            "Deloitte", "Celebal", "HP", "Mobolutions", "Human Resocia", "Schneider Electric",
            "Tresvista", "Embitel", "Alcatel", "Infosys", "Myntra", "Capgemini", "Palo Alto",
            "Citi India", "Masal.ai", "LTIMindtree", "Virtusa", "TCS", "Wipro", "Amazon",
            "Microsoft", "Google", "DE Shaw", "L&T", "Larsen & Toubro", "Oracle", "Cisco",
            "Goldman Sachs", "JPMorgan", "Morgan Stanley", "Optum", "BNY Mellon", "Accenture"
        ]
        for comp in KNOWN_COMPANIES:
            if re.search(r'\b' + re.escape(comp) + r'\b', clean_sub, re.IGNORECASE):
                return comp

        # 2. Mock Drive check
        m_mock = re.search(r'mock for\s+([A-Za-z0-9\s&.\-]+?)(?:\s+\d|\s+pm|\s+am|$)', clean_sub, re.IGNORECASE)
        if m_mock:
            return f"{m_mock.group(1).strip()} (Mock Drive)"

        # 3. Selection / Shortlist / Drive pattern matching
        m_prefix = re.search(
            r'(?:selection\s*list\s*(?:of|for)?|selects\s*of|shortlist(?:ed)?\s*(?:for|of|candidates)?|'
            r'results?\s*of|campus\s*drive\s*(?:for|of)?|hiring\s*(?:at|for)?|opportunity\s*at|'
            r'registration\s*(?:for|of)?|recruitment\s*(?:for|of)?)\s+([A-Za-z0-9\s&.\-]{2,30})',
            clean_sub,
            re.IGNORECASE
        )
        if m_prefix:
            c = m_prefix.group(1).strip()
            c_clean = re.sub(r'\b(campus|drive|batch|\d{4}|written|online|test|round|interview|process|announcement)\b', '', c, flags=re.IGNORECASE).strip()
            if c_clean and len(c_clean) >= 2:
                return c_clean

        m = re.search(r'^(?:Campus Drive|Hiring|Recruitment|Assessment|Drive|Placement)?\s*[-:]?\s*([A-Za-z0-9\s&.\-]{2,30}?)\s+(?:written test|online test|next round|recruitment|drive|test link|hiring|shortlist|super dream|dream offer|registration|regular offer|hackathon|interview|selection)', clean_sub, re.IGNORECASE)
        if m:
            c = m.group(1).strip()
            c_clean = re.sub(r'^(congratulations|urgent|important|dear students|all students|notice|regarding|schedule|kind attention)\s*[:!]?\s*', '', c, flags=re.IGNORECASE).strip()
            if c_clean and len(c_clean) >= 2 and c_clean.lower() not in ["god bless", "prayer", "all", "students", "batch", "important", "urgent", "campus", "selection list", "shortlist"]:
                return c_clean

        if has_placement_kw:
            words = clean_sub.split()
            if len(words) >= 2 and words[0].lower() not in ["circular", "notice", "important", "urgent", "meeting", "dear", "all", "students", "schedule", "god", "prayer", "selection"]:
                return f"{words[0]} {words[1]}".replace(":", "").replace("-", "").strip()

        return None

    @classmethod
    def check_eligibility(cls, body_text: str, subject: str, profile: Dict[str, Any], campus_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        user_cgpa = float(profile.get("current_cgpa", 7.85))
        user_10th = float(profile.get("tenth_percentage", 72.6))
        user_12th = float(profile.get("twelfth_percentage", 69.0))
        user_batch = int(profile.get("batch_year", 2027))
        user_branch = str(profile.get("branch", "CSE (AI & ML)")).lower()

        combined_text = f"{subject}\n{body_text}"
        notes = []
        ineligible_reasons = []
        is_eligible = True

        if campus_info and campus_info.get("is_bhopal_excluded"):
            is_eligible = False
            ineligible_reasons.append("Restricted to VIT Vellore/Chennai campus (You are at VIT Bhopal)")

        cgpa_matches = re.findall(r'(?:CGPA|GPA|grade point)\s*(?:>=|:|of|above|>)?\s*([0-9]\.[0-9]{1,2})', body_text, re.IGNORECASE)
        if cgpa_matches:
            required_cgpa = max([float(c) for c in cgpa_matches if float(c) <= 10.0])
            if user_cgpa >= required_cgpa:
                notes.append(f"CGPA >= {required_cgpa} (You: {user_cgpa})")
            else:
                is_eligible = False
                ineligible_reasons.append(f"Requires CGPA >= {required_cgpa} (You have {user_cgpa})")

        perc_matches = re.findall(r'([5-9][0-9])%\s*(?:in|throughout|in 10th|and 12th|in 12th|in 10th/12th|academics)', body_text, re.IGNORECASE)
        if perc_matches:
            req_perc = max([float(p) for p in perc_matches])
            if user_10th >= req_perc and user_12th >= req_perc:
                notes.append(f"Academics >= {req_perc}% (You: 10th {user_10th}%, 12th {user_12th}%)")
            else:
                is_eligible = False
                if user_12th < req_perc:
                    ineligible_reasons.append(f"Requires 12th >= {req_perc}% (You have {user_12th}%)")
                if user_10th < req_perc:
                    ineligible_reasons.append(f"Requires 10th >= {req_perc}% (You have {user_10th}%)")

        batch_match = re.search(r'\b(202[4-9])\s*(?:batch|passing|graduating)', combined_text, re.IGNORECASE)
        if batch_match:
            req_batch = int(batch_match.group(1))
            if req_batch == user_batch:
                notes.append(f"Batch: {req_batch}")
            else:
                is_eligible = False
                ineligible_reasons.append(f"Targeting {req_batch} Batch (You are {user_batch} Batch)")

        core_cse_only = bool(re.search(
            r'\b(?:computer science and engineering\s*only|core\s*cse\s*only|b\.?tech\s*cse\s*\(?core\)?\s*only|only\s*b\.?tech\s*cse\s*\(?core\)?|cse\s*only\s*\(no specializations?\))\b',
            combined_text,
            re.IGNORECASE
        ))
        if core_cse_only:
            is_eligible = False
            ineligible_reasons.append("Restricted to Core CSE only (You are CSE AI & ML)")

        non_cse_match = re.search(r'\b(mechanical|mech|civil|chemical|biotech|biomedical|aerospace|automobile|production|mining|metallurgy|mba|b\.com|bcom|bba|mca|bca|m\.sc|msc|b\.sc|bsc|m\.tech|mtech|law)\b', combined_text, re.IGNORECASE)
        if non_cse_match:
            has_btech_cse = bool(re.search(r'\b(b\.?tech\s*(?:cse|it|ai|aiml)?|cse\b|computer science|circuital|all\s*branches|all\s*b\.?tech|all\s*degrees)\b', combined_text, re.IGNORECASE))
            is_non_cse_exclusive = bool(re.search(r'\b(?:mechanical|mech|civil|chemical|biotech|mba|b\.com|bba|mca|m\.sc|b\.sc)(?:\s*(?:and|&|,)\s*(?:mechanical|mech|civil|chemical|biotech|mba|b\.com|bba|mca))*\s*(?:only|students\s*only|branch\s*only|branches\s*only|department\s*only)\b', combined_text, re.IGNORECASE))
            if not has_btech_cse or is_non_cse_exclusive:
                is_eligible = False
                ineligible_reasons.append(f"Restricted to {non_cse_match.group(0).upper()} (You are B.Tech CSE AI&ML)")

        status = "Eligible" if is_eligible else "Ineligible"
        
        return {
            "is_eligible": is_eligible,
            "status": status,
            "notes": " | ".join(notes) if notes else "Meets B.Tech CSE (AI & ML) 2027 criteria",
            "ineligible_reason": " | ".join(ineligible_reasons) if ineligible_reasons else "Criteria mismatch"
        }
