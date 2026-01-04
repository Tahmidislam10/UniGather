<h1>UniGather – University Event Management Platform</h1>

<p>GitHub Link to project - <a href="https://github.com/Tahmidislam10/UniGather">https://github.com/Tahmidislam10/UniGather</a></p>

<h2>Overview</h2>
<p>UniGather is a cloud-native university event management platform designed to help students and staff discover, book, and manage campus events. Built with a Python Flask backend and a serverless AWS infrastructure, it provides a secure, scalable, and reliable environment for academic communities.</p>

<h3>Group Members</h3>
<ul>
    <li>Tahmid – Backend Lead and Database</li>
    <li>Steven – Frontend Lead and Version Control Management</li>
    <li>Younes – Cloud Integration Lead and CI/CD</li>
</ul>

<h2>Technology Stack</h2>

<h3>Backend</h3>
<ul>
    <li>Python 3.12</li>
    <li>Flask</li>
</ul>

<h3>Frontend</h3>
<ul>
    <li>HTML5</li>
    <li>CSS3</li>
    <li>JavaScript (Vanilla)</li>
    <li>Jinja2 Templates</li>
</ul>

<h3>Database</h3>
<ul>
    <li>Amazon DynamoDB</li>
</ul>

<h3>Cloud and Infrastructure</h3>
<ul>
    <li>AWS
        <ul>
            <li>VPC</li>
            <li>ECS Fargate</li>
            <li>Application Load Balancer (ALB)</li>
            <li>S3</li>
            <li>ECR</li>
            <li>CloudWatch</li>
        </ul>
    </li>
</ul>

<h3>Infrastructure as Code</h3>
<ul>
    <li>Terraform</li>
</ul>

<h3>CI/CD</h3>
<ul>
    <li>GitHub Actions</li>
</ul>

<h2>Prerequisites</h2>
<ul>
    <li>Python 3.12 or later</li>
    <li>AWS CLI configured with permissions to access DynamoDB</li>
    <li>A local or cloud DynamoDB instance</li>
</ul>

<h2>Installation</h2>

<h3>Clone the repository</h3>
<pre><code>git clone &lt;repository-url&gt;
cd UniGather</code></pre>

<h3>Create Python Virtual Environment</h3>
<pre><code>.venv\Scripts\activate</code></pre>

<h3>Install required dependencies</h3>
<pre><code>pip install -r requirements.txt</code></pre>

<h2>Running the Application</h2>
<pre><code>python app.py</code></pre>

<p>The application will run locally at:<br>
<a href="http://localhost:5000">http://localhost:5000</a></p>

<h2>Languages Used</h2>
<ol>
    <li>Python</li>
    <li>HTML</li>
    <li>CSS</li>
    <li>JavaScript</li>
</ol>

<h2>Core Objectives Met From Proposal</h2>
<ul>
    <li><b>Objective 1 – User Management</b><br>Secure registration restricted to academic email addresses (.ac.uk) with hashed password storage.</li>
    <li><b>Objective 2 – Event Creation</b><br>Role-based event creation restricted to staff and administrators.</li>
    <li><b>Objective 3 – Event Searching</b><br>Centralised retrieval and display of university events.</li>
    <li><b>Objective 4 – Event Booking</b><br>Capacity-aware event booking with duplicate booking prevention.</li>
    <li><b>Objective 5 – Reminders</b><br>User-specific reminders sorted by upcoming event date and time.</li>
</ul>

<h2>Additional Core Functionality met from proposal</h2>
<ul>
    <li><b>Objective 5 – Traffic-Based Scaling</b><br>Automatic scaling of ECS tasks based on CPU utilisation.</li>
    <li><b>Objective 6 – Application Load Balancer</b><br>All application traffic is routed through an Application Load Balancer.</li>
    <li><b>Objective 7 – Downloadable Booking Confirmation</b><br>Booking confirmation PDFs generated server-side and downloadable by users.</li>
    <li><b>Objective 8 – Waitlist</b><br>Automatic waitlist handling with promotion on cancellations.</li>
</ul>

<h2>Bonus Features Added</h2>
<ul>
    <li>Analytics and graphs dashboard</li>
    <li>Academic email validation</li>
    <li>Password hash encryption</li>
    <li>Role-based access control</li>
    <li>Modular backend architecture using Flask Blueprints</li>
</ul>

<h2>Infrastructure (Terraform)</h2>
<p>The infrastructure is defined using Infrastructure as Code, provisioning a highly available VPC with public and private subnets, an Application Load Balancer, and ECS Fargate clusters.</p>

<h3>Terraform Commands</h3>
<pre><code>cd terraform

terraform init
terraform plan
terraform apply -var="image_tag=latest"</code></pre>

<h2>Docker and Deployment (ECR to ECS)</h2>

<h3>Local Docker Build</h3>
<pre><code>docker build -t unigather .
docker run -p 5000:5000 unigather</code></pre>

<h3>Push to Amazon ECR</h3>
<pre><code>aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin &lt;AWS_ACCOUNT_ID&gt;.dkr.ecr.eu-west-2.amazonaws.com

docker tag unigather:latest &lt;AWS_ACCOUNT_ID&gt;.dkr.ecr.eu-west-2.amazonaws.com/g13-web-app:latest
docker push &lt;AWS_ACCOUNT_ID&gt;.dkr.ecr.eu-west-2.amazonaws.com/g13-web-app:latest</code></pre>

<h3>ECS Service</h3>
<p>The ECS service g13-web-app-service runs the application on Fargate and is configured with Auto Scaling. The service scales between 1 and 4 tasks based on a 70 percent average CPU utilisation threshold.</p>

<h2>CI/CD Pipeline</h2>
<p>UniGather uses GitHub Actions for automated deployment. On every push to the main branch:</p>
<ul>
    <li>A new Docker image is built for linux/amd64.</li>
    <li>The image is pushed to Amazon ECR.</li>
    <li>The ECS task definition is updated with the new image tag.</li>
    <li>The ECS service is redeployed automatically.</li>
</ul>
