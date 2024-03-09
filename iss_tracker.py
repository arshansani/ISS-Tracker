# !/usr/bin/env python3
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import requests
import xmltodict
from datetime import datetime, timedelta
import numpy as np
import logging
import math
from geopy.geocoders import Nominatim

# Configure logging
logging.basicConfig(level='WARNING', format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Flask app and database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///iss_data.db'
db = SQLAlchemy(app)

# Constants
URL = "https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.xml"
MEAN_EARTH_RADIUS = 6371  # Earth's radius in km

class ISSData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.JSON, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

def parse_date(date_str: str) -> datetime:
    """
    Parse the custom date format used in the ISS data.

    Args:
        date_str (str): Date string in the ISS data format.

    Returns:
        datetime: Parsed datetime object.
    """
    return datetime.strptime(date_str, '%Y-%jT%H:%M:%S.%fZ')

def download_and_parse_iss_data(URL: str) -> dict:
    """
    Download and parse the ISS data from the given URL into a dictionaries.

    Args:
        URL (str): URL to download the ISS data from.

    Returns:
        iss_data (dict): A dictionary containing ISS data including header, metadata, state vectors, and comments.
    """
    try:
        # Downloading the data from the URL
        response = requests.get(URL)
        response.raise_for_status()
        data = xmltodict.parse(response.content)

        # Extracting the header and metadata
        iss_data = {
            'header': data['ndm']['oem']['header'],
            'metadata': data['ndm']['oem']['body']['segment']['metadata'],
            'state_vectors': [],
            'comments': []
        }

        # Separating segment data
        segment_data = data['ndm']['oem']['body']['segment']['data']

        # Extracting comments
        if 'COMMENT' in segment_data:
            comments = [comment for comment in segment_data['COMMENT'] if comment is not None and isinstance(comment, str)]
            iss_data['comments'] = comments
        else:
            logging.warning("No 'COMMENT' key found in segment_data")

        # Extracting data from each stateVector
        for state_vector in segment_data['stateVector']:
            iss_data['state_vectors'].append({
                # Timestamp
                'EPOCH': parse_date(state_vector['EPOCH']).isoformat(),
                # Position vectors (in km)
                'X': float(state_vector['X']['#text']),
                'Y': float(state_vector['Y']['#text']),
                'Z': float(state_vector['Z']['#text']),
                # Velocity vectors (in km/s)
                'X_DOT': float(state_vector['X_DOT']['#text']),
                'Y_DOT': float(state_vector['Y_DOT']['#text']),
                'Z_DOT': float(state_vector['Z_DOT']['#text'])
            })
        return iss_data

    except requests.RequestException as e:
        logging.error(f"Error fetching data from URL: {e}")
        raise
    except Exception as e:
        logging.error(f"Error parsing data: {e}")
        raise
    
def fetch_iss_data() -> dict:
    """
    Fetch the latest ISS data, either from the cache or by downloading it.

    Args:
        None

    Returns:
        dict: The ISS data.
    """
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    cached_data = ISSData.query.filter(ISSData.timestamp > one_hour_ago).first()
    
    # Debugging: Force fetching new data
    #cached_data = False

    if cached_data:
        logging.info("Using cached ISS data")
        return cached_data.data
    else:
        logging.info("Fetching new ISS data")
        iss_data = download_and_parse_iss_data(URL)
        new_data = ISSData(data=iss_data)
        db.session.add(new_data)
        db.session.commit()
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

def find_epoch_by_date(state_vectors: list, epoch_date: datetime) -> dict:
    """
    Searches for and return the epoch data for a specific date within the data set.

    Args:
        state_vectors (list of dict): List of state vectors from the ISS data.
        epoch_date (datetime): The specific date and time to find in the ISS data set.

    Returns:
        dict: The state vector that matches the given `epoch_date`. Returns `None` if not found.
    """
    for vector in state_vectors:
        if vector['EPOCH'] == epoch_date:
            return vector
    return None

def calculate_location(epoch_data: dict) -> tuple:
    """
    Calculate the latitude, longitude, and altitude of an object in Earth orbit from its Cartesian coordinates.

    Args:
        epoch_data (dict): Dictionary containing 'X', 'Y', and 'Z' keys with the object's coordinates.

    Returns:
        tuple: A tuple of (latitude, longitude, altitude).
    """
    x, y, z = epoch_data['X'], epoch_data['Y'], epoch_data['Z']
    
    epoch_time = datetime.fromisoformat(epoch_data['EPOCH'])
    hrs = epoch_time.hour
    mins = epoch_time.minute
    logging.debug(f"Epoch time: {epoch_time}, Hrs: {hrs}, Mins: {mins}")

    lat = math.degrees(math.atan2(z, math.sqrt(x**2 + y**2))) 
    lon = math.degrees(math.atan2(y, x)) - ((hrs-12)+(mins/60))*(360/24) + 19

    lon = (lon + 180) % 360 - 180

    alt = np.sqrt(x**2 + y**2 + z**2) - MEAN_EARTH_RADIUS
    return lat, lon, alt

def get_geoposition(lat: float, lon: float) -> str:
    """
    Retrieve the geolocation information for given latitude and longitude coordinates.

    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.

    Returns:
        str: The address of the location if available; otherwise, returns 'No location data'.
    """
    try:
        geolocator = Nominatim(user_agent="iss_tracker")
        location = geolocator.reverse(f"{lat}, {lon}")
        
        if location is None:
            return "No location data"
        else:
            return location.address
    except Exception as e:
        logging.error(f"Error in get_geoposition: {e}")
        raise Exception("Error retrieving address")

# Flask routes
@app.route('/comment', methods=['GET'])
def get_comment():
    try:
        iss_data = fetch_iss_data()
        comments = iss_data['comments']
        return jsonify(comments)
    except KeyError:
        logging.error(f"Error accessing comments: {e}")
        return jsonify([])
    except Exception as e:
        logging.error(f"Error in get_comment: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/header', methods=['GET'])
def get_header():
    try:
        iss_data = fetch_iss_data()
        header = iss_data['header']
        return jsonify(header)
    except KeyError as e:
        logging.error(f"Error accessing header data: {e}")
        return jsonify({}), 404
    except Exception as e:
        logging.error(f"Error in get_header: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/metadata', methods=['GET'])
def get_metadata():
    try:
        iss_data = fetch_iss_data()
        metadata = iss_data['metadata']
        return jsonify(metadata)
    except KeyError as e:
        logging.error(f"Error accessing metadata: {e}")
        return jsonify({}), 404
    except Exception as e:
        logging.error(f"Error in get_metadata: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/epochs', methods=['GET'])
def get_epochs_data():
    try:
        def parse_int(param_name, default=None, allow_negative=False, must_be_positive=False):
            param_value = request.args.get(param_name, default=default, type=str)
            logging.debug(f"{param_name}: {param_value}")
            if param_value is None:
                return default
            else:
                try:
                    logging.debug(f"{param_name}: {param_value}")
                    # Check for floating point numbers
                    if '.' in param_value:
                        raise ValueError(f"{param_name} must be an integer")
                    # Check for non-numeric strings and convert to int
                    try:
                        param_value = int(param_value)
                    except ValueError:
                        raise ValueError(f"{param_name} must be a number")
                    # Check for negative and positive numbers
                    if not allow_negative and param_value < 0:
                        raise ValueError(f"{param_name} must be non-negative")
                    if must_be_positive and param_value <= 0:
                        raise ValueError(f"{param_name} must be positive")
                except ValueError as e:
                    raise ValueError(f"Invalid value for {param_name}: {param_value}", f"{e}")
                
                return param_value

        # Parse limit and offset with error handling
        limit = parse_int('limit', default=None, must_be_positive=True)
        offset = parse_int('offset', default='0', allow_negative=False)
        
        # Debugging
        #logging.debug(f"Limit: {limit}, Offset: {offset}")

        # Fetch the ISS data
        iss_data = fetch_iss_data()
        if iss_data is None:
            raise Exception("No data available")

        dataset = iss_data['state_vectors']

        if offset >= len(dataset):
            raise ValueError("Offset exceeds the size of the dataset")

        # Modify returned data based on limit and offset
        if limit is not None:
            dataset = dataset[offset:offset + limit]
        return jsonify(dataset)
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logging.error(f"Error in get_epochs_data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/epochs/<epoch>', methods=['GET'])
def get_specific_epoch_data(epoch):
    try:
        # Check if the date is in the correct format
        try:
            epoch_date = datetime.fromisoformat(epoch)
        except ValueError:
            raise ValueError("Invalid date format. Please use the ISO format: YYYY-MM-DDTHH:MM:SS")

        iss_data = fetch_iss_data()

        epoch_data = find_epoch_by_date(iss_data['state_vectors'], epoch)
        if epoch_data:
            return jsonify(epoch_data)
        else:
            return jsonify({"error": "Epoch not found"}), 404

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logging.error(f"Error in get_specific_epoch_data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/epochs/<epoch>/speed', methods=['GET'])
def get_specific_epoch_speed(epoch):
    try:
        # Check if the date is in the correct format
        try:
            epoch_date = datetime.fromisoformat(epoch)
        except ValueError:
            raise ValueError("Invalid date format. Please use the ISO format: YYYY-MM-DDTHH:MM:SS")

        iss_data = fetch_iss_data()

        epoch_data = find_epoch_by_date(iss_data['state_vectors'], epoch)
        if epoch_data:
            speed = calculate_speed(epoch_data['X_DOT'], epoch_data['Y_DOT'], epoch_data['Z_DOT'])
            return jsonify({"SPEED": speed})
            
        else:
            return jsonify({"error": "Epoch not found"}), 404

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logging.error(f"Error in get_specific_epoch_speed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/epochs/<epoch>/location', methods=['GET'])
def get_specific_epoch_location(epoch):
    try:
        # Check if the date is in the correct format
        try:
            epoch_date = datetime.fromisoformat(epoch)
        except ValueError:
            raise ValueError("Invalid date format. Please use the ISO format: YYYY-MM-DDTHH:MM:SS")

        iss_data = fetch_iss_data()

        epoch_data = find_epoch_by_date(iss_data['state_vectors'], epoch)
        if epoch_data:
            lat, lon, alt = calculate_location(epoch_data)
            geoposition = get_geoposition(lat, lon)

            location_data = {
                "LATITUDE": lat,
                "LONGITUDE": lon,
                "ALTITUDE": alt,
                "GEOPOSITION": geoposition
            }
            return jsonify(location_data)
        else:
            return jsonify({"error": "Epoch not found"}), 404
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logging.error(f"Error in get_specific_epoch_speed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/now', methods=['GET'])
def get_current_epoch_data():
    try:
        iss_data = fetch_iss_data()
        state_vectors = iss_data['state_vectors']

        now = datetime.utcnow()
        closest_epoch = min(state_vectors, key=lambda x: abs(datetime.fromisoformat(x['EPOCH']) - now))

        epoch_data = {
            'EPOCH': closest_epoch['EPOCH'],
            'X': closest_epoch['X'],
            'Y': closest_epoch['Y'],
            'Z': closest_epoch['Z'],
            'X_DOT': closest_epoch['X_DOT'],
            'Y_DOT': closest_epoch['Y_DOT'],
            'Z_DOT': closest_epoch['Z_DOT']
        }

        speed = calculate_speed(epoch_data['X_DOT'], epoch_data['Y_DOT'], epoch_data['Z_DOT'])
        epoch_data['SPEED'] = speed
        lat, lon, alt = calculate_location(epoch_data)
        geoposition = get_geoposition(lat, lon)
        epoch_data['LATITUDE'] = lat
        epoch_data['LONGITUDE'] = lon
        epoch_data['ALTITUDE'] = alt
        epoch_data['GEOPOSITION'] = geoposition

        return jsonify(epoch_data)

    except Exception as e:
        logging.error(f"Error in get_current_epoch_data: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)