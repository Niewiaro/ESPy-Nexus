<template>
	<div>
		<div class="relative overflow-hidden bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
			<div class="absolute inset-0 bg-[linear-gradient(to_right,#e5e7eb_1px,transparent_1px),linear-gradient(to_bottom,#e5e7eb_1px,transparent_1px)] dark:bg-[linear-gradient(to_right,#1f2937_1px,transparent_1px),linear-gradient(to_bottom,#1f2937_1px,transparent_1px)] bg-size-[24px_24px] mask-[linear-gradient(to_bottom,white,transparent)] [-webkit-mask-image:linear-gradient(to_bottom,white,transparent)]" />

			<UPageHero
				headline="Baza pomiarów"
				title="Eksplorator Danych"
				description="Przeglądaj, filtruj i przeszukuj surowe wyniki testów sieciowych. Zmieniaj presety widoków, aby skupić się na najważniejszych metrykach."
				:links="[
					{
						label: 'Wróć do wykresów',
						icon: 'i-heroicons-arrow-left',
						to: '/',
						color: 'neutral',
						variant: 'outline',
					},
				]"
				:ui="{
					wrapper: 'relative z-10',
					container: 'py-10 sm:py-14',
				}"
			/>
		</div>

		<UContainer class="py-12">
			<UCard
				class="w-full flex flex-col"
				:ui="{ body: 'p-0 sm:p-0' }"
			>
				<div class="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 border-b border-gray-200 dark:border-gray-800">
					<UInput
						v-model="globalFilter"
						icon="i-heroicons-magnifying-glass"
						placeholder="Szukaj w danych (np. UDP, 1000Hz)..."
						class="w-full sm:max-w-sm"
					/>

					<div class="flex items-center gap-2 w-full sm:w-auto">
						<UDropdownMenu
							:items="presetItems"
							:content="{ align: 'end' }"
						>
							<UButton
								label="Presety widoku"
								color="primary"
								variant="soft"
								icon="i-heroicons-bookmark"
								trailing-icon="i-heroicons-chevron-down"
							/>
						</UDropdownMenu>

						<UDropdownMenu
							:items="table?.tableApi?.getAllColumns().filter(c => c.getCanHide()).map(column => ({
								label: getFriendlyColumnName(column.id),
								type: 'checkbox' as const,
								checked: column.getIsVisible(),
								onUpdateChecked(checked: boolean) {
									table?.tableApi?.getColumn(column.id)?.toggleVisibility(!!checked);
								},
								onSelect(e: Event) { e.preventDefault(); },
							}))"
							:content="{ align: 'end' }"
						>
							<UButton
								label="Widoczność kolumn"
								color="neutral"
								variant="outline"
								icon="i-heroicons-view-columns"
								trailing-icon="i-heroicons-chevron-down"
							/>
						</UDropdownMenu>
					</div>
				</div>

				<div class="overflow-x-auto">
					<UTable
						ref="table"
						v-model:pagination="pagination"
						v-model:global-filter="globalFilter"
						v-model:column-visibility="columnVisibility"
						:data="data"
						:columns="columns"
						:pagination-options="{
							getPaginationRowModel: getPaginationRowModel(),
						}"
						class="flex-1"
					/>
				</div>

				<div class="flex items-center justify-between border-t border-gray-200 dark:border-gray-800 p-4">
					<div class="text-sm text-gray-500">
						Wyświetlanie {{ table?.tableApi?.getRowModel().rows.length || 0 }} z {{ table?.tableApi?.getFilteredRowModel().rows.length || 0 }} wyników
					</div>
					<UPagination
						:page="(table?.tableApi?.getState().pagination.pageIndex || 0) + 1"
						:items-per-page="table?.tableApi?.getState().pagination.pageSize"
						:total="table?.tableApi?.getFilteredRowModel().rows.length"
						@update:page="(p) => table?.tableApi?.setPageIndex(p - 1)"
					/>
				</div>
			</UCard>
		</UContainer>
	</div>
</template>

<script setup lang="ts">
import { h, resolveComponent, ref } from "vue";
import type { TableColumn, DropdownMenuItem } from "@nuxt/ui";
import { getPaginationRowModel } from "@tanstack/vue-table";

const UBadge = resolveComponent("UBadge");

const { data } = useAnalytics();
type HilDataRow = typeof data.value[0];

const table = useTemplateRef("table");
const globalFilter = ref("");
const pagination = ref({ pageIndex: 0, pageSize: 15 });
const columnVisibility = ref<Record<string, boolean>>({});

