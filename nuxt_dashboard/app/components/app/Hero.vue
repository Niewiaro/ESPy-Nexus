<script setup lang="ts">
import type { ButtonProps } from "@nuxt/ui";

const config = useRuntimeConfig();

const links = ref<ButtonProps[]>([
	{
		label: "Rozpocznij analizę",
		icon: "i-heroicons-chart-bar",
		size: "lg",
		onClick: () => {
			document.getElementById("dashboard-section")?.scrollIntoView({ behavior: "smooth" });
		},
	},
	{
		label: "Kod źródłowy",
		to: config.public.gitRepoURL,
		target: "_blank",
		color: "neutral",
		variant: "subtle",
		size: "lg",
		trailingIcon: "i-simple-icons-github",
	},
]);
</script>

<template>
	<UPageHero
		headline="Hardware-in-the-Loop"
		:title="config.public.appName"
		description="Interaktywna analiza i porównywanie wyników testów sieciowych z systemów ESP32 i Python. Filtruj dane, porównuj metryki i wyciągaj wnioski w czasie rzeczywistym."
		:links="links"
	/>
</template>
