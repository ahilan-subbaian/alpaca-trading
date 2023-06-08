#!/bin/bash

# this script will set the state of an aws schedule to disabled

script_dir=$(dirname "$0")
schedule_name=$1

# get the json config of the schedule
schedule_json=$(aws scheduler get-schedule --name $schedule_name)
echo schedule_json: $schedule_json

# pulls the flexible time window from schedule json
flexible_time_window=$(echo $schedule_json | jq '.FlexibleTimeWindow')
echo flexible_time_window: $flexible_time_window

# delete the arn, creation date and last modification date from the json config
schedule_json=$(echo $schedule_json | jq 'del(.Arn, .CreationDate, .LastModificationDate)')
echo schedule_arn: $schedule_json

# Use the script directory to build the path to the config file
config_file="$script_dir/../configs/$schedule_name.json"

# get the config of the schedule
config=$(cat "$config_file" | tr '*' 'X')
echo config: $config

# pull input from config
input=$(echo $config | jq -r '.Input')
echo input: $input

# pulls the schedule expression from schedule json
schedule_expression=$(echo $config | jq -r '.ScheduleExpression'| tr 'X' '*')
echo schedule_expression: $schedule_expression

# pulls the target from schedule json and sets the input
target=$(echo $schedule_json | jq -r '.Target' | jq --arg input "$input" '.Input = $input')
echo target: $target


# passes the schedule json and the state of disabled to update-schedule and other variables into update-schedule
aws scheduler update-schedule --name $schedule_name --cli-input-json "$schedule_json" --flexible-time-window "$flexible_time_window" --schedule-expression "$schedule_expression" --target "$target"
