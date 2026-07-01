<template>
	<div class="relative overflow-hidden bg-gray-50 dark:bg-gray-900 border-b border-gray-300 dark:border-gray-800">
		<div
			class="absolute inset-0
    bg-[linear-gradient(to_right,#e5e7eb_1px,transparent_1px),linear-gradient(to_bottom,#e5e7eb_1px,transparent_1px)]
    dark:bg-[linear-gradient(to_right,#1f2937_1px,transparent_1px),linear-gradient(to_bottom,#1f2937_1px,transparent_1px)]
    bg-size-[24px_24px]
    mask-[linear-gradient(to_bottom,white,transparent)]
    [-webkit-mask-image:linear-gradient(to_bottom,white,transparent)]"
		/>
		<UContainer class="relative pt-16 pb-20 sm:pt-24 sm:pb-28">
			<div class="flex flex-col items-center text-center gap-8">
				<!-- Headline / Badge -->
				<UBadge
					color="primary"
					variant="subtle"
					size="md"
					class="rounded-full px-4 py-1.5 font-medium"
				>
					<UIcon
						name="i-heroicons-cpu-chip"
						class="w-4 h-4 mr-2"
					/>
					Hardware in the Loop Analytics
				</UBadge>

				<h1 class="text-4xl sm:text-6xl font-extrabold tracking-tight text-gray-900 dark:text-white max-w-4xl">
					Eksploruj wyniki testów z <span class="text-primary">niespotykaną precyzją</span>
				</h1>

				<p class="text-lg sm:text-xl text-gray-600 dark:text-gray-300 max-w-2xl">
					Interaktywny dashboard do analizy telemetrii sieciowej. Porównuj wydajność topologii <span class="font-semibold text-gray-800 dark:text-gray-200">AP i STA</span>, analizuj opóźnienia, Jitter oraz PDR w czasie rzeczywistym.
				</p>

				<div class="flex flex-wrap items-center justify-center gap-4 mt-4">
					<UButton
						label="Zacznij analizę"
						icon="i-heroicons-chart-bar"
						size="lg"
						color="primary"
						variant="solid"
						@click="scrollToDashboard"
					/>
					<UButton
						label="Tabela surowych danych"
						icon="i-heroicons-table-cells"
						size="lg"
						color="neutral"
						variant="outline"
						to="/data"
					/>
				</div>

				<div class="mt-12 grid grid-cols-2 sm:grid-cols-3 gap-4 sm:gap-8 pt-8 border-t border-gray-200/80 dark:border-gray-800/80 text-center w-full max-w-3xl">
					<div class="flex flex-col gap-1">
						<span class="text-3xl font-bold text-gray-900 dark:text-white">
							<AnimatedCounter :value="availableTests.length" />
						</span>
						<span class="text-xs font-medium text-gray-500 uppercase tracking-wider">Serie Testów</span>
					</div>
					<div class="flex flex-col gap-1">
						<span class="text-3xl font-bold text-gray-900 dark:text-white">
							<AnimatedCounter :value="availableProtocols.length" />
						</span>
						<span class="text-xs font-medium text-gray-500 uppercase tracking-wider">Protokoły</span>
					</div>
					<div class="flex flex-col gap-1">
						<span class="text-3xl font-bold text-gray-900 dark:text-white">
							<AnimatedCounter :value="availableTopologies.length" />
						</span>
						<span class="text-xs font-medium text-gray-500 uppercase tracking-wider">Topologie</span>
					</div>

					<div class="flex flex-col gap-1">
						<span class="text-3xl font-bold text-gray-900 dark:text-white">
							<AnimatedCounter :value="data.length" />
						</span>
						<span class="text-xs font-medium text-gray-500 uppercase tracking-wider">Scenariusze</span>
					</div>

					<div class="flex flex-col gap-1">
						<span class="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">
							<AnimatedCounter :value="hzRange.min" />-<AnimatedCounter :value="hzRange.max" />
							<span class="text-base sm:text-lg font-semibold ml-0.5">Hz</span>
						</span>
						<span class="text-xs font-medium text-gray-500 uppercase tracking-wider">Zakres analizy</span>
					</div>

					<div class="flex flex-col gap-1">
						<span class="text-3xl font-bold text-gray-900 dark:text-white">
							<AnimatedCounter :value="totalPackets" />
						</span>
						<span class="text-xs font-medium text-gray-500 uppercase tracking-wider">Przesłane pakiety</span>
					</div>
				</div>
			</div>
		</UContainer>
	</div>
</template>

<script setup lang="ts">
const { availableTests, availableProtocols, availableTopologies, data, hzRange, totalPackets } = useAnalytics();

const scrollToDashboard = () => {
	document.getElementById("dashboard-section")?.scrollIntoView({ behavior: "smooth" });
};
</script>
