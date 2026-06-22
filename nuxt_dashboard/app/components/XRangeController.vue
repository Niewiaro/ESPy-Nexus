<template>
	<UCard
		title="Zakres częstotliwości (Oś X)"
		description="Dostosuj widoczny zakres częstotliwości na wykresie."
	>
		<template #footer>
			<div class="flex justify-end">
				<UButton
					label="Resetuj zakres"
					icon="i-heroicons-arrow-path"
					color="neutral"
					variant="ghost"
					size="sm"
					@click="resetRange"
				/>
			</div>
		</template>

		<div class="flex flex-col gap-6">
			<USlider
				v-model="selectedXRange"
				:min="xRangeLimit[0]"
				:max="xRangeLimit[1]"
				tooltip
			/>

			<div class="flex items-center gap-4">
				<UFormField
					label="Min. [Hz]"
					class="flex-1"
				>
					<UInputNumber
						v-model="selectedXRange[0]"
						:min="xRangeLimit[0]"
						:max="selectedXRange[1]"
						size="sm"
					/>
				</UFormField>

				<span class="text-muted mt-6">-</span>

				<UFormField
					label="Max. [Hz]"
					class="flex-1"
				>
					<UInputNumber
						v-model="selectedXRange[1]"
						:min="selectedXRange[0]"
						:max="xRangeLimit[1]"
						size="sm"
					/>
				</UFormField>
			</div>
		</div>
	</UCard>
</template>

<script setup lang="ts">
const { xRangeLimit, selectedXRange } = useAnalytics();

const resetRange = () => {
	selectedXRange.value = [...xRangeLimit.value];
};
</script>
