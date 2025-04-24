
# Copilot Instructions for Siege Project

## General Guidelines
1. **Follow PEP8 Conventions**: Ensure all generated code adheres to PEP8 standards for readability and maintainability.
2. **Use Built-in Libraries**: Prefer Python's built-in libraries over external dependencies whenever possible.
3. **Modularize Code**: Break down functionality into reusable, modular functions or classes.
4. **Type Annotations**: Include type annotations for all function arguments and return values.
5. **Function Documentation**: Provide concise Markdown-style docstrings for all functions, including:
   - A brief description of the function.
   - Arguments with their types and descriptions.
   - The return type and description.
6. **Use Pytest for Tests**: When generating tests, use the `pytest` framework to ensure consistency and ease of testing.

## Suggested Python Instructions
### 1. Generate a Utility Function
- Create a function that performs a specific task, such as file handling or data processing.
- Example:
    ```python
    def read_file(file_path: str) -> List[str]:
        """
        Reads a file and returns its contents as a list of lines.

        Args:
            file_path (str): The path to the file.

        Returns:
            List[str]: A list of lines from the file.
        """
        with open(file_path, 'r') as file:
            return file.readlines()
    ```

### 2. Generate a Class with Methods
- Define a class to encapsulate related functionality.
- Example:
    ```python
    class FileProcessor:
        """
        A class to handle file processing tasks.
        """

        def __init__(self, file_path: str):
            """
            Initializes the FileProcessor with a file path.

            Args:
                file_path (str): The path to the file.
            """
            self.file_path = file_path

        def get_file_size(self) -> int:
            """
            Returns the size of the file in bytes.

            Returns:
                int: The size of the file in bytes.
            """
            return os.path.getsize(self.file_path)
    ```

### 3. Generate Error Handling Code
- Include proper error handling using `try-except` blocks.
- Example:
    ```python
    def safe_divide(a: float, b: float) -> Optional[float]:
        """
        Safely divides two numbers, returning None if division by zero occurs.

        Args:
            a (float): The numerator.
            b (float): The denominator.

        Returns:
            Optional[float]: The result of the division, or None if division by zero.
        """
        try:
            return a / b
        except ZeroDivisionError:
            return None
    ```

### 4. Generate Logging Code
- Use Python's built-in `logging` module for logging.
- Example:
    ```python
    import logging

    logging.basicConfig(level=logging.INFO)

    def log_message(message: str) -> None:
        """
        Logs a message at the INFO level.

        Args:
            message (str): The message to log.
        """
        logging.info(message)
    ```

## Additional Notes
- Always test generated code for correctness and edge cases.
- Use meaningful variable and function names to improve code readability.
- Avoid hardcoding values; use constants or configuration files where appropriate.

