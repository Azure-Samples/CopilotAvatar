# Use the official Python image as the base image  
FROM python:3.9-slim  
  
# Set the working directory in the container  
WORKDIR /app  
  
# Copy the requirements file to the container  
COPY requirements.txt ./  
  
# Install the Python dependencies  
RUN pip install --no-cache-dir -r requirements.txt  
  
# Copy the application code to the container  
COPY . .  
  
# Set environment variables  
ENV FLASK_APP=app.py  
ENV FLASK_RUN_HOST=0.0.0.0  
ENV FLASK_RUN_PORT=5000  
ENV SPEECH_REGION=westeurope
ENV SPEECH_KEY=D1EAH4lipnhibjqQJYV1BHZQuQVM2pVT4SExzbouv0YXMh11HGvZJQQJ99BCAC5RqLJXJ3w3AAAYACOGXKuc  
ENV COPILOT_ENDPOINT=https://3da91219fae9e6bf878a89078d0db4.1c.environment.api.powerplatform.com/powervirtualagents/botsbyschema/cra66_dianne/directline/token?api-version=2022-03-01-preview 
  
# Expose the port Flask will run on  
EXPOSE 5000  
  
# Command to run the Flask app  
CMD ["flask", "run"]  