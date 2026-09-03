<script setup>
import Icon from "./Icon.vue";

defineProps({
  tabs: { type: Array, required: true },
  activeTab: { type: String, required: true },
  authState: { type: Object, required: true },
});

const emit = defineEmits(["select"]);
</script>

<template>
  <aside class="app-sidebar">
    <div>
      <div class="app-sidebar-title">
        <Icon name="waveform" :size="18" />
        Spotify API Explorer
      </div>
      <div class="app-sidebar-subtitle">Dev tool — não é o produto Spotify</div>
    </div>

    <nav class="sidebar-nav">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        type="button"
        class="sidebar-nav-item"
        :class="{ active: activeTab === tab.id }"
        @click="emit('select', tab.id)"
      >
        <Icon :name="tab.icon" :size="18" />
        {{ tab.label }}
      </button>
    </nav>

    <div class="sidebar-footer">
      <div v-if="authState.loggedIn" class="sidebar-user">
        <span>{{ authState.profile.display_name || authState.profile.id }}</span>
        <a href="/logout" class="btn btn-secondary">
          <Icon name="logout" :size="14" />
          Desconectar
        </a>
      </div>
      <a v-else href="/login" class="btn">Conectar Spotify</a>
    </div>
  </aside>
</template>
