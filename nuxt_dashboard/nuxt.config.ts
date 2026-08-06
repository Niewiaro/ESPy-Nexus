const appName = "ESPy-Nexus";

export default defineNuxtConfig({
	modules: ["@nuxt/eslint", "@nuxt/ui"],
	devtools: { enabled: true },

	app: {
		head: {
			title: appName,
			titleTemplate: `%s - ${appName}`,

			htmlAttrs: {
				lang: "pl",
			},
			meta: [
				{ name: "apple-mobile-web-app-title", content: appName },
			],
			link: [
				{ rel: "icon", type: "image/png", sizes: "96x96", href: "/favicon-96x96.png?v=20260807" },
				{ rel: "icon", type: "image/svg+xml", href: "/favicon.svg?v=20260807" },
				{ rel: "shortcut icon", href: "/favicon.ico?v=20260807" },
				{ rel: "apple-touch-icon", sizes: "180x180", href: "/apple-touch-icon.png?v=20260807" },
				{ rel: "manifest", href: "/site.webmanifest?v=20260807" },
			],
		},
	},

	css: ["~/assets/css/main.css"],

	runtimeConfig: {
		public: {
			appName: appName,
			appURL: "https://espy-nexus.niewiaro.cc",
			gitURL: "https://github.com/Niewiaro",
			gitRepoURL: "https://github.com/Niewiaro/ESPy-Nexus",
			linkedInURL: "https://www.linkedin.com/in/jakub-niewiarowski",
		},
	},
	compatibilityDate: "2026-06-22",

	eslint: {
		config: {
			stylistic: {
				semi: true,
				quotes: "double",
				commaDangle: "always-multiline",
				indent: "tab",
			},
		},
	},
});
