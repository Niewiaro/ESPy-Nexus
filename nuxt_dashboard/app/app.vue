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

const config = useRuntimeConfig();
const { locale, t } = useI18n();

useSeoMeta({
	// basic
	description: () => t("seo.description"),

	// og
	ogTitle: () => t("seo.title"),
	ogDescription: () => t("seo.descriptionLong"),
	ogSiteName: config.public.appName,
	ogType: "website",
	ogImage: "/og-image.png",

	// X
	twitterCard: "summary_large_image",

	// other
	author: "Jakub Niewiarowski",
	themeColor: "#0f172a",
});

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
