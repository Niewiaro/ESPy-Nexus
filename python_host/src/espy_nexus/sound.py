import winsound
from time import sleep

# Corrected notes (low bass) and the song's exact rhythm
RIFF = (
    (164, 0.90),  # E2 (Long, proud note)
    (0, 0.10),  # Short separator pause
    (164, 0.30),  # E2 (Short)
    (196, 0.50),  # G2
    (164, 0.50),  # E2
    (146, 0.50),  # D2
    (130, 1.10),  # C2 (Longer)
    (124, 1.20),  # B1 (Longest at the end of the phrase)
    (0, 0.40),  # Pause before the next loop
)

MELODY = RIFF * 12


def main() -> None:
    for frequency, duration in MELODY:
        duration_ms = int(duration * 1000)

        if frequency > 0:
            # winsound.Beep is synchronous (blocks the thread)
            winsound.Beep(frequency, duration_ms)
            sleep(0.2)
        else:
            # If this is a pause (frequency 0), sleep the loop
            sleep(duration)


if __name__ == "__main__":
    main()
