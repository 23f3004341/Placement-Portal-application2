window.DriveTable = {
  template: "<div class=\"table-responsive card border-0 shadow-sm rounded-4 overflow-hidden\">\n    <table class=\"table table-hover align-middle mb-0\">\n      <thead class=\"table-light\"><tr><th class=\"p-3\">Position</th><th class=\"p-3\">Company</th><th class=\"p-3\">Skills</th><th class=\"p-3\">Deadline</th><th class=\"p-3\">Status</th><th class=\"p-3\">Actions</th></tr></thead>\n      <tbody><tr v-if=\"!drives.length\"><td colspan=\"6\" class=\"text-center text-secondary py-5\">No drives found.</td></tr>\n        <tr v-for=\"drive in drives\" :key=\"drive.id\"><td class=\"p-3\"><strong>{{ drive.title }}</strong></td><td class=\"p-3\">{{ drive.company }}</td><td class=\"p-3\">{{ drive.skills_required || \"-\" }}</td><td class=\"p-3\">{{ drive.deadline }}</td><td class=\"p-3\"><StatusBadge :value=\"drive.status\" /></td><td class=\"p-3\"><div class=\"d-flex flex-wrap gap-2\"><template v-if=\"admin\"><button class=\"btn btn-sm btn-outline-secondary\" @click=\"$emit('view', drive)\">View details</button><button class=\"btn btn-sm btn-outline-danger\" @click=\"$emit('action', drive, 'delete')\">Delete</button></template><template v-if=\"company\"><button class=\"btn btn-sm\" :class=\"actionClass\" @click=\"$emit('edit', drive)\">Edit</button><button class=\"btn btn-outline-danger btn-sm\" @click=\"$emit('action', drive, 'close')\">Close</button></template></div></td></tr>\n      </tbody></table></div>",
  components: { StatusBadge },
  props: {
    drives: { type: Array, default: () => [] },
    admin: { type: Boolean, default: false },
    company: { type: Boolean, default: false },
    actionClass: { type: String, default: "btn-outline-primary" }
  },
  emits: ["edit", "view", "action"]
};
