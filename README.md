# alpaca-trading

## Description

Used to make trades on [Alpaca](https://alpaca.markets/) based on supplied configurations.

This code is meant to be hosted on an AWS Lambda instance and called by AWS EventBridge Scheduler. Scheduled to execute every Friday. Logs are published every run and will alert on any errors that occur during the execution.

## Workflow

![](./images/workflow.jpg)

## Configuration

```json
{
  "tickers": ["VONG", "SCHD", "SCHG", "SPGP", "RSP"],
  "limit": 50,
  "displace": 5,
  "timeout": 10,
  "logging": "INFO",
  "paper": true,
  "prior_trades": true
}
```

limit: Total amount that will be invested  
displace: Day of the month that money is transfered  
timeout: How long to wait to check status

## Codeflow

![](./images/codeflow.jpg)

## Recreating

1. Clone this repo
2. Create AWS account
3. Add AWS keys into Github secret keeper
4. Create [AWS Lambda](https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions)

   - Add keys into configuration
   - Add layers (python libraries)
   - Verify lambda_function name and handler

5. Create metric [AWS CloudWatch Metric](https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricsV2:)

   - Track every occurance of "ERROR"

6. Create an [AWS CloudWatch Alarm](https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#alarmsV2:?)

   - Calculate on sum over 0
   - Set missing data as good
   - Set notifications to email

7. Create an [AWS EventBridge Scheduler](https://us-east-1.console.aws.amazon.com/scheduler/home?region=us-east-1#schedules)

   - Input target payload from event.json

8. Verify execution on [Alpaca](https://alpaca.markets/)
