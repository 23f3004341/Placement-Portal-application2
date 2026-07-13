window.StatusBadge = {
  template: "<span class=\"badge text-capitalize\" :class=\"badgeClass\">{{ value }}</span>",
  props: { value: { type: String, required: true } },
  computed: {
    badgeClass() {
      const classes = {
        approved: "text-bg-success",
        placed: "text-bg-success",
        offer: "text-bg-primary",
        offered: "text-bg-primary",
        active: "text-bg-success",
        inactive: "text-bg-danger",
        blacklisted: "text-bg-danger",
        shortlisted: "text-bg-info",
        interview: "text-bg-primary",
        applied: "text-bg-secondary",
        pending: "text-bg-warning",
        rejected: "text-bg-danger",
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
