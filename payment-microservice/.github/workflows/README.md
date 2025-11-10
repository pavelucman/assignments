# GitHub Actions CI/CD Workflows

This directory contains GitHub Actions workflows for continuous integration and deployment.

## 📋 Workflows

### CI Workflow (`ci.yml`)

**Trigger**: Runs on push and pull requests to `main` or `master` branches

**Pipeline Stages**:

```
lint → typecheck → test → build → summary
```

#### Stage 1: Lint (Code Quality)
- **Runs on**: `ubuntu-latest`
- **Purpose**: Check code quality and formatting
- **Tools**: Ruff linter and formatter
- **Actions**:
  - Check code style with `ruff check`
  - Verify formatting with `ruff format --check`
- **Dependencies**: None (runs first)

#### Stage 2: Type Check (Static Analysis)
- **Runs on**: `ubuntu-latest`
- **Purpose**: Verify type hints and type safety
- **Tools**: Mypy
- **Actions**:
  - Install all dependencies
  - Generate gRPC code from proto files
  - Run mypy on source code
- **Dependencies**: Requires `lint` to pass

#### Stage 3: Test (Unit & Integration)
- **Runs on**: `ubuntu-latest`
- **Purpose**: Run comprehensive test suite with coverage
- **Tools**: Pytest, pytest-cov
- **Actions**:
  - Install all dependencies
  - Generate gRPC code from proto files
  - Run tests with coverage tracking
  - Fail if coverage < 80%
  - Upload HTML and XML coverage reports
  - Comment coverage on pull requests
- **Dependencies**: Requires `typecheck` to pass
- **Artifacts**:
  - `coverage-report-html/` - HTML coverage report (30 days)
  - `coverage-report-xml` - XML coverage report (30 days)

#### Stage 4: Build (Docker)
- **Runs on**: `ubuntu-latest`
- **Purpose**: Build and test Docker image
- **Tools**: Docker Buildx
- **Actions**:
  - Build Docker image with caching
  - Start container
  - Wait for health check to pass
  - Test gRPC endpoint connectivity
  - Export image as artifact (main/master only)
- **Dependencies**: Requires `test` to pass
- **Artifacts** (main/master only):
  - `docker-image` - Compressed Docker image (7 days)

#### Stage 5: Summary (Reporting)
- **Runs on**: `ubuntu-latest`
- **Purpose**: Provide overall pipeline status
- **Actions**:
  - Create summary table
  - Fail if any stage failed
- **Dependencies**: Requires all previous stages to complete
- **Always runs**: Even if previous stages fail

## 🔧 Configuration

### Environment Variables

The workflow uses the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_TOKEN` | Auto-generated token for GitHub API | Provided by Actions |

### Caching

Pip dependencies are cached per job to speed up workflow execution:

- **Cache key**: `${{ runner.os }}-pip-{job}-${{ hashFiles('pyproject.toml') }}`
- **Cache path**: `~/.cache/pip`
- **Benefits**: Faster dependency installation, reduced network usage

### Coverage Requirements

- **Minimum coverage**: 80%
- **Green threshold**: 90% (for PR comments)
- **Orange threshold**: 80% (for PR comments)
- **Failure**: Pipeline fails if coverage < 80%

## 📊 Artifacts

### Coverage Reports (Test Stage)

**HTML Report** (`coverage-report-html`):
- Browse-able coverage report
- Line-by-line coverage visualization
- Retention: 30 days
- Download from Actions UI

**XML Report** (`coverage-report-xml`):
- Machine-readable coverage data
- Compatible with coverage tools
- Retention: 30 days

### Docker Image (Build Stage)

**Compressed Image** (`docker-image`):
- Only on main/master branches
- Gzipped Docker image
- Can be loaded with: `docker load < payments-service-image.tar.gz`
- Retention: 7 days

## 🚀 Usage

### Running Locally

Simulate the CI pipeline locally:

```bash
# 1. Lint
ruff check .
ruff format --check .

# 2. Type Check
make proto
mypy src/

