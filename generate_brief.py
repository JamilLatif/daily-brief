#!/usr/bin/env python3
"""
Daily Brief Generator
Generates a comprehensive daily news brief covering AI/Tech, Finance, Real Estate, 
HackerNews, and regional news from around the world.
"""

import os
import sys
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import anthropic
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

# Configuration
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
RECIPIENT_EMAIL = os.environ.get('RECIPIENT_EMAIL', 'jamil.latif@hotmail.co.uk')

def search_news(client, query, max_results=5, section_type="general"):
    """Search for news using Claude with web search."""
    try:
        # Customize instructions based on section type
        format_instructions = """
Format each story with clear separation:

[Priority indicator if breaking/urgent: 🔴 for urgent, ⚡ for breaking]
**Title** [Source]
Brief summary (1-2 sentences)
→ Why this matters: One-line context explaining significance

[Blank line between stories]

Only include stories if they're genuinely important. Better to have 1-2 great stories than force 3 mediocre ones.
For priority indicators:
- Use 🔴 for urgent stories requiring immediate attention
- Use ⚡ for breaking news in the past few hours
- No indicator for standard important news

Important: Add a blank line (use two line breaks) between each story for readability.
"""
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search"
            }],
            messages=[{
                "role": "user",
                "content": f"{query}\n\n{format_instructions}"
            }]
        )
        
        # Extract text from response
        full_text = ""
        for block in message.content:
            if hasattr(block, 'text'):
                full_text += block.text
        
        return full_text if full_text else "No significant news found."
    
    except Exception as e:
        print(f"Error searching for '{query}': {e}")
        return f"Error retrieving news: {str(e)}"


