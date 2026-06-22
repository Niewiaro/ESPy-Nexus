<template>
	<div>
		<AppHero />

		<UContainer
			id="dashboard-section"
			class="py-24"
		>
			<div class="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
				<div class="lg:col-span-1 flex flex-col gap-4">
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

				<div class="lg:col-span-3 flex flex-col gap-6">
					<UCard class="w-full">
						<template #header>
							<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
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
						</template>
						<div class="p-1 sm:p-2">
							<DynamicLineChart />
						</div>
					</UCard>

					<XRangeController />
				</div>
			</div>
		</UContainer>
	</div>
</template>

<script setup lang="ts">
const { selectedMetric } = useAnalytics();
</script>
