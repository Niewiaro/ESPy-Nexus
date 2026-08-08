<template>
	<div class="flex flex-col gap-4 w-full h-full flex-1 min-h-150">
		<div
			v-if="chartData.datasets.length"
			class="flex flex-wrap justify-end gap-6 px-4"
		>
			<UCheckbox
				v-model="isLogX"
				name="logX"
				:label="$t('chart.axes.logX')"
				color="primary"
			/>
			<UCheckbox
				v-model="isLogY"
				name="logY"
				:label="$t('chart.axes.logY')"
				color="secondary"
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
				class="flex flex-col h-full items-center justify-center text-dimmed border-2 border-dashed border-muted rounded-xl p-6 text-center bg-muted/10"
			>
				<UIcon
					name="heroicons:presentation-chart-line"
					class="w-12 h-12 mb-3 opacity-40"
				/>
				<span class="font-semibold text-toned text-lg">{{ $t('chart.emptyState.title') }}</span>
				<span class="text-sm mt-1 max-w-sm">
					{{ $t('chart.emptyState.description') }}
				</span>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Line } from "vue-chartjs";
import {
	Chart,
	Interaction,
	CategoryScale,
	LinearScale,
	LogarithmicScale,
	PointElement,
	LineElement,
	Title,
	Tooltip,
	Legend,
} from "chart.js";
import type {
	InteractionOptions,
	Chart as ChartJS,
	ChartOptions,
	ChartEvent,
	ActiveElement,
} from "chart.js";

declare module "chart.js" {
	interface InteractionModeMap {
		hilMode: (chart: ChartJS, e: ChartEvent, options: InteractionOptions, useFinalPosition?: boolean) => ActiveElement[];
	}
}

const MAX_TOOLTIP_DISTANCE_Y = 20;
const TOOLTIP_OVERLAP_TOLERANCE_Y = 5;

Interaction.modes.hilMode = function (
	chart: ChartJS,
	e: ChartEvent,
	options: InteractionOptions,
	useFinalPosition?: boolean,
): ActiveElement[] {
	const indexItems = Interaction.modes.index(chart, e, options, useFinalPosition);
	if (!indexItems || indexItems.length === 0) return [];

	let minDistanceY = Number.POSITIVE_INFINITY;

	const eventY = e.y ?? 0;

	indexItems.forEach((item: ActiveElement) => {
		const distanceY = Math.abs(item.element.y - eventY);
		if (distanceY < minDistanceY) {
			minDistanceY = distanceY;
		}
	});

	if (minDistanceY > MAX_TOOLTIP_DISTANCE_Y) return [];

	return indexItems.filter((item: ActiveElement) => {
		const distanceY = Math.abs(item.element.y - eventY);
		return Math.abs(distanceY - minDistanceY) <= TOOLTIP_OVERLAP_TOLERANCE_Y;
	});
};

Chart.register(
	CategoryScale, LinearScale, LogarithmicScale,
	PointElement, LineElement, Title, Tooltip, Legend,
);

const { chartData, selectedMetric, isLogX, isLogY } = useAnalytics();
const { t } = useI18n();
const colorMode = useColorMode();
const isDark = computed(() => colorMode.value === "dark");

const chartOptions = computed<ChartOptions<"line">>(() => {
	const textColor = isDark.value ? "#94a3b8" : "#475569";
	const gridColor = isDark.value ? "#334155" : "#e2e8f0";
	const tooltipBg = isDark.value ? "rgba(15, 23, 42, 0.95)" : "rgba(255, 255, 255, 0.95)";
	const tooltipText = isDark.value ? "#f8fafc" : "#0f172a";
	const tooltipBorder = isDark.value ? "#475569" : "#cbd5e1";

	return {
		responsive: true,
		maintainAspectRatio: false,
		interaction: {
			mode: "hilMode",
			intersect: false,
		},
		elements: {
			point: { radius: 1.414, hitRadius: 8, hoverRadius: 7 },
			line: { borderWidth: 2, cubicInterpolationMode: "monotone" },
		},
		scales: {
			x: {
				type: isLogX.value ? "logarithmic" : "linear",
				title: { display: true, text: t("chart.axisLabels.frequencyHz"), color: textColor, font: { weight: "bold", family: "system-ui" } },
				ticks: { color: textColor, font: { family: "monospace" } },
				grid: { color: gridColor },
			},
			y: {
				type: isLogY.value ? "logarithmic" : "linear",
				title: { display: !!selectedMetric.value, text: selectedMetric.value || "", color: textColor, font: { weight: "bold", family: "system-ui" } },
				ticks: { color: textColor, font: { family: "monospace" } },
				grid: { color: gridColor },
			},
		},
		plugins: {
			legend: {
				position: "bottom" as const,
				labels: { color: textColor, usePointStyle: true, boxWidth: 8, font: { family: "system-ui" } },
			},
			tooltip: {
				backgroundColor: tooltipBg,
				titleColor: tooltipText,
				bodyColor: tooltipText,
				borderColor: tooltipBorder,
				borderWidth: 1,
				padding: 12,
				cornerRadius: 8,
				titleFont: { family: "system-ui", size: 14, weight: "bold" },
				bodyFont: { family: "monospace", size: 13 },
				itemSort: (a, b) => (b.parsed.y ?? 0) - (a.parsed.y ?? 0),
			},
		},
	};
});
</script>
