import os
import uuid
from typing import List, Dict, Any
from datetime import datetime, timedelta
import pypdf
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

class MockPlacementDataGenerator:
    """
    Generates realistic college placement test emails, trailing updates, and shortlist PDFs with Shashwat's credentials.
    """

    @staticmethod
    def create_sample_pdf(target_roll="23BAI11174", target_name="Shashwat Pratap Singh", company_name="Cognizant") -> str:
        os.makedirs("sample_attachments", exist_ok=True)
        pdf_path = os.path.join("sample_attachments", f"{company_name.lower()}_shortlist_round1.pdf")
        
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, 750, f"{company_name.upper()} CAMPUS RECRUITMENT DRIVE - 2027 BATCH")
        c.setFont("Helvetica", 10)
        c.drawString(50, 730, "Shortlisted Candidates for Technical Interview (Round 2)")
        c.drawString(50, 715, f"Published on: {datetime.utcnow().strftime('%d %B %Y')} | Department of Placement & Training")
        
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.line(50, 705, 550, 705)
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(50, 685, "S.No")
        c.drawString(90, 685, "Registration No")
        c.drawString(200, 685, "Candidate Name")
        c.drawString(360, 685, "Branch")
        c.drawString(450, 685, "Slot Time")
        
        c.line(50, 675, 550, 675)
        c.setFont("Helvetica", 8)
        
        y = 655
        dummy_students = [
            ("23BCE10012", "Aarav Sharma", "B.Tech CSE", "09:30 AM"),
            ("23BAI10452", "Diya Patel", "B.Tech CSE (AI & ML)", "09:45 AM"),
            (target_roll, target_name, "B.Tech CSE (AI & ML)", "10:00 AM"),
            ("23BIT10982", "Rohan Verma", "B.Tech IT", "10:15 AM"),
            ("23BCE11204", "Ananya Sen", "B.Tech CSE", "10:30 AM"),
            ("23BAI11099", "Karthik Raj", "B.Tech CSE (AI & ML)", "10:45 AM"),
        ]

        for idx, (roll, name, branch, slot) in enumerate(dummy_students, start=1):
            if roll == target_roll:
                c.setFont("Helvetica-Bold", 8)
            else:
                c.setFont("Helvetica", 8)
                
            c.drawString(50, y, str(idx))
            c.drawString(90, y, roll)
            c.drawString(200, y, name)
            c.drawString(360, y, branch)
            c.drawString(450, y, slot)
            y -= 20

        c.setFont("Helvetica-Oblique", 8)
        c.drawString(50, y - 30, "* Note: All shortlisted candidates must join the virtual room 10 mins prior with College ID.")
        
        c.save()
        return pdf_path

    @classmethod
    def get_simulation_scenarios(cls) -> List[Dict[str, Any]]:
        return [
            {
                "id": "scenario_cognizant_shortlist",
                "title": "🎯 Shortlist PDF Match (Cognizant)",
                "description": "Email with attached PDF containing Shashwat Pratap Singh (23BAI11174) for Round 2.",
                "thread_id": "thread_cog_2027",
                "sender": "placements@college.edu.in",
                "subject": "Cognizant GenC Elevate - Shortlisted Candidates for Technical Interview",
                "body": "Dear Students,\n\nPlease find attached the list of candidates shortlisted for Round 2 Technical Interviews for Cognizant GenC Elevate drive.\n\nAll shortlisted students are requested to be available on MS Teams as per the slot time.\n\nRegards,\nPlacement Office",
                "company_name": "Cognizant",
                "attachment_generator": "create_sample_pdf"
            },
            {
                "id": "scenario_tcs_reschedule",
                "title": "⚠️ Trailing Mail: Schedule Changed (TCS)",
                "description": "Trailing update on an applied company drive rescheduling slot timings.",
                "thread_id": "thread_tcs_2027",
                "sender": "tcs.campus@college.edu.in",
                "subject": "Re: TCS NQT 2027 Batch - Assessment Slot 1 Rescheduled",
                "body": "Dear Applied Students,\n\nKindly note that due to server maintenance, the TCS NQT National Qualifier Test scheduled for tomorrow morning at 09:00 AM has been RESCHEDULED to 02:00 PM.\n\nThe revised test link and NeoPAT login credentials have been sent.\n\nRegards,\nCDC Placement Cell",
                "company_name": "TCS",
                "attachment_generator": None
            },
            {
                "id": "scenario_google_drive",
                "title": "🟡 New Drive: Applied Watchlist Match (Google)",
                "description": "New hiring drive from a company on Shashwat's Applied Watchlist.",
                "thread_id": "thread_google_2027",
                "sender": "university.relations@google.com",
                "subject": "Google Summer Internship 2026-27 - Application Form & Test Guidelines",
                "body": "Hello Applicants,\n\nThank you for applying to the Google Software Engineer Intern position. Please complete your profile and coding assessment by Sunday 11:59 PM.\n\nTarget Batch: 2027 Passing Out\nCriteria: B.Tech CSE / AI & ML\n\nBest of Luck,\nGoogle University Team",
                "company_name": "Google",
                "attachment_generator": None
            },
            {
                "id": "scenario_unapplied_placement",
                "title": "🔇 Unapplied Company Drive (Deloitte)",
                "description": "Placement announcement for a company not on Shashwat's applied watchlist (Stored silently).",
                "thread_id": "thread_deloitte_2027",
                "sender": "placements@college.edu.in",
                "subject": "Campus Drive: Deloitte USI Analyst - Registrations Open",
                "body": "Dear 2027 Batch Students,\n\nDeloitte USI is visiting our campus for Analyst roles.\nEligibility: B.Tech CSE/ECE/IT, CGPA >= 7.5, 10th/12th >= 65%.\nRegistration closes tomorrow.\n\nRegards,\nPlacement Cell",
                "company_name": "Deloitte",
                "attachment_generator": None
            },
            {
                "id": "scenario_general_circular",
                "title": "🔇 General College Circular (Holiday Notice)",
                "description": "General non-placement circular (Stored silently in backend).",
                "thread_id": "thread_circular_holiday",
                "sender": "dean.academics@college.edu.in",
                "subject": "Circular: Campus Holiday on Occasion of Festival",
                "body": "Dear Faculty and Students,\n\nThis is to notify that the college campus and administrative offices will remain closed tomorrow. Regular classes will resume on Monday.\n\nDean Academics",
                "company_name": None,
                "attachment_generator": None
            }
        ]
