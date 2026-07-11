# Guardian360

### *AI-Powered Climate Preparedness & Citizen Assistance Platform*

Guardian360 is a production-quality, enterprise-grade climate preparedness platform designed to guide individuals and families through a safety journey during monsoon season. It integrates live weather insights, rule-based hazard risk metrics, and context-locked GenAI advice to deliver customized, actionable survival guidelines.

---

## Table of Contents
1. [Project Overview & Problem Statement](#project-overview--problem-statement)
2. [Key Architecture & Folder Structure](#key-architecture--folder-structure)
3. [Technology Stack](#technology-stack)
4. [Story-Driven User Flow](#story-driven-user-flow)
5. [Deterministic Risk Assessment Engine](#deterministic-risk-assessment-engine)
6. [Hallucination Prevention Strategy](#hallucination-prevention-strategy)
7. [Security Configurations](#security-configurations)
8. [Accessibility Standards](#accessibility-standards)
9. [Testing Framework & Pytest Cases](#testing-framework--pytest-cases)
10. [Deployment & Secrets Setup](#deployment--secrets-setup)
11. [Assumptions, Known Limitations & Future Enhancements](#assumptions-known-limitations--future-enhancements)

---

## Project Overview & Problem Statement

Monsoons often present sudden local hazards: flash flooding, severe road waterlogging, high-wind trees collapsing, and stagnant-water illnesses. Citizens struggle to find relevant, cohesive advice tailored to their specific dwelling conditions (e.g., ground floor exposures), family vulnerabilities (seniors, children), or transit plans (two-wheelers vs. cars). 

Existing solutions typically present generic weather readouts or rely on hallucination-prone AI models to estimate safety threat scores.

**Guardian360** bridges this gap by combining:
- **Real-Time Data**: Live weather parameters resolved via coordinates lookup.
- **Deterministic Python Rules**: Zero-hallucination mathematical models assessing travel, flood, and health risks.
- **Dynamic Checklists**: Interactive household trackers modifying preparedness outcomes on-the-fly.
- **Context-Locked GenAI (Gemini 2.5 Flash)**: Strictly restricted natural language translation of calculated risk reports.
- **Fail-Safe UI**: Automatically triggers high-contrast, offline-ready emergency dashboards under critical weather indicators.

---

## Key Architecture & Folder Structure

The application separates core data boundaries, calculations, LLM routines, and presentation states:

```
├── app.py                      # Streamlit UI router & story journey pages
├── requirements.txt            # Python dependencies (streamlit, google-genai, etc.)
├── README.md                   # System documentation
├── models/
│   ├── __init__.py
│   └── data_models.py          # Pydantic schemas validating profiles & weather objects
├── services/
│   ├── __init__.py
│   ├── weather_service.py      # Open-Meteo API consumer (Forecast/Geocoding)
│   ├── risk_engine.py          # Pure Python deterministic risk assessment rules
│   ├── llm_service.py          # Gemini 2.5 Flash SDK implementation with safety guards
│   └── checklist_service.py    # Standard, transit, and emergency checklists configurations
├── utils/
│   ├── __init__.py
│   └── helpers.py              # XSS HTML sanitization, CSS themes, and FPDF2 report generator
└── tests/
    ├── __init__.py
    ├── test_weather_service.py # Mock tests for weather timeouts & geocoding failures
    ├── test_risk_engine.py      # Assertions on rule permutations (seniors, ground floor, etc.)
    ├── test_llm_service.py      # Asserts prompt contents contain structure context and guardrails
    ├── test_security_validation.py # SQL injection, XSS checks, unicode translation tests
    └── test_checklist_accessibility.py # Test contrast ratios, styling and checklist content mapping
```

---

## Technology Stack

- **Frontend Dashboard**: Streamlit (v1.52.1)
- **Programming Language**: Python (v3.13.7)
- **GenAI SDK**: Google GenAI SDK (`google-genai` v2.8.0)
- **Language Model**: Gemini 2.5 Flash (`gemini-2.5-flash`)
- **Data Validation**: Pydantic (v2.13.4)
- **Weather API**: Open-Meteo API (Open Source, Keyless)
- **PDF Exporter**: FPDF2 (v2.8.7)
- **Test Engine**: Pytest (v9.1.1)

---

## Story-Driven User Flow

The application organizes the citizen journey into 7 logical steps:
1. **Welcome Landing Page**: Highlighting platform scope and security configurations.
2. **Onboarding Form**: Captures Name, Age, Location, Dwelling Floor, Vehicle commute details, and Emergency Contacts. Safely validates inputs using Pydantic. Saved profiles persist locally in `user_profile.json`.
3. **Live Weather & Safety Dashboard**: Displays temperature, humidity, wind gusts, and rainfall alongside interactive WMO weather codes. Plots a 24-hour rain trend and calculates rule-based risks.
4. **AI Action Planner**: Leverages Gemini 2.5 Flash to summarize the metrics into a clear natural-language document.
5. **Interactive Assistant**: Conversational chat client strictly restricted to the user's current context.
6. **Emergency Portal**: High-contrast dark crimson dashboard triggered automatically during high-wind, heavy storm or high flood warnings. Displays emergency directory checklists and offline water/power security tips.
7. **Report Export**: Compiles all observations and action plans into a clean, portable PDF summary file.

---

## Deterministic Risk Assessment Engine

Risks are evaluated using explicit Python rule tables, preventing GenAI hallucinations of severity levels.

- **Weather Severity Rating**: Computed out of 100 based on precipitation volumes, wind speeds, and severe WMO weather codes. Classified into `Low`, `Moderate`, `High`, and `Extreme`.
- **Flood Exposure Risk**: Combined impact of rainfall volume and dwelling characteristics. Ground-floor residents are automatically classified under `Extreme` risk if precipitation exceeds 50mm.
- **Travel Hazard Risk**: Elevated for commuters during wet weather, particularly two-wheeler riders due to reduced stability and high skidding coefficients on slick roads.
- **Health Vulnerability Risk**: Evaluates pre-existing conditions (Asthma, Arthritis) against atmospheric humidity (>80%) and temperature drops (<20°C).
- **Preparedness Score**: Evaluated dynamically based on profile completeness (40 points) and checkmark list completions (60 points).

---

## Hallucination Prevention Strategy

To ensure zero hallucination, every system prompt injected into Gemini 2.5 Flash enforces:
1. **Context Anchoring**: The raw JSON outputs of `UserProfile`, `WeatherData`, and `RiskAssessment` are appended directly.
2. **Strict System Instructions**:
   > *Only answer using the supplied structured context. Never invent weather details, warnings, road closures, or medical advice not present in the supplied data. If information is unavailable, state so clearly.*
3. **Low Temperature**: Configured to `0.1` - `0.2` to restrict creative language variations, encouraging exact text lookups.

---

## Security Configurations

- **Secret Key isolation**: Gemini API key is extracted directly from Streamlit secrets (`st.secrets["GEMINI_API_KEY"]`) or environment variables, avoiding hardcoding.
- **XSS Prevention**: User inputs are sanitized using regex routines and HTML escaping before being rendered or passed to models.
- **Safe Serialization**: Avoids using `eval()` or `pickle` libraries to load profiles, utilizing safe JSON bindings and Pydantic validators.
- **Length Boundaries**: Limits inputs (e.g. text inputs capped via validators) to prevent memory crashes.

---

## Accessibility Standards

- **Color Contrast**: Complies with dark-mode guidelines. High-contrast rose white and cyan elements ensure maximum legibility against deep dark backgrounds.
- **Text & Icons**: Warnings are never shown purely as colors; they are paired with text labels and high-contrast alert icons (e.g. 🟢 Low, 🚨 Extreme).
- **Responsive Layout**: Engineered with Streamlit columns, ensuring clean, fluid structures on desktop, tablet, and mobile screens.

---

## Testing Framework & Pytest Cases

Run the test suite using python's module executor:
```bash
python -m pytest tests/
```

We validate **28 specific test scenarios**:
- **Weather Service**: Standard lookups, invalid cities, timeouts, and incomplete geocoding responses.
- **Risk calculations**: Single and multiple risk factors (elderly profiles, ground-floor dwellings during severe storms).
- **LLM Prompt Verification**: Confirming the presence of structured payload indices and system instructions.
- **Security Checkmarks**: XSS stripping, unicode normalization for PDFs, and Pydantic range constraints.
- **Checklist & Contrast Accessibility**: Contrast styling classes and offline safety matrix items.

---

## Deployment & Secrets Setup

### 1. Local Development
1. Clone the repository into your local system.
2. Install the requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your Gemini API key in your environment variables:
   ```bash
   # Windows PowerShell
   $env:GEMINI_API_KEY="your_api_key_here"
   
   # Linux/MacOS
   export GEMINI_API_KEY="your_api_key_here"
   ```
4. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```

### 2. Streamlit Community Cloud Deployment
1. Push your codebase to a public GitHub repository.
2. Connect your GitHub account to [Streamlit Community Cloud](https://share.streamlit.io/).
3. Create a new app, selecting your repository, branch, and `app.py` as the entrypoint file.
4. Navigate to **App Settings** -> **Secrets** and add your Gemini API key:
   ```toml
   GEMINI_API_KEY = "your_actual_gemini_api_key"
   ```
5. Click **Deploy**.

---

## Assumptions, Known Limitations & Future Enhancements

### Assumptions
- The system assumes coordinate lookup via Geocoding is sufficient for municipal boundaries.
- Monsoon risks are modeled primarily around precipitation, wind speed, dwelling floor, vehicle type, and pre-existing medical triggers.

### Known Limitations
- Real-time road closures are not fetched from live maps due to third-party API key restrictions (avoiding hardcoded keys/payment walls).
- Ephemeral containers on Streamlit Community Cloud reset local JSON profiles if the container undergoes container re-spinning (though `st.session_state` preserves active sessions).

### Future Enhancements
- Integration of open-source crowd-sourced transit alerts (e.g., OpenStreetMap incident markers).
- Support for automated push notifications for users who save coordinates.
- Multi-user data syncing with encrypted SQLite databases for offline local caching.

---

*Screenshots Placeholders*
* [Welcome Interface](images/welcome_landing.png)
* [Weather & Risk Dashboard](images/weather_risks.png)
* [Emergency Mode Layout](images/emergency_portal.png)
