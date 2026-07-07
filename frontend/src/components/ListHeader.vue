<template>
  <div class="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
    <h1 class="h3 mb-0">{{ title }}</h1>
    <form class="d-flex gap-2" @submit.prevent="$emit('search')">
      <input
        class="form-control"
        :placeholder="placeholder"
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
      >
      <button class="btn btn-primary">Search</button>
    </form>
  </div>
</template>

<script>
export default {
  name: "ListHeader",
  props: {
    title: { type: String, required: true },
    placeholder: { type: String, default: "Search" },
    modelValue: { type: String, default: "" },
  },
  emits: ["update:modelValue", "search"],
};
</script>
