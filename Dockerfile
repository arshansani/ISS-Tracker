FROM python:3.10

WORKDIR /code

ENV PYTHONPATH=/code
ENV FLASK_APP=iss_tracker.py
ENV FLASK_ENV=development

# Install requirements first to leverage Docker cache
COPY requirements.txt /code/
RUN pip install -r requirements.txt

COPY . /code

# Expose the port the app runs on
EXPOSE 5000

# Set the default command to run the app
CMD ["flask", "run", "--host=0.0.0.0"]