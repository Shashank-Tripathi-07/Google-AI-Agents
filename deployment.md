# Deployment Guide
## Deploy Your Agent System to the Cloud (5 Bonus Points)

This guide shows how to deploy the Intelligent Customer Support Triage System to production environments.

---

## Table of Contents

1. [Google Cloud Agent Engine](#google-cloud-agent-engine) (Recommended)
2. [Google Cloud Run](#google-cloud-run)
3. [AWS Lambda](#aws-lambda)
4. [Docker Container](#docker-container)
5. [Heroku](#heroku)

---

## Google Cloud Agent Engine

**Best for:** AI agent applications  
**Difficulty:** Easy  
**Cost:** Pay per use  
**Bonus Points:** ✅ Yes (5 points)

### Prerequisites

```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### Deployment Steps

#### 1. Prepare Application

Create `agent_config.yaml`:

```yaml
name: support-triage-agent
runtime: python39
entrypoint: python support_triage_system.py

env_variables:
  GEMINI_API_KEY: "your-key-here"  # Or use Secret Manager

resources:
  memory: 512Mi
  cpu: 1

scaling:
  min_instances: 0
  max_instances: 10
```

#### 2. Create Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy application files
COPY support_triage_system.py .
COPY gemini_integration.py .
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run application
CMD ["python", "support_triage_system.py"]
```

#### 3. Deploy to Agent Engine

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/support-triage
gcloud run deploy support-triage \
  --image gcr.io/YOUR_PROJECT_ID/support-triage \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi
```

#### 4. Verify Deployment

```bash
# Get service URL
gcloud run services describe support-triage \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)'

# Test endpoint
curl https://your-service-url.run.app
```

### Add to Writeup

```markdown
**Deployment:** Deployed to Google Cloud Agent Engine

**Endpoint:** https://support-triage-xyz.run.app

**Configuration:**
- Runtime: Python 3.9
- Memory: 512Mi
- Scaling: 0-10 instances
- Region: us-central1

**Deployment Command:**
```bash
gcloud run deploy support-triage \
  --image gcr.io/PROJECT_ID/support-triage \
  --platform managed
```

**Evidence:** See `deployment_screenshot.png` and logs at
`gcloud run services logs read support-triage`
```

---

## Google Cloud Run

**Best for:** Containerized applications  
**Difficulty:** Easy  
**Cost:** Free tier available  
**Bonus Points:** ✅ Yes (5 points)

### Quick Deploy

#### 1. Create Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir google-generativeai

EXPOSE 8080

CMD ["python", "support_triage_system.py"]
```

#### 2. Build and Deploy

```bash
# Build container
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/support-triage

# Deploy to Cloud Run
gcloud run deploy support-triage \
  --image gcr.io/YOUR_PROJECT_ID/support-triage \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### 3. Add Web Interface (Optional)

Create `api.py`:

```python
from flask import Flask, request, jsonify
from support_triage_system import SupportTriageSystem, Ticket
import os

app = Flask(__name__)
system = SupportTriageSystem()

@app.route('/')
def home():
    return '''
    <h1>Customer Support Triage API</h1>
    <p>POST /process to submit a ticket</p>
    '''

@app.route('/process', methods=['POST'])
def process_ticket():
    data = request.json
    
    ticket = Ticket(
        id=data.get('id', 'AUTO'),
        customer_id=data['customer_id'],
        subject=data['subject'],
        description=data['description']
    )
    
    result = system.process_ticket(ticket)
    return jsonify(result)

@app.route('/metrics')
def get_metrics():
    return jsonify(system.get_metrics())

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
```

Update Dockerfile:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir flask google-generativeai

EXPOSE 8080

CMD ["python", "api.py"]
```

Test locally:

```bash
# Build
docker build -t support-triage .

# Run
docker run -p 8080:8080 support-triage

# Test
curl -X POST http://localhost:8080/process \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST-123",
    "subject": "Cannot login",
    "description": "Forgot password"
  }'
```

---

## AWS Lambda

**Best for:** Serverless  
**Difficulty:** Medium  
**Cost:** Free tier generous  
**Bonus Points:** ✅ Yes (5 points)

### Deployment Steps

#### 1. Create Lambda Handler

Create `lambda_handler.py`:

```python
import json
from support_triage_system import SupportTriageSystem, Ticket

system = SupportTriageSystem()

def lambda_handler(event, context):
    """AWS Lambda handler for ticket processing"""
    
    try:
        # Parse input
        body = json.loads(event['body']) if isinstance(event.get('body'), str) else event
        
        # Create ticket
        ticket = Ticket(
            id=body.get('id', 'AUTO'),
            customer_id=body['customer_id'],
            subject=body['subject'],
            description=body['description']
        )
        
        # Process
        result = system.process_ticket(ticket)
        
        return {
            'statusCode': 200,
            'body': json.dumps(result),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

#### 2. Package for Lambda

```bash
# Create deployment package
mkdir lambda_package
cp support_triage_system.py lambda_package/
cp lambda_handler.py lambda_package/
cd lambda_package

# Add dependencies (if any)
pip install -t . google-generativeai

# Create ZIP
zip -r ../lambda_deployment.zip .
cd ..
```

#### 3. Deploy with AWS CLI

```bash
# Create Lambda function
aws lambda create-function \
  --function-name support-triage \
  --runtime python3.9 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role \
  --handler lambda_handler.lambda_handler \
  --zip-file fileb://lambda_deployment.zip \
  --timeout 30 \
  --memory-size 512

# Create API Gateway
aws apigatewayv2 create-api \
  --name support-triage-api \
  --protocol-type HTTP \
  --target arn:aws:lambda:us-east-1:YOUR_ACCOUNT:function:support-triage
```

#### 4. Test

```bash
# Invoke directly
aws lambda invoke \
  --function-name support-triage \
  --payload '{"customer_id":"CUST-123","subject":"Test","description":"Test ticket"}' \
  response.json

# Check response
cat response.json
```

---

## Docker Container

**Best for:** Platform-independent deployment  
**Difficulty:** Easy  
**Cost:** Hosting dependent  
**Bonus Points:** ✅ Yes (5 points)

### Full Dockerfile

```dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy application files
COPY support_triage_system.py .
COPY gemini_integration.py .
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN useradd -m -u 1000 agent && chown -R agent:agent /app
USER agent

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import sys; sys.exit(0)"

# Run application
CMD ["python", "-u", "support_triage_system.py"]
```

### Build and Run

```bash
# Build image
docker build -t support-triage:latest .

# Run container
docker run -d \
  --name support-triage \
  -e GEMINI_API_KEY=your-key \
  -p 8080:8080 \
  support-triage:latest

# View logs
docker logs -f support-triage

# Stop container
docker stop support-triage
```

### Push to Registry

```bash
# Tag for Docker Hub
docker tag support-triage:latest yourusername/support-triage:latest

# Push
docker push yourusername/support-triage:latest

# Or for Google Container Registry
docker tag support-triage:latest gcr.io/YOUR_PROJECT/support-triage:latest
docker push gcr.io/YOUR_PROJECT/support-triage:latest
```

### Docker Compose (Multi-Service)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  agent:
    build: .
    ports:
      - "8080:8080"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    restart: unless-stopped
    
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    
  postgres:
    image: postgres:14-alpine
    environment:
      - POSTGRES_DB=support_triage
      - POSTGRES_USER=agent
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  redis-data:
  postgres-data:
```

Run stack:

```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

---

## Heroku

**Best for:** Quick prototypes  
**Difficulty:** Easy  
**Cost:** Free tier available  
**Bonus Points:** ✅ Yes (5 points)

### Deployment Steps

#### 1. Create Heroku Config

Create `Procfile`:

```
web: python api.py
```

Create `runtime.txt`:

```
python-3.9.16
```

#### 2. Deploy

```bash
# Login to Heroku
heroku login

# Create app
heroku create support-triage-agent

# Set environment variables
heroku config:set GEMINI_API_KEY=your-key

# Deploy
git add .
git commit -m "Deploy to Heroku"
git push heroku main

# Open app
heroku open

# View logs
heroku logs --tail
```

#### 3. Scale

```bash
# Scale up
heroku ps:scale web=2

# Scale down
heroku ps:scale web=1
```

---

## Kubernetes (Advanced)

**Best for:** Enterprise production  
**Difficulty:** Hard  
**Cost:** Variable  
**Bonus Points:** ✅ Yes (5 points)

### Kubernetes Manifests

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: support-triage
spec:
  replicas: 3
  selector:
    matchLabels:
      app: support-triage
  template:
    metadata:
      labels:
        app: support-triage
    spec:
      containers:
      - name: agent
        image: gcr.io/YOUR_PROJECT/support-triage:latest
        ports:
        - containerPort: 8080
        env:
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: gemini-api-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: support-triage-service
spec:
  selector:
    app: support-triage
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer
```

Create secret:

```bash
kubectl create secret generic agent-secrets \
  --from-literal=gemini-api-key=your-key-here
```

Deploy:

```bash
kubectl apply -f k8s/deployment.yaml
kubectl get pods
kubectl get services
```

---

## Monitoring & Observability

### Add Health Checks

```python
# In api.py
@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Test system initialization
        system = SupportTriageSystem()
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500
```

### Add Logging

```python
import logging
from google.cloud import logging as cloud_logging

# Configure Cloud Logging
client = cloud_logging.Client()
client.setup_logging()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
```

### Add Metrics

```python
from prometheus_client import Counter, Histogram, generate_latest

# Define metrics
ticket_counter = Counter('tickets_processed', 'Total tickets processed')
processing_time = Histogram('processing_duration_seconds', 'Processing time')

@app.route('/metrics')
def metrics():
    return generate_latest()
```

---

## Evidence for Submission

### Screenshots to Include

1. **Deployment Success**
   - Cloud console showing deployed service
   - Service URL and status

2. **API Response**
   - Successful ticket processing via deployed endpoint
   - curl command and response

3. **Logs**
   - Application logs showing ticket processing
   - Metrics dashboard (if available)

### Writeup Section

Add to your Kaggle writeup:

```markdown
## Deployment (5 Bonus Points)

The Intelligent Customer Support Triage System has been deployed to
production on [Google Cloud Run / AWS Lambda / etc.].

**Deployment Details:**
- **Platform:** Google Cloud Run
- **Region:** us-central1
- **Endpoint:** https://support-triage-xyz.run.app
- **Scaling:** Auto-scale 0-10 instances
- **Memory:** 512Mi per instance
- **Deployment Date:** [Date]

**Deployment Process:**
1. Containerized application with Docker
2. Built image with Cloud Build
3. Deployed to Cloud Run with auto-scaling
4. Configured environment variables via Secret Manager
5. Set up health checks and logging

**Evidence:**
- See `deployment_screenshot.png` for deployment confirmation
- See `api_test.png` for successful API call
- Deployment can be reproduced with provided Docker and Cloud Run configs

**Cost Estimate:**
- Free tier covers up to 2M requests/month
- Estimated cost for 10K daily tickets: $5-10/month
```

---

## Troubleshooting

### Common Issues

**1. Out of Memory**
```yaml
# Increase memory allocation
resources:
  memory: "1Gi"  # Increase from 512Mi
```

**2. Cold Start Latency**
```yaml
# Set minimum instances
scaling:
  min_instances: 1  # Keep warm
```

**3. API Key Issues**
```bash
# Use Secret Manager instead of env vars
gcloud secrets create gemini-api-key --data-file=-
# Paste key and press Ctrl+D
```

**4. Timeouts**
```python
# Add timeout handling
import signal
signal.alarm(30)  # 30 second timeout
```

---

## Cost Optimization

### Tips to Minimize Costs

1. **Use Free Tiers**
   - Google Cloud Run: 2M requests/month free
   - AWS Lambda: 1M requests/month free
   - Heroku: 1 free dyno

2. **Optimize Cold Starts**
   - Keep containers small (<500MB)
   - Minimize dependencies
   - Use slim base images

3. **Scale to Zero**
   - Set min_instances=0 for dev/staging
   - Scale up only for production

4. **Monitor Usage**
   - Set up billing alerts
   - Review logs regularly
   - Optimize inefficient code

---

## Security Best Practices

### Secrets Management

```bash
# Google Cloud
gcloud secrets create api-key --data-file=key.txt
gcloud secrets add-iam-policy-binding api-key \
  --member=serviceAccount:YOUR_SA \
  --role=roles/secretmanager.secretAccessor

# AWS
aws secretsmanager create-secret \
  --name gemini-api-key \
  --secret-string "your-key"
```

### Network Security

```yaml
# Restrict access
spec:
  networkPolicy:
    ingress:
    - from:
      - ipBlock:
          cidr: 10.0.0.0/8  # Internal only
```

### Authentication

```python
# Add API key authentication
from functools import wraps

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != os.environ.get('EXPECTED_API_KEY'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/process', methods=['POST'])
@require_api_key
def process_ticket():
    # Your code here
    pass
```

---

## Next Steps After Deployment

1. **Monitor Performance**
   - Set up alerts for errors
   - Track response times
   - Monitor costs

2. **Add CI/CD**
   - Automate deployments
   - Run tests before deploy
   - Use GitHub Actions

3. **Scale Gradually**
   - Start with minimal resources
   - Monitor and adjust
   - Plan for peak loads

4. **Document Everything**
   - Deployment process
   - Configuration
   - Troubleshooting steps

---

**Deployment Complete! ✅**

You now have a production-ready AI agent system deployed to the cloud, earning you 5 bonus points for the Kaggle competition.

*Include deployment screenshots and logs in your submission!*
