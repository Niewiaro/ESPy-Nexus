import rawJsonData from "~/assets/data.json";

export interface HilDataRow {
	test_id: number;
	router_topology: string;
	protocol: string;
	freq_hz: number;
	status: string;
	payload_b: number;
	[key: string]: string | number;
}

export interface ChartPoint {
	x: number;
	y: number;
}

const rawDataRef = ref<HilDataRow[]>(rawJsonData as HilDataRow[]);

function shuffleArray<T>(array: T[]): T[] {
	const shuffled = [...array];
	for (let i = shuffled.length - 1; i > 0; i--) {
		const j = Math.floor(Math.random() * (i + 1));
		[shuffled[i]!, shuffled[j]!] = [shuffled[j]!, shuffled[i]!];
	}
	return shuffled;
}

export const useAnalytics = () => {
	const selectedTests = useState<string[]>("hil-selected-tests", () => []);
	const selectedMetric = useState<string | undefined>("hil-selected-metric", () => undefined);

	const xRangeLimit = useState<[number, number]>("hil-x-range-limit", () => [0, 1000]);
	const selectedXRange = useState<[number, number]>("hil-selected-x-range", () => [0, 1000]);

	const isLogX = useState<boolean>("hil-log-x", () => true);
	const isLogY = useState<boolean>("hil-log-y", () => false);

	const isInitialized = useState<boolean>("hil-is-initialized", () => false);

	const availableTests = computed(() => {
		const names = rawDataRef.value.map(row => `${row.protocol}_${row.router_topology}_${row.payload_b}b`);
		return [...new Set(names)];
	});

	const availableMetrics = computed(() => {
		const firstRow = rawDataRef.value?.[0];
		if (!firstRow) return [];
		const allKeys = Object.keys(firstRow);
		const ignoredColumns = ["test_id", "router_topology", "protocol", "freq_hz", "status", "payload_b", "expected_cnt", "pdr_expected", "pdr_received"];
		return allKeys.filter(key => !ignoredColumns.includes(key));
	});

	const availableProtocols = computed(() => {
		const protocols = rawDataRef.value.map((row) => {
			if (row.protocol === "SERIAL_BIN" || row.protocol === "SERIAL_STR") {
				return "SERIAL";
			}
			return row.protocol;
		});

		return [...new Set(protocols)];
	});

	const availableTopologies = computed(() => {
		const topologies = rawDataRef.value.map(row => row.router_topology);
		return [...new Set(topologies)];
	});

	const availablePayloads = computed(() => {
		const payloads = rawDataRef.value.map(row => Number(row.payload_b));
		return [...new Set(payloads)].sort((a, b) => a - b);
	});

	const hzRange = computed(() => {
		if (!rawDataRef.value.length) return { min: 0, max: 0 };

		return rawDataRef.value.reduce((acc, row) => {
			const hz = Number(row.freq_hz) || 0;
			if (hz < acc.min) acc.min = hz;
			if (hz > acc.max) acc.max = hz;
			return acc;
		}, { min: Infinity, max: -Infinity });
	});

	const totalPackets = computed(() => {
		return rawDataRef.value.reduce((sum, row) => sum + (Number(row.expected_cnt) || 0), 0);
	});

	const randomizeSelection = () => {
		if (availableTests.value.length === 0 || availableMetrics.value.length === 0) return;

		const shuffledTests = shuffleArray(availableTests.value);
		selectedTests.value = shuffledTests.slice(0, 5);

		const shuffledMetrics = shuffleArray(availableMetrics.value);
		selectedMetric.value = shuffledMetrics[0];

		selectedXRange.value = [...xRangeLimit.value];
	};

	if (!isInitialized.value && availableTests.value.length > 0 && availableMetrics.value.length > 0) {
		randomizeSelection();

		const frequencies = rawDataRef.value.map(row => Number(row.freq_hz));
		const minFreq = Math.min(...frequencies);
		const maxFreq = Math.max(...frequencies);

		xRangeLimit.value = [minFreq, maxFreq];
		selectedXRange.value = [minFreq, maxFreq];

		isInitialized.value = true;
	}

	const chartData = computed(() => {
		if (selectedTests.value.length === 0 || !selectedMetric.value) {
			return { datasets: [] };
		}

		const chartColors = [
			"#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6",
			"#ec4899", "#06b6d4", "#84cc16", "#f97316", "#6366f1",
		];

		const datasets = selectedTests.value.map((testName, index) => {
			const testRows = rawDataRef.value.filter((row) => {
				const currentTestName = `${row.protocol}_${row.router_topology}_${row.payload_b}b`;
				const freq = Number(row.freq_hz);
				const isInRange = freq >= selectedXRange.value[0] && freq <= selectedXRange.value[1];

				return currentTestName === testName && isInRange;
			});

			const dataPoints: ChartPoint[] = testRows.map(row => ({
				x: Number(row.freq_hz),
				y: Number(row[selectedMetric.value as string]),
			}));

			dataPoints.sort((a: ChartPoint, b: ChartPoint) => a.x - b.x);

			const color = chartColors[index % chartColors.length];

			return {
				label: testName,
				data: dataPoints,
				tension: 0.2,
				borderColor: color,
				backgroundColor: color,
			};
		});

		return { datasets };
	});

	const selectAllTests = () => {
		selectedTests.value = [...availableTests.value];
	};

	const clearAllTests = () => {
		selectedTests.value = [];
	};

	const selectByProtocol = (protocol: string) => {
		const matchingRows = rawDataRef.value.filter((row) => {
			if (protocol === "SERIAL") {
				return row.protocol === "SERIAL_BIN" || row.protocol === "SERIAL_STR";
			}
			return row.protocol === protocol;
		});

		const names = matchingRows.map(row => `${row.protocol}_${row.router_topology}_${row.payload_b}b`);
		selectedTests.value = [...new Set(names)];
	};

	const selectByTopology = (topology: string) => {
		const matchingRows = rawDataRef.value.filter(row => row.router_topology === topology);
		const names = matchingRows.map(row => `${row.protocol}_${row.router_topology}_${row.payload_b}b`);
		selectedTests.value = [...new Set(names)];
	};

	const selectByPayload = (payload: number) => {
		const matchingRows = rawDataRef.value.filter(row => Number(row.payload_b) === payload);
		const names = matchingRows.map(row => `${row.protocol}_${row.router_topology}_${row.payload_b}b`);
		selectedTests.value = [...new Set(names)];
	};

	return {
		availableTests,
		availableMetrics,
		availableProtocols,
		availableTopologies,
		availablePayloads,
		selectedTests,
		selectedMetric,
		chartData,
		data: rawDataRef,
		selectAllTests,
		clearAllTests,
		randomizeSelection,
		selectByProtocol,
		selectByTopology,
		selectByPayload,
		xRangeLimit,
		selectedXRange,
		isLogX,
		isLogY,
		hzRange,
		totalPackets,
	};
};
