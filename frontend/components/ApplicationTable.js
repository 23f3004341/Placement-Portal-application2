window.ApplicationTable = {
  template: `
    <div class="table-responsive card border-0 shadow-sm rounded-4 overflow-hidden">
      <table class="table table-hover align-middle mb-0">
        <thead>
          <tr>
            <th class="p-3">Student</th>
            <th class="p-3">Company</th>
            <th class="p-3">Position</th>
            <th class="p-3">Applied</th>
            <th class="p-3">Status</th>
            <th class="p-3">Feedback</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!applications.length"><td colspan="6" class="text-center text-secondary py-5">No applications found.</td></tr>
          <tr v-for="application in applications" :key="application.id">
            <td class="p-3">
              {{ application.student.user.name }}<br>
              <small>Student ID: {{ application.student.roll_number }}</small>
            </td>
            <td class="p-3">{{ application.drive.company }}</td>
            <td class="p-3">{{ application.drive.title }}</td>
            <td class="p-3">{{ new Date(application.applied_at).toLocaleDateString() }}</td>
            <td class="p-3">
              <span
                v-if="application.feedback === 'Already placed at a different role'"
                class="badge text-bg-secondary"
              >
                Already placed at a different role
              </span>
              <StatusBadge v-else :value="application.status" />
            </td>
            <td class="p-3">{{ application.feedback || "-" }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  `,
  components: { StatusBadge },
  props: { applications: { type: Array, default: () => [] } }
};
