import requests
import json
import re 
from bs4 import BeautifulSoup

def get_course_info(crn):

    url = "https://cab.brown.edu/api/?page=fose&route=details"

    payload = {
        # "group": "code:ECON 0170",
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
    # print(resp.json())

    # Parse the "seats" HTML
    soup = BeautifulSoup(data["seats"], "html.parser")
    max_enrollment = int(soup.find("span", class_="seats_max").text)
    seats_available = int(soup.find("span", class_="seats_avail").text)

    # Parse the "regdemog_html" HTML
    enrolled_match = re.search(r"Current enrollment:\s*(\d+)", data["regdemog_html"])
    current_enrolled = int(enrolled_match.group(1)) if enrolled_match else None

    # print("Max Enrollment:", max_enrollment)
    # print("Enrolled:", current_enrolled)
    # print("Seats Available:", seats_available)
    return {
        "max_enrollment": max_enrollment,
        "current_enrolled": current_enrolled,
        "seats_available": seats_available
    }

if __name__ == "__main__":
    print(get_course_info("10129")["seats_available"])  # Example CRN for testing