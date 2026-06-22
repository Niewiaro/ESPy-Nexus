<template>
	<div>
		<AppHero />

		<UContainer
			id="dashboard-section"
			class="py-24"
		>
			<div class="grid grid-cols-1 lg:grid-cols-7 gap-6 items-start">
				<div class="lg:col-span-2 flex flex-col gap-4">
					<UCard>
						<template #header>
							<div class="flex items-center gap-2 font-semibold text-muted text-sm">
								<UIcon
									name="i-heroicons-adjustments-horizontal"
									class="w-5 h-5"
								/>
								Konfiguracja widoku
							</div>
						</template>
						<DataExplorerFilters />
					</UCard>
				</div>

				<div class="lg:col-span-5 flex flex-col gap-6">
					<UCard
						class="w-full flex flex-col"
						:ui="{ body: 'flex-1' }"
					>
						<template #header>
							<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
								<div class="flex items-center gap-4">
									<h2 class="flex items-center gap-2 font-semibold text-primary text-base">
										<UIcon
											name="i-heroicons-chart-bar"
											class="w-7 h-7"
										/>
										Wykres liniowy
									</h2>
									<UBadge
										v-if="selectedMetric"
										color="secondary"
										variant="soft"
										size="lg"
									>
										{{ selectedMetric }}
									</UBadge>
								</div>

								<UButton
									icon="i-heroicons-arrows-pointing-out"
									color="neutral"
									variant="ghost"
									size="sm"
									@click="isFullscreenModalOpen = true"
								>
									Pełny ekran
								</UButton>
							</div>
						</template>

						<div class="h-full flex flex-col">
							<DynamicLineChart />
						</div>
					</UCard>

					<XRangeController />
				</div>
			</div>
		</UContainer>

		<UModal
			v-model:open="isFullscreenModalOpen"
			fullscreen
			title="Analiza wykresu - Widok pełnoekranowy"
			:ui="{ body: 'flex flex-col flex-1 min-h-0' }"
		>
			<template #body>
				<DynamicLineChart />
			</template>
		</UModal>
	</div>
</template>

<script setup lang="ts">
const { selectedMetric } = useAnalytics();

const isFullscreenModalOpen = ref(false);
</script>
