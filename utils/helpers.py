import html
import re
from fpdf import FPDF
from models.data_models import UserProfile, WeatherData, RiskAssessment

def sanitize_html(text: str) -> str:
    """
    Sanitizes user input to prevent HTML injection (XSS).
    """
    if not text:
        return ""
    # Strip basic HTML tags
    clean = re.sub(r"<[^>]*>", "", text)
    # Convert special characters to HTML entities
    return html.escape(clean.strip())

def clean_pdf_text(text: str) -> str:
    """
    Normalizes unicode characters to equivalent ASCII/Latin-1 strings
    to prevent FPDF encoding crashes.
    """
    if not text:
        return ""
    
    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00b0": " deg ",
        "\u2022": "- ",
        "\u2103": " deg C",
        "\u2109": " deg F",
        "\u20a8": "Rs.",
        "\u20b9": "Rs.",
        "°": " deg "
    }
    
    for key, val in replacements.items():
        text = text.replace(key, val)
        
    # Replace non-latin-1 characters with a fallback
    encoded = text.encode("latin-1", errors="replace")
    return encoded.decode("latin-1")

def generate_preparedness_pdf(profile: UserProfile, weather: WeatherData, risks: RiskAssessment, plan_text: str) -> bytes:
    """
    Generates a personalized PDF preparedness report.
    Returns the raw PDF file bytes.
    """
    pdf = FPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # 1. Header & Title Block
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(18, 53, 91) # Slate Blue
    pdf.cell(w=0, h=10, text="Guardian360 Climate Preparedness Summary", new_x="LMARGIN", new_y="NEXT", align="C")
    
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(w=0, h=8, text="AI-Powered Personalized Disaster Preparedness & Citizen Assistance Report", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)
    
    # Draw horizontal divider
    pdf.set_draw_color(18, 53, 91)
    pdf.set_line_width(0.5)
    pdf.line(10, 30, 200, 30)
    pdf.ln(5)
    
    # Reset text color
    pdf.set_text_color(0, 0, 0)
    
    # 2. Section: Profile Details
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(w=0, h=8, text="1. Personal Profile Context", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(w=0, h=6, text=clean_pdf_text(f"Name: {profile.name} (Age: {profile.age})"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(w=0, h=6, text=clean_pdf_text(f"Location: {profile.city}, {profile.state}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(w=0, h=6, text=clean_pdf_text(f"Preferred Language: {profile.preferred_language}"), new_x="LMARGIN", new_y="NEXT")
    
    vuln_list = []
    if profile.has_seniors: vuln_list.append("Senior Citizens")
    if profile.has_children: vuln_list.append("Children")
    if profile.medical_conditions: vuln_list.extend(profile.medical_conditions)
    vuln_str = ", ".join(vuln_list) if vuln_list else "None declared"
    pdf.cell(w=0, h=6, text=clean_pdf_text(f"Vulnerability Factors: {vuln_str}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(w=0, h=6, text=clean_pdf_text(f"Dwelling details: {'Ground Floor (Higher flood risk)' if profile.lives_on_ground_floor else 'Above Ground Floor'}"), new_x="LMARGIN", new_y="NEXT")
    
    commute_info = "Yes" if profile.daily_commute else "No"
    vehicle_info = profile.vehicle_type if profile.has_vehicle else "None"
    pdf.cell(w=0, h=6, text=clean_pdf_text(f"Daily Commute: {commute_info} | Vehicle: {vehicle_info} | Distance: {profile.commute_distance_km} km"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    
    # 3. Section: Live Weather
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(w=0, h=8, text="2. Local Weather Observations", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(w=0, h=6, text=clean_pdf_text(f"Temperature: {weather.temperature:.1f} C | Humidity: {weather.humidity:.1f}%"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(w=0, h=6, text=clean_pdf_text(f"Rainfall: {weather.rain:.1f} mm | Showers: {weather.showers:.1f} mm | Total Precipitation: {weather.precipitation:.1f} mm"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(w=0, h=6, text=clean_pdf_text(f"Wind Speed: {weather.wind_speed:.1f} km/h (Gusts: {weather.wind_gusts:.1f} km/h)"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    
    # 4. Section: Risk Assessment
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(w=0, h=8, text="3. Deterministic Safety Risk Diagnostics", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(w=0, h=6, text=clean_pdf_text(f"Weather Severity Level: {risks.weather_severity_level.value}"), new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(w=0, h=5, text=clean_pdf_text(f"Severity Details: {risks.weather_severity_desc}"))
    pdf.ln(1)
    
    pdf.cell(w=0, h=6, text=clean_pdf_text(f"Flood Exposure Risk: {risks.flood_risk_level.value}"), new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(w=0, h=5, text=clean_pdf_text(f"Flood Details: {risks.flood_risk_desc}"))
    pdf.ln(1)
    
    pdf.cell(w=0, h=6, text=clean_pdf_text(f"Travel Hazard Risk: {risks.travel_risk_level.value}"), new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(w=0, h=5, text=clean_pdf_text(f"Travel Details: {risks.travel_risk_desc}"))
    pdf.ln(1)
    
    pdf.cell(w=0, h=6, text=clean_pdf_text(f"Health Vulnerability Risk: {risks.health_risk_level.value}"), new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(w=0, h=5, text=clean_pdf_text(f"Health Details: {risks.health_risk_desc}"))
    pdf.ln(1)
    
    pdf.cell(w=0, h=6, text=clean_pdf_text(f"Overall Preparedness Score: {risks.overall_preparedness_score}/100"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    
    # 5. Section: AI Preparedness Plan
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(w=0, h=8, text="4. Guardian360 Recommended Actions", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "", 10)
    cleaned_plan = plan_text.replace("**", "").replace("### ", "").replace("## ", "").replace("# ", "")
    cleaned_plan = clean_pdf_text(cleaned_plan)
    pdf.multi_cell(w=0, h=5.5, text=cleaned_plan)
    
    # 6. Emergency Contacts
    if profile.emergency_contacts:
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(w=0, h=8, text="5. Saved Emergency Contacts", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        for contact in profile.emergency_contacts:
            contact_str = f"- {contact.name} ({contact.relation}): {contact.phone}"
            pdf.cell(w=0, h=6, text=clean_pdf_text(contact_str), new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())


def get_custom_css(emergency_mode: bool = False) -> str:
    """
    Returns custom CSS styles for clean UI dark aesthetics.
    Adapts based on emergency mode status.
    """
    base_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* App-wide styling rules */
    .stApp {
        background-color: #f8fafc;
        color: #0f172a;
    }
    
    /* Card design system (Glassmorphism) */
    .glass-card {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(15, 23, 42, 0.08);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(15, 23, 42, 0.05);
        transition: all 0.3s ease;
        color: #0f172a;
    }
    
    .glass-card:hover {
        border-color: rgba(15, 23, 42, 0.15);
        box-shadow: 0 8px 32px 0 rgba(15, 23, 42, 0.1);
        transform: translateY(-2px);
    }
    
    /* Bullet styling and spacing */
    .accent-header {
        font-weight: 700;
        background: linear-gradient(120deg, #1e3a8a 0%, #4f46e5 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }
    
    /* Custom risk badges */
    .risk-badge-low {
        background-color: #d1fae5;
        color: #065f46;
        border: 1px solid #10b981;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: 600;
        display: inline-block;
    }
    .risk-badge-moderate {
        background-color: #fef3c7;
        color: #92400e;
        border: 1px solid #f59e0b;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: 600;
        display: inline-block;
    }
    .risk-badge-high {
        background-color: #fee2e2;
        color: #991b1b;
        border: 1px solid #ef4444;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: 600;
        display: inline-block;
    }
    .risk-badge-extreme {
        background-color: #fecaca;
        color: #991b1b;
        border: 2px solid #dc2626;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.9em;
        font-weight: 700;
        display: inline-block;
        animation: pulse-red 2s infinite;
    }
    
    /* Pulse red animation */
    @keyframes pulse-red {
        0% { transform: scale(1); }
        50% { transform: scale(1.03); box-shadow: 0 0 15px rgba(220, 38, 38, 0.5); }
        100% { transform: scale(1); }
    }
    
    /* Floating button style */
    .stButton>button {
        background: linear-gradient(135deg, #0284c7 0%, #4f46e5 100%);
        color: white;
        border: none;
        padding: 8px 20px;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    .stButton>button:hover {
        opacity: 0.95;
        transform: scale(1.01);
    }
    
    /* Footer layout styling */
    .footer-text {
        text-align: center;
        font-size: 0.8em;
        color: #475569;
        margin-top: 50px;
        border-top: 1px solid rgba(15, 23, 42, 0.08);
        padding-top: 15px;
    }
    </style>
    """
    
    emergency_css = """
    <style>
    /* Emergency Mode override */
    .stApp {
        background-color: #170505 !important;
        background-image: radial-gradient(circle at top, #2e0909 0%, #120303 100%) !important;
        color: #fee2e2 !important;
    }
    
    .glass-card {
        background: rgba(45, 15, 15, 0.5) !important;
        border: 1px solid rgba(239, 68, 68, 0.2) !important;
        box-shadow: 0 8px 32px 0 rgba(185, 28, 28, 0.15) !important;
    }
    
    .glass-card:hover {
        border-color: rgba(239, 68, 68, 0.4) !important;
        box-shadow: 0 8px 32px 0 rgba(185, 28, 28, 0.25) !important;
    }
    
    .accent-header {
        background: linear-gradient(120deg, #f87171 0%, #f43f5e 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
    }
    
    /* Emergency specific animations */
    .emergency-banner {
        background: linear-gradient(90deg, #991b1b 0%, #dc2626 50%, #991b1b 100%);
        border: 2px solid #f87171;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        font-weight: 700;
        font-size: 1.2rem;
        color: white;
        margin-bottom: 25px;
        animation: pulse-border 1.5s infinite;
    }
    
    @keyframes pulse-border {
        0% { box-shadow: 0 0 10px rgba(239, 68, 68, 0.5); }
        50% { box-shadow: 0 0 25px rgba(239, 68, 68, 0.85); }
        100% { box-shadow: 0 0 10px rgba(239, 68, 68, 0.5); }
    }
    </style>
    """
    
    if emergency_mode:
        return base_css + emergency_css
    return base_css
