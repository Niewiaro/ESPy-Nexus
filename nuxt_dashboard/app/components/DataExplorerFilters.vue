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
			<div class="flex flex-col gap-4 my-3 px-1 max-h-[60vh] overflow-y-auto scrollbar-thin">
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

				<USeparator class="opacity-40" />

				<div>
					<div class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2 px-1">
						Tylko protokół
					</div>
					<div class="grid grid-cols-2 gap-2">
						<UButton
							v-for="protocol in availableProtocols"
							:key="protocol"
							:label="protocol"
							icon="i-heroicons-globe-alt"
							color="info"
							variant="soft"
							class="justify-center"
							@click="selectByProtocol(protocol as string)"
						/>
					</div>
				</div>

				<USeparator class="opacity-40" />

				<div>
					<div class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2 px-1">
						Tylko topologia
					</div>
					<div class="grid grid-cols-2 gap-2">
						<UButton
							v-for="topology in availableTopologies"
							:key="topology"
							:label="topology as string"
							icon="i-heroicons-share"
							color="success"
							variant="soft"
							class="justify-center"
							@click="selectByTopology(topology as string)"
						/>
					</div>
				</div>

				<USeparator class="opacity-40" />

				<div>
					<div class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2 px-1">
						Tylko rozmiar paczki
					</div>
					<div class="grid grid-cols-3 gap-2">
						<UButton
							v-for="payload in availablePayloads"
							:key="payload"
							:label="`${payload}B`"
							icon="i-heroicons-cube"
							color="error"
							variant="soft"
							class="justify-center"
							@click="selectByPayload(payload as number)"
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
	availableTests, availableMetrics, availableProtocols, availableTopologies, availablePayloads,
	selectedTests, selectedMetric,
	selectAllTests, clearAllTests, randomizeSelection, selectByProtocol,
	selectByTopology, selectByPayload,
} = useAnalytics();

const accordionItems = [
	{ label: "Wybór testów", icon: "i-heroicons-beaker", value: "tests", slot: "tests" },
	{ label: "Metryka (Oś Y)", icon: "i-heroicons-chart-bar-square", value: "metric", slot: "metric" },
	{ label: "Szybkie filtry", icon: "i-heroicons-bolt", value: "presets", slot: "presets" },
];
</script>
