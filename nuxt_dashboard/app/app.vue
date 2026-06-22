<template>
	<UApp>
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
const config = useRuntimeConfig();

useSeoMeta({
	ogImage: config.public.appURL + "/og-image.png",
	twitterCard: "summary_large_image",
	themeColor: "#3b82f6",
});
</script>
