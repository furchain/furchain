import functools
import inspect
import logging
import os
import time

# Create a logger
logger = logging.getLogger(__name__)

# Set the level of the logger based on the DEBUG environment variable.
if os.environ.get("DEBUG") == 'true':
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

# Create a file handler for outputting log messages to a file
handler = logging.FileHandler('furchain.log')

# Set the level of the handler.
handler.setLevel(logging.DEBUG)

# Create a formatter and add it to the handler
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s')
handler.setFormatter(formatter)

# Add the handler to the logger if it's not already added
if not logger.handlers:
    logger.addHandler(handler)


def logit(log_time=True, log_output=False, log_level=logging.DEBUG):
    def decorator(func):
        _logger = logging.getLogger(func.__name__)
        if os.environ.get("DEBUG"):
            _logger.setLevel(logging.DEBUG)
        else:
            _logger.setLevel(logging.INFO)
        if not _logger.handlers:
            _logger.addHandler(handler)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Start the timer
            start_time = time.time()

            # Call the function/method
            result = func(*args, **kwargs)

            # Calculate the execution time
            execution_time = time.time() - start_time

            # Log the execution time if requested
            bound_to = None

            # If there are arguments, the first one is typically 'self' for instance methods.
            if args:
                # Get the type of the first argument.
                first_arg = args[0]

                # Check if we're dealing with a method by seeing if 'self' is an instance of a class.
                if inspect.ismethod(func) or inspect.isfunction(func):
                    if hasattr(first_arg, '__class__'):
                        bound_to = first_arg.__class__.__name__
                    else:
                        bound_to = type(first_arg).__name__

            if bound_to:
                message = f"{bound_to}.{func.__name__} - "
                stack_level = 2
            else:
                message = f"{func.__name__} - "
                stack_level = 1

            if log_time:
                message += f"Execution Time: {execution_time:.4f}s. "

            # Log the function output if requested
            if log_output:
                message += f"Output: {result}"

            # Log the message using the global logger with an increased stacklevel
            _logger.log(log_level, message, stacklevel=stack_level)
            return result

        return wrapper

    return decorator
