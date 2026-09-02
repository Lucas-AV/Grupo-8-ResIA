<script setup>
import { reactive } from "vue";
import { useApi } from "../composables/useApi.js";
import JsonViewer from "../components/JsonViewer.vue";

const form = reactive({ q: "", type: "track", limit: 10 });
const { status, call } = useApi();
const result = reactive({ data: null });

async function onSubmit() {
  const { data } = await call("/api/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ q: form.q, type: form.type, limit: Number(form.limit) }),
  });
  result.data = data;
}
</script>

<template>
  <section>
    <form @submit.prevent="onSubmit">
      <label>Query <input type="text" v-model="form.q" required></label>
      <label>Type
        <select v-model="form.type">
          <option value="track">track</option>
          <option value="artist">artist</option>
          <option value="album">album</option>
        </select>
      </label>
      <label>Limit <input type="number" v-model.number="form.limit" min="1" max="50"></label>
      <button type="submit">Buscar</button>
    </form>
    <p :class="status.className">{{ status.text }}</p>
    <div class="result"><JsonViewer v-if="result.data !== null" :data="result.data" /></div>
  </section>
</template>
