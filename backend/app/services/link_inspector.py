import re
import os
import requests
import csv
import io
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import openpyxl

logger = logging.getLogger("link_inspector")

class LinkInspector:
    """
    Extracts hyperlinks, Google Sheets, Google Drive files, OneDrive, and classroom/lab venues from email content.
    Automatically fetches and inspects online spreadsheets, drive files, and shortened links for student shortlist matches,
    extracting assigned Slot, Venue, Class Number, and Timing.
    """

    SHORTENER_DOMAINS = [
        "lnkd.in", "bit.ly", "tinyurl.com", "cutt.ly", "rb.gy", "t.co", "goo.gl",
        "forms.gle", "is.gd", "buff.ly", "ow.ly", "rebrand.ly"
    ]

    @classmethod
    def extract_links_and_venues(cls, text: str, html: Optional[str] = "") -> Dict[str, Any]:
        combined = f"{text or ''}\n{html or ''}"
        
        raw_urls = re.findall(r'https?://[^\s<>"\'\)]+', combined)
        
        if html:
            try:
                soup = BeautifulSoup(html, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a["href"].strip()
                    if href.startswith("http"):
                        raw_urls.append(href)
            except Exception as e:
                logger.debug(f"HTML link extraction note: {e}")

        clean_urls = []
        for u in raw_urls:
            u_clean = re.sub(r'[\.,;:\)>\]]+$', '', u.strip())
            u_clean = u_clean.replace("&amp;", "&")
            if u_clean and u_clean not in clean_urls:
                clean_urls.append(u_clean)

        google_sheets = []
        google_drive = []
        action_links = []
        linkedin_links = []
        direct_excel_csv = []
        short_links = []

        for url in clean_urls:
            url_lower = url.lower()
            if "docs.google.com/spreadsheets" in url_lower:
                if url not in google_sheets:
                    google_sheets.append(url)
            elif "drive.google.com" in url_lower:
                if url not in google_drive:
                    google_drive.append(url)
            elif "lnkd.in" in url_lower or "linkedin.com" in url_lower:
                m = re.search(r'url=([^&]+)', url)
                if m:
                    import urllib.parse
                    decoded_url = urllib.parse.unquote(m.group(1))
                    if decoded_url not in clean_urls:
                        clean_urls.append(decoded_url)
                if url not in linkedin_links:
                    linkedin_links.append(url)
            elif any(ext in url_lower for ext in [".xlsx", ".xls", ".csv", ".tsv"]):
                if url not in direct_excel_csv:
                    direct_excel_csv.append(url)
            elif any(dom in url_lower for dom in cls.SHORTENER_DOMAINS):
                if url not in short_links:
                    short_links.append(url)
            elif any(k in url_lower for k in ["forms.gle", "neopat", "hackerearth", "hackerrank", "unstop", "surveymonkey"]):
                if url not in action_links:
                    action_links.append(url)

        venues = re.findall(r'\b(?:LC\s*\d{3}|SJT\s*\d{3}|CDC\s*\d{3}|MB\s*\d{3}|AB\s*\d{3}|Lab\s*\d{1,2}|@\s*own location|virtual mode|virtual|campus lab)\b', combined, re.IGNORECASE)
        slots = re.findall(r'\b(?:slot\s*\d|batch\s*\d|slot\s*[1-5]\s*(?:is|at)?\s*[\d\.:\s]*(?:am|pm|noon)?|first\s*batch|second\s*batch|third\s*batch)\b', combined, re.IGNORECASE)

        clean_venues = list(set([v.strip() for v in venues if len(v.strip()) > 1]))
        clean_slots = list(set([s.strip() for s in slots if len(s.strip()) > 1]))

        return {
            "all_links": clean_urls,
            "google_sheets": google_sheets,
            "google_drive": google_drive,
            "linkedin_links": linkedin_links,
            "direct_excel_csv": direct_excel_csv,
            "short_links": short_links,
            "action_links": action_links,
            "venues": clean_venues,
            "slots": clean_slots
        }

    @classmethod
    def resolve_short_url(cls, short_url: str) -> str:
        """
        Follows HTTP redirects to resolve shortened URLs like bit.ly, lnkd.in, tinyurl.com.
        """
        try:
            res = requests.head(short_url, allow_redirects=True, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
            return res.url
        except Exception:
            return short_url

    @classmethod
    def scan_online_google_sheet(cls, sheet_url: str, search_terms: List[str]) -> Dict[str, Any]:
        """
        Attempts to fetch public Google Sheet as CSV or Excel and search for student identity matches (Roll No, NeoPAT ID, Name).
        Extracts row details, slot, classroom/lab, and time if found.
        """
        result = {
            "url": sheet_url,
            "has_match": False,
            "matches": [],
            "extracted_slot": None,
            "extracted_venue": None,
            "preview": ""
        }

        m = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', sheet_url)
        if not m:
            return result
        
        sheet_id = m.group(1)
        csv_export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"

        try:
            res = requests.get(csv_export_url, timeout=7, headers={"User-Agent": "Mozilla/5.0"})
            if res.status_code == 200 and len(res.text) > 10:
                reader = csv.reader(io.StringIO(res.text))
                header = []
                for row_idx, row in enumerate(reader, start=1):
                    if row_idx == 1:
                        header = [str(c).strip() for c in row if c]
                    row_str = " | ".join([str(c).strip() for c in row if c])
                    if not row_str:
                        continue
                    for term in search_terms:
                        if term and re.search(r'\b' + re.escape(term) + r'\b', row_str, re.IGNORECASE):
                            result["has_match"] = True
                            
                            venue_match = re.search(r'\b(LC\s*\d{3}|SJT\s*\d{3}|CDC\s*\d{3}|MB\s*\d{3}|AB\s*\d{3}|Lab\s*\d{1,2})\b', row_str, re.IGNORECASE)
                            slot_match = re.search(r'\b(Slot\s*\d|Batch\s*\d|Slot\s*[1-5]\s*(?:is|at)?\s*[\d\.:\s]*(?:am|pm|noon)?)\b', row_str, re.IGNORECASE)
                            
                            venue_val = venue_match.group(1) if venue_match else None
                            slot_val = slot_match.group(1) if slot_match else None

                            if venue_val:
                                result["extracted_venue"] = venue_val
                            if slot_val:
                                result["extracted_slot"] = slot_val

                            result["matches"].append({
                                "term": term,
                                "source": "Google Sheet (Linked Online)",
                                "row": row_idx,
                                "snippet": row_str[:250],
                                "venue": venue_val,
                                "slot": slot_val
                            })
                result["preview"] = res.text[:500]
        except Exception as e:
            logger.warning(f"Could not fetch public Google Sheet CSV {sheet_url}: {e}")

        return result

    @classmethod
    def scan_online_drive_or_direct_file(cls, url: str, search_terms: List[str]) -> Dict[str, Any]:
        """
        Attempts to download and inspect a Google Drive or direct file link (.xlsx, .csv).
        """
        result = {
            "url": url,
            "has_match": False,
            "matches": [],
            "extracted_slot": None,
            "extracted_venue": None
        }

        download_url = url
        drive_match = re.search(r'drive\.google\.com/file/d/([a-zA-Z0-9-_]+)', url)
        if drive_match:
            file_id = drive_match.group(1)
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"

        try:
            res = requests.get(download_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if res.status_code == 200 and len(res.content) > 100:
                content_type = res.headers.get("Content-Type", "").lower()
                
                if "spreadsheet" in content_type or "excel" in content_type or download_url.endswith((".xlsx", ".xls")):
                    try:
                        wb = openpyxl.load_workbook(io.BytesIO(res.content), data_only=True)
                        for sheetname in wb.sheetnames:
                            sheet = wb[sheetname]
                            for row_idx, row in enumerate(sheet.iter_rows(values_only=True), start=1):
                                row_str = " | ".join([str(c) for c in row if c is not None])
                                if not row_str.strip():
                                    continue
                                for term in search_terms:
                                    if term and re.search(r'\b' + re.escape(term) + r'\b', row_str, re.IGNORECASE):
                                        result["has_match"] = True
                                        venue_m = re.search(r'\b(LC\s*\d{3}|SJT\s*\d{3}|CDC\s*\d{3}|MB\s*\d{3}|AB\s*\d{3}|Lab\s*\d{1,2})\b', row_str, re.IGNORECASE)
                                        slot_m = re.search(r'\b(Slot\s*\d|Batch\s*\d|Slot\s*[1-5]\s*(?:is|at)?\s*[\d\.:\s]*(?:am|pm|noon)?)\b', row_str, re.IGNORECASE)
                                        
                                        result["matches"].append({
                                            "term": term,
                                            "source": f"Online Excel File ({sheetname})",
                                            "row": row_idx,
                                            "snippet": row_str[:250],
                                            "venue": venue_m.group(1) if venue_m else None,
                                            "slot": slot_m.group(1) if slot_m else None
                                        })
                    except Exception as e:
                        logger.debug(f"Could not parse downloaded stream as Excel: {e}")

                elif "csv" in content_type or "text" in content_type or download_url.endswith((".csv", ".tsv", ".txt")):
                    try:
                        text_data = res.content.decode("utf-8", errors="ignore")
                        reader = csv.reader(io.StringIO(text_data))
                        for row_idx, row in enumerate(reader, start=1):
                            row_str = " | ".join([str(c).strip() for c in row if c])
                            if not row_str:
                                continue
                            for term in search_terms:
                                if term and re.search(r'\b' + re.escape(term) + r'\b', row_str, re.IGNORECASE):
                                    result["has_match"] = True
                                    result["matches"].append({
                                        "term": term,
                                        "source": "Online CSV File",
                                        "row": row_idx,
                                        "snippet": row_str[:250]
                                    })
                    except Exception as e:
                        logger.debug(f"Could not parse downloaded stream as CSV: {e}")
        except Exception as e:
            logger.warning(f"Failed to fetch online drive/direct file {url}: {e}")

        return result
