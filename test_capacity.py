import time

def simulate_test_openings():
    capacity = 100  # Initial capacity
    link = "https://www.argon-online.com/online/ibrahim"
    for i in range(1, 50):  # Simulate 23 test openings
        bandwidth = 10  # Example bandwidth
        print(f"Test Opening {i}:")
        print(f"Link: {link}")
        print(f"Bandwidth: {bandwidth} Mbps")
        print(f"Capacity: {capacity}%")
        print("Opening link...")
        time.sleep(1)  # Simulate opening link
        capacity -= 100 / 23  # Decrease capacity for each opening
        print()
    print("Test openings stopped.")

if __name__ == "__main__":
    simulate_test_openings()
