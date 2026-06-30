from dotenv import load_dotenv
import os

load_dotenv()

# LLM
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Models
SUPERVISOR_MODEL = "gpt-5.4-nano"        # reasoning — needs to be smart
ANALYST_MODEL = "gpt-5.4-mini"           # implications — needs to be smart  
RESEARCH_MODEL = "gpt-5.4-nano"          # search queries — fast + cheap
BRIEFING_MODEL = "gpt-5.4-mini"          # final brief — needs to be smart
REGULATORY_MODEL = "gpt-4o-mini"         # final brief — needs to be smart

# Competitors to monitor
COMPETITORS = [
    "HDFC Pension Fund Management",
    "ICICI Prudential Pension fund",
    "Axis Bank NPS",
    "DSP Pension Fund",
    "Aditya Birla Sun Life Pension fund management limited",
    "SBI Pension Funds",
    "Kotak Mahindra Pension Fund",
    "UTI pension Fund",
    "LIC Pension Fund",
    "NJ India Invest",
    "Tata pension fund"
]

# PensionBox context — injected into every agent prompt
PENSIONBOX_CONTEXT = """
PensionBox.in is an Indian B2B fintech platform helping SMEs and large enterprises manage:
- Corporate NPS (National Pension System) enrollment and compliance
- EPF, PPF administration
- Employee benefits management
Target customers: Indian SMEs with 20-500 employees and large enterprises with 500+ employees
Key value prop: Simplifying pension and benefits compliance for HR teams and corporates
"""

