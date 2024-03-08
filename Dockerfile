FROM ubuntu:20.04

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y python3 && \
    apt-get install -y python3-pip
    
RUN pip3 install pytest==8.0.0
RUN pip3 install requests
RUN pip3 install xmltodict
RUN pip3 install numpy
RUN pip3 install Flask

COPY iss_tracker.py \
     test_iss_tracker.py \
     run_app.sh \
     run_tests.sh \
     /code/

# Set execute permissions on the scripts
RUN chmod +x /code/run_app.sh \
             /code/run_tests.sh \
             /code/iss_tracker.py

ENV PATH="/code:$PATH"

# Expose the port the app runs on
EXPOSE 5000

# Set the default command to run the app
CMD ["run_app.sh"]