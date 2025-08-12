# Simple Dockerfile - just use pip with requirements
FROM public.ecr.aws/lambda/python:3.13

# Copy source files
COPY pyproject.toml ./
COPY agent/ ${LAMBDA_TASK_ROOT}/agent/
COPY utils/ ${LAMBDA_TASK_ROOT}/utils/
COPY main.py ${LAMBDA_TASK_ROOT}/
COPY config.py ${LAMBDA_TASK_ROOT}/config.py

# Install dependencies directly with pip (simpler than uv for Lambda)
RUN pip install --no-cache-dir -e . --target ${LAMBDA_TASK_ROOT}

# Set AWS Lambda handler
CMD ["main.lambda_handler"]