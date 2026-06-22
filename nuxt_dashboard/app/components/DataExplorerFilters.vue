<template>
	<UAccordion
		:items="accordionItems"
		type="multiple"
		:default-value="['tests', 'presets', 'metric']"
		class="w-full"
	>
		<template #tests>
			<div class="max-h-72 overflow-y-auto p-1 mt-1 mb-2">
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
			<div class="flex flex-col gap-4 my-3 px-1">
				<div class="grid grid-cols-2 gap-2">
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
					<UButton
						label="Losowe (5)"
						icon="i-heroicons-sparkles"
						color="warning"
						variant="subtle"
						class="justify-center col-span-2"
						@click="randomizeSelection"
					/>
				</div>

				<USeparator class="opacity-50" />

				<div>
					<div class="text-xs font-semibold text-muted uppercase tracking-wider mb-2 px-1">
						Tylko protokół
					</div>
					<div class="grid grid-cols-2 gap-2">
						<UButton
							v-for="protocol in availableProtocols"
							:key="protocol"
							:label="protocol"
							icon="i-heroicons-funnel"
							color="info"
							variant="soft"
							class="justify-center"
							@click="selectByProtocol(protocol as string)"
						/>
					</div>
				</div>
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
	availableTests, availableMetrics, availableProtocols,
	selectedTests, selectedMetric,
	selectAllTests, clearAllTests, randomizeSelection, selectByProtocol,
} = useAnalytics();

const accordionItems = [
	{ label: "Wybór testów", icon: "i-heroicons-beaker", value: "tests", slot: "tests" },
	{ label: "Metryka (Oś Y)", icon: "i-heroicons-chart-bar-square", value: "metric", slot: "metric" },
	{ label: "Szybkie filtry", icon: "i-heroicons-bolt", value: "presets", slot: "presets" },
];
</script>
