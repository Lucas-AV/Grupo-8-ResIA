<script setup>
import { ref } from "vue";
import Icon from "./Icon.vue";
import SkeletonBlock from "./SkeletonBlock.vue";
import EmptyState from "./EmptyState.vue";
import JsonViewer from "./JsonViewer.vue";

const props = defineProps({
  status: { type: Object, required: true },
  data: { type: null, default: null },
  emptyHint: { type: String, default: "" },
});

const copied = ref(false);

async function copyJSON() {
  try {
    await navigator.clipboard.writeText(JSON.stringify(props.data, null, 2));
    copied.value = true;
    setTimeout(() => {
      copied.value = false;
    }, 2000);
  } catch (err) {
    // clipboard indisponível (permissão negada, contexto não seguro) — ignora
  }
}
</script>

<template>
  <div>
    <SkeletonBlock v-if="status.loading" />
    <EmptyState v-else-if="data === null" :hint="emptyHint" />
    <div v-else>
      <slot name="preview" />
      <div class="result-panel-header">
        <p :class="status.className">{{ status.text }}</p>
        <button type="button" class="btn btn-secondary" @click="copyJSON">
          <Icon :name="copied ? 'check' : 'copy'" :size="14" />
          {{ copied ? "Copiado!" : "Copiar JSON" }}
        </button>
      </div>
      <div class="result">
        <JsonViewer :data="data" />
      </div>
    </div>
  </div>
</template>
