FROM public.ecr.aws/lambda/python:3.12-arm64

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# Copy function code
COPY lambda_function.py ${LAMBDA_TASK_ROOT}

# Copy the model
COPY nih-pc-chex-mimic_ch-google-openi-kaggle-densenet121-d121-tw-lr001-rot45-tr15-sc15-seed0-best.pt /home/sbx_user1051/.torchxrayvision/models_data/
COPY nihpcrsnamimic_ch-resnet101-2-ae-test2-elastic-e250.pt /home/sbx_user1051/.torchxrayvision/models_data/

# For local dev
# COPY nih-pc-chex-mimic_ch-google-openi-kaggle-densenet121-d121-tw-lr001-rot45-tr15-sc15-seed0-best.pt /root/.torchxrayvision/models_data/
# COPY nihpcrsnamimic_ch-resnet101-2-ae-test2-elastic-e250.pt /root/.torchxrayvision/models_data/

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "lambda_function.handler" ]