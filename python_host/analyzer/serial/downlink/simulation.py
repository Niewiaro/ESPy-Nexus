from pdr import calculate_pdr, print_pdr_result
from jitter import calculate_jitter, print_jitter_result
from burst_loss import calculate_burst_loss, print_burst_loss_result


class Config:
    def __init__(self, total_sent: int = 5, packet_id=None, esp_ts=None):
        import pandas as pd

        # Simulation of received packet IDs with some losses and duplicates
        self.total_sent = total_sent
        self.packet_id = packet_id
        self.esp_ts = esp_ts

        if self.packet_id is None:
            # Missing 3, but 2 is duplicated (MAC duplicate)
            self.packet_id = [0, 1, 2, 2, 5]
        if self.esp_ts is None:
            self.esp_ts = [100, 200, 300, 310, 500]

        self.df = pd.DataFrame(
            {
                "packet_id": self.packet_id,
                "esp_ts": self.esp_ts,
            }
        )


def main() -> None:
    config = Config()

    result_pdr = calculate_pdr(config.df["packet_id"], config.total_sent)
    print_pdr_result(result_pdr)
    print()

    result_jitter = calculate_jitter(config.df["esp_ts"])
    print_jitter_result(result_jitter)
    print()

    result_burst_loss = calculate_burst_loss(config.df["packet_id"], config.total_sent)
    print_burst_loss_result(result_burst_loss)
    print()


if __name__ == "__main__":
    main()
