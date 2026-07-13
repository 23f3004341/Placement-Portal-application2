window.ApplicationTable = {
  template: `
    <div class="table-responsive card border-0 shadow-sm">
      <table class="table mb-0">
        <thead>
          <tr>
            <th>Student</th>
            <th>Company</th>
            <th>Position</th>
            <th>Applied</th>
            <th>Status</th>
            <th>Feedback</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="application in applications" :key="application.id">
            <td>
              {{ application.student.user.name }}<br>
              <small>Student ID: {{ application.student.roll_number }}</small>
            </td>
            <td>{{ application.drive.company }}</td>
            <td>{{ application.drive.title }}</td>
            <td>{{ new Date(application.applied_at).toLocaleDateString() }}</td>
            <td>
              <span
                v-if="application.feedback === 'Already placed at a different role'"
                class="badge text-bg-secondary"
              >
                Already placed at a different role
              </span>
              <StatusBadge v-else :value="application.status" />
            </td>
            <td>{{ application.feedback || "-" }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  `,
  components: { StatusBadge },
  props: { applications: { type: Array, default: () => [] } }
};
