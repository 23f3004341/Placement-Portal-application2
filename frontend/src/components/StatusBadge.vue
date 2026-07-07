<template>
  <span class="badge text-capitalize" :class="badgeClass">{{ value }}</span>
</template>

<script>
export default {
  name: "StatusBadge",
  props: {
    value: { type: String, required: true },
  },
  computed: {
    badgeClass() {
      const classes = {
        approved: "text-bg-success",
        placed: "text-bg-success",
        offer: "text-bg-primary",
        shortlisted: "text-bg-info",
        pending: "text-bg-warning",
        rejected: "text-bg-danger",
        withdrawn: "text-bg-secondary",
      };
      return classes[this.value] || "text-bg-light border";
    },
  },
};
</script>
