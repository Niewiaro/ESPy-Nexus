<template>
	<div>
		<div class="relative overflow-hidden border-b border-muted bg-default">
			<div class="absolute inset-0 bg-[linear-gradient(to_right,#e2e8f0_1px,transparent_1px),linear-gradient(to_bottom,#e2e8f0_1px,transparent_1px)] dark:bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-size-[24px_24px] mask-[linear-gradient(to_bottom,white,transparent)] [-webkit-mask-image:linear-gradient(to_bottom,white,transparent)]" />

			<UPageHero
				headline="Baza Logów"
				title="Eksplorator Danych HIL"
				description="Przeglądaj, filtruj i przeszukuj surowe wyniki testów telemetrii z maszyny HIL. Przełączaj profile widoku, aby odkrywać anomalie na poziomie mikrosekundowym."
				:links="[
					{
						label: 'Wróć do analizatora',
						icon: 'heroicons:arrow-left-solid',
						to: '/',
						color: 'neutral',
						variant: 'solid',
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
				class="w-full flex flex-col border border-muted shadow-sm"
				:ui="{ body: 'p-0 sm:p-0' }"
			>
				<div class="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 border-b border-muted bg-muted/10">
					<UInput
						v-model="globalFilter"
						icon="heroicons:magnifying-glass-solid"
						placeholder="Filtruj logi (np. UDP, SERIAL, 1000Hz)..."
						class="w-full sm:max-w-sm font-mono text-sm"
						color="neutral"
					/>

					<div class="flex items-center gap-2 w-full sm:w-auto">
						<UDropdownMenu
							:items="presetItems"
							:content="{ align: 'end' }"
						>
							<UButton
								label="Profile widoku"
								color="primary"
								variant="soft"
								icon="heroicons:bookmark-solid"
								trailing-icon="heroicons:chevron-down-solid"
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
								label="Kolumny"
								color="neutral"
								variant="outline"
								icon="heroicons:view-columns-solid"
								trailing-icon="heroicons:chevron-down-solid"
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

				<div class="flex items-center justify-between border-t border-muted bg-muted/10 p-4">
					<div class="text-sm text-dimmed font-medium">
						Rekordy: <span class="font-bold text-highlighted">{{ table?.tableApi?.getRowModel().rows.length || 0 }}</span> / {{ table?.tableApi?.getFilteredRowModel().rows.length || 0 }}
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

useSeoMeta({
	title: "Eksplorator Danych HIL",
	description: "Surowa baza pomiarów i testów sieciowych. Filtruj miliony rekordów telemetrii i analizuj ukryte anomalie.",
});

const UBadge = resolveComponent("UBadge");

const { data } = useAnalytics();
type HilDataRow = typeof data.value[0];
type UColumn = TableColumn<HilDataRow> & { accessorKey?: string };

const table = useTemplateRef("table");
const globalFilter = ref("");
const pagination = ref({ pageIndex: 0, pageSize: 15 });
const columnVisibility = ref<Record<string, boolean>>({});

const renderMono = (value: string | number) => h("span", { class: "font-mono text-xs" }, value);

const metadataColumns: UColumn[] = [
	{ accessorKey: "test_id", header: "ID", cell: ({ row }) => renderMono(row.getValue("test_id")) },
	{ accessorKey: "protocol", header: "Protokół" },
	{ accessorKey: "router_topology", header: "Topologia" },
	{ accessorKey: "freq_hz", header: "Freq [Hz]", cell: ({ row }) => renderMono(`${row.getValue("freq_hz")}`) },
	{
		accessorKey: "status",
		header: "Status",
		cell: ({ row }) => {
			const status = row.getValue("status") as string;
			return h(UBadge, { variant: "soft", size: "sm", color: status === "OK" ? "success" : "error" }, () => status);
		},
	},
	{ accessorKey: "payload_b", header: "Payload [B]", cell: ({ row }) => renderMono(`${row.getValue("payload_b")}`) },
	{ accessorKey: "expected_cnt", header: "Pakiety [Oczekiwane]", cell: ({ row }) => renderMono(row.getValue("expected_cnt")) },
];

const normalizedColumns: UColumn[] = [
	{ accessorKey: "pdr_ratio_percent", header: "PDR [%]", cell: ({ row }) => renderMono(`${Number(row.getValue("pdr_ratio_percent")).toFixed(2)}%`) },
	{ accessorKey: "jitter_cv_percent", header: "Jitter CV [%]", cell: ({ row }) => renderMono(`${Number(row.getValue("jitter_cv_percent")).toFixed(4)}%`) },
	{ accessorKey: "goodput_efficiency_percent", header: "Efficiency [%]", cell: ({ row }) => renderMono(`${Number(row.getValue("goodput_efficiency_percent")).toFixed(2)}%`) },
	{ accessorKey: "timing_bloat_percent", header: "Queue Delay [%]", cell: ({ row }) => renderMono(`${Number(row.getValue("timing_bloat_percent")).toFixed(4)}%`) },
];

const rawColumns: UColumn[] = [
	{ accessorKey: "pdr_expected", header: "PDR Exp.", cell: ({ row }) => renderMono(row.getValue("pdr_expected")) },
	{ accessorKey: "pdr_received", header: "PDR Recv.", cell: ({ row }) => renderMono(row.getValue("pdr_received")) },
	{ accessorKey: "pdr_lost", header: "PDR Lost", cell: ({ row }) => renderMono(row.getValue("pdr_lost")) },
	{ accessorKey: "pdr_mac_dups", header: "MAC Dups", cell: ({ row }) => renderMono(row.getValue("pdr_mac_dups")) },
	{ accessorKey: "pdr_ghost_dups", header: "Ghost Dups", cell: ({ row }) => renderMono(row.getValue("pdr_ghost_dups")) },
	{ accessorKey: "jitter_expected_iat_us", header: "Jitter Exp IAT [µs]", cell: ({ row }) => renderMono(Number(row.getValue("jitter_expected_iat_us")).toFixed(2)) },
	{ accessorKey: "jitter_mean_iat_us", header: "Jitter Mean IAT [µs]", cell: ({ row }) => renderMono(Number(row.getValue("jitter_mean_iat_us")).toFixed(2)) },
	{ accessorKey: "jitter_err_iat_us", header: "Jitter Err [µs]", cell: ({ row }) => renderMono(Number(row.getValue("jitter_err_iat_us")).toFixed(4)) },
	{ accessorKey: "jitter_std_us", header: "Jitter STD [µs]", cell: ({ row }) => renderMono(Number(row.getValue("jitter_std_us")).toFixed(2)) },
	{ accessorKey: "jitter_max_iat_us", header: "Jitter Max IAT [µs]", cell: ({ row }) => renderMono(Number(row.getValue("jitter_max_iat_us")).toFixed(2)) },
	{ accessorKey: "jitter_min_iat_us", header: "Jitter Min IAT [µs]", cell: ({ row }) => renderMono(Number(row.getValue("jitter_min_iat_us")).toFixed(2)) },
	{ accessorKey: "jitter_max_iat_dev_us", header: "Jitter Max Dev [µs]", cell: ({ row }) => renderMono(Number(row.getValue("jitter_max_iat_dev_us")).toFixed(2)) },
	{ accessorKey: "jitter_min_iat_dev_us", header: "Jitter Min Dev [µs]", cell: ({ row }) => renderMono(Number(row.getValue("jitter_min_iat_dev_us")).toFixed(2)) },
	{ accessorKey: "burst_total_events", header: "Burst Events", cell: ({ row }) => renderMono(row.getValue("burst_total_events")) },
	{ accessorKey: "burst_max_len", header: "Burst Max Len", cell: ({ row }) => renderMono(row.getValue("burst_max_len")) },
	{ accessorKey: "burst_max_blackout_ms", header: "Burst Max Blackout [ms]", cell: ({ row }) => renderMono(Number(row.getValue("burst_max_blackout_ms")).toFixed(2)) },
	{ accessorKey: "goodput_bytes_sec", header: "Goodput [B/s]", cell: ({ row }) => renderMono(Number(row.getValue("goodput_bytes_sec")).toFixed(2)) },
	{ accessorKey: "goodput_kbps", header: "Goodput [kbps]", cell: ({ row }) => renderMono(Number(row.getValue("goodput_kbps")).toFixed(4)) },
	{ accessorKey: "goodput_mbps", header: "Goodput [Mbps]", cell: ({ row }) => renderMono(Number(row.getValue("goodput_mbps")).toFixed(6)) },
	{ accessorKey: "ooo_count", header: "OOO Count", cell: ({ row }) => renderMono(row.getValue("ooo_count")) },
	{ accessorKey: "ooo_max_dist", header: "OOO Max Dist", cell: ({ row }) => renderMono(row.getValue("ooo_max_dist")) },
	{ accessorKey: "timing_drift_ppm", header: "Timing Drift [ppm]", cell: ({ row }) => renderMono(Number(row.getValue("timing_drift_ppm")).toFixed(4)) },
	{ accessorKey: "timing_max_bloat_us", header: "Max Bloat [µs]", cell: ({ row }) => renderMono(Number(row.getValue("timing_max_bloat_us")).toFixed(2)) },
	{ accessorKey: "timing_avg_bloat_us", header: "Avg Bloat [µs]", cell: ({ row }) => renderMono(Number(row.getValue("timing_avg_bloat_us")).toFixed(2)) },
	{ accessorKey: "timing_slope", header: "Timing Slope", cell: ({ row }) => renderMono(Number(row.getValue("timing_slope")).toFixed(8)) },
	{ accessorKey: "engine_time_tx_theory", header: "Eng TX Theory [µs]", cell: ({ row }) => renderMono(Number(row.getValue("engine_time_tx_theory")).toFixed(2)) },
	{ accessorKey: "engine_time_tx_actual", header: "Eng TX Actual [µs]", cell: ({ row }) => renderMono(Number(row.getValue("engine_time_tx_actual")).toFixed(2)) },
	{ accessorKey: "engine_time_fetch", header: "Eng Fetch [µs]", cell: ({ row }) => renderMono(Number(row.getValue("engine_time_fetch")).toFixed(2)) },
	{ accessorKey: "engine_time_total_loop", header: "Eng Total Loop [µs]", cell: ({ row }) => renderMono(Number(row.getValue("engine_time_total_loop")).toFixed(2)) },
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
		{ label: "Tylko Metadane", icon: "heroicons:identification-solid", onSelect: () => applyPreset("metadata") },
		{ label: "Znormalizowane (Standard)", icon: "heroicons:star-solid", onSelect: () => applyPreset("normalized") },
		{ label: "Pełna baza (Wszystkie dane)", icon: "heroicons:circle-stack-solid", onSelect: () => applyPreset("all") },
	],
	[
		{ type: "label", label: "Analiza sekcyjna" },
		{ label: "PDR", icon: "heroicons:arrow-trending-up-solid", onSelect: () => applyPreset("section-pdr") },
		{ label: "Jitter", icon: "heroicons:bolt-solid", onSelect: () => applyPreset("section-jitter") },
		{ label: "Burst", icon: "heroicons:sparkles-solid", onSelect: () => applyPreset("section-burst") },
		{ label: "Goodput", icon: "heroicons:cube-solid", onSelect: () => applyPreset("section-goodput") },
		{ label: "OOO", icon: "heroicons:list-bullet-solid", onSelect: () => applyPreset("section-ooo") },
		{ label: "Timing", icon: "heroicons:clock-solid", onSelect: () => applyPreset("section-timing") },
		{ label: "Engine", icon: "heroicons:cog-6-tooth-solid", onSelect: () => applyPreset("section-engine") },
	],
	[
		{ label: "Ukryj wszystko", icon: "heroicons:eye-slash-solid", color: "error", onSelect: () => applyPreset("none") },
	],
]);

applyPreset("normalized");

const getFriendlyColumnName = (accessorKey: string) => {
	const column = columns.find(c => c.accessorKey === accessorKey);
	return column && typeof column.header === "string" ? column.header : accessorKey;
};
</script>
