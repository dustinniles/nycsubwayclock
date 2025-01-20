import logging
from display.update import update_display

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def test_update_display():
    # Test case 1: Normal scenario with valid train times
    print("Test Case 1: Normal scenario with valid train times")
    closest_arrival = ("1 Train to South Ferry 5m", 5)
    next_arrival = ("2 Train to Wakefield 241st 10m", 10)
    line_number = 2
    update_display(closest_arrival, next_arrival, line_number)

    # Test case 2: No trains available
    print("Test Case 2: No trains available")
    closest_arrival = ("No trains available", 0)
    next_arrival = ("", 0)
    line_number = 2
    update_display(closest_arrival, next_arrival, line_number)

    # Test case 3: Single train available
    print("Test Case 3: Single train available")
    closest_arrival = ("3 Train to Times Square 7m", 7)
    next_arrival = ("", 0)
    line_number = 2
    update_display(closest_arrival, next_arrival, line_number)

    # Add more test cases as needed
    # ...

if __name__ == "__main__":
    test_update_display()
