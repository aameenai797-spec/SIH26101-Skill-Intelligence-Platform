# CI/CD Pipeline Diagram

```mermaid
flowchart TD
 A[Developer changes code] --> B[Git commit and push]
 B --> C[GitHub repository]
 C --> D[Jenkins checkout]
 D --> E[Install Python dependencies]
 E --> F[Pytest automated tests]
 F --> G[Bandit security scan]
 G --> H[Build Docker image]
 H --> I{Manual deployment approval}
 I -->|Approved| J[Deploy to staging]
 I -->|Rejected| K[Stop release]
 J --> L[Health and smoke verification]
 L --> M{Verification passed?}
 M -->|Yes| N[Production approval and release]
 M -->|No| O[Rollback to previous image]
 N --> P[Monitor logs and application]
```

## Stage explanation
1. SCM: Git and GitHub preserve source history and trigger pipeline execution.
2. Build: Jenkins installs pinned Python dependencies.
3. Test: Pytest validates health endpoint, authentication, authorization and profile update.
4. Quality/security: Bandit checks Python source for common security issues.
5. Package: Docker creates a versioned, portable container image.
6. Deploy: Jenkins deploys an approved image to staging.
7. Verify: health endpoint and smoke tests confirm service readiness.
8. Release/rollback: production approval is separate; previous image tag and database backup are retained for recovery.
