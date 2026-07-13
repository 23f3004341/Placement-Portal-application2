window.StatusBadge = {
  template: "<span class=\"badge text-capitalize\" :class=\"badgeClass\">{{ value }}</span>",
  props: { value: { type: String, required: true } },
  computed: {
    badgeClass() {
      const classes = {
        approved: "bg-success-subtle text-success-emphasis border border-success-subtle",
        placed: "bg-success-subtle text-success-emphasis border border-success-subtle",
        offer: "text-bg-primary",
        offered: "text-bg-primary",
        active: "bg-success-subtle text-success-emphasis border border-success-subtle",
        inactive: "bg-danger-subtle text-danger-emphasis border border-danger-subtle",
        blacklisted: "bg-danger-subtle text-danger-emphasis border border-danger-subtle",
        shortlisted: "text-bg-info",
        interview: "text-bg-primary",
        applied: "text-bg-secondary",
        pending: "bg-warning-subtle text-warning-emphasis border border-warning-subtle",
        rejected: "bg-danger-subtle text-danger-emphasis border border-danger-subtle",
        withdrawn: "text-bg-secondary",
        failed: "text-bg-danger",
        completed: "text-bg-success",
        running: "text-bg-primary",
        queued: "text-bg-warning",
        closed: "text-bg-dark"
      };
      return classes[this.value] || "text-bg-light border";
    }
  }
};
