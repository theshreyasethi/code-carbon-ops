# Contributing to CodeCarbonOps

We welcome contributions from researchers, software engineers, and sustainability advocates. This document establishes guidelines for collaborating on the CodeCarbonOps repository.

---

## 1. Branching Strategy

To maintain repository stability and code quality, **direct pushes to the `main` branch are strictly prohibited**. All changes must be developed in isolated feature branches and submitted via Pull Requests (PRs).

Recommended branch naming conventions:
* `feature/<feature-name>`: For new capabilities, algorithms, or dashboard components.
* `fix/<bug-name>`: For bug fixes and patch releases.
* `docs/<topic>`: For documentation improvements and academic references.
* `refactor/<module>`: For structural improvements without functional behavior changes.

---

## 2. Development Workflow

1. **Synchronize local repository**:
   ```bash
   git checkout main
   git pull origin main
   ```

2. **Create an isolated working branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Implement modifications and verify against the test suite**:
   ```bash
   python -m pytest tests/ -v
   ```
   Ensure that all 54 existing tests execute successfully and add new test cases for introduced functional modules.

4. **Commit changes with descriptive commit messages**:
   ```bash
   git add .
   git commit -m "feat(router): Implement adaptive learning rate decay"
   ```

5. **Push working branch to remote repository**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request**: Submit a PR against the `main` branch on GitHub, providing a clear summary of architectural changes and test verification results.

---

## 3. Code Style & Quality Guidelines

* **Python Backend**:
  * Adhere to PEP 8 formatting standards.
  * Include explicit type hints for all function arguments and return values.
  * Document all public classes and functions using docstrings.
* **React Dashboard**:
  * Maintain clean functional component architecture using React Hooks.
  * Avoid hardcoded styling values; utilize CSS variables defined in the central stylesheet.
* **General**:
  * Keep code logs and console outputs professional and informative. Avoid emojis or informal language in production logs and user-facing notices.