# 3. Test
make proto
pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# 4. Build
docker build -t payments-service:test .
docker run -d --name test -p 7000:7000 payments-service:test
# Wait for health check...
docker rm -f test
```

### Triggering Workflows

**Automatic Triggers**:
- Push to `main` or `master` branch
- Open/update pull request to `main` or `master`

**Manual Trigger**:
- Go to Actions tab in GitHub
- Select "CI" workflow
- Click "Run workflow"
- Choose branch

### Viewing Results

1. **GitHub Actions Tab**:
   - Navigate to repository → Actions
   - Click on workflow run
   - View job details and logs

2. **Pull Request Checks**:
   - View status checks at bottom of PR
   - Click "Details" for specific job logs
   - Coverage comment auto-posted by bot

3. **Artifacts**:
   - Go to workflow run page
   - Scroll to "Artifacts" section
   - Download coverage reports or Docker image

## 🐛 Troubleshooting

### Common Issues

**1. Lint Failures**

```bash
# Fix formatting issues
ruff format .

# Check what would change
ruff format --check --diff .
```

**2. Type Check Failures**

```bash
# Run mypy locally with same config
mypy src/

# Generate fresh proto files
make proto
```

**3. Test Failures**

```bash
# Run tests with verbose output
pytest -v

# Run specific test
pytest tests/unit/test_payment.py::TestPaymentCreation::test_create_payment_with_factory
```

**4. Coverage Too Low**

```bash
# Run coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Find uncovered lines
pytest --cov=src --cov-report=term-missing
```

**5. Docker Build Failures**

```bash
# Build locally
docker build -t test .

# Check logs
docker run --rm test

# Interactive debugging
docker run --rm -it --entrypoint bash test
```

### Debugging Workflow

**Enable debug logging**:
1. Go to repository Settings
2. Secrets and variables → Actions
3. Add variable: `ACTIONS_STEP_DEBUG` = `true`

**Re-run with debug**:
- Go to failed workflow run
- Click "Re-run all jobs"
- Select "Enable debug logging"

## 📚 Best Practices

### For Contributors

1. **Run locally first**: Test changes locally before pushing
2. **Fix lint/format**: Run `ruff format .` before committing
3. **Check types**: Ensure `mypy src/` passes
4. **Write tests**: Maintain 80%+ coverage
5. **Update docs**: Document significant changes

### For Maintainers

1. **Review coverage**: Check coverage reports on PRs
2. **Monitor build times**: Optimize slow jobs
3. **Update dependencies**: Keep actions up to date
4. **Adjust thresholds**: Modify coverage requirements as needed
5. **Clean artifacts**: Remove old workflow runs periodically

## 🔒 Security

### Secrets

No secrets are currently used in the CI workflow. If you need to add secrets:

1. Go to repository Settings → Secrets and variables → Actions
2. Add repository secret
3. Reference in workflow: `${{ secrets.SECRET_NAME }}`

### Permissions

The workflow uses minimal permissions:

- **contents**: read (checkout code)
- **pull-requests**: write (coverage comments)

## 📈 Metrics

### Typical Execution Times

| Stage | Duration | Cached |
|-------|----------|--------|
| Lint | ~30s | ~20s |
| Type Check | ~2m | ~1m |
| Test | ~3m | ~2m |
| Build | ~5m | ~3m |
| **Total** | **~10m** | **~6m** |

*Times may vary based on GitHub Actions runner availability*

## 🔄 Future Enhancements

Potential improvements to consider:

- [ ] Add deployment job for main branch
- [ ] Implement semantic versioning
- [ ] Add performance testing stage
- [ ] Create release workflow
- [ ] Add security scanning (Snyk, Trivy)
- [ ] Implement matrix testing (Python 3.11, 3.12, 3.13)
- [ ] Add benchmarking with regression detection
- [ ] Publish Docker image to registry
- [ ] Generate and publish documentation

## 📞 Support

For issues with the CI pipeline:

1. Check workflow logs in Actions tab
2. Review this documentation
3. Run locally to reproduce
4. Open issue with logs attached

