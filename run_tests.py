import pytest
import os

if __name__ == "__main__":
    # Create the tests directory if it doesn't exist
    os.makedirs("tests", exist_ok=True)
    
    # Run all tests
    pytest.main(["-v", "tests/"])
