window.ListHeader = {
  template: "<div class=\"d-flex flex-column flex-lg-row justify-content-between align-items-lg-end gap-3 mb-4\">\n    <div><div class=\"small fw-semibold text-uppercase mb-1\" :class=\"eyebrowClass\">Placement Portal</div><h1 class=\"h3 mb-0\">{{ title }}</h1></div>\n    <form class=\"input-group w-auto\" role=\"search\" @submit.prevent=\"$emit('search')\">\n      <input class=\"form-control\" :placeholder=\"placeholder\" :value=\"modelValue\" aria-label=\"Search\" @input=\"$emit('update:modelValue', $event.target.value)\">\n      <button class=\"btn px-4\" :class=\"buttonClass\">Search</button>\n    </form>\n  </div>",
  props: {
    title: { type: String, required: true },
    placeholder: { type: String, default: "Search" },
    modelValue: { type: String, default: "" },
    buttonClass: { type: String, default: "btn-primary" },
    eyebrowClass: { type: String, default: "text-primary" }
  },
  emits: ["update:modelValue", "search"]
};
