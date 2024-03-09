#!/usr/bin/env python3
import pytest
from datetime import datetime, timedelta
from iss_tracker import download_and_parse_iss_data, parse_date, calculate_speed, find_epoch_by_date, fetch_iss_data, calculate_location, get_geoposition, app
from flask.testing import FlaskClient
import requests

# Constants
URL = "https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.xml"

mock_state_vectors = [
    {
        'EPOCH': '2024-02-22T12:00:00.000Z',
        'X': 42164.0,
        'Y': -231.4,
        'Z': 1450.5,
        'X_DOT': 0.67,
        'Y_DOT': 2.08,
        'Z_DOT': -0.03
    },
    {
        'EPOCH': '2024-02-22T13:00:00.000Z',
        'X': 42165.2,
        'Y': -230.1,
        'Z': 1451.7,
        'X_DOT': 0.68,
        'Y_DOT': 2.09,
        'Z_DOT': -0.02
    },
    {
        'EPOCH': '2024-02-22T14:00:00.000Z',
        'X': 42166.4,
        'Y': -228.8,
        'Z': 1452.9,
        'X_DOT': 0.69,
        'Y_DOT': 2.10,
        'Z_DOT': -0.01
    },
    {
        'EPOCH': '2024-02-22T15:00:00.000Z',
        'X': 42167.6,
        'Y': -227.5,
        'Z': 1454.1,
        'X_DOT': 0.70,
        'Y_DOT': 2.11,
        'Z_DOT': 0.00
    },
    {
        'EPOCH': '2024-02-22T16:00:00.000Z',
        'X': 42168.8,
        'Y': -226.2,
        'Z': 1455.3,
        'X_DOT': 0.71,
        'Y_DOT': 2.12,
        'Z_DOT': 0.01
    }
]

def test_parse_date():
    """
    Tests the parse_date function to ensure it correctly processes the data.

    Args:
        None

    Returns:
        None
    """
    test_date_str = "2024-047T12:00:00.000Z"
    expected_date = datetime(2024, 2, 16, 12, 0, 0, 0)

    assert parse_date(test_date_str) == expected_date

    with pytest.raises(ValueError):
        parse_date("Invalid-Date-String")

def test_download_and_parse_iss_data():
    """
    Tests the download_and_parse_iss_data function to ensure it can download and parse data from the NASA website.

    Args:
        None

    Returns:
        None
    """
    data = download_and_parse_iss_data(URL)

    # Basic assertions to ensure we got data
    assert isinstance(data, dict)
    assert len(data) > 0 
    
    # Check the presence of expected keys in the data
    assert 'header' in data
    assert 'metadata' in data
    assert 'state_vectors' in data
    assert 'comments' in data

    # Check the structure of the header
    assert isinstance(data['header'], dict)

    # Check the structure of the metadata
    assert isinstance(data['metadata'], dict)

    # Check the structure of the comments
    assert isinstance(data['comments'], list)

    # Check the structure of the state vectors
    state_vectors = data['state_vectors']
    assert isinstance(state_vectors, list)
    assert len(state_vectors) > 0
    
    # Check the structure of a single state vector
    example_vector = state_vectors[0]
    assert isinstance(example_vector, dict)
    assert 'EPOCH' in example_vector and isinstance(example_vector['EPOCH'], str)
    assert 'X' in example_vector and isinstance(example_vector['X'], float)
    assert 'Y' in example_vector and isinstance(example_vector['Y'], float)
    assert 'Z' in example_vector and isinstance(example_vector['Z'], float)
    assert 'X_DOT' in example_vector and isinstance(example_vector['X_DOT'], float)
    assert 'Y_DOT' in example_vector and isinstance(example_vector['Y_DOT'], float)
    assert 'Z_DOT' in example_vector and isinstance(example_vector['Z_DOT'], float)

    # Check the format of the EPOCH string
    epoch_str = example_vector['EPOCH']
    assert datetime.fromisoformat(epoch_str)

def test_fetch_iss_data():
    """
    Tests the fetch_iss_data function to ensure it can retrieve data from the server or database.
    
    Args:
        None

    Returns:
        None
    """
    with app.app_context():
        data = fetch_iss_data()

        # Ensure we got data
        assert isinstance(data, dict)
        assert 'state_vectors' in data
        assert isinstance(data['state_vectors'], list)
        assert len(data['state_vectors']) > 0

        # Check a single state vector for expected keys and types
        example_vector = data['state_vectors'][0]
        assert isinstance(example_vector, dict)
        assert all(key in example_vector for key in ['EPOCH', 'X', 'Y', 'Z', 'X_DOT', 'Y_DOT', 'Z_DOT'])
        assert all(isinstance(example_vector[key], float) for key in ['X', 'Y', 'Z', 'X_DOT', 'Y_DOT', 'Z_DOT'])
        assert isinstance(example_vector['EPOCH'], str)

def test_calculate_speed():
    """
    Tests the calculate_speed function to ensure it returns the correct value for speed.

    Args:
        None

    Returns:
        None
    """
    x_dot, y_dot, z_dot = 4.0, 3.0, 0.0
    expected_speed = 5.0
    assert calculate_speed(x_dot, y_dot, z_dot) == expected_speed

def test_find_epoch_by_date():
    """
    Tests the find_epoch_by_date function to ensure it correctly finds and returns the data for a given date.

    Args:
        None

    Returns:
        None
    """
    with app.app_context():
        data = fetch_iss_data()
        valid_epoch = data['state_vectors'][0]['EPOCH']
        result = find_epoch_by_date(data['state_vectors'], valid_epoch)

        assert result is not None
        assert result['EPOCH'] == valid_epoch

