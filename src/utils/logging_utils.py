import logging
import sys
import os
import codecs

class UnicodeStreamHandler(logging.StreamHandler):
    """
    A StreamHandler that properly handles Unicode characters on Windows.
    """
    def __init__(self, stream=None):
        # Force UTF-8 encoding for stdout on Windows
        if stream is None:
            if sys.platform == "win32":
                # Use utf-8 encoding for Windows console
                if sys.stdout.isatty():
                    try:
                        # Try to use UTF-8 on Windows console
                        sys.stdout.reconfigure(encoding='utf-8')
                    except AttributeError:
                        # For older Python versions
                        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
                stream = sys.stdout
            else:
                stream = sys.stdout
                
        super().__init__(stream)
    
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

def setup_logging(log_level=logging.INFO, log_file=None):
    """
    Set up logging with Unicode support.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove all handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add Unicode-compatible console handler
    console_handler = UnicodeStreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger
