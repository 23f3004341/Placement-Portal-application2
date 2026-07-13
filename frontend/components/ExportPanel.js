window.ExportPanel = {
  template: "<div class=\"d-flex flex-wrap align-items-center gap-2\">\n    <button class=\"btn btn-sm\" :class=\"buttonClass\" @click=\"$emit('start')\">Generate CSV export</button>\n    <template v-if=\"value\">\n      <StatusBadge :value=\"value.status\" />\n      <span class=\"small text-secondary\">{{ value.message }}</span>\n      <a v-if=\"value.file_url\" class=\"btn btn-success btn-sm\" :href=\"value.file_url\" download>Download CSV</a>\n    </template>\n  </div>",
  components: { StatusBadge },
  props: {
    value: { type: Object, default: null },
    buttonClass: { type: String, default: "btn-outline-primary" }
  },
  emits: ["start"]
};
