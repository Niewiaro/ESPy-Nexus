import math
import sqlite3

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter
from matplotlib.figure import Figure
import pandas as pd
import seaborn as sns

FILE_NAME = "hil_analytics.csv"
DB_NAME = "hil_analytics.sqlite"
TABLE_NAME = "test_results"

sns.set_theme(
    style="whitegrid",
    context="talk",
    rc={
        "figure.dpi": 120,
        "savefig.dpi": 300,
        "axes.titlesize": 15,
        "axes.labelsize": 13,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
        "legend.fontsize": 10,
        "font.family": "DejaVu Sans",
    },
)


def _prepare_data(file_name: str) -> pd.DataFrame:
    df = pd.read_csv(file_name, encoding="utf-8")
    # with sqlite3.connect(file_name) as conn:
    #     df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conn)

    # Build series label for each protocol-topology combination.
    df["name"] = df["protocol"].astype(str) + "-" + df["router_topology"].astype(str)

    # Ensure numeric plotting columns and stable ordering on X axis.
    df["freq_hz"] = pd.to_numeric(df["freq_hz"], errors="coerce")
    df["pdr_ratio_percent"] = pd.to_numeric(df["pdr_ratio_percent"], errors="coerce")
    df = df.dropna(subset=["freq_hz", "pdr_ratio_percent"]).sort_values(
        ["name", "freq_hz"]
    )
    return df


def _style_log_x_axis(ax: Axes) -> None:
    ax.set_xscale("log")
    ax.xaxis.set_major_locator(LogLocator(base=10, subs=(1.0,)))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
    ax.xaxis.set_minor_locator(LogLocator(base=10, subs=tuple(range(2, 10))))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.tick_params(axis="x", which="major", length=7, width=1.0)
    ax.tick_params(axis="x", which="minor", length=4, width=0.7)
    ax.grid(which="major", axis="x", linewidth=1.25, color="#4f4f4f", alpha=1.0)
    ax.grid(which="minor", axis="x", linewidth=0.45, color="#bdbdbd", alpha=0.9)


def _plot_combined(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(13, 7.5), constrained_layout=True)

    sns.lineplot(
        data=df,
        x="freq_hz",
        y="pdr_ratio_percent",
        hue="name",
        style="name",
        markers=True,
        dashes=False,
        linewidth=2.2,
        markersize=7,
        ax=ax,
    )

    _style_log_x_axis(ax)
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("PDR [%]")
    ax.set_title("PDR vs freq_hz - wszystkie serie na jednym wykresie")
    ax.set_ylim(0, 105)
    ax.legend(title="protocol-topology", bbox_to_anchor=(1.02, 1), loc="upper left")


def _plot_subplots_window(df: pd.DataFrame) -> None:
    names = sorted(df["name"].unique())
    cols = 3
    rows = math.ceil(len(names) / cols)
    fig, axes = plt.subplots(
        rows,
        cols,
        figsize=(5.6 * cols, 4.2 * rows),
        sharex=True,
        sharey=True,
        constrained_layout=True,
    )
    axes = axes.ravel() if hasattr(axes, "ravel") else [axes]

    for idx, name in enumerate(names):
        ax = axes[idx]
        group = df[df["name"] == name].sort_values("freq_hz")
        sns.lineplot(
            data=group,
            x="freq_hz",
            y="pdr_ratio_percent",
            marker="o",
            linewidth=2.0,
            markersize=6,
            color=sns.color_palette("deep", 1)[0],
            ax=ax,
            legend=False,
        )
        _style_log_x_axis(ax)
        ax.set_title(name, fontsize=11)
        ax.set_ylim(0, 105)

    for idx in range(len(names), len(axes)):
        axes[idx].set_visible(False)

    fig.suptitle("PDR - osobne subploty dla każdej kombinacji", fontsize=16)
    fig.supxlabel("Frequency [Hz]")
    fig.supylabel("PDR [%]")


def _plot_by_protocol(df: pd.DataFrame) -> None:
    for protocol, group in df.groupby("protocol", sort=True):
        fig, ax = plt.subplots(figsize=(10.5, 6.5), constrained_layout=True)
        sns.lineplot(
            data=group.sort_values("freq_hz"),
            x="freq_hz",
            y="pdr_ratio_percent",
            hue="router_topology",
            style="router_topology",
            markers=True,
            dashes=False,
            linewidth=2.2,
            markersize=7,
            ax=ax,
        )
        _style_log_x_axis(ax)
        ax.set_xlabel("freq_hz")
        ax.set_ylabel("PDR (%)")
        ax.set_title(f"PDR dla protokołu {protocol}")
        ax.set_ylim(0, 105)
        ax.legend(title="router_topology", bbox_to_anchor=(1.02, 1), loc="upper left")


def _plot_by_router_topology(df: pd.DataFrame) -> None:
    for topology, group in df.groupby("router_topology", sort=True):
        fig, ax = plt.subplots(figsize=(10.5, 6.5), constrained_layout=True)
        sns.lineplot(
            data=group.sort_values("freq_hz"),
            x="freq_hz",
            y="pdr_ratio_percent",
            hue="protocol",
            style="protocol",
            markers=True,
            dashes=False,
            linewidth=2.2,
            markersize=7,
            ax=ax,
        )
        _style_log_x_axis(ax)
        ax.set_xlabel("freq_hz")
        ax.set_ylabel("PDR (%)")
        ax.set_title(f"PDR dla topologii {topology}")
        ax.set_ylim(0, 105)
        ax.legend(title="protocol", bbox_to_anchor=(1.02, 1), loc="upper left")


def main() -> None:
    df = _prepare_data(FILE_NAME)
    # df = _prepare_data(DB_NAME)
    _plot_combined(df)
    _plot_subplots_window(df)
    _plot_by_protocol(df)
    _plot_by_router_topology(df)
    plt.show()


if __name__ == "__main__":
    main()
