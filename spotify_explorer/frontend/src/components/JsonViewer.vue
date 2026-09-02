<script setup>
defineProps({
  data: {
    type: null,
    default: null,
  },
});

function isContainer(value) {
  return value !== null && typeof value === "object";
}

function entries(value) {
  if (Array.isArray(value)) {
    return value.map((v, i) => [i, v]);
  }
  return Object.entries(value);
}

function brackets(value) {
  return Array.isArray(value) ? ["[", "]"] : ["{", "}"];
}
</script>

<template>
  <template v-if="data === null || data === undefined">
    <span>null</span>
  </template>
  <template v-else-if="isContainer(data)">
    <span v-if="entries(data).length === 0">{{ brackets(data)[0] }}{{ brackets(data)[1] }}</span>
    <details v-else open>
      <summary>{{ brackets(data)[0] }} {{ entries(data).length }} item(s) {{ brackets(data)[1] }}</summary>
      <div class="json-indent">
        <div v-for="[key, val] in entries(data)" :key="key">
          <span class="json-key">{{ key }}: </span>
          <JsonViewer :data="val" />
        </div>
      </div>
    </details>
  </template>
  <template v-else>
    <span>{{ JSON.stringify(data) }}</span>
  </template>
</template>
