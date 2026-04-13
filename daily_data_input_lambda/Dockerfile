FROM amazon/aws-lambda-python:3.9
RUN pip install boto3
COPY . ./
CMD [ "daily_data_input_lambda.lambda_handler" ]