def test_calculate_location():
    """
    Tests the calculate_location function to ensure it calculates the latitude, longitude, and altitude.
    
    Args:
        None

    Returns:
        None
    """
    with app.app_context():
        data = fetch_iss_data()
        test_epoch_data = data['state_vectors'][0]

        lat, lon, alt = calculate_location(test_epoch_data)
        assert isinstance(lat, float)
        assert isinstance(lon, float)
        assert isinstance(alt, float)

def test_get_geoposition():
    """
    Tests the get_geoposition function to ensure it retrieves the correct geolocation information.
    
    Args:
        None

    Returns:
        None
    """
    with app.app_context():
        # Test with a known set of coordinates
        known_lat, known_lon = 40.7128, -74.0060  # Coordinates for New York City
        location_info = get_geoposition(known_lat, known_lon)

        assert isinstance(location_info, str)
        assert "New York" in location_info

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_comment(client):
    """
    Tests the /comment route to ensure it returns the comments.

    Args:
        client (FlaskClient): Flask test client.

    Returns:
        None
    """
    response = client.get('/comment')
    assert response.status_code == 200

def test_get_header(client):
    """
    Tests the /header route to ensure it returns the header.

    Args:
        client (FlaskClient): Flask test client.

    Returns:
        None
    """
    response = client.get('/header')
    assert response.status_code == 200

def test_get_metadata(client):
    """
    Tests the /metadata route to ensure it returns the metadata.

    Args:
        client (FlaskClient): Flask test client.

    Returns:
        None
    """
    response = client.get('/metadata')
    assert response.status_code == 200

def test_get_epochs_data(client):
    """
    Tests the /epochs route with & without query parameters to ensure it returns the correct list of epochs.

    Args:
        client (FlaskClient): Flask test client.

    Returns:
        None
    """
    # Test no query parameters
    response = client.get('/epochs')
    assert response.status_code == 200

    # Test invalid limit and offset
    invalid_params = [
        ('?limit=0', 400),
        ('?limit=-10', 400),
        ('?offset=-5', 400),
        ('?offset=9999999999999999999', 400),
        ('?limit=abc', 400),
        ('?offset=def', 400),
        ('?limit=0.5', 400),
        ('?offset=1.5', 400),
    ]
    valid_params = [
        ('?limit=10', 200),
        ('?offset=5', 200),
        ('?limit=9999999999999999999', 200),
        ('?offset=0', 200)
    ]
    for param, status_code in invalid_params:
        response = client.get(f'/epochs{param}')
        assert response.status_code == status_code

    for param, status_code in valid_params:
        response = client.get(f'/epochs{param}')
        assert response.status_code == status_code

def test_get_specific_epoch_data(client):
    """
    Tests the /epochs/<epoch> route to ensure it returns data for a specific epoch.

    Args:
        client (FlaskClient): Flask test client.

    Returns:
        None
    """
    # Test valid epoch
    with app.app_context():
        data = fetch_iss_data()
        valid_epoch = data['state_vectors'][0]['EPOCH']
    response = client.get(f'/epochs/{valid_epoch}')
    assert response.status_code == 200
    data = response.get_json()
    assert 'EPOCH' in data
    assert data['EPOCH'] == valid_epoch

    # Test invalid epochs
    invalid_epochs = [
        'invalid_epoch',
        '2024-13-32T25:61:61',
        '2024-00-00T00:00:00',
        '2023-02-29T00:00:00',
        '1.5',
        '-1',
        'abc'
    ]
    for epoch in invalid_epochs:
        response = client.get(f'/epochs/{epoch}')
        assert response.status_code == 400

    # Test empty epoch
    response = client.get('/epochs/')
    assert response.status_code == 404

    # Test epoch not found
    not_found_epoch = '2022-01-01T00:00:00'
    response = client.get(f'/epochs/{not_found_epoch}')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
    assert data['error'] == 'Epoch not found'

def test_get_specific_epoch_speed(client):
    """
    Tests the /epochs/<epoch>/speed route to ensure it returns the speed.

    Args:
        client (FlaskClient): Flask test client.

    Returns:
        None
    """
    with app.app_context():
        data = fetch_iss_data()
        valid_epoch = data['state_vectors'][0]['EPOCH']
    response = client.get(f'/epochs/{valid_epoch}/speed')
    assert response.status_code == 200
    assert 'SPEED' in response.json

def test_get_specific_epoch_location(client):
    """
    Tests the /epochs/<epoch>/location route to ensure it returns the latitude, longitude, altitude, and geolocation.

    Args:
        client (FlaskClient): Flask test client.

    Returns:
        None
    """
    with app.app_context():
        data = fetch_iss_data()
        valid_epoch = data['state_vectors'][0]['EPOCH']
    response = client.get(f'/epochs/{valid_epoch}/location')
    assert response.status_code == 200
    assert 'LATITUDE' in response.json
    assert 'LONGITUDE' in response.json
    assert 'ALTITUDE' in response.json
    assert 'GEOPOSITION' in response.json

def test_get_current_epoch_data(client):
    """
    Tests the /now route to ensure it returns current epoch data and speed.

    Args:
        client (FlaskClient): Flask test client.

    Returns:
        None
    """
    response = client.get('/now')
    assert response.status_code == 200
    assert 'ALTITUDE' in response.json
    assert 'EPOCH' in response.json
    assert 'GEOPOSITION' in response.json
    assert 'LATITUDE' in response.json
    assert 'LONGITUDE' in response.json
    assert 'SPEED' in response.json