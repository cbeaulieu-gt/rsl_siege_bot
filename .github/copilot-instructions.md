# GitHub Copilot Instructions for Python Code Generation

These instructions guide GitHub Copilot to generate Python code that follows best practices for readability, maintainability, and robustness. All code must be production-ready, consistent in style, and accompanied by appropriate documentation and tests.

## ✅ General Coding Principles

* Generate **clear and concise** code that solves the problem directly.
* Follow **PEP-8** standards for formatting and naming conventions.
* Keep code **modular and reusable** with single-responsibility functions and classes.
* Avoid redundant or overly complex constructs.
* Always prefer built-in or standard library features when suitable.

## 🧠 Code Structure and Practices

* Use **explicit type hints** for all functions, parameters, and return values.
* Add **docstrings** to all public functions, classes, and modules using [PEP 257](https://www.python.org/dev/peps/pep-0257/) conventions.
* Use **f-strings** for string formatting.
* Encapsulate constants using `ALL_CAPS` naming and group them near the top of the file.
* Avoid side effects in module-level code (e.g., wrap run logic in `if __name__ == "__main__":`).

## 🧪 Testing with Pytest

* Generate test functions using the `pytest` framework.
* Each function or method should have at least one corresponding unit test.
* Use descriptive test names (e.g., `test_function_behavior_under_condition`).
* Use `pytest.mark.parametrize` for testing multiple input/output scenarios when applicable.
* Keep tests **isolated** and **stateless**.

## 📄 Documentation and Comments

* Always include a module-level docstring summarizing the file purpose.
* Use inline comments **sparingly**, only to clarify non-obvious logic.
* Avoid repeating information in comments that is already evident from code.

## 🔒 Error Handling

* Use appropriate exception handling with clear, specific exception types.
* Avoid using bare `except:` blocks.
* Validate inputs and raise exceptions early for invalid states.

## 🧰 Suggested Imports and Libraries

* Keep all imports at the top of the file and ensure 
* Use `typing` for type annotations (e.g., `List`, `Dict`, `Optional`, `Tuple`).
* Use `dataclasses` for simple data containers when appropriate.
* Use `pathlib` for file system paths instead of `os.path`.
* Prefer `enumerate()` and `zip()` over manual index tracking.

---

## Example Template for Copilot

```python
from typing import List, Optional

def filter_even_numbers(numbers: List[int]) -> List[int]:
    """
    Filter out even numbers from a list of integers.

    Args:
        numbers (List[int]): List of integers to filter.

    Returns:
        List[int]: List containing only odd numbers.
    """
    return [n for n in numbers if n % 2 != 0]
```

```python
# test_module.py
import pytest
from my_module import filter_even_numbers

@pytest.mark.parametrize("input_data,expected_output", [
    ([1, 2, 3, 4], [1, 3]),
    ([2, 4, 6], []),
    ([1, 3, 5], [1, 3, 5]),
])
def test_filter_even_numbers(input_data, expected_output):
    assert filter_even_numbers(input_data) == expected_output
```

> Use this style consistently for all Python code generation with GitHub Copilot.

---

By adhering to these practices, Copilot will generate Python code that is production-quality, easy to understand, and ready for collaborative development.
