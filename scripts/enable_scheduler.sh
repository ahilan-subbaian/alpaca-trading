#!/bin/bash

# this script will set the state of an aws schedule to disabled

schedule_name=$1

# get the json config of the schedule
schedule_json=$(aws scheduler get-schedule --name $schedule_name)

# delete the arn, creation date and last modification date from the json config
schedule_json=$(echo $schedule_json | jq 'del(.Arn, .CreationDate, .LastModificationDate)')
echo schedule_arn: $schedule_json

# pulls the flexible time window from schedule json
flexible_time_window=$(echo $schedule_json | jq '.FlexibleTimeWindow')
echo flexible_time_window: $flexible_time_window

# pulls the schedule expression from schedule json
schedule_expression=$(echo $schedule_json | jq -r '.ScheduleExpression')
echo schedule_expression: $schedule_expression

# pulls the target from schedule json
target=$(echo $schedule_json | jq -r '.Target')
echo target: $target

# passes the schedule json and the state of disabled to update-schedule and other variables into update-schedule
aws scheduler update-schedule --name $schedule_name --cli-input-json "$schedule_json" --state ENABLED --flexible-time-window "$flexible_time_window" --schedule-expression "$schedule_expression" --target "$target"
