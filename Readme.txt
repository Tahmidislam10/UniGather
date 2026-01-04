UniGather – University Event Management Platform

Overview
UniGather is a cloud-native university event management platform designed to help students and staff discover, book, and manage campus events. Built with a Python Flask backend and a serverless AWS infrastructure, it provides a secure, scalable, and reliable environment for academic communities.

Group Members
Tahmid – Backend Lead and Database
Steven – Frontend Lead and Version Control Management
Younes – Cloud Integration Lead and CI/CD

Technology Stack

Backend
Python 3.12
Flask

Frontend
HTML5
CSS3
JavaScript (Vanilla)
Jinja2 Templates

Database
Amazon DynamoDB

Cloud and Infrastructure
AWS

* VPC
* ECS Fargate
* Application Load Balancer (ALB)
* S3
* ECR
* CloudWatch

Infrastructure as Code
Terraform

CI/CD
GitHub Actions

Prerequisites
Python 3.12 or later
AWS CLI configured with permissions to access DynamoDB
A local or cloud DynamoDB instance

Installation

Clone the repository
git clone <repository-url>
cd UniGather

Install required dependencies
pip install -r requirements.txt

Database Initialization
Before running the application, seed the DynamoDB tables with initial users:

python seed_users.py

Note:
This script creates a default system administrator account:
Email: [admin@university.ac.uk](mailto:admin@university.ac.uk)
Password: admin123

Running the Application

python app.py

The application will run locally at:
[http://localhost:5000](http://localhost:5000)


Languages Used

1. Python
2. HTML
3. CSS
4. JavaScript


Core Objectives Met From Proposal

Objective 1 – User Management
Secure registration restricted to academic email addresses (.ac.uk) with hashed password storage.

Objective 2 – Event Creation
Role-based event creation restricted to staff and administrators.

Objective 3 – Event Searching
Centralised retrieval and display of university events.

Objective 4 – Event Booking
Capacity-aware event booking with duplicate booking prevention.

Objective 5 – Reminders
User-specific reminders sorted by upcoming event date and time.


Additional Core Functionality met from proposal

Objective 5 – Traffic-Based Scaling
Automatic scaling of ECS tasks based on CPU utilisation.

Objective 6 – Application Load Balancer
All application traffic is routed through an Application Load Balancer.

Objective 7 – Downloadable Booking Confirmation
Booking confirmation PDFs generated server-side and downloadable by users.

Objective 8 – Waitlist
Automatic waitlist handling with promotion on cancellations.

Bonus Features Added
Analytics and graphs dashboard
Academic email validation
Password hash encryption
Role-based access control
Modular backend architecture using Flask Blueprints

Infrastructure (Terraform)
The infrastructure is defined using Infrastructure as Code, provisioning a highly available VPC with public and private subnets, an Application Load Balancer, and ECS Fargate clusters.

Terraform Commands

cd terraform

terraform init
terraform plan
terraform apply -var="image_tag=latest"

Docker and Deployment (ECR to ECS)

Local Docker Build

docker build -t unigather .
docker run -p 5000:5000 unigather

Push to Amazon ECR

aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.eu-west-2.amazonaws.com

docker tag unigather:latest <AWS_ACCOUNT_ID>.dkr.ecr.eu-west-2.amazonaws.com/g13-web-app:latest
docker push <AWS_ACCOUNT_ID>.dkr.ecr.eu-west-2.amazonaws.com/g13-web-app:latest

ECS Service
The ECS service g13-web-app-service runs the application on Fargate and is configured with Auto Scaling. The service scales between 1 and 4 tasks based on a 70 percent average CPU utilisation threshold.

CI/CD Pipeline
UniGather uses GitHub Actions for automated deployment. On every push to the main branch:

A new Docker image is built for linux/amd64.
The image is pushed to Amazon ECR.
The ECS task definition is updated with the new image tag.
The ECS service is redeployed automatically.
