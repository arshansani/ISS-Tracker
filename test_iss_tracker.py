#!/usr/bin/env python3
import pytest
from datetime import datetime, timedelta
from iss_tracker import download_and_parse_iss_data, parse_date, calculate_speed, find_epoch_by_date, app
from flask.testing import FlaskClient
import requests

url = "https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.xml"

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

def test_parse_date_raises_error():
    """
    Tests the parse_date function to ensure it correctly raises an exception.

    Args:
        None

    Returns:
        None
    """
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
    data = download_and_parse_iss_data(url)

    # Basic assertions to ensure we got data
    assert isinstance(data, list)
    assert len(data) > 0  # Ensure there is data

    # Check the structure of a single data point
    example_data = data[0]
    assert 'EPOCH' in example_data and isinstance(example_data['EPOCH'], datetime)
    assert 'X' in example_data and isinstance(example_data['X'], float)
    assert 'Y' in example_data and isinstance(example_data['Y'], float)
    assert 'Z' in example_data and isinstance(example_data['Z'], float)
    assert 'X_DOT' in example_data and isinstance(example_data['X_DOT'], float)
    assert 'Y_DOT' in example_data and isinstance(example_data['Y_DOT'], float)
    assert 'Z_DOT' in example_data and isinstance(example_data['Z_DOT'], float)

def test_download_and_parse_iss_data_raises_error():
    """
    Tests the download_and_parse_iss_data function to ensure it raises an exception when given an invalid URL.

    Args:
        None

    Returns:
        None
    """
    invalid_url = "https://thisisdefinetelyaninvalidurl.com"
    with pytest.raises(requests.RequestException):
        download_and_parse_iss_data(invalid_url)
        
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
    test_date = datetime(2024, 2, 22, 12, 0, 0, 0)
    data = download_and_parse_iss_data(url)

    # Assuming the data contains the date we are looking for
    result = find_epoch_by_date(data, test_date)

    # Assert that the result is not None and the date matches
    assert result is not None
    assert 'EPOCH' in result and result['EPOCH'] == test_date

    # Check other fields
    assert 'X' in result and isinstance(result['X'], float)
    assert 'Y' in result and isinstance(result['Y'], float)
    assert 'Z' in result and isinstance(result['Z'], float)
    assert 'X_DOT' in result and isinstance(result['X_DOT'], float)
    assert 'Y_DOT' in result and isinstance(result['Y_DOT'], float)
    assert 'Z_DOT' in result and isinstance(result['Z_DOT'], float)

def test_find_epoch_by_date_not_found():
    """
    Tests the find_epoch_by_date function to ensure it returns None when no matching date is found.

    Args:
        None

    Returns:
        None
    """
    # Use a date that doesn't exist in the dataset
    test_date = datetime(2099, 1, 1, 0, 0, 0)

    data = download_and_parse_iss_data(url)

    result = find_epoch_by_date(data, test_date)

    # Assert that the result is None
    assert result is None

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_get_epochs_data(client):
    """
    Tests the /epochs route to ensure it returns the correct data.

    Args:
        client (FlaskClient): Flask test client.

    Returns:
        None
    """
    response = client.get('/epochs')
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_get_epochs_data_with_query(client):
    """
    Tests the /epochs route with query parameters to ensure it returns a modified list of epochs.

    Args:
        client (FlaskClient): Flask test client.

    Returns:
        None
    """
    limit = 5
    offset = 2
    response = client.get(f'/epochs?limit={limit}&offset={offset}')
    assert response.status_code == 200
    data = response.json

    # Assert that the returned data has the expected length
    assert isinstance(data, list)
    assert len(data) == limit

def test_get_specific_epoch_data(client):
    """
    Tests the /epochs/<epoch> route to ensure it returns data for a specific epoch.

    Args:
        client (FlaskClient): Flask test client.

    Returns:
        None
    """
    # Assuming test_date_str corresponds to a valid epoch in your dataset
    test_date_str = "2024-02-22T12:00:00.000Z"
    response = client.get(f'/epochs/{test_date_str}')
    assert response.status_code == 200
    assert 'EPOCH' in response.json

def test_get_specific_epoch_speed(client):
    """
    Tests the /epochs/<epoch>/speed route to ensure it returns the speed.

    Args:
        client (FlaskClient): Flask test client.

    Returns:
        None
    """
    test_date_str = "2024-02-22T12:00:00.000Z"
    response = client.get(f'/epochs/{test_date_str}/speed')
    assert response.status_code == 200
    assert 'speed' in response.json

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
    assert 'EPOCH' in response.json
    assert 'speed' in response.json