const metadataColumns: TableColumn<HilDataRow>[] = [
	{ accessorKey: "test_id", header: "ID" },
	{ accessorKey: "protocol", header: "Protokół" },
	{ accessorKey: "router_topology", header: "Topologia" },
	{ accessorKey: "freq_hz", header: "Freq [Hz]", cell: ({ row }) => `${row.getValue("freq_hz")} Hz` },
	{
		accessorKey: "status",
		header: "Status",
		cell: ({ row }) => {
			const status = row.getValue("status") as string;
			return h(UBadge, { variant: "subtle", color: status === "OK" ? "success" : "error" }, () => status);
		},
	},
	{ accessorKey: "payload_b", header: "Payload [B]", cell: ({ row }) => `${row.getValue("payload_b")} B` },
	{ accessorKey: "expected_cnt", header: "Oczekiwane [szt.]" },
];

const normalizedColumns: TableColumn<HilDataRow>[] = [
	{ accessorKey: "pdr_ratio_percent", header: "PDR [%]", cell: ({ row }) => `${Number(row.getValue("pdr_ratio_percent")).toFixed(2)}%` },
	{ accessorKey: "jitter_cv_percent", header: "Jitter CV [%]", cell: ({ row }) => `${Number(row.getValue("jitter_cv_percent")).toFixed(4)}%` },
	{ accessorKey: "goodput_efficiency_percent", header: "Efficiency [%]", cell: ({ row }) => `${Number(row.getValue("goodput_efficiency_percent")).toFixed(2)}%` },
	{ accessorKey: "timing_bloat_percent", header: "Queue Delay [%]", cell: ({ row }) => `${Number(row.getValue("timing_bloat_percent")).toFixed(4)}%` },
];

const rawColumns: TableColumn<HilDataRow>[] = [
	{ accessorKey: "pdr_expected", header: "PDR Expected" },
	{ accessorKey: "pdr_received", header: "PDR Received" },
	{ accessorKey: "pdr_lost", header: "PDR Lost" },
	{ accessorKey: "pdr_mac_dups", header: "MAC Dups" },
	{ accessorKey: "pdr_ghost_dups", header: "Ghost Dups" },
	{ accessorKey: "jitter_expected_iat_us", header: "Jitter Expected IAT [µs]", cell: ({ row }) => Number(row.getValue("jitter_expected_iat_us")).toFixed(2) },
	{ accessorKey: "jitter_mean_iat_us", header: "Jitter Mean IAT [µs]", cell: ({ row }) => Number(row.getValue("jitter_mean_iat_us")).toFixed(2) },
	{ accessorKey: "jitter_err_iat_us", header: "Jitter Err [µs]", cell: ({ row }) => Number(row.getValue("jitter_err_iat_us")).toFixed(4) },
	{ accessorKey: "jitter_std_us", header: "Jitter STD [µs]", cell: ({ row }) => Number(row.getValue("jitter_std_us")).toFixed(2) },
	{ accessorKey: "jitter_max_iat_us", header: "Jitter Max IAT [µs]", cell: ({ row }) => Number(row.getValue("jitter_max_iat_us")).toFixed(2) },
	{ accessorKey: "jitter_min_iat_us", header: "Jitter Min IAT [µs]", cell: ({ row }) => Number(row.getValue("jitter_min_iat_us")).toFixed(2) },
	{ accessorKey: "jitter_max_iat_dev_us", header: "Jitter Max Dev [µs]", cell: ({ row }) => Number(row.getValue("jitter_max_iat_dev_us")).toFixed(2) },
	{ accessorKey: "jitter_min_iat_dev_us", header: "Jitter Min Dev [µs]", cell: ({ row }) => Number(row.getValue("jitter_min_iat_dev_us")).toFixed(2) },
	{ accessorKey: "burst_total_events", header: "Burst Events" },
	{ accessorKey: "burst_max_len", header: "Burst Max Len" },
	{ accessorKey: "burst_max_blackout_ms", header: "Burst Max Blackout [ms]", cell: ({ row }) => Number(row.getValue("burst_max_blackout_ms")).toFixed(2) },
	{ accessorKey: "goodput_bytes_sec", header: "Goodput [B/s]", cell: ({ row }) => Number(row.getValue("goodput_bytes_sec")).toFixed(2) },
	{ accessorKey: "goodput_kbps", header: "Goodput [kbps]", cell: ({ row }) => Number(row.getValue("goodput_kbps")).toFixed(4) },
	{ accessorKey: "goodput_mbps", header: "Goodput [Mbps]", cell: ({ row }) => Number(row.getValue("goodput_mbps")).toFixed(6) },
	{ accessorKey: "ooo_count", header: "OOO Count" },
	{ accessorKey: "ooo_max_dist", header: "OOO Max Dist" },
	{ accessorKey: "timing_drift_ppm", header: "Timing Drift [ppm]", cell: ({ row }) => Number(row.getValue("timing_drift_ppm")).toFixed(4) },
	{ accessorKey: "timing_max_bloat_us", header: "Max Bloat [µs]", cell: ({ row }) => Number(row.getValue("timing_max_bloat_us")).toFixed(2) },
	{ accessorKey: "timing_avg_bloat_us", header: "Avg Bloat [µs]", cell: ({ row }) => Number(row.getValue("timing_avg_bloat_us")).toFixed(2) },
	{ accessorKey: "timing_slope", header: "Timing Slope", cell: ({ row }) => Number(row.getValue("timing_slope")).toFixed(8) },
	{ accessorKey: "engine_time_tx_theory", header: "Engine TX Theory [µs]", cell: ({ row }) => Number(row.getValue("engine_time_tx_theory")).toFixed(2) },
	{ accessorKey: "engine_time_tx_actual", header: "Engine TX Actual [µs]", cell: ({ row }) => Number(row.getValue("engine_time_tx_actual")).toFixed(2) },
	{ accessorKey: "engine_time_fetch", header: "Engine Fetch [µs]", cell: ({ row }) => Number(row.getValue("engine_time_fetch")).toFixed(2) },
	{ accessorKey: "engine_time_total_loop", header: "Engine Total Loop [µs]", cell: ({ row }) => Number(row.getValue("engine_time_total_loop")).toFixed(2) },
];

