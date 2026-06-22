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

		<UNavigationMenu
			:items="navItems"
			class="hidden md:flex"
		/>

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

		<template #body>
			<UNavigationMenu
				:items="navItems"
				orientation="vertical"
				class="-mx-2.5"
			/>
		</template>
	</UHeader>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import type { NavigationMenuItem } from "@nuxt/ui";

const config = useRuntimeConfig();
const route = useRoute();

const navItems = computed<NavigationMenuItem[]>(() => [
	{
		label: "Dashboard",
		icon: "i-heroicons-chart-pie",
		to: "/",
		active: route.path === "/",
	},
	{
		label: "Surowe Dane",
		icon: "i-heroicons-table-cells",
		to: "/data",
		active: route.path.startsWith("/data"),
	},
]);
</script>
