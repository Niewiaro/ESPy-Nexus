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

const data = ref<HilDataRow[]>(rawJsonData as HilDataRow[]);
const selectedTests = ref<string[]>([]);
const selectedMetric = ref<string>();

const xRangeLimit = ref<[number, number]>([0, 1000]);
const selectedXRange = ref<[number, number]>([0, 1000]);

let isInitialized = false;

function shuffleArray<T>(array: T[]): T[] {
	const shuffled = [...array];
	for (let i = shuffled.length - 1; i > 0; i--) {
		const j = Math.floor(Math.random() * (i + 1));
		[shuffled[i]!, shuffled[j]!] = [shuffled[j]!, shuffled[i]!];
	}
	return shuffled;
}

export const useAnalytics = () => {
	const pending = ref(false);
	const error = ref(null);

	const availableTests = computed(() => {
		const rawData = data.value;
		if (!rawData) return [];
		const names = rawData.map(row => `${row.protocol}_${row.router_topology}_${row.payload_b}b`);
		return [...new Set(names)];
	});

	const availableMetrics = computed(() => {
		const firstRow = data.value?.[0];
		if (!firstRow) return [];
		const allKeys = Object.keys(firstRow);
		const ignoredColumns = ["test_id", "router_topology", "protocol", "freq_hz", "status", "payload_b", "expected_cnt", "pdr_expected", "pdr_received"];
		return allKeys.filter(key => !ignoredColumns.includes(key));
	});

	if (!isInitialized && availableTests.value.length > 0 && availableMetrics.value.length > 0) {
		const shuffledTests = shuffleArray(availableTests.value);
		selectedTests.value = shuffledTests.slice(0, 5);

		const shuffledMetrics = shuffleArray(availableMetrics.value);
		selectedMetric.value = shuffledMetrics[0];

		const frequencies = data.value.map(row => Number(row.freq_hz));
		const minFreq = Math.min(...frequencies);
		const maxFreq = Math.max(...frequencies);

		xRangeLimit.value = [minFreq, maxFreq];
		selectedXRange.value = [minFreq, maxFreq];

		isInitialized = true;
	}

	const chartData = computed(() => {
		const rawData = data.value;

		if (!rawData || selectedTests.value.length === 0 || !selectedMetric.value) {
			return { datasets: [] };
		}

		const chartColors = [
			"#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6",
			"#ec4899", "#06b6d4", "#84cc16", "#f97316", "#6366f1",
		];

		const datasets = selectedTests.value.map((testName, index) => {
			const testRows = rawData.filter((row) => {
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

	return {
		pending, error, availableTests, availableMetrics, selectedTests, selectedMetric, chartData, data,
		selectAllTests, clearAllTests,
		xRangeLimit,
		selectedXRange,
	};
};
