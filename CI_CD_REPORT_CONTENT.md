# CI/CD Pipeline Design – SIH26101
## 1. Requirement and Pipeline Analysis
The proposed Skill Intelligence Platform supports competency profiling, self-assessment, skill-gap identification, personalized learning recommendations, learning-material upload, MCQ generation, quiz evaluation and learner/administrator dashboards. It stores learner profiles and assessment records; therefore the pipeline must validate application behavior, access control, file handling and database operations before packaging and release.

CI/CD needs: version-controlled source, repeatable dependency installation, automated functional tests, source security analysis, container packaging, environment-specific configuration, staging verification, controlled production approval, monitoring and rollback.

## 2. Pipeline Architecture and Workflow
Developer commit → GitHub → Jenkins checkout → dependency installation → Pytest → Bandit → Docker build → staging deployment → health verification → production approval → production release. A failed test or security gate prevents the pipeline from advancing. The diagram is in PIPELINE_DIAGRAM.md.

## 3. Tools and Justification
- Python/Flask: backend and web application.
- SQLite: lightweight prototype persistence; production should use a managed relational database.
- Git/GitHub: source control, collaboration and version history.
- Jenkins: pipeline orchestration and stage logs.
- Pytest: repeatable functional and access-control tests.
- Bandit: static security checks for Python.
- Docker: consistent packaging across environments.
- Container registry: store immutable versioned images (Docker Hub or approved private registry).
- Deployment host: staging and production runtime; configure HTTPS and secrets outside source code.

## 4. Automated Testing and Quality
Unit/functional coverage includes health endpoint, successful learner login, learner restriction from administrator route, profile update and API authentication requirement. Extend with tests for upload validation, file size limits, quiz scoring, database constraints and admin analytics. Bandit runs before image creation. Production should additionally use dependency vulnerability scanning, container image scanning, SAST, DAST and load testing.

## 5. Deployment, Security and Rollback
Development uses local Flask and synthetic data. Testing uses isolated temporary SQLite databases and Pytest. Staging runs a Docker image on a separate port with non-production data. Production requires approved immutable image, HTTPS, secret manager, persistent managed database, backups, monitoring and role-based access.

Passwords are hashed; learner/admin routes are separated; upload extensions and size are restricted; secrets are environment variables. Do not commit credentials or real personal data. Keep the previous image tag and database backup. If health verification fails, route traffic back to the previous image and restore a verified backup when required. Pipeline notifications are provided through Jenkins build status; email/Teams notifications can be configured in Jenkins.

## 6. Diagram and Documentation
The Mermaid diagram in PIPELINE_DIAGRAM.md explains the workflow from code commit to deployment, approval gates and rollback. Jenkins console output, Pytest report, Bandit output, Docker image/container status and staging health endpoint should be captured as implementation evidence.

## Prototype limitations
iGOT Karmayogi API integration is represented by a sample catalogue because official API credentials and documentation are not available in this prototype. The MCQ engine uses extractive NLP and is not a production LLM. Production SSO, government cloud integration, multilingual delivery and predictive analytics require approved infrastructure and further implementation.
