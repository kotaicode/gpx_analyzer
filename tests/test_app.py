import pytest
from flask import Flask
from werkzeug.datastructures import FileStorage
from io import BytesIO
import json
from app import (
    validate_gpx_file,
    process_gpx_file,
    query_overpass_api,
    calculate_suitability,
    calculate_elevation_gain
)
from config import Config

# Sample GPX content for testing
SAMPLE_GPX = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1">
    <trk>
        <trkseg>
            <trkpt lat="47.123" lon="8.123">
                <ele>100</ele>
            </trkpt>
            <trkpt lat="47.124" lon="8.124">
                <ele>150</ele>
            </trkpt>
            <trkpt lat="47.125" lon="8.125">
                <ele>120</ele>
            </trkpt>
        </trkseg>
    </trk>
</gpx>
"""

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app

@pytest.fixture
def valid_gpx_file():
    return FileStorage(
        stream=BytesIO(SAMPLE_GPX.encode()),
        filename="test.gpx",
        content_type="application/gpx+xml"
    )

def test_validate_gpx_file_valid(valid_gpx_file):
    """Test validation of a valid GPX file"""
    result = validate_gpx_file(valid_gpx_file)
    assert result == valid_gpx_file

def test_validate_gpx_file_invalid_extension():
    """Test validation fails with wrong file extension"""
    invalid_file = FileStorage(
        stream=BytesIO(b"test content"),
        filename="test.txt"
    )
    with pytest.raises(Exception) as exc_info:
        validate_gpx_file(invalid_file)
    assert "Invalid file format" in str(exc_info.value)

def test_process_gpx_file(valid_gpx_file):
    """Test processing of a valid GPX file"""
    points = process_gpx_file(valid_gpx_file)
    assert len(points) == 3
    assert len(points[0]) == 3  # Each point should have lon, lat, ele
    assert points[0] == (8.123, 47.123, 100.0)

def test_process_gpx_file_invalid():
    """Test processing fails with invalid GPX content"""
    invalid_file = FileStorage(
        stream=BytesIO(b"invalid content"),
        filename="test.gpx"
    )
    with pytest.raises(Exception) as exc_info:
        process_gpx_file(invalid_file)
    assert "Invalid GPX file format" in str(exc_info.value)

@pytest.mark.vcr()  # Requires vcrpy for API mocking
def test_query_overpass_api():
    """Test Overpass API query"""
    bbox = "47.123,8.123,47.125,8.125"
    result = query_overpass_api(bbox)
    assert isinstance(result, dict)
    assert 'elements' in result

def test_calculate_suitability():
    """Test suitability calculation with various surface types"""
    surface_data = {
        "asphalt": 1.5,
        "gravel": 0.8,
        "dirt": 0.7
    }
    result = calculate_suitability(surface_data)
    assert isinstance(result, dict)
    assert "roadbike" in result
    assert "gravelbike" in result
    assert 0 <= result["roadbike"] <= 1
    assert 0 <= result["gravelbike"] <= 1

def test_calculate_suitability_empty():
    """Test suitability calculation with empty surface data"""
    result = calculate_suitability({})
    assert result == {"roadbike": 0.0, "gravelbike": 0.0}

def test_calculate_elevation_gain():
    """Test elevation gain calculation"""
    points = [
        (8.123, 47.123, 100),  # lon, lat, elevation
        (8.124, 47.124, 150),
        (8.125, 47.125, 120)
    ]
    result = calculate_elevation_gain(points)
    assert result["elevation_up"] == 50.0
    assert result["elevation_down"] == 30.0

def test_calculate_elevation_gain_flat():
    """Test elevation gain calculation with flat terrain"""
    points = [
        (8.123, 47.123, 100),
        (8.124, 47.124, 100),
        (8.125, 47.125, 100)
    ]
    result = calculate_elevation_gain(points)
    assert result["elevation_up"] == 0.0
    assert result["elevation_down"] == 0.0 