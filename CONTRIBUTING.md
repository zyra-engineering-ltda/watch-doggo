# Contributing to WatchDoggo 🐶

First off — thank you for your interest in contributing!  
WatchDoggo is an open-source project by **Zyra Engineering** that helps developers monitor the health of multiple services with simplicity and transparency.  
We welcome issues, pull requests, and ideas from anyone who wants to make the project better.

---

## 🧭 Getting Started

1. **Fork the repository** on GitHub:
```

[https://github.com/zyra-engineering-ltda/watch-doggo](https://github.com/zyra-engineering-ltda/watch-doggo)

````

2. **Clone your fork locally:**
```bash
git clone https://github.com/YOUR-USERNAME/watch-doggo.git
cd watch-doggo
````

3. **Set up your development environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Run the app locally:**

   ```bash
   flask run
   ```

   or if using FastAPI:

   ```bash
   uvicorn main:app --reload
   ```

---

## 🧩 How to Contribute

### 🐛 Reporting Bugs

* Use the [Issues](https://github.com/zyra-engineering-ltda/watch-doggo/issues) tab.
* Include:

  * A clear description of the problem.
  * Steps to reproduce the issue.
  * Expected vs. actual results.
  * Any relevant logs or screenshots.

### 💡 Suggesting Enhancements

* Open a feature request issue labeled `enhancement`.
* Describe:

  * The problem your idea solves.
  * How you’d like to see it implemented (optional).

### 🧪 Submitting Code

1. Create a feature branch:

   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Write clean, well-documented code.
3. Run linting or tests (if applicable).
4. Commit with a clear message:

   ```bash
   git commit -m "Add: feature description"
   ```
5. Push and open a Pull Request.

---

## ✅ Code Guidelines

* Use **Python 3.10+**.
* Follow **PEP8** style conventions.
* Keep PRs small, focused, and easy to review.
* Include comments where behavior isn’t obvious.
* Avoid committing secrets, `.env` files, or large binary data.

---

## 🧠 Community Standards

All contributors are expected to follow our
[Code of Conduct](./CODE_OF_CONDUCT.md).

If you witness or experience harassment or unacceptable behavior, report it via:
📧 **[cristiano at zyraeng [dot] com](mailto:cristiano at zyraeng [dot] com)**

---

## 🏷️ License

By contributing to WatchDoggo, you agree that your contributions will be licensed under the [MIT License](./LICENSE).

---

Thank you again for helping make WatchDoggo better!
Together, we’re building tools that keep systems running with reliability and a bit of personality 🐾

```
That way your repo will meet all GitHub “Community Standards” badges.
```
