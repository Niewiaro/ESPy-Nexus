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
	ogDescription: "Profesjonalne narzędzie analityczne do zastosowań Hardware-in-the-Loop. Przeglądaj znormalizowane wyniki pomiarów PDR, Jittera, Goodputu i wielu innych parametrów.",
	author: "Jakub Niewiarowski",
	themeColor: "#0f172a",
});

const { locale } = useI18n();

const i18nHead = useLocaleHead({ seo: true });

useHead(() => ({
	htmlAttrs: {
		lang: i18nHead.value.htmlAttrs!.lang,
		dir: i18nHead.value.htmlAttrs!.dir,
	},
	link: [...(i18nHead.value.link || [])],
	meta: [...(i18nHead.value.meta || [])],
}));
</script>
