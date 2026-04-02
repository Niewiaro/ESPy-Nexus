from espy_nexus.core.config import Protocol
from espy_nexus.runner.matrix import (
    generate_test_matrix,
    generate_linear_rates,
    generate_exponential_rates,
)
from espy_nexus.runner.engine import TestEngine


def main():
    PORT = "COM5"
    BAUDRATE = 921600
    PAYLOAD_SIZE = 16

    frequencies = generate_linear_rates(start=10, stop=3000, step=10)
    # frequencies = generate_exponential_rates(base=100, max_val=10000)

    test_matrix = generate_test_matrix(
        protocols=[Protocol.SERIAL],
        rates_hz=frequencies,
        payloads_bytes=[PAYLOAD_SIZE],
        packet_count=10000,
    )

    engine = TestEngine(port=PORT, baudrate=BAUDRATE)

    engine.run_matrix(matrix=test_matrix, output_csv="test_matrix.csv")


if __name__ == "__main__":
    main()
