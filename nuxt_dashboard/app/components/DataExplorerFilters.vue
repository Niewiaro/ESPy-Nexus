<template>
	<UAccordion
		:items="accordionItems"
		type="multiple"
		:default-value="['tests', 'presets', 'metric']"
		class="w-full"
	>
		<template #tests>
			<div class="max-h-72 overflow-y-auto p-1 mt-1 mb-2 scrollbar-thin">
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
						:label="$t('dataExplorer.filters.all')"
						icon="heroicons:check-circle"
						color="primary"
						variant="soft"
						class="justify-center"
						@click="selectAllTests"
					/>
					<UButton
						:label="$t('dataExplorer.filters.none')"
						icon="heroicons:x-circle"
						color="neutral"
						variant="outline"
						class="justify-center"
						@click="clearAllTests"
					/>
					<UButton
						:label="$t('dataExplorer.filters.random', { count: 5 })"
						icon="heroicons:sparkles"
						color="warning"
						variant="subtle"
						class="justify-center col-span-2"
						@click="randomizeSelection"
					/>
				</div>

				<USeparator class="opacity-40" />

				<div>
					<div class="text-xs font-semibold text-dimmed uppercase tracking-wider mb-2 px-1">
						{{ $t('dataExplorer.filters.onlyProtocol') }}
					</div>
					<div class="grid grid-cols-2 gap-2">
						<UButton
							v-for="protocol in availableProtocols"
							:key="protocol"
							:label="protocol"
							icon="heroicons:globe-alt"
							color="info"
							variant="soft"
							class="justify-center"
							@click="selectByProtocol(protocol as string)"
						/>
					</div>
				</div>

				<USeparator class="opacity-40" />

				<div>
					<div class="text-xs font-semibold text-dimmed uppercase tracking-wider mb-2 px-1">
						{{ $t('dataExplorer.filters.onlyTopology') }}
					</div>
					<div class="grid grid-cols-2 gap-2">
						<UButton
							v-for="topology in availableTopologies"
							:key="topology"
							:label="topology as string"
							icon="heroicons:share"
							color="success"
							variant="soft"
							class="justify-center"
							@click="selectByTopology(topology as string)"
						/>
					</div>
				</div>

				<USeparator class="opacity-40" />

				<div>
					<div class="text-xs font-semibold text-dimmed uppercase tracking-wider mb-2 px-1">
						{{ $t('dataExplorer.filters.onlyPayloadSize') }}
					</div>
					<div class="grid grid-cols-2 gap-2">
						<UButton
							v-for="payload in availablePayloads"
							:key="payload"
							:label="`${payload}B`"
							icon="heroicons:cube"
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
					:placeholder="$t('dataExplorer.filters.metricPlaceholder')"
					class="w-full"
				/>
			</div>
		</template>
	</UAccordion>
</template>

<script setup lang="ts">
const {
	availableTests,
	availableMetrics,
	availableProtocols,
	availableTopologies,
	availablePayloads,
	selectedTests,
	selectedMetric,
	selectAllTests,
	clearAllTests,
	randomizeSelection,
	selectByProtocol,
	selectByTopology,
	selectByPayload,
} = useAnalytics();

const { t } = useI18n();

const accordionItems = [
	{ label: t("dataExplorer.accordion.tests"), icon: "heroicons:beaker", value: "tests", slot: "tests" },
	{ label: t("dataExplorer.accordion.metric"), icon: "heroicons:chart-bar-square", value: "metric", slot: "metric" },
	{ label: t("dataExplorer.accordion.presets"), icon: "heroicons:bolt", value: "presets", slot: "presets" },
];
</script>
