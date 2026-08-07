<script setup lang="ts">
import { useTransition, TransitionPresets } from "@vueuse/core";

const props = defineProps<{
	value: number;
}>();

const formatNumber = (num: number): string => {
	return new Intl.NumberFormat("pl-PL").format(Math.floor(num));
};

const source = ref(0);
const output = useTransition(source, {
	duration: 1500,
	transition: TransitionPresets.easeOutExpo,
});

onMounted(() => {
	source.value = props.value;
});

const displayValue = computed(() => formatNumber(output.value));
</script>

<template>
	<span>{{ displayValue }}</span>
</template>
