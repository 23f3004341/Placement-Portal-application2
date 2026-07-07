<template>
  <div class="d-flex flex-wrap align-items-center gap-2">
    <button class="btn btn-outline-primary btn-sm" @click="$emit('start')">Generate CSV export</button>
    <template v-if="value">
      <StatusBadge :value="value.status" />
      <span class="small text-secondary">{{ value.message }}</span>
      <a v-if="value.file_url" class="btn btn-success btn-sm" :href="value.file_url" download>Download CSV</a>
    </template>
  </div>
</template>

<script>
import StatusBadge from "./StatusBadge.vue";

export default {
  name: "ExportPanel",
  components: { StatusBadge },
  props: {
    value: { type: Object, default: null },
  },
  emits: ["start"],
};
</script>
