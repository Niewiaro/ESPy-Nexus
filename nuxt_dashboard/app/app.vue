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
useSeoMeta({
	description: "Profesjonalna platforma analityczna dla testów Hardware-in-the-Loop na mikrokontrolerach ESP32.",
	ogType: "website",
	ogImage: "/og-image.png",
	ogTitle: "Platforma Analityczna | ESPy-Nexus",
	ogDescription: "Przeglądaj znormalizowane wyniki pomiarów PDR, Jittera i Goodputu. Profesjonalne narzędzie analityczne do zastosowań Hardware-in-the-Loop.",
	author: "Jakub Niewiarowski",
	themeColor: "#0f172a",
});
</script>
