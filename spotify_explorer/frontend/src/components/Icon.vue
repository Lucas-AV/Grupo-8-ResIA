<script setup>
const props = defineProps({
  name: { type: String, required: true },
  size: { type: Number, default: 20 },
});

const paths = {
  search: "M9 3a6 6 0 104.472 10.032l3.248 3.248a1 1 0 001.414-1.414l-3.248-3.248A6 6 0 009 3zm-4 6a4 4 0 118 0 4 4 0 01-8 0z",
  disc: "M10 2a8 8 0 100 16 8 8 0 000-16zm0 5a3 3 0 110 6 3 3 0 010-6z",
  mic: "M10 2a3 3 0 00-3 3v5a3 3 0 006 0V5a3 3 0 00-3-3zM5 10a1 1 0 10-2 0 7 7 0 006 6.92V19a1 1 0 102 0v-2.08A7 7 0 0017 10a1 1 0 10-2 0 5 5 0 01-10 0z",
  sparkles: "M6 2l1 3 3 1-3 1-1 3-1-3-3-1 3-1 1-3zM15 9l1.5 4 4 1.5-4 1.5-1.5 4-1.5-4-4-1.5 4-1.5 1.5-4z",
  heart: "M10 17.5l-1.1-1C4.4 12.9 2 10.6 2 7.8 2 5.6 3.7 4 5.9 4c1.2 0 2.4.6 3.1 1.5A4 4 0 0112.1 4c2.2 0 3.9 1.6 3.9 3.8 0 2.8-2.4 5.1-6.9 8.7l-1.1 1z",
  waveform: "M3 10h2v4H3v-4zm4-4h2v12H7V6zm4 2h2v8h-2V8zm4-5h2v18h-2V3z",
  copy: "M8 2a2 2 0 00-2 2v8a2 2 0 002 2h6a2 2 0 002-2V6.83a2 2 0 00-.59-1.41l-2.83-2.83A2 2 0 0011.17 2H8zm0 2h3v3a1 1 0 001 1h3v6H8V4zM4 6a2 2 0 00-2 2v8a2 2 0 002 2h6a2 2 0 002-2h-2v0H4V8h2V6H4z",
  check: "M16.7 5.3a1 1 0 010 1.4l-8 8a1 1 0 01-1.4 0l-4-4a1 1 0 111.4-1.4L8 12.6l7.3-7.3a1 1 0 011.4 0z",
  logout: "M7 3a1 1 0 00-1 1v12a1 1 0 001 1h4a1 1 0 100-2H8V5h3a1 1 0 100-2H7zm7.29 3.29a1 1 0 011.42 0l3 3a1 1 0 010 1.42l-3 3a1 1 0 01-1.42-1.42L15.59 11H9a1 1 0 110-2h6.59l-1.3-1.29a1 1 0 010-1.42z",
};

const path = paths[props.name] ?? "";
</script>

<template>
  <svg :width="size" :height="size" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
    <path :d="path" />
  </svg>
</template>
