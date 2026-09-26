import os
import sys
import json
from dotenv import load_dotenv

# Load env from both backend/.env and .env
for p in [
    os.path.join(os.path.dirname(__file__), "..", ".env"),
    os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
]:
    if os.path.exists(p):
        load_dotenv(p, override=True)

# Path setup
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.agent.graph import clearroom_agent

USER_TRANSCRIPT = """MEETING REPORT
Date: 6th June 2026
Time: 10:00 PM – 11:30pm
Platform: Online-Google Meet
Conducted by:
- Afraaz Hashmi – WIE Chairperson
- Md Aasif – JHSB Chairperson
- IEEE Core
Attendees –
• Aadil Naseem
• aalima ahmad
• aamna khan
• Adiba Bushra Khan
• Afraaz Hashmi
• Aliza Khan
• Anusha Siddiqui
• Areeba Aslam
• Astafa Hilal
• Erneeb Zehra
• faria zehra
• IEEE JHSB
• Lamaan Khan
• Mariya Mallick
• md saeem
• Mohammad Ghazaal
• Mohd Faruaz
• Rayyan Ahmad
• Sadif Razi
• Sameer Khan
• Sarosh Alam
• Shehzain Nadeem
• Tooba Siddiqui
• Umra Khan
• Wahila Ahmad
Agenda:
first meeting of the tenure! Introduction and plan of action for the further tenure
Meeting Summary:
- The meeting started with a roll-call
- Afraaz shared the duty-sheet that has been prepared so everyone is aware of how they’re meant to contribute
- The role of heads in each board was explained broadly and they were told to maintain a bridge between their leads and the team members!
- The new editorial format was explained
- Afraaz touched upon the podcast! Aadil was told to keep an eye out for this (scripting and structure)
- All boards were touched upon briefly and their duties specifically were explained to them!
- Editorial, Creative and social media were advised to stay in constant communication to avoid pushing deadlines and streamline their work
- Media team was told to prepare a drive similar to last year
- Membership team was told to maintain a good communication channel with the treasurers for funding
- Data and forms team was explained which 2 forms need to be made and to get them done before and to maintain a database for all events and analyse and track insights
- All leads were told to not be hesitant to reach out to the former position holders better to ask than make a mistake and all former position holders will be available for any help!
- Aasif touched upon WIE week and informed the event leads that we need to conduct 5 online events!
- DSSYWLC was explained.. happening on 20-21 June, two of our execom members have applied for campus ambassador
- All members need to be added to the new 2026 JHSB members group and community
- All leads to share their groups individual links to the members group once the members have been added and then start their intro meetings upcoming Monday se
- We already have 3 speakers on the backfoot for WIE week.. need to find 3 more speakers in the upcoming days and finalise the webinars
- Membership drive to happen and membership needs to be pushed.. the bar set by the outgoing batch is high! The goal is to surpass it.. membership to be pushed heavily after new batch of juniors join
- The outgoing core said a few words of advice to end off the meeting and to ensure streamlined functionality in the new execom!
Prepared by:
Lamaan Khan
Designation: WIE General Secretary, 2026-2027
Date: 6th June 2026"""

def main():
    print("=" * 70)
    print("RUNNING LIVE MEETLOOP AUDIT ON USER IEEE WIE TRANSCRIPT")
    print(f"OpenRouter Key: {'set' if os.getenv('OPENROUTER_API_KEY') else 'MISSING'}")
    print(f"Swytchcode Key: {'set' if os.getenv('SWYTCHCODE_API_KEY') else 'MISSING'}")
    print(f"Notion Parent ID: {os.getenv('NOTION_HEALTH_REPORT_PARENT_PAGE_ID')}")
    print(f"Gmail Account: {os.getenv('GMAIL_TEST_ACCOUNT')}")
    print(f"Slack Channel: {os.getenv('SLACK_CHANNEL_ID')}")
    print("=" * 70)

    initial_state = {
        "mode": "audit",
        "prompt": "",
        "raw_meeting_notes": [USER_TRANSCRIPT],
        "gmeet_meeting_code": "",
        "gmeet_date_range": [],
        "brief_topic": "",
        "reasoning_trace": [],
        "errors": [],
    }

    result = clearroom_agent.invoke(initial_state)

    print("\n" + "=" * 70)
    print("EXECUTION RESULTS:")
    print(f"Mode: {result.get('mode')}")
    print(f"Notion Report URL: {result.get('notion_report_url')}")
    print(f"Notion Decision Pages: {result.get('notion_decision_page_urls')}")
    print(f"Gmail Sent: {result.get('gmail_digest_sent')}")
    print(f"Slack Sent: {result.get('slack_pulse_sent')}")
    print(f"Stuck Topics Count: {len(result.get('stuck_topics', []))}")
    print(f"Commitment Load: {json.dumps(result.get('commitment_load', {}), indent=2)}")
    print(f"Errors: {result.get('errors')}")
    print("=" * 70)

if __name__ == "__main__":
    main()
