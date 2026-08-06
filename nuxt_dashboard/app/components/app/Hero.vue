<template>
	<div class="relative overflow-hidden bg-linear-to-b from-muted/40 to-default border-b border-muted">
		<div class="absolute -top-10 -left-10 w-72 h-72 sm:-top-40 sm:-left-40 sm:w-125 sm:h-125 bg-primary/20 rounded-full blur-[80px] sm:blur-[120px] pointer-events-none animate-float-slow" />
		<div class="absolute top-40 -right-10 w-72 h-72 sm:top-20 sm:-right-40 sm:w-125 sm:h-125 bg-secondary/20 rounded-full blur-[80px] sm:blur-[120px] pointer-events-none animate-float-slower" />

		<div
			class="absolute inset-0 z-0
                   bg-[linear-gradient(to_right,var(--ui-border-muted)_1px,transparent_1px),linear-gradient(to_bottom,var(--ui-border-muted)_1px,transparent_1px)]
                   bg-size-[24px_24px] opacity-40
                   mask-[linear-gradient(to_bottom,white,transparent)]
                   [-webkit-mask-image:linear-gradient(to_bottom,white,transparent)]"
		/>

		<UContainer class="relative z-10 pt-16 pb-20 sm:pt-24 sm:pb-28">
			<div class="flex flex-col items-center text-center gap-8">
				<UBadge
					color="secondary"
					variant="subtle"
					size="md"
					class="rounded-full px-4 py-1.5 font-medium border border-secondary/30 shadow-sm"
				>
					<UIcon
						name="heroicons:cpu-chip-solid"
						class="w-4 h-4 mr-2 animate-pulse"
					/>
					Mikrosekundowa analityka Hardware-in-the-Loop
				</UBadge>

				<h1 class="text-4xl sm:text-6xl font-extrabold tracking-tight text-highlighted max-w-4xl leading-tight">
					Rygorystyczne badanie stabilności <br class="hidden sm:block">
					<span class="bg-linear-to-r from-primary to-secondary bg-clip-text text-transparent pb-1">
						systemów wbudowanych
					</span>
				</h1>

				<p class="text-lg sm:text-xl text-muted max-w-3xl leading-relaxed px-2 sm:px-0">
					Platforma analizująca determinizm komunikacyjny między komputerem PC (GPOS) a mikrokontrolerem ESP32 (RTOS).
					Obserwuj <span class="font-semibold text-toned">mikro-zawieszenia planisty</span>, oceniaj asymetryczny <span class="font-semibold text-toned">Jitter</span> i weryfikuj wydajność radiową dla krytycznych aplikacji sterowania.
				</p>

				<div class="flex flex-wrap items-center justify-center gap-4 mt-6">
					<UButton
						label="Zacznij analizę HIL"
						icon="heroicons:chart-bar-square"
						size="xl"
						color="primary"
						variant="solid"
						@click="scrollToDashboard"
					/>
					<UButton
						label="Przegląd logów"
						icon="heroicons:table-cells"
						size="xl"
						color="neutral"
						variant="outline"
						to="/data"
					/>
				</div>

				<div class="mt-16 grid grid-cols-2 sm:grid-cols-3 gap-y-10 gap-x-4 sm:gap-x-8 pt-10 border-t border-muted/60 text-center w-full max-w-4xl">
					<div class="flex flex-col gap-1.5">
						<span class="text-2xl sm:text-3xl font-bold text-highlighted">
							<AnimatedCounter :value="availableTests.length" />
						</span>
						<span class="text-[10px] sm:text-xs font-semibold text-dimmed uppercase tracking-wider">Iteracje Testowe</span>
					</div>

					<div class="flex flex-col gap-1.5">
						<span class="text-2xl sm:text-3xl font-bold text-highlighted">
							<AnimatedCounter :value="availableProtocols.length" />
						</span>
						<span class="text-[10px] sm:text-xs font-semibold text-dimmed uppercase tracking-wider">Transport</span>
					</div>

					<div class="flex flex-col gap-1.5">
						<span class="text-2xl sm:text-3xl font-bold text-highlighted">
							<AnimatedCounter :value="availableTopologies.length" />
						</span>
						<span class="text-[10px] sm:text-xs font-semibold text-dimmed uppercase tracking-wider">Topologie</span>
					</div>

					<div class="flex flex-col gap-1.5">
						<span class="text-2xl sm:text-3xl font-bold text-highlighted">
							<AnimatedCounter :value="data.length" />
						</span>
						<span class="text-[10px] sm:text-xs font-semibold text-dimmed uppercase tracking-wider">Scenariusze</span>
					</div>

					<div class="flex flex-col gap-1.5">
						<span class="text-xl sm:text-3xl font-bold text-highlighted flex justify-center items-baseline gap-1">
							<AnimatedCounter :value="hzRange.min" /> - <AnimatedCounter :value="hzRange.max" />
							<span class="text-sm sm:text-lg font-semibold text-secondary">Hz</span>
						</span>
						<span class="text-[10px] sm:text-xs font-semibold text-dimmed uppercase tracking-wider">Próbkowanie</span>
					</div>

					<div class="flex flex-col gap-1.5">
						<span class="text-2xl sm:text-3xl font-bold text-highlighted">
							<AnimatedCounter :value="totalPackets" />
						</span>
						<span class="text-[10px] sm:text-xs font-semibold text-dimmed uppercase tracking-wider">Przesłane pakiety</span>
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

<style scoped>
@keyframes float {
    0% { transform: translate3d(0, 0, 0) scale(1); }
    33% { transform: translate3d(20px, -30px, 0) scale(1.05); }
    66% { transform: translate3d(-20px, 20px, 0) scale(0.95); }
    100% { transform: translate3d(0, 0, 0) scale(1); }
}

.animate-float-slow {
    animation: float 12s ease-in-out infinite;
}

.animate-float-slower {
    animation: float 16s ease-in-out infinite reverse;
}
</style>
