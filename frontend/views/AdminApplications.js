window.AdminApplicationsView = `
      <section v-else-if="page === 'admin-applications'">
        <div class="mb-4"><h1 class="h3 mb-1">All Applications</h1><p class="text-secondary mb-0">Review placement activity across students and companies.</p></div>
        <application-table :applications="applications"></application-table>
      </section>
`;
