# Load Testing with Locust for a gRPC-based Vacancy Server

This project was created to perform realistic load testing against a vacancy server that communicates via gRPC. It uses Locust to simulate concurrent users interacting with the system in a way that reflects typical usage.

The main goal is to evaluate how the server performs under load by measuring response times, observing failure rates, and identifying possible performance bottlenecks during common operations such as creating, updating, retrieving, and deleting job vacancies.

## What this script does

At the beginning of the test, the script automatically creates three temporary users using disposable email addresses. It then verifies each email address by checking for the verification code received via email and confirming the user accounts with the server.

After that, each simulated Locust user logs in with one of the verified accounts. Every 30 seconds, each user executes a full cycle that includes creating a new vacancy with randomized content, updating one or more fields in that vacancy, retrieving the vacancy, and then deleting it.

In parallel to this cycle, every 45 seconds each user fetches a list of all vacancies available on the server.

Each gRPC request is monitored individually. The script logs detailed response times and records any errors reported by the server, making it easy to analyze system performance from Locust’s web interface.

## How to run the test

Before running the test, make sure you have Python 3.8 or higher installed, along with pip. The gRPC server must be accessible, and the necessary `.proto` files must be compiled into Python modules and placed in the `proto/` directory.

Start by cloning the repository and installing the required dependencies:

```bash
git clone https://github.com/bertuccii/Locust-for-Cyrex.git
cd Locust-for-Cyrex
pip install -r requirements.txt
```

Then, create a `.env` file in the root directory with the server address

The test script will attempt to connect to this server address.

To run the test, simply launch Locust:

```bash
locust -f locustfile.py
```

Once it starts, open your browser and go to:

```
http://localhost:8089
```

From there, you can configure how many simulated users to spawn and how quickly. Once you start the test, Locust will display real-time statistics for each gRPC operation, including detailed response times, error counts, and throughput.

## Notes

The testing logic is structured to simulate real usage patterns rather than random or artificial traffic. All operations follow a clear sequence and include realistic delays between requests to reflect human behavior. This makes the results more meaningful for performance tuning and capacity planning.

The script also handles the full user registration flow, including email verification, which ensures that the test reflects actual usage from start to finish.

If needed, the code can be easily adapted for testing other gRPC services by changing the `.proto` files and updating the corresponding service calls in the script.

## Author

This project was developed by Felipe Bertucci Maurer as part of a load testing challenge using Locust and gRPC. If you have any questions or suggestions, feel free to reach out or fork the repository.
