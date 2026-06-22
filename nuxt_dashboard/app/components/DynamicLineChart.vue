<template>
	<div class="flex flex-col gap-4 h-full w-full">
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

		<div class="h-[450px] w-full relative">
			<Line
				v-if="chartData.datasets.length"
				:data="chartData"
				:options="chartOptions"
			/>

			<div
				v-else
				class="flex h-full items-center justify-center text-gray-500 border-2 border-dashed border-gray-200 dark:border-gray-800 rounded-lg p-6 text-center"
			>
				Wybierz co najmniej jeden test i metrykę w panelu bocznym, aby wygenerować wykres...
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { Line } from "vue-chartjs";
import {
	Chart as ChartJS,
	CategoryScale,
	LinearScale,
	LogarithmicScale,
	PointElement,
	LineElement,
	Title,
	Tooltip,
	Legend,
	type ChartOptions,
} from "chart.js";

// Rejestrujemy komponenty Chart.js
ChartJS.register(
	CategoryScale,
	LinearScale,
	LogarithmicScale,
	PointElement,
	LineElement,
	Title,
	Tooltip,
	Legend,
);

// Pobieramy dane analityczne
const { chartData, selectedMetric } = useAnalytics();

// Pobieramy informację o aktualnym motywie z Nuxt UI
const colorMode = useColorMode();
const isDark = computed(() => colorMode.value === "dark");

// Sterowanie skalami
const isLogX = ref(false);
const isLogY = ref(false);

// Dynamiczna konfiguracja wykresu reagująca na zmianę motywu i skali
const chartOptions = computed<ChartOptions<"line">>(() => {
	// Definiujemy kolory siatki i tekstu zależne od Dark Mode
	const textColor = isDark.value ? "#9ca3af" : "#4b5563"; // gray-400 : gray-600
	const gridColor = isDark.value ? "#374151" : "#e5e7eb"; // gray-700 : gray-200

	return {
		responsive: true,
		maintainAspectRatio: false,

		// Interakcje i wygląd samej linii
		interaction: {
			mode: "index",
			intersect: false,
		},
		elements: {
			point: {
				radius: 2, // Mniejsze kropeczki domyślnie
				hoverRadius: 6, // Powiększają się, gdy najedziemy myszką
			},
			line: {
				borderWidth: 2, // Delikatnie cieńsze, nowoczesne linie
				cubicInterpolationMode: "monotone", // Gładkie krzywe (zgodnie z dokumentacją)
			},
		},

		scales: {
			x: {
				type: isLogX.value ? "logarithmic" : "linear",
				title: {
					display: true,
					text: "Częstotliwość [Hz]",
					color: textColor,
					font: { weight: "bold" },
				},
				ticks: { color: textColor },
				grid: { color: gridColor },
			},
			y: {
				type: isLogY.value ? "logarithmic" : "linear",
				title: {
					display: !!selectedMetric.value,
					text: selectedMetric.value || "",
					color: textColor,
					font: { weight: "bold" },
				},
				ticks: { color: textColor },
				grid: { color: gridColor },
			},
		},
		plugins: {
			legend: {
				position: "bottom" as const,
				labels: {
					color: textColor,
					usePointStyle: true, // Zmienia kwadraty w legendzie na ładne kółka
					boxWidth: 8,
				},
			},
			tooltip: {
				backgroundColor: isDark.value ? "rgba(17, 24, 39, 0.9)" : "rgba(255, 255, 255, 0.9)", // Tło podpowiedzi
				titleColor: isDark.value ? "#f3f4f6" : "#111827",
				bodyColor: isDark.value ? "#d1d5db" : "#374151",
				borderColor: gridColor,
				borderWidth: 1,
				padding: 12,
			},
		},
	};
});
</script>
