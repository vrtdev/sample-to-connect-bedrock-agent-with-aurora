
## Connect Bedrock Agent with Aurora PostgreSQL using RDS Data API !

This solution combines Bedrock Agent's AI capabilities with Aurora PostgreSQL's robust database functionality through the RDS Data API. Bedrock Agent, powered by large language models, interprets natural language queries and generates appropriate SQL statements. These queries are then executed against Aurora PostgreSQL using the RDS Data API, which provides a serverless, connection-free method for database interactions. This integration allows for dynamic data retrieval and analysis without managing direct database connections. For instance, a user request to "show sales data for the last quarter" is transformed into SQL, executed via the Data API, and results are presented in a user-friendly format. 

>While the solution can technically support write operations, allowing AI-generated queries to modify your database presents significant risks to data integrity and security, therefore production implementations should restrict access to write operations through appropriate IAM policies and database role permissions. 

>From a security and data integrity perspective, we **strongly** recommend implementing this solution exclusively for **read-only** workloads such as analytics, reporting, and data exploration. 

The solution is represented in the following architecture diagram: 

![Architecture](./images/architecture.png)

The high-level steps in this architecture are:

1.	The generative AI application invokes the Amazon Bedrock agent with natural language input data to orchestrate the integration with the backend relational database.
2.	The agent invokes the FM on Amazon Bedrock for pre-processing the prompt to determine the actions to be taken. 
3.	The agent then decides to use the generate-query action group. 
4.	The agent invokes /generate API implemented by the AWS Lambda function.
5.	The Lambda function uses the schema artifacts as context to augment the prompt.
6.	The Lambda function then invokes an LLM on Amazon Bedrock to generate the SQL query.
7.	Post generating the SQL query, the agent then decides to use the execute-query action group. 
8.	The agent invokes the /execute API implemented by the Lambda function, passing the generated SQL query 
9.	The Lambda function uses RDS Data API with a read-only role to run the SQL query against the Aurora PostgreSQL database.
10.	The agent finally returns the query results to the generative AI application.


### Use cases
- Read only workloads like analytics, reporting & data exploration.
- Environments with continuously changing query requirements.
- Database schemas that undergo frequent changes in columns and data types. 

### Prerequisites

- An AWS account with AWS Identity and Access Management (IAM) permissions to create an Aurora PostgreSQL database.
- Python installed with the Boto3 library.
- An IDE like Visual Studio Code. 

### Step 1: Setup your development environment

Ensure you have Node.js installed (v10.13.0 or later)

Install AWS CDK
```
npm install -g aws-cdk
```

Configure AWS CLI with your credentials: 
```
aws configure
```

To manually create a virtualenv on MacOS and Linux:

```
python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
source .venv/bin/activate
```

Once the virtualenv is activated, you can install the required dependencies.

```
pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
cdk synth
```

You can list all the stacks

```
cdk ls
```


### Step 2 : Deploy Aurora PostgreSQL cluster

Using CDK you can deploy an Aurora PostgreSQL cluster using the command:

```
cdk deploy RDSAuroraStack

```
Make a note of the Aurora resources like the CLUSTER_ARN, ADMIN_SECRET_ARN, READONLY_SECRET_ARN, DB_NAME. 

### Step 3 : Deploy the BedrockAgent Stack

Now you can deploy the Amazon Bedrock Agent using the command:

```
cdk deploy BedrockAgentStack
```
Make a note of the Bedrock AgentId. 

### Step 4: Review the provisioned Amazon Bedrock Agent

Navigate to the Amazon Bedrock Agent console and review the following configurations : 

- The agent named query-agent is configured to use Anthrophic Claude LLMs.
- Review the Instructions for the agent as this describes what the Agent will perform.
- The next to review will be the two Action groups named generate-query and execute-query.
- The generate-query Action Group invocation is configured to invoke the /generate API implemented by a Lambda function. 
- The execute-query Action Group invocation is configured to invoke the /execute API implemented by a Lambda function.
- Review the query-protection-guardrail that has been configured with denied topics and word filters to prevent prompts that attempt to modify the data. 

#### Bedrock Agent Configurations
![Bedrock Agent configurations](./images/query_agent.png)

#### Bedrock Guardrail Configuration
![Bedrock Guardrail configuration](./images/guardrail.png)

### Step 5 : Test the Bedrock Agent

You need to create a sample schema with data using scripts/create_schema.py before you can proceed with the testing. This will create bunch of schemas, tables and ingest sample data. The test is very straight forward where you send a natural language prompt as input to the Bedrock Agent which then has to generate the necessary SQL query and execute the query against the configured Aurora PostgreSQL database using RDS Data APIs. The Bedrock Agent should then return you a response that is based on the results queried from the Aurora PostgreSQL database using RDS data API.

**Note** : Be sure to update the script with the CLUSTER_ARN, ADMIN_SECRET_ARN, DB_NAME noted in step 2. 

```
python3 scripts/create_schema.py
```

There are couple of ways you can test with the deployed Bedrock Agent named:  generative-agent

#### a. Using the Test console of Amazon Bedrock Agent 

Navigate to Amazon Bedrock Agent console and you can input a prompt from the Test console. 

![Test Bedrock Agent](./images/test_bedrock_agent.png)

To review all the steps of the agent you can expand the Test console and review the Trace section to understand the query that was generated. 

![Review Agent Traces](./images/review_agent_traces.png)


#### b. Using the Amazon Bedrock InvokeAgent API SDK. 


### Step 6 : Cleanup 

Cleanup all the resources provisioned using the following command:

```
cdk destroy --all
```


To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!