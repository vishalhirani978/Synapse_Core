# Use a lightweight Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# (Optional) Install requests just in case we ever need it later
RUN pip install requests

# This container will just stay open or run the scripts we send it
CMD ["python"]