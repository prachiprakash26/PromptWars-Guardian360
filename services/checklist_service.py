from typing import List, Dict

def get_standard_checklist() -> List[str]:
    """
    Returns standard monsoon preparedness actions.
    """
    return [
        "Clean gutters and storm drains around the property to prevent water accumulation.",
        "Inspect roof, ceilings, and window frames for structural cracks or leaks.",
        "Stock up on 3 days of non-perishable food and bottled drinking water.",
        "Check and replenish the first-aid kit with personal medicines and anti-septic liquids.",
        "Fully charge emergency lanterns, power banks, and check backup power generators.",
        "Secure loose outdoor objects (e.g., plants, trash cans) against high winds."
    ]

def get_travel_checklist() -> List[str]:
    """
    Returns transit preparedness actions when travel is planned.
    """
    return [
        "Check local navigation maps and local news channels for road closures before departure.",
        "Pack high-quality waterproof gear (raincoat, umbrella, dry boots).",
        "Place mobile phones, wallets, and documents into sealed waterproof zip bags.",
        "Check vehicle tires, wiper blades, headlight indicators, and brake fluids.",
        "Verify emergency towing and roadside assistance contacts are saved in your phone."
    ]

def get_emergency_checklist() -> List[str]:
    """
    Returns severe emergency warnings and immediate survival steps.
    """
    return [
        "Turn off the main electrical power grid and gas valves immediately if water approaches.",
        "Secure all critical documents (IDs, property deeds, medical files) in a waterproof bag.",
        "Move valuable items, electronics, and food stocks to an elevated floor or surface.",
        "Keep a battery-operated radio or mobile phone active for official evacuation alerts.",
        "Keep emergency contacts pre-dialed and notify family members of your current location.",
        "Check on elderly neighbors, infants, and pets to ensure they are safe."
    ]

def get_offline_tips() -> List[Dict[str, str]]:
    """
    Returns safety tips for offline or low-connectivity scenarios.
    """
    return [
        {
            "title": "Water Safety",
            "tip": "Only drink boiled, filtered, or sealed bottled water. Stagnant flood waters contaminate local aquifers instantly."
        },
        {
            "title": "Power Outage Protocol",
            "tip": "Keep refrigerator and freezer doors closed. Unopened refrigerators keep food cold for up to 4 hours."
        },
        {
            "title": "Floodwater Danger",
            "tip": "Never walk, swim, or drive through floodwaters. Just 6 inches of moving water can knock you down, and 12 inches can sweep a vehicle away."
        },
        {
            "title": "Wind Protection",
            "tip": "During high wind storms, stay inside and away from windows. Take shelter in interior corridors or closets."
        }
    ]
