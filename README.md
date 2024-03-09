# ISS Tracker API

## Overview
This project analyzes the International Space Station's (ISS) trajectory data. It includes scripts for downloading and parsing data, and exposes this functionality to the end user using Flask API's.

## Contents
- `Dockerfile`: Defines the Docker container setup.
- `README.md`: Information on how to use this API.
- `diagram.png`: Diagram illustrating the program architecture.
- `docker-compose.yml`: Automates the deployment of the docker container.
- `iss_tracker.py`: The main script for downloading, parsing, and analyzing the ISS trajectory data as well as running the Flask server.
- `requirements.txt`: Required python libraries to be installed to the container.
- `test/test_iss_tracker.py`: Unit tests for iss_tracker.py.

## Getting Started
### Prerequisites
- Docker installed on host machine
- Internet connection

### Data Source
- The ISS trajectory data is sourced from NASA's Public Data: [ISS OEM Data](https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.xml).
- This XML file contains detailed state vectors of the ISS over a given period.
- Dataset Citation: NASA. ISS OEM Data [Data file](https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.xml). Retrieved from https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.xml

### Running the Containerized App
- Navigate to the directory containing the Dockerfile & docker-compose.yml.
- Build and run the Docker image with the command: 
    - `docker-compose up`
    - This command builds the Docker image based on the Dockerfile and starts the container, running the Flask app inside it.

### Running the Containerized Unit Tests
- To run the unit tests within the Docker container, run the following command: 
    - `docker-compose run --rm app pytest -v /code/test/`

## API Examples & Result Interpretation
The iss_tracker application provides several API endpoints to access different sets of data related to the International Space Station (ISS). Below is a description of each endpoint and how to use them:
- `/comment` (Comments): 
    - **Description**: Retrieves the comments associated with the ISS data.
    - **Usage**: `GET /comment`
    - **Example Usage**: 
        - `curl 127.0.0.1:5000/comment`
    - **Output**: A list of comments providing additional information or metadata about the ISS data set. Useful for understanding the context and any specific notes related to the data.
- `/header` (Header): 
    - **Description**: Retrieves the header information for the ISS data set.
    - **Usage**: `GET /header`
    - **Example Usage**: 
        - `curl 127.0.0.1:5000/header`
    - **Output**: Header details such as the creation date and originator of the data set. The header provides high-level information about the source and generation of the ISS data.
- `/metadata` (Metadata): 
    - **Description**: Retrieves the metadata information for the ISS data set.
    - **Usage**: `GET /metadata`
    - **Example Usage**: 
        - `curl 127.0.0.1:5000/metadata`
    - **Output**: Metadata details such as the object name, object ID, center name, reference frame, time system, and start/stop times of the data set. Metadata provides essential information for interpreting and using the ISS data accurately.
- `/epochs` (Full Data Set): 
    - **Description**: Retrieves a complete set of state vectors for the ISS over all available epochs.
    - **Usage**: `GET /epochs`
    - **Example Usage**: 
        - `curl 127.0.0.1:5000/epochs`
    - **Output**: Each entry in the response includes time (EPOCH), position coordinates (X, Y, Z), and velocity components (X_DOT, Y_DOT, Z_DOT). Useful for analyzing the entire orbital path of the ISS.
- `/epochs` with Pagination
    - **Description**: Similar to /epochs, but supports pagination.
    - **Usage**: `GET /epochs?limit=<int>&offset=<int>`
        - **limit**: The number of records to return (integer).
        - **offset**: The starting position in the data set (integer).
    - **Example Usage**: 
        - `curl 127.0.0.1:5000/epochs?limit=10&offset=5`
    - **Output**: A subset of the data based on the specified limit and offset. Helpful when dealing with large data sets.
- `/epochs/<epoch>` (Specific Epoch Data)
    - **Description**: Retrieves state vectors for a specific epoch.
    - **Usage**: `GET /epochs/<yyyy-MM-ddTHH:mm:ss>`
        - Replace `<yyyy-MM-ddTHH:mm:ss>` with the desired date and time.
    - **Example Usage**: 
        - `curl 127.0.0.1:5000/epochs/2024-03-19T04:29:00`
    - **Output**: State vectors (position and velocity) for the specified epoch.
- `/epochs/<epoch>/speed` (Speed at a Specific Epoch)
    - **Description**: Provides the speed of the ISS at a specified epoch.
    - **Usage**: `GET /epochs/<yyyy-MM-ddTHH:mm:ss>/speed`
        - Replace `<yyyy-MM-ddTHH:mm:ss>` with the desired date and time.
    - **Example Usage**: 
        - `curl 127.0.0.1:5000/epochs/2024-03-19T04:29:00/speed`
    - **Output**: The instantaneous speed of the ISS at the specified epoch, calculated from velocity components.
- `/epochs/<epoch>/location` (Location at a Specific Epoch)
    - **Description**: Provides the location of the ISS at a specified epoch.
    - **Usage**: `GET /epochs/<yyyy-MM-ddTHH:mm:ss>/location`
        - Replace `<yyyy-MM-ddTHH:mm:ss>` with the desired date and time.
    - **Example Usage**: 
        - `curl 127.0.0.1:5000/epochs/2024-03-19T04:29:00/location`
    - **Output**: The instantaneous longitude, latitude, altitude, and geolocation of the ISS at the specified epoch, calculated from position coordinates.
- `/now` (Current Epoch Data)
    - **Description**: Provides the most recent state vectors and speed of the ISS.
    - **Usage**: `GET /now`
    - **Example Usage**: 
        - `curl 127.0.0.1:5000/now`
    - **Output**: Current or latest state vectors (position and velocity) of the ISS, along with its instantaneous speed. Essential for real-time monitoring.

## Software Architecture Diagram
- The software architecture diagram visualizes the Dockerized environment of the ISS Tracker Flask app. Within the Docker container, the Flask App is depicted with `iss_tracker.py` running within. The individual functions and routes are highlighted (denoted by bubbles) within `iss_tracker.py`. The diagram also illustrates the unit tests managed by pytest and the flow of data from the web as well as between the client and Flask App.
![Software Architecture Diagram](diagram.png)