const columns = [...metadataColumns, ...normalizedColumns, ...rawColumns];

const metadataKeys = metadataColumns.map(c => c.accessorKey as string);
const normalizedKeys = normalizedColumns.map(c => c.accessorKey as string);

const applyPreset = (presetType: "metadata" | "normalized" | "all" | "none" | "section-pdr" | "section-jitter" | "section-burst" | "section-goodput" | "section-ooo" | "section-timing" | "section-engine") => {
	const newVisibility: Record<string, boolean> = {};

	columns.forEach((col) => {
		const key = col.accessorKey as string;
		if (!key) return;

		switch (presetType) {
			case "metadata":
				newVisibility[key] = metadataKeys.includes(key);
				break;

			case "normalized":
				newVisibility[key] = metadataKeys.includes(key) || normalizedKeys.includes(key);
				break;

			case "all":
				newVisibility[key] = true;
				break;

			case "section-pdr":
				newVisibility[key] = metadataKeys.includes(key) || key.startsWith("pdr_");
				break;

			case "section-jitter":
				newVisibility[key] = metadataKeys.includes(key) || key.startsWith("jitter_");
				break;

			case "section-burst":
				newVisibility[key] = metadataKeys.includes(key) || key.startsWith("burst_");
				break;

			case "section-goodput":
				newVisibility[key] = metadataKeys.includes(key) || key.startsWith("goodput_");
				break;

			case "section-ooo":
				newVisibility[key] = metadataKeys.includes(key) || key.startsWith("ooo_");
				break;

			case "section-timing":
				newVisibility[key] = metadataKeys.includes(key) || key.startsWith("timing_");
				break;

			case "section-engine":
				newVisibility[key] = metadataKeys.includes(key) || key.startsWith("engine_");
				break;

			case "none":
			default:
				newVisibility[key] = key === "test_id";
				break;
		}
	});

	columnVisibility.value = newVisibility;
};

const presetItems = ref<DropdownMenuItem[][]>([
	[
		{ type: "label", label: "Podstawowe widoki" },
		{ label: "Tylko Metadane", icon: "i-heroicons-identification", onSelect: () => applyPreset("metadata") },
		{ label: "Znormalizowane (Standard)", icon: "i-heroicons-star", onSelect: () => applyPreset("normalized") },
		{ label: "Pełna baza (Wszystkie dane)", icon: "i-heroicons-circle-stack", onSelect: () => applyPreset("all") },
	],
	[
		{ type: "label", label: "Analiza sekcyjna" },
		{ label: "PDR", icon: "i-heroicons-arrow-trending-up", onSelect: () => applyPreset("section-pdr") },
		{ label: "Jitter", icon: "i-heroicons-bolt", onSelect: () => applyPreset("section-jitter") },
		{ label: "Burst", icon: "i-heroicons-sparkles", onSelect: () => applyPreset("section-burst") },
		{ label: "Goodput", icon: "i-heroicons-cube", onSelect: () => applyPreset("section-goodput") },
		{ label: "OOO", icon: "i-heroicons-cube", onSelect: () => applyPreset("section-ooo") },
		{ label: "Timing", icon: "i-heroicons-clock", onSelect: () => applyPreset("section-timing") },
		{ label: "Engine", icon: "i-heroicons-cog-6-tooth", onSelect: () => applyPreset("section-engine") },
	],
	[
		{ label: "Ukryj wszystko (Żadne)", icon: "i-heroicons-eye-slash", color: "error", onSelect: () => applyPreset("none") },
	],
]);

applyPreset("normalized");

const getFriendlyColumnName = (accessorKey: string) => {
	const column = columns.find(c => c.accessorKey === accessorKey);
	return column && typeof column.header === "string" ? column.header : accessorKey;
};
</script>
