# Difference Between Errors and Exceptions

Errors and exceptions are both issues in a program, but they differ in severity and handling. Let's see how:

Error: Serious problems in the program logic that cannot be handled. Examples include syntax errors or memory errors.
Exception: Less severe problems that occur at runtime and can be managed using exception handling (e.g., invalid input, missing files).
Example: This example shows the difference between a syntax error and a runtime exception.

# Syntax Error (Error)

print("Hello world" # Missing closing parenthesis
​

# ZeroDivisionError (Exception)

n = 10
res = n / 0
Explanation: A syntax error stops the code from running at all, while an exception like ZeroDivisionError occurs during execution and can be caught with exception handling.

Syntax and Usage
Python provides four main keywords for handling exceptions: try, except, else and finally each plays a unique role. Let's see syntax:

try: # Code
except SomeException: # Code
else: # Code
finally: # Code

try: Runs the risky code that might cause an error.
except: Catches and handles the error if one occurs.
else: Executes only if no exception occurs in try.
finally: Runs regardless of what happens useful for cleanup tasks like closing files.
Example: This code attempts division and handles errors gracefully using try-except-else-finally.

try:
n = 0
res = 100 / n

except ZeroDivisionError:
print("You can't divide by zero!")

except ValueError:
print("Enter a valid number!")

else:
print("Result is", res)

finally:
print("Execution complete.")

Output
You can't divide by zero!
Execution complete.
Explanation: try block attempts division, except blocks catch specific errors, else block executes only if no errors occur, while finally block always runs, signaling end of execution.

Please refer Python Built-in Exceptions for some common exceptions.
