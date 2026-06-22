<script setup lang="ts">
const config = useRuntimeConfig();
</script>

<template>
	<UHeader>
		<template #title>
			<div class="flex items-center gap-2.5">
				<img
					src="/favicon.svg"
					:alt="`Logo ${config.public.appName}`"
					class="w-7 h-7"
				>
				<span class="font-bold text-lg tracking-tight">{{ config.public.appName }}</span>
			</div>
		</template>

		<template #right>
			<UColorModeButton />

			<UButton
				color="neutral"
				variant="ghost"
				:to="config.public.gitURL"
				target="_blank"
				icon="i-simple-icons-github"
				aria-label="GitHub"
			/>
		</template>
	</UHeader>
</template>
