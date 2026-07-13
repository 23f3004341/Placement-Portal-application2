window.ListHeader = {
  template: "<div class=\"d-flex flex-column flex-lg-row justify-content-between align-items-lg-end gap-3 mb-4\">\n    <div><h1 class=\"h3 mb-1\">{{ title }}</h1><p class=\"text-secondary mb-0\">Manage and review {{ title.toLowerCase() }}.</p></div>\n    <form class=\"input-group w-50\" role=\"search\" @submit.prevent=\"$emit('search')\">\n      <span class=\"input-group-text bg-white border-end-0\" aria-hidden=\"true\">⌕</span><input class=\"form-control border-start-0 ps-0\" :placeholder=\"placeholder\" :value=\"modelValue\" aria-label=\"Search\" @input=\"onInput\">\n    </form>\n  </div>",
  props: {
    title: { type: String, required: true },
    placeholder: { type: String, default: "Search" },
    modelValue: { type: String, default: "" },
    buttonClass: { type: String, default: "btn-primary" },
    eyebrowClass: { type: String, default: "text-primary" }
  },
  emits: ["update:modelValue", "search"],
  methods: { onInput(event) { this.$emit('update:modelValue', event.target.value); setTimeout(() => this.$emit('search'), 0); } }
};
