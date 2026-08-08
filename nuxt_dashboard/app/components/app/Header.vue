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

			<UDrawer>
				<UButton
					icon="heroicons:language"
					color="neutral"
					variant="ghost"
					:aria-label="t('i18n.selectLanguage')"
				/>

				<template #content>
					<div class="flex flex-col gap-3 p-6 max-w-md mx-auto w-full">
						<div class="flex items-center justify-between mb-2">
							<h3 class="text-xl font-semibold text-highlighted">
								{{ t('i18n.selectLanguage') }}
							</h3>
							<div class="rounded-full border border-muted/70 bg-muted/40 px-2.5 py-1 text-[11px] font-medium uppercase tracking-[0.2em] text-dimmed">
								{{ locales.length }}
							</div>
						</div>

						<NuxtLink
							v-for="l in locales"
							:key="l.code"
							:to="switchLocalePath(l.code)"
							class="flex items-center justify-between rounded-xl border px-4 py-3 text-sm transition-all duration-200"
							:class="l.code === locale
								? 'border-primary/30 bg-primary/10 text-highlighted shadow-sm'
								: 'border-muted/70 bg-default/70 text-muted hover:border-primary/20 hover:bg-muted/40 hover:text-highlighted'"
						>
							<div class="flex items-center gap-3">
								<UBadge
									:label="l.code"
									size="md"
									variant="subtle"
									:color="l.code === locale ? 'primary' : 'neutral'"
									class="uppercase tracking-widest font-mono"
								/>

								<span class="text-base font-medium">{{ l.name }}</span>
							</div>

							<UIcon
								v-if="l.code === locale"
								name="heroicons:check"
								class="shrink-0 size-5 text-primary"
							/>
						</NuxtLink>
					</div>
				</template>
			</UDrawer>

			<UButton
				color="neutral"
				variant="ghost"
				:to="config.public.gitURL"
				target="_blank"
				icon="simple-icons:github"
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

const { locale, locales, t } = useI18n();
const switchLocalePath = useSwitchLocalePath();

const navItems = computed<NavigationMenuItem[]>(() => [
	{
		label: t("nav.dashboard"),
		icon: "heroicons:chart-pie",
		to: "/",
		active: route.path === "/" || route.path === "/en",
	},
	{
		label: t("nav.rawData"),
		icon: "heroicons:table-cells",
		to: "/data",
		active: route.path.startsWith("/data") || route.path.startsWith("/en/data"),
	},
]);
</script>
