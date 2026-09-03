<script setup>
defineProps({
  hint: { type: String, default: "" },
});
</script>

<template>
  <div class="empty-state">
    <p>{{ hint }}</p>
  </div>
</template>
