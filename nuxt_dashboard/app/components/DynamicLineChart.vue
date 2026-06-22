<template>
	<div class="flex flex-col gap-4 w-full h-full flex-1 min-h-100">
		<div
			v-if="chartData.datasets.length"
			class="flex flex-wrap justify-end gap-6 px-2"
		>
			<UCheckbox
				v-model="isLogX"
				name="logX"
				label="Skala logarytmiczna (Oś X)"
			/>
			<UCheckbox
				v-model="isLogY"
				name="logY"
				label="Skala logarytmiczna (Oś Y)"
			/>
		</div>

		<div class="flex-1 w-full relative">
			<Line
				v-if="chartData.datasets.length"
				:data="chartData"
				:options="chartOptions"
			/>
			<div
				v-else
				class="flex h-full items-center justify-center text-gray-500 border-2 border-dashed border-gray-200 dark:border-gray-800 rounded-lg p-6 text-center"
			>
				Wybierz co najmniej jeden test i metrykę w panelu bocznym...
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Line } from "vue-chartjs";
import {
	Chart as ChartJS, CategoryScale, LinearScale, LogarithmicScale,
	PointElement, LineElement, Title, Tooltip, Legend, type ChartOptions,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, LogarithmicScale, PointElement, LineElement, Title, Tooltip, Legend);

const { chartData, selectedMetric, isLogX, isLogY } = useAnalytics();
const colorMode = useColorMode();
const isDark = computed(() => colorMode.value === "dark");

const chartOptions = computed<ChartOptions<"line">>(() => {
	const textColor = isDark.value ? "#9ca3af" : "#4b5563";
	const gridColor = isDark.value ? "#374151" : "#e5e7eb";

	return {
		responsive: true,
		maintainAspectRatio: false,
		interaction: { mode: "index", intersect: false },
		elements: {
			point: { radius: 2, hoverRadius: 6 },
			line: { borderWidth: 2, cubicInterpolationMode: "monotone" },
		},
		scales: {
			x: {
				type: isLogX.value ? "logarithmic" : "linear",
				title: { display: true, text: "Częstotliwość [Hz]", color: textColor, font: { weight: "bold" } },
				ticks: { color: textColor }, grid: { color: gridColor },
			},
			y: {
				type: isLogY.value ? "logarithmic" : "linear",
				title: { display: !!selectedMetric.value, text: selectedMetric.value || "", color: textColor, font: { weight: "bold" } },
				ticks: { color: textColor }, grid: { color: gridColor },
			},
		},
		plugins: {
			legend: { position: "bottom" as const, labels: { color: textColor, usePointStyle: true, boxWidth: 8 } },
			tooltip: {
				backgroundColor: isDark.value ? "rgba(17, 24, 39, 0.9)" : "rgba(255, 255, 255, 0.9)",
				titleColor: isDark.value ? "#f3f4f6" : "#111827",
				bodyColor: isDark.value ? "#d1d5db" : "#374151",
				borderColor: gridColor, borderWidth: 1, padding: 12,
			},
		},
	};
});
</script>
