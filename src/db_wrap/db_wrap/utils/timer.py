import time
import logging

from typing import Any, TypedDict
from contextlib import asynccontextmanager, contextmanager


class TimerProperties(TypedDict):
    level: int
    total: float
    runtimes: dict[int, float]


class Timer:
    name: str

    startTimes: dict[str, float]
    totalTimes: dict[str, TimerProperties]

    timers: list[tuple[int, str]]
    level: int
    runIndex: int

    def __init__(self, name: str):
        self.name = name

        self.startTimes = {}
        self.totalTimes = {}
        self.timers = []
        self.level = 0
        self.runIndex = 0

    # * Class generator
    @contextmanager
    def enter(self, name: str):
        self.level += 1
        self.start(name=name)

        try:
            yield self
        finally:
            self.stop(name=name)
            self.level -= 1

    @asynccontextmanager
    async def aenter(self, name: str):
        self.level += 1
        self.start(name=name)

        try:
            yield self
        finally:
            self.stop(name=name)
            self.level -= 1

    # * Class context manager
    def __enter__(self) -> "Timer":
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.stop()

    async def __aenter__(self) -> "Timer":
        self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.stop()

    # * Start / stop
    def start(self, name: str | None = None, skipAppend: bool = False):
        if name is None:
            name = self.name

        if len(self.timers) > 0:
            (
                level,
                prevTimerName,
            ) = self.timers[-1]
            if prevTimerName != name and level != self.level:
                self.stop(name=prevTimerName, skipRemove=True)

        self.startTimes[name] = time.perf_counter()

        if not skipAppend:
            self.timers.append(
                (
                    self.level,
                    name,
                )
            )

    def stop(
        self,
        name: str | None = None,
        skipRemove: bool = False,
    ):
        if name is None:
            name = self.name
        endTime = time.perf_counter()

        if not name in self.startTimes:
            logging.getLogger().warning(f"Timer {name} stopped before it was started")
            return

        elapsed = endTime - self.startTimes[name]
        if not name in self.totalTimes:
            self.totalTimes[name] = TimerProperties(
                level=self.level, total=0, runtimes={}
            )

        self.totalTimes[name]["runtimes"][self.runIndex] = elapsed
        self.totalTimes[name]["total"] += elapsed

        if not skipRemove:
            # Remove current timer
            self.timers.pop()

            # Continue previous timer
            if len(self.timers) > 0:
                (
                    level,
                    prevTimerName,
                ) = self.timers[-1]
                if prevTimerName != name and level != self.level:
                    self.start(name=prevTimerName, skipAppend=True)

    # * Stats
    def resetTimers(self):
        """Resets the current timer. Call this at the start of an iteration."""
        self.startTimes = {}
        self.totalTimes = {}

    # * Output
    def printTimerStatsTable(self, returnData: bool = False) -> str | None:
        """Prints the current timing information into a table."""
        timerStats = "\n\n"

        all_fn_names = [k for k in self.totalTimes.keys()]
        if len(all_fn_names) == 0:
            return

        # Max width of level column
        max_level_width = max([self.totalTimes[k].get("level") for k in all_fn_names])
        if max_level_width % 2 == 1:
            max_level_width += 1
        max_level_width = max(max_level_width, 6)

        # Max width of name column
        max_name_width = max([len(k) for k in all_fn_names] + [4])
        if max_name_width % 2 == 1:
            max_name_width += 1

        # Format string
        format_str = (
            "{:>%d} | {:>%d} | {:>10.4f} | {:>10.4f} | {:>10.4f} | {:>10.4f} | {:>5}"
            % (
                max_level_width,
                max_name_width,
            )
        )

        header = (
            "{:>%d} | {:>%d} | {:^10} | {:^10} | {:^10} | {:^10} | {:^5}"
            % (
                max_level_width,
                max_name_width,
            )
        ).format(
            "Level", "Name", "Total (ms)", "Min (ms)", "Max (ms)", "Avg (ms)", "Count"
        )
        timerStats += f"{header}\n"

        sepIdx = header.find("|")
        sepText = ("-" * sepIdx) + "+" + ("-" * (len(header) - sepIdx - 1))
        timerStats += f"{sepText}\n"

        for name in all_fn_names:
            runtimes = self.totalTimes[name].get("runtimes", {}).values()
            total_time = self.totalTimes[name].get("total", 0) * 1000
            min_time = min(runtimes) * 1000 if runtimes else 0
            max_time = max(runtimes) * 1000 if runtimes else 0
            avg_time = (sum(runtimes) / len(runtimes)) * 1000 if runtimes else 0
            run_count = len(runtimes)

            timerStats += format_str.format(
                self.totalTimes[name].get("level"),
                name,
                total_time,
                min_time,
                max_time,
                avg_time,
                run_count,
            )
            timerStats += "\n"

        totals_format_str = (
            "{:>%d} | {:>%d} | {:>10.4f} | {:>10.4} | {:>10.4} | {:>10.4} | {:>10.4}"
            % (
                max_level_width,
                max_name_width,
            )
        )
        timerStats += f"{sepText}\n"
        timerStats += totals_format_str.format(
            "",
            "Total",
            self.totalTime(self.totalTimes) * 1000,
            "",
            "",
            "",
            "",
        )
        timerStats += "\n\n"

        if returnData:
            return timerStats

        logging.getLogger().debug(timerStats)

    def printTimerStatsJSON(self, returnData: bool = False) -> str | None:
        """Prints the current timing information into a JSON string."""
        pass

    def printTimerStatsCSV(self, returnData: bool = False) -> str | None:
        """Prints the current timing information into a CSV string."""
        all_fn_names = list(self.totalTimes.keys())
        if not all_fn_names:
            return

        # Prepare header
        header = all_fn_names + ["Total"]

        # Get all runtime indices and find the maximum index
        all_indices: set[int] = set()
        for name in all_fn_names:
            all_indices.update(self.totalTimes[name].get("runtimes", {}).keys())
        max_index = max(all_indices) if all_indices else 0

        # Prepare data rows
        data_rows: "list[list[str]]" = []
        for i in range(max_index + 1):
            row: "list[str]" = []
            row_total = 0
            for name in all_fn_names:
                runtime = self.totalTimes[name].get("runtimes", {}).get(i)
                if runtime is not None:
                    value = runtime * 1000
                    row.append(f"{value:.4f}")
                    row_total += value
                else:
                    row.append("")
            row.append(f"{row_total:.4f}")
            data_rows.append(row)

        # Prepare total row
        total_row: "list[str]" = []
        grand_total = 0
        for name in all_fn_names:
            total = sum(self.totalTimes[name].get("runtimes", {}).values()) * 1000
            total_row.append(f"{total:.4f}")
            grand_total += total
        total_row.append(f"{grand_total:.4f}")

        # Combine all rows
        all_rows = [header] + data_rows + [total_row]

        # Convert to CSV string
        output = "\n".join([",".join(str(cell) for cell in row) for row in all_rows])

        if returnData:
            return output

        logging.getLogger().info(f"\n{output}")

    def printTimerStats(
        self,
        outputFormat: str = "table",
        returnData: bool = False,
    ) -> str | None:
        """
        Prints the current timing information into a table.

        outputFormat: str - choices: ["table", "json", "csv"]
        """

        if outputFormat == "table":
            return self.printTimerStatsTable(returnData=returnData)
        elif outputFormat == "json":
            return self.printTimerStatsJSON(returnData=returnData)
        elif outputFormat == "csv":
            return self.printTimerStatsCSV(returnData=returnData)

    def totalTime(self, totalTimes: dict[str, TimerProperties]) -> float:
        """Returns the total amount accumulated across all functions in seconds."""
        return sum([timer.get("total") for _name, timer in totalTimes.items()])
