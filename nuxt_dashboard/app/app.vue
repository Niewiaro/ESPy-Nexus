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

const { locale, t } = useI18n();

useSeoMeta({
	description: () => t("seo.description"),
	ogTitle: () => t("seo.title"),
	ogDescription: () => t("seo.descriptionLong"),
	ogType: "website",
	ogImage: "/og-image.png",
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
