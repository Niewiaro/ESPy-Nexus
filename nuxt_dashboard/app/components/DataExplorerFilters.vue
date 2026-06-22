<template>
	<UAccordion
		:items="accordionItems"
		type="multiple"
		:default-value="['tests', 'presets', 'metric']"
		class="w-full"
	>
		<template #tests>
			<div class="max-h-80 overflow-y-auto p-1 mt-1 mb-2">
				<UCheckboxGroup
					v-model="selectedTests"
					:items="availableTests"
					variant="table"
					size="sm"
					color="primary"
				/>
			</div>
		</template>

		<template #presets>
			<div class="grid grid-cols-2 gap-2 my-2 p-1">
				<UButton
					label="Wszystkie"
					icon="i-heroicons-check-circle"
					color="primary"
					variant="soft"
					class="justify-center"
					@click="selectAllTests"
				/>
				<UButton
					label="Żadne"
					icon="i-heroicons-x-circle"
					color="neutral"
					variant="outline"
					class="justify-center"
					@click="clearAllTests"
				/>
			</div>
		</template>

		<template #metric>
			<div class="my-2 p-1">
				<USelectMenu
					v-model="selectedMetric"
					:items="availableMetrics"
					searchable
					placeholder="np. jitter_mean_iat_us"
					class="w-full"
				/>
			</div>
		</template>
	</UAccordion>
</template>

<script setup lang="ts">
const {
	availableTests, availableMetrics, selectedTests, selectedMetric,
	selectAllTests, clearAllTests,
} = useAnalytics();

const accordionItems = [
	{ label: "Wybór testów (Serie)", icon: "i-heroicons-beaker", value: "tests", slot: "tests" },
	{ label: "Metryka (Oś Y)", icon: "i-heroicons-chart-bar-square", value: "metric", slot: "metric" },
	{ label: "Szybkie presety", icon: "i-heroicons-bolt", value: "presets", slot: "presets" },
];
</script>
