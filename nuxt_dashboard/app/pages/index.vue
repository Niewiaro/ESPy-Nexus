<template>
	<div>
		<AppHero />

		<UContainer
			id="dashboard-section"
			class="py-24"
		>
			<div class="grid grid-cols-1 lg:grid-cols-7 gap-8 items-start">
				<div class="lg:col-span-2 flex flex-col gap-4">
					<UCard class="border border-muted shadow-sm">
						<template #header>
							<div class="flex items-center gap-2 font-bold text-highlighted tracking-tight">
								<UIcon
									name="heroicons:adjustments-horizontal-solid"
									class="w-5 h-5 text-primary"
								/>
								{{ t('home.hilParameters') }}
							</div>
						</template>
						<DataExplorerFilters />
					</UCard>
				</div>

				<div class="lg:col-span-5 flex flex-col gap-6">
					<UCard
						class="w-full flex flex-col border border-muted shadow-sm"
						:ui="{ body: 'flex-1 p-2 sm:p-4' }"
					>
						<template #header>
							<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
								<div class="flex items-center gap-4">
									<h2 class="flex items-center gap-2 font-bold text-highlighted text-lg tracking-tight">
										<UIcon
											name="heroicons:presentation-chart-line-solid"
											class="w-6 h-6 text-primary"
										/>
										{{ t('home.frequencyResponse') }}
									</h2>
									<UBadge
										v-if="selectedMetric"
										color="secondary"
										variant="soft"
										size="md"
										class="font-mono uppercase tracking-widest shadow-sm"
									>
										{{ selectedMetric }}
									</UBadge>
								</div>

								<UButton
									icon="heroicons:arrows-pointing-out-solid"
									color="neutral"
									variant="ghost"
									size="sm"
									@click="() => { isFullscreenModalOpen = true }"
								>
									{{ t('home.fullscreen') }}
								</UButton>
							</div>
						</template>

						<div class="w-full flex flex-col bg-default rounded-md">
							<DynamicLineChart v-if="!isFullscreenModalOpen" />
						</div>
					</UCard>

					<XRangeController />
				</div>
			</div>
		</UContainer>

		<UModal
			v-model:open="isFullscreenModalOpen"
			fullscreen
			:title="t('home.fullscreenModalTitle')"
			:ui="{ body: 'flex flex-col flex-1 min-h-0 bg-default p-4' }"
		>
			<template #body>
				<DynamicLineChart v-if="isFullscreenModalOpen" />
			</template>
		</UModal>
	</div>
</template>

<script setup lang="ts">
const { t } = useI18n();

useSeoMeta({
	title: () => t("seo.title"),
	description: () => t("seo.description"),
});

const { selectedMetric } = useAnalytics();

const isFullscreenModalOpen = ref(false);
</script>
