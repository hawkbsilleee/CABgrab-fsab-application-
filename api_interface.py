import requests
import json
import re 
from bs4 import BeautifulSoup

def get_course_info(crn):
    url = "https://cab.brown.edu/api/?page=fose&route=details"
    payload = {
        "key": f"crn:{crn}",
        "srcdb": "202510",  # Fall 2025
        "matched": f"crn:{crn}",
        "userWithRolesStr": "!!!!!!"
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Origin": "https://cab.brown.edu",
        "Referer": "https://cab.brown.edu/",
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest"
    }

    resp = requests.post(url, headers=headers, data=json.dumps(payload))
    data = resp.json()

    # Parse the "seats" HTML
    soup = BeautifulSoup(data.get("seats", ""), "html.parser")

    max_elem = soup.find("span", class_="seats_max")
    avail_elem = soup.find("span", class_="seats_avail")

    if not max_elem or not avail_elem:
        # Invalid CRN or no seat info returned
        return None

    try:
        max_enrollment = int(max_elem.text.strip())
        seats_available = int(avail_elem.text.strip())
    except ValueError:
        return None

    # Parse the "regdemog_html" HTML
    enrolled_match = re.search(r"Current enrollment:\s*(\d+)", data.get("regdemog_html", ""))
    current_enrolled = int(enrolled_match.group(1)) if enrolled_match else None

    return {
        "max_enrollment": max_enrollment,
        "current_enrolled": current_enrolled,
        "seats_available": seats_available
    }

if __name__ == "__main__":
    print(get_course_info("10129")["seats_available"])  # Example CRN for testing