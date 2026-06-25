# Contributing to Secure Exam Portal

Thank you for your interest in contributing to Secure Exam Portal! 🎉

We welcome contributions that improve functionality, security, performance, documentation, and user experience.

## Table of Contents

* Code of Conduct
* Getting Started
* Development Setup
* Branching Strategy
* Commit Guidelines
* Pull Request Process
* Security Contributions
* Reporting Bugs
* Feature Requests
* Coding Standards

---

## Code of Conduct

By participating in this project, you agree to:

* Be respectful and constructive.
* Welcome different viewpoints and ideas.
* Focus on improving the project.
* Avoid abusive, discriminatory, or offensive behavior.

---

## Getting Started

### 1. Fork the Repository

Fork the repository to your GitHub account and clone it locally.

```bash
git clone https://github.com/<your-username>/SecureExamPortal.git
cd SecureExamPortal
```

### 2. Create a Branch

Create a new branch for your changes.

```bash
git checkout -b feature/your-feature-name
```

Examples:

```bash
feature/student-dashboard-improvements
feature/question-randomization
fix/login-validation
fix/exam-timer-bug
```

---

## Development Setup

### Prerequisites

Ensure you have:

* Python 3.10+
* pip
* Virtual Environment (recommended)
* Database configured as described in the project documentation

### Create Virtual Environment

```bash
python -m venv venv
```

Activate:

**Linux/macOS**

```bash
source venv/bin/activate
```

**Windows**

```bash
venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the Application

```bash
python manage.py migrate
python manage.py runserver
```

---

## Branching Strategy

| Branch    | Purpose               |
| --------- | --------------------- |
| main      | Production-ready code |
| develop   | Active development    |
| feature/* | New features          |
| fix/*     | Bug fixes             |
| docs/*    | Documentation updates |

Please avoid pushing directly to `main`.

---

## Commit Guidelines

Use clear and descriptive commit messages.

### Recommended Format

```text
type(scope): short description
```

Examples:

```text
feat(exam): add auto-submit on timeout
fix(auth): resolve session expiration issue
docs(readme): update installation guide
refactor(student): simplify result calculation
```

Common types:

* feat
* fix
* docs
* refactor
* test
* chore
* security

---

## Pull Request Process

### Before Submitting

Make sure:

* Code builds successfully.
* Existing functionality is not broken.
* New code is tested.
* Documentation is updated if needed.
* No sensitive credentials are committed.

### PR Checklist

* [ ] Code follows project conventions
* [ ] Tests pass successfully
* [ ] Documentation updated
* [ ] No unnecessary files included
* [ ] Security implications reviewed

### Pull Request Description

Please include:

1. What problem is being solved.
2. Summary of changes.
3. Screenshots (if UI changes).
4. Testing performed.

---

## Security Contributions

Since this project deals with online examinations and user authentication, security is a high priority.

Contributions are encouraged in areas such as:

* Authentication improvements
* Authorization controls
* Session management
* Input validation
* CSRF protection
* Rate limiting
* Exam integrity protection
* Monitoring and audit logging

### Responsible Disclosure

Please do **not** open public issues for critical vulnerabilities.

Instead:

* Create a private security report through GitHub Security Advisories, or
* Contact the maintainer directly.

---

## Reporting Bugs

When reporting a bug, include:

### Environment

* Operating System
* Python version
* Browser (if applicable)

### Bug Details

```text
Expected behavior:
Actual behavior:
Steps to reproduce:
Screenshots/logs:
```

---

## Feature Requests

Feature requests should include:

* Problem statement
* Proposed solution
* Alternative approaches considered
* Expected benefits

Examples:

* Question randomization
* Exam analytics
* Proctoring enhancements
* Accessibility improvements
* Performance optimizations

---

## Coding Standards

### Python

* Follow PEP 8.
* Use meaningful variable names.
* Keep functions focused and small.
* Add docstrings where appropriate.

### Security

* Validate all user input.
* Never trust client-side validation alone.
* Avoid hardcoded secrets.
* Use environment variables for configuration.

### Documentation

Update relevant documentation when:

* Adding new features
* Modifying setup steps
* Introducing new configuration options

---

## Testing

Before opening a PR:

```bash
python manage.py test
```

Ensure all tests pass successfully.

If introducing new functionality, add corresponding tests whenever possible.

---

## Questions?

If you are unsure about a change, open an issue first to discuss the proposal before investing significant development effort.

Thank you for helping improve Secure Exam Portal! 🚀
