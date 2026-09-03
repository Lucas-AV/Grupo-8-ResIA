<script setup>
defineProps({
  lines: { type: Number, default: 3 },
});
</script>

<template>
  <div>
    <div
      v-for="n in lines"
      :key="n"
      class="skeleton-block"
      :style="{ width: n === lines ? '60%' : '100%' }"
    ></div>
  </div>
</template>
