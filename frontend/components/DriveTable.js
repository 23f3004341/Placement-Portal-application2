window.DriveTable = {
  template: "<div class=\"table-responsive card border-0 shadow-sm\">\n    <table class=\"table mb-0\">\n      <thead>\n        <tr>\n          <th>Position</th>\n          <th>Company</th>\n          <th>Skills</th>\n          <th>Deadline</th>\n          <th>Status</th>\n          <th>Actions</th>\n        </tr>\n      </thead>\n      <tbody>\n        <tr v-if=\"!drives.length\"><td colspan=\"6\" class=\"text-center text-secondary py-5\">No drives found.</td></tr>\n        <tr v-for=\"drive in drives\" :key=\"drive.id\">\n          <td><strong>{{ drive.title }}</strong></td>\n          <td>{{ drive.company }}</td>\n          <td>{{ drive.skills_required || \"-\" }}</td>\n          <td>{{ drive.deadline }}</td>\n          <td><StatusBadge :value=\"drive.status\" /></td>\n          <td>\n            <div class=\"d-flex flex-wrap gap-1\">\n              <template v-if=\"admin\">\n                <button class=\"btn btn-sm\" :class=\"actionClass\" @click=\"$emit('view', drive)\">View details</button>\n                <button class=\"btn btn-danger btn-sm\" @click=\"$emit('action', drive, 'delete')\">Delete</button>\n              </template>\n              <template v-if=\"company\">\n                <button class=\"btn btn-sm\" :class=\"actionClass\" @click=\"$emit('edit', drive)\">Edit</button>\n                <button class=\"btn btn-outline-danger btn-sm\" @click=\"$emit('action', drive, 'close')\">Close</button>\n              </template>\n            </div>\n          </td>\n        </tr>\n      </tbody>\n    </table>\n  </div>",
  components: { StatusBadge },
  props: {
    drives: { type: Array, default: () => [] },
    admin: { type: Boolean, default: false },
    company: { type: Boolean, default: false },
    actionClass: { type: String, default: "btn-outline-primary" }
  },
  emits: ["edit", "view", "action"]
};
