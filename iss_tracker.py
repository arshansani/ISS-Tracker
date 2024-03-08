#!/usr/bin/env python3
from flask import Flask, jsonify, request
import requests
import xmltodict
from datetime import datetime
import numpy as np
import logging

# Initialize Flask app
app = Flask(__name__)
url = "https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.xml"

# Configure logging
logging.basicConfig(level='WARNING', format='%(asctime)s - %(levelname)s - %(message)s')

def parse_date(date_str: str) -> datetime:
    """
    Parse the custom date format used in the ISS data.

    Args:
        date_str (str): Date string in the ISS data format.

    Returns:
        datetime: Parsed datetime object.
    """
    return datetime.strptime(date_str, '%Y-%jT%H:%M:%S.%fZ')

def download_and_parse_iss_data(url: str) -> list:
    """
    Download and parse the ISS data from the given URL into a list of dictionaries.

    Each element in the list is a dictionary representing a state vector of the ISS, 
    containing the epoch as a datetime object and the position and velocity vectors as floats.

    Args:
        url (str): URL to download the ISS data from.

    Returns:
        data (list of dict): List of dictionaries containing ISS data.
    """
    try:
        # Downloading the data from the URL
        response = requests.get(url)
        response.raise_for_status()
        data = xmltodict.parse(response.content)

        # Extracting data from each stateVector
        iss_data = []
        for state_vector in data['ndm']['oem']['body']['segment']['data']['stateVector']:
            iss_data.append({
                # Timestamp
                'EPOCH': parse_date(state_vector['EPOCH']),
                # Position vectors (in km)
                'X': float(state_vector['X']['#text']),
                'Y': float(state_vector['Y']['#text']),
                'Z': float(state_vector['Z']['#text']),
                # Velocity vectors (in km/s)
                'X_DOT': float(state_vector['X_DOT']['#text']),
                'Y_DOT': float(state_vector['Y_DOT']['#text']),
                'Z_DOT': float(state_vector['Z_DOT']['#text'])
            })
    except requests.RequestException as e:
        logging.error(f"Error fetching data from URL: {e}")
        raise
    except Exception as e:
        logging.error(f"Error parsing data: {e}")
        raise
    return iss_data

def calculate_speed(x_dot: float, y_dot: float, z_dot: float) -> float:
    """
    Calculate the speed of the ISS based on its velocity vectors.

    Args:
        x_dot (float): X component of the ISS's velocity in km/s.
        y_dot (float): Y component of the ISS's velocity in km/s.
        z_dot (float): Z component of the ISS's velocity in km/s.

    Returns:
        float: The speed of the ISS in km/s.
    """
    return np.sqrt(x_dot**2 + y_dot**2 + z_dot**2)

def find_epoch_by_date(iss_data, epoch_date):
    """
    Searches for and returns the epoch data for a specific date within the data set.

    Args:
        iss_data (list of dict): Each element in the list is a dictionary representing a state vector of the ISS, 
                                 containing the epoch as a datetime object and the position and velocity vectors as floats.
        epoch_date (datetime): The specific date and time to find in the ISS data set.

    Returns:
        dict: The state vector that matches the given `epoch_date`. 
              Returns `None` if no matching epoch is found.
    """
    for epoch in iss_data:
        if epoch['EPOCH'] == epoch_date:
            return epoch
    return None

# Flask routes
@app.route('/epochs', methods=['GET'])
def get_epochs_data():
    try:
        limit = request.args.get('limit', default=None, type=int)
        offset = request.args.get('offset', default=0, type=int)

        iss_data = download_and_parse_iss_data(url)

        # Modify returned data based on limit and offset
        if limit is not None:
            iss_data = iss_data[offset:offset + limit]
        return jsonify(iss_data)

    except Exception as e:
        logging.error(f"Error in get_epochs_data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/epochs/<epoch>', methods=['GET'])
def get_specific_epoch_data(epoch):
    try:
        iss_data = download_and_parse_iss_data(url)
        epoch_date = datetime.strptime(epoch, '%Y-%m-%dT%H:%M:%S.%fZ')
        epoch_data = find_epoch_by_date(iss_data, epoch_date)
        return jsonify(epoch_data) if epoch_data else (jsonify({"error": "Epoch not found"}), 404)

    except Exception as e:
        logging.error(f"Error in get_specific_epoch_data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/epochs/<epoch>/speed', methods=['GET'])
def get_specific_epoch_speed(epoch):
    try:
        iss_data = download_and_parse_iss_data(url)
        epoch_date = datetime.strptime(epoch, '%Y-%m-%dT%H:%M:%S.%fZ')
        epoch_data = find_epoch_by_date(iss_data, epoch_date)

        if epoch_data:
            speed = calculate_speed(epoch_data['X_DOT'], epoch_data['Y_DOT'], epoch_data['Z_DOT'])
            return jsonify({"speed": speed})
        else:
            return "Epoch not found", 404

    except Exception as e:
        logging.error(f"Error in get_specific_epoch_speed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/now', methods=['GET'])
def get_current_epoch_data():
    try:
        iss_data = download_and_parse_iss_data(url)
        now = datetime.utcnow()
        closest_epoch = min(iss_data, key=lambda x: abs(x['EPOCH'] - now))
        closest_speed = calculate_speed(closest_epoch['X_DOT'], closest_epoch['Y_DOT'], closest_epoch['Z_DOT'])
        
        closest_epoch['speed'] = closest_speed
        return jsonify(closest_epoch)

    except Exception as e:
        logging.error(f"Error in get_current_epoch_data: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)