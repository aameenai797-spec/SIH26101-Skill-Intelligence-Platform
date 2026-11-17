# AI-Enabled Skill Intelligence and Personalized Learning Platform

Prototype aligned to SIH26101 – MoSPI / DIID.

## Features
- Learner registration and login with password hashing
- Learner profile: designation, department, experience and qualification
- Four-domain Official Statistics competency framework
- Self-assessment (levels 1–5), skill-gap analysis and course recommendations
- PDF, DOCX and TXT upload; extractive NLP baseline MCQ generation
- Quiz evaluation, explanations, score and audit log
- Learner dashboard, administrator analytics and role-based access
- Health endpoint and JSON competency endpoint
- Docker packaging, Pytest tests, Bandit security scan and Jenkins pipeline

## Important prototype boundaries
- iGOT Karmayogi and NSSTA TPAC course records are sample catalogue entries. Live integration requires authorized API documentation, credentials and approval.
- MCQ generation is an extractive NLP baseline. It creates fill-in-the-blank MCQs from extracted factual sentences; it is not a production LLM.
- SSO, government identity federation, production-grade encryption/key management, multilingual delivery and predictive ML analytics are extension points, not claimed as implemented.
- Do not upload confidential or personal government data to this prototype.

## Run on Windows PowerShell
```powershell
cd SkillIntelligencePlatform
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

Demo accounts:
- Administrator: `admin@skill.gov` / `Admin@123`
- Learner: `learner@skill.gov` / `Learner@123`

Change demo passwords and `SECRET_KEY` before any shared deployment.

## Test
```powershell
python -m pytest -v
python -m bandit -r app.py -ll
```

## Docker
```powershell
docker build -t skill-intelligence-platform:1.0 .
docker run --name skill-platform -p 5000:5000 -e SECRET_KEY="replace-with-a-long-random-value" skill-intelligence-platform:1.0
```
Open http://localhost:5000. Health check: http://localhost:5000/health

## Jenkins
Create a Pipeline job, connect your Git repository, select "Pipeline script from SCM", and set Script Path to `Jenkinsfile`.
The Jenkins agent must have Python 3, pip and Docker CLI/daemon access. If Jenkins runs inside a container, configure Docker-outside-of-Docker safely; the current Jenkins container may not have Docker access by default.
The Jenkinsfile uses Linux shell steps (`sh`). For a Windows Jenkins agent, convert these to `bat` steps and use Windows-compatible paths.

## CI/CD workflow
Git commit → GitHub SCM → Jenkins checkout → dependency install → Pytest → Bandit → Docker build → manual approval → staging container → health check / verification.
Production release should require approval, backup of persistent database, image version tagging, and a documented rollback to the previous known-good image.

## Deployment environments
- Development: local Flask server and SQLite test data.
- Testing: isolated pytest database and automated checks.
- Staging: Docker container on port 5001 with non-production data.
- Production: deploy approved immutable image to a managed host; use managed database/volume, HTTPS, secret manager, backups, monitoring and access controls.

## Rollback
Keep the previous successful image tag. If health checks or smoke tests fail, stop the new container and restart the previous image tag. Restore the last verified database backup if a migration/data issue occurred. Never delete the persistent database volume during rollback.

## Project structure
```
app.py
requirements.txt
Dockerfile
Jenkinsfile
tests/test_app.py
templates/
static/
uploads/
```
