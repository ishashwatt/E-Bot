import sys, os
sys.stdout.reconfigure(encoding='utf-8')
from app.db.database import SessionLocal
from app.db.models import EmailThread, EmailMessage, Profile, Attachment
from app.services.relevance_engine import RelevanceEngine
from app.core.config import settings

db = SessionLocal()
profile = db.query(Profile).first()
profile_dict = {
    'name': profile.name if profile else settings.student_name,
    'roll_number': profile.roll_number if profile else settings.student_roll,
    'neopat_id': profile.neopat_id if profile else settings.student_neopat,
    'name_variations': [settings.student_name, settings.student_roll, 'Shashwat', 'Shashwat Singh'],
    'degree': profile.degree if profile else settings.student_degree,
    'branch': profile.branch if profile else settings.student_branch,
    'batch_year': profile.batch_year if profile else settings.student_batch,
    'tenth_percentage': profile.tenth_percentage if profile else settings.student_10th,
    'twelfth_percentage': profile.twelfth_percentage if profile else settings.student_12th,
    'current_cgpa': profile.current_cgpa if profile else settings.student_cgpa
}

threads = db.query(EmailThread).all()
print(f"Total threads to re-evaluate: {len(threads)}")

for t in threads:
    msgs = t.messages
    if not msgs:
        continue
    latest_msg = msgs[-1]
    prev_msgs = [{"subject": m.subject, "body": m.body_text} for m in msgs[:-1]]
    
    atts_data = []
    for att in latest_msg.attachments:
        atts_data.append({
            'filename': att.filename,
            'matches': att.match_locations or [],
            'file_type': att.file_type
        })
        
    eval_res = RelevanceEngine.evaluate_email(
        subject=latest_msg.subject,
        body=latest_msg.body_text or '',
        attachments_data=atts_data,
        profile_data=profile_dict,
        sender=latest_msg.sender or '',
        previous_thread_messages=prev_msgs
    )
    
    t.priority = eval_res['priority']
    t.category = eval_res['category']
    t.status_summary = eval_res['reason']
    t.company_name = eval_res.get('company_name')
    t.has_identity_match = eval_res['matched_identity']
    
    latest_msg.eligibility_status = eval_res['eligibility_status']
    latest_msg.eligibility_notes = eval_res['eligibility_notes']
    
    print(f"[{t.priority.upper():<8}] ({t.category}) Company: {t.company_name} | Date: {eval_res.get('schedule_date')} | Time: {eval_res.get('schedule_time')}")
    print(f"   Subject: {latest_msg.subject[:65]}")
    print(f"   Reason:  {eval_res['reason'][:85]}")
    print("-" * 75)

db.commit()
print("All threads re-evaluated and database synchronized!")
