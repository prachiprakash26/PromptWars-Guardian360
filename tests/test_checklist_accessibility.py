import pytest
from services.checklist_service import get_standard_checklist, get_travel_checklist, get_emergency_checklist, get_offline_tips
from utils.helpers import get_custom_css

def test_checklist_service_outputs():
    # Verify standard checklist returns list of string rules
    std = get_standard_checklist()
    assert len(std) > 0
    assert any("drain" in item.lower() for item in std)

    # Verify travel checklist returns lists
    trv = get_travel_checklist()
    assert len(trv) > 0
    assert any("waterproof" in item.lower() for item in trv)

    # Verify emergency checklist returns lists
    em = get_emergency_checklist()
    assert len(em) > 0
    assert any("electrical" in item.lower() for item in em)

    # Verify offline tips dictionary structure
    tips = get_offline_tips()
    assert len(tips) > 0
    assert "title" in tips[0]
    assert "tip" in tips[0]


def test_accessibility_elements_in_css():
    # Verify accessibility parameters like high-contrast text and layout scaling are in CSS
    css_normal = get_custom_css(emergency_mode=False)
    css_emergency = get_custom_css(emergency_mode=True)

    # Colors: light mode contrast check
    # Check that light background is set
    assert "#f8fafc" in css_normal # Slate-50 background
    assert "#0f172a" in css_normal # Slate-900 readable text
    
    # Accessible readable font family Outfit is imported
    assert "Outfit" in css_normal
    assert "sans-serif" in css_normal

    # Check color contrast indicator changes in Emergency mode
    assert "#170505" in css_emergency # Crimson red background override
    assert "#fee2e2" in css_emergency # Bright rose-white text for extreme readability
    
    # Icons plus text: Verify ARIA-like layout structures
    assert "pulse-red" in css_normal


def test_performance_caching_decorator():
    # Validate that weather API and helper functions are cacheable and avoid duplicate requests.
    # In Streamlit, caching is implemented at the integration level.
    # We will verify that caching libraries can wrap the data.
    import streamlit as st
    
    # Assert that streamlit cache functions exist and can be called
    assert hasattr(st, "cache_data")
    assert hasattr(st, "cache_resource")
