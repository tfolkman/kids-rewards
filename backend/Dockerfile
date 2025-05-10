# Use an official AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.12-x86_64

# Set the working directory in the container
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy requirements.txt first to leverage Docker layer caching for dependencies
COPY requirements.txt ./

# Install Python dependencies using pip and requirements.txt
# The AWS Lambda base images for Python have pip pre-installed.
# This will install packages into the Python environment provided by the base image.
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
# This copies main.py, crud.py, etc., into ${LAMBDA_TASK_ROOT} (which is /var/task)
COPY . .

# Set the CMD to your handler in main.py
CMD [ "main.handler" ]