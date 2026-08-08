<template>
	<UCard class="border border-muted shadow-sm">
		<template #header>
			<div class="flex items-center justify-between">
				<div>
					<h3 class="text-sm font-bold text-highlighted uppercase tracking-wider flex items-center gap-2">
						<UIcon
							name="heroicons:arrows-right-left-solid"
							class="w-4 h-4 text-primary"
						/>
						{{ $t('xRange.title') }}
					</h3>
					<p class="text-xs text-dimmed mt-0.5">
						{{ $t('xRange.description') }}
					</p>
				</div>

				<UButton
					:label="$t('xRange.reset')"
					icon="heroicons:arrow-path"
					color="neutral"
					variant="ghost"
					size="sm"
					@click="resetRange"
				/>
			</div>
		</template>

		<div class="flex flex-col lg:flex-row items-center gap-8 px-2">
			<div class="flex-1 w-full mt-2">
				<USlider
					v-model="selectedXRange"
					:min="xRangeLimit[0]"
					:max="xRangeLimit[1]"
					color="primary"
					:step="10"
				/>
			</div>

			<div class="flex items-center justify-between gap-3 w-full lg:w-auto shrink-0">
				<UFormField :label="$t('xRange.minHz')">
					<UInputNumber
						v-model="selectedXRange[0]"
						:min="xRangeLimit[0]"
						:max="selectedXRange[1]"
						size="sm"
						class="w-28 font-mono text-center"
						color="secondary"
					/>
				</UFormField>

				<span class="text-muted mt-6 font-bold">-</span>

				<UFormField :label="$t('xRange.maxHz')">
					<UInputNumber
						v-model="selectedXRange[1]"
						:min="selectedXRange[0]"
						:max="xRangeLimit[1]"
						size="sm"
						class="w-28 font-mono text-center"
						color="secondary"
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
