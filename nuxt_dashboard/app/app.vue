<template>
	<UApp :locale="locales[locale]">
		<NuxtRouteAnnouncer />

		<AppHeader />

		<UMain>
			<NuxtLayout>
				<NuxtPage />
			</NuxtLayout>
		</UMain>

		<AppFooter />
	</UApp>
</template>

<script setup lang="ts">
import * as locales from "@nuxt/ui/locale";

useSeoMeta({
	description: "Profesjonalna platforma analityczna dla testów Hardware-in-the-Loop na mikrokontrolerach ESP32.",
	ogType: "website",
	ogImage: "/og-image.png",
	ogTitle: "Platforma Analityczna | ESPy-Nexus",
	ogDescription: "Przeglądaj znormalizowane wyniki pomiarów PDR, Jittera i Goodputu. Profesjonalne narzędzie analityczne do zastosowań Hardware-in-the-Loop.",
	author: "Jakub Niewiarowski",
	themeColor: "#0f172a",
});

const { locale } = useI18n();

const lang = computed(() => locales[locale.value].code);
const dir = computed(() => locales[locale.value].dir);

useHead({
	htmlAttrs: {
		lang,
		dir,
	},
});
</script>
