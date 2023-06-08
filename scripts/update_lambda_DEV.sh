#!/bin/bash

script_dir=$(dirname "$0")

# load .env file
source script_dir/../.env

# specify lambda function name
lambda_function_name="alpaca_orders_func_DEV"

# specify the variables you want to update in your lambda function
variables_to_update="API_KEY_PAPER SECRET_KEY_PAPER"

# start json string
json='Variables={'

# loop through variables and add to json string
for var in $variables_to_update
do
    json+="$var=\"${!var}\","
done

# remove trailing comma and close json string
json=${json::-1}
json+='}'

# update the lambda configuration
aws lambda update-function-configuration \
    --function-name $lambda_function_name \
    --environment "$json"