def generate_brief():
    """Generate the complete daily brief."""
    print("Generating daily brief...")
    
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set!")
        sys.exit(1)
    
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    today = datetime.now().strftime("%B %d, %Y")
    
    # Generate PDF
    pdf_filename = f"/tmp/daily_brief_{datetime.now().strftime('%Y%m%d')}.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter,
                           topMargin=0.75*inch, bottomMargin=0.75*inch,
                           leftMargin=0.75*inch, rightMargin=0.75*inch)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor='#1a1a1a',
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor='#666666',
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor='#1a1a1a',
        spaceAfter=8,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    # Color-coded section styles
    tech_section_style = ParagraphStyle(
        'TechSection',
        parent=section_style,
        textColor='#0066cc',  # Blue for Tech
    )
    
    finance_section_style = ParagraphStyle(
        'FinanceSection',
        parent=section_style,
        textColor='#00a86b',  # Green for Finance
    )
    
    realestate_section_style = ParagraphStyle(
        'RealEstateSection',
        parent=section_style,
        textColor='#ff6b35',  # Orange for Real Estate
    )
    
    hn_section_style = ParagraphStyle(
        'HNSection',
        parent=section_style,
        textColor='#ff6600',  # HN Orange
    )
    
    regional_section_style = ParagraphStyle(
        'RegionalSection',
        parent=section_style,
        textColor='#6b4c9a',  # Purple for Regional
    )
    
    content_style = ParagraphStyle(
        'Content',
        parent=styles['Normal'],
        fontSize=10,
        textColor='#2a2a2a',
        alignment=TA_JUSTIFY,
        spaceAfter=8,
        leading=14
    )
    
    story = []
    
    # Title
    story.append(Paragraph("DAILY INTELLIGENCE BRIEF", title_style))
    story.append(Paragraph(f"<i>{today}</i>", date_style))
    story.append(Spacer(1, 0.1*inch))
    
    print("Searching AI & Technology news...")
    story.append(Paragraph("ARTIFICIAL INTELLIGENCE & TECHNOLOGY", tech_section_style))
    ai_tech_news = search_news(client, 
        "Search for the most important AI and technology news stories from the past 24 hours (aim for 2-3 stories, but only include if genuinely significant). "
        "Focus on: new AI model releases, major tech company announcements, AI policy/regulation, "
        "breakthrough research, significant product launches, or major industry shifts. "
        "Quality over quantity - skip if nothing important happened.",
        max_results=3, section_type="tech")
    story.append(Paragraph(ai_tech_news, content_style))
    story.append(Spacer(1, 0.15*inch))
    
    print("Searching Finance news...")
    story.append(Paragraph("FINANCE & MARKETS", finance_section_style))
    finance_news = search_news(client,
        "Search for the most important financial and market news stories from the past 24 hours (aim for 2-3 stories, but only include if genuinely significant). "
        "Focus on: major market movements, Federal Reserve or central bank decisions, significant "
        "corporate earnings or announcements, economic policy changes, crypto developments, or major "
        "sector shifts. Quality over quantity.",
        max_results=3, section_type="finance")
    story.append(Paragraph(finance_news, content_style))
    story.append(Spacer(1, 0.15*inch))
    
    print("Searching Real Estate news...")
    story.append(Paragraph("REAL ESTATE", realestate_section_style))
    real_estate_news = search_news(client,
        "Search for the most important real estate news stories from the past 24 hours (aim for 2-3 stories, but only include if genuinely significant). "
        "Focus on: residential and commercial real estate markets, major policy changes, significant "
        "transactions, market trend shifts, or regulatory developments. Quality over quantity.",
        max_results=3, section_type="realestate")
    story.append(Paragraph(real_estate_news, content_style))
    story.append(Spacer(1, 0.15*inch))
    
    print("Searching HackerNews top stories...")
    story.append(Paragraph("HACKER NEWS HIGHLIGHTS", hn_section_style))
    hn_news = search_news(client,
        "Search for the top stories on Hacker News from the past 24 hours (aim for 2-3 stories, but only include if genuinely interesting). "
        "Focus on the most interesting technical discussions, product launches, or thought-provoking "
        "articles. Avoid 'Show HN' posts unless exceptionally noteworthy. Quality over quantity.",
        max_results=3, section_type="hackernews")
    story.append(Paragraph(hn_news, content_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Regional News
    regions = [
        ("NORTH AMERICA", "Search for 2-3 needle-moving news stories from North America (US, Canada, Mexico) "
         "in the past 24 hours that are NOT being widely covered by mainstream media like CNN or BBC. "
         "Focus on local sources, regional developments, policy changes, or significant events that mainstream "
         "media is missing or underreporting."),
        
        ("EUROPE", "Search for 2-3 needle-moving news stories from Europe in the past 24 hours that are NOT "
         "being widely covered by mainstream media like BBC or major EU outlets. Focus on local sources, "
         "regional political developments, economic changes, or significant events that mainstream media "
         "is missing or underreporting."),
        
        ("ASIA-PACIFIC", "Search for 2-3 needle-moving news stories from Asia-Pacific region in the past 24 hours "
         "that are NOT being widely covered by mainstream Western media. Focus on local sources, regional "
         "political developments, economic changes, or significant events that mainstream media is missing."),
        
        ("MIDDLE EAST & AFRICA", "Search for 2-3 needle-moving news stories from Middle East and Africa in the "
         "past 24 hours that are NOT being widely covered by mainstream Western media. Focus on local sources, "
         "regional developments, policy changes, or significant events that mainstream media is missing."),
        
        ("LATIN AMERICA", "Search for 2-3 needle-moving news stories from Latin America in the past 24 hours "
         "that are NOT being widely covered by mainstream media. Focus on local sources, regional political "
         "and economic developments, or significant events that mainstream media is missing.")
    ]
    
    for region_name, region_query in regions:
        print(f"Searching {region_name} news...")
        story.append(Paragraph(region_name, regional_section_style))
        # Add quality over quantity to query
        enhanced_query = region_query.replace("2-3 needle-moving", "needle-moving (aim for 2-3 but only if genuinely significant)")
        enhanced_query += " Quality over quantity."
        region_news = search_news(client, enhanced_query, max_results=3, section_type="regional")
        story.append(Paragraph(region_news, content_style))
        story.append(Spacer(1, 0.15*inch))
    
    # Deep Dive Recommendations
    print("Generating deep dive recommendations...")
    story.append(Spacer(1, 0.2*inch))
    deepdive_style = ParagraphStyle(
        'DeepDiveSection',
        parent=section_style,
        textColor='#d4af37',  # Gold color for emphasis
    )
    story.append(Paragraph("RECOMMENDED DEEP DIVES", deepdive_style))
    
    deepdive_query = """Based on all the news stories from today, identify 1-2 stories that are particularly worth reading the full articles on. 
    These should be stories that:
    - Have significant long-term implications
    - Are complex enough to benefit from deeper reading
    - Represent important trends or turning points
    
    Format as:
    **Story Title** [Source with link if available]
    Why read the full article: One sentence explaining why this deserves deeper attention."""
    
    deepdive_news = search_news(client, deepdive_query, max_results=2, section_type="deepdive")
    story.append(Paragraph(deepdive_news, content_style))
    
    # Build PDF
    print("Building PDF document...")
    doc.build(story)
    print(f"PDF generated: {pdf_filename}")
    
    return pdf_filename


def send_email(pdf_path):
    """Send the daily brief via email."""
    print("Sending email...")
    
    if not all([EMAIL_ADDRESS, EMAIL_PASSWORD, RECIPIENT_EMAIL]):
        print("ERROR: Email credentials not configured!")
        print(f"EMAIL_ADDRESS: {'Set' if EMAIL_ADDRESS else 'Not set'}")
        print(f"EMAIL_PASSWORD: {'Set' if EMAIL_PASSWORD else 'Not set'}")
        print(f"RECIPIENT_EMAIL: {RECIPIENT_EMAIL}")
        sys.exit(1)
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = f"Daily Intelligence Brief - {datetime.now().strftime('%B %d, %Y')}"
    
    body = """Your daily intelligence brief is attached.

This automated brief covers:
- AI & Technology
- Finance & Markets  
- Real Estate
- Hacker News Highlights
- Regional News (North America, Europe, Asia-Pacific, Middle East & Africa, Latin America)
- Deep Dive Recommendations

Best regards,
Your Daily Brief System
"""
    
    msg.attach(MIMEText(body, 'plain'))
    
    # Attach PDF
    with open(pdf_path, 'rb') as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 
                       f'attachment; filename=daily_brief_{datetime.now().strftime("%Y%m%d")}.pdf')
        msg.attach(part)
    
    # Send via Gmail SMTP
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Email sent successfully to {RECIPIENT_EMAIL}")
    except Exception as e:
        print(f"Error sending email: {e}")
        sys.exit(1)


def main():
    """Main execution function."""
    try:
        print(f"Starting Daily Brief Generation at {datetime.now()}")
        pdf_path = generate_brief()
        send_email(pdf_path)
        print("Daily brief completed successfully!")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
