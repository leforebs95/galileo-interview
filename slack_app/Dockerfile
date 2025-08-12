# Use AWS Lambda Python runtime
FROM public.ecr.aws/lambda/python:3.13

# Copy application code
COPY pyproject.toml ./
COPY main.py ${LAMBDA_TASK_ROOT}/
COPY listeners/ ${LAMBDA_TASK_ROOT}/listeners/
COPY utils/ ${LAMBDA_TASK_ROOT}/utils/

RUN pip install --no-cache-dir -e . --target ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (main.lambda_handler)
CMD ["main.lambda_handler"]