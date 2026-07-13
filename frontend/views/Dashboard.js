window.DashboardView = `
      <section v-else-if="page === 'dashboard'">
        <div
          class="card border-0 shadow-sm mb-4"
          :class="{
            'bg-success-subtle': user && user.role === 'student',
            'bg-warning-subtle': user && user.role === 'company',
            'bg-danger-subtle': user && user.role === 'admin'
          }"
        >
          <div class="card-body p-4 p-lg-5">
            <div class="d-flex flex-wrap justify-content-between align-items-center gap-3">
              <div>
                <div class="small fw-semibold text-uppercase mb-1" :class="themeTextClass">Overview</div>
                <h1 v-if="user && user.role === 'company'" class="display-6 fw-bold mb-2">
                  Welcome {{ dashboard.company?.name || user?.name }}
                </h1>
                <h1 v-else class="display-6 fw-bold mb-2">{{ roleTitle }} Dashboard</h1>
                <p class="lead text-secondary mb-0" v-if="user && user.role === 'student'">
                  Your applications, interviews, exports, and placement records.
                </p>
                <p class="lead text-secondary mb-0" v-else-if="user && user.role === 'company'">
                  Your drives, applicants, interviews, and final results.
                </p>
                <p class="lead text-secondary mb-0" v-else>
                  A clean overview of campus placement activity.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div class="row g-3 mb-4">
          <div
            v-for="(value, key) in dashboard.metrics"
            :key="key"
            class="col-6 col-lg-4 col-xl-2"
          >
            <div class="card border-0 shadow-sm h-100 border-start border-4" :class="themeBorderClass">
              <div class="card-body">
                <div class="small text-secondary text-uppercase text-capitalize">
                  {{ key.replaceAll("_", " ") }}
                </div>
                <div class="display-6 fw-bold">{{ value }}</div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="user && user.role === 'student'" class="row g-4">
          <div class="col-lg-7">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body">
                <h2 class="h5 fw-normal mb-3">Current status</h2>
                <div v-if="dashboard.current_statuses?.length" class="d-grid gap-2">
                  <div v-for="item in dashboard.current_statuses" :key="item.label + item.company" class="d-flex flex-wrap align-items-center gap-2 p-3 border border-success-subtle rounded-3 bg-success-subtle text-success-emphasis">
                    <span class="text-secondary">Status:</span>
                    <strong>{{ item.label }}</strong>
                    <span>at <strong>{{ item.company }}</strong></span>
                  </div>
                </div>
                <p v-else class="text-secondary mb-0">No active placement status yet.</p>
              </div>
            </div>
          </div>
          <div class="col-lg-5">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body">
                <h2 class="h5">Reports and exports</h2>
                <export-panel :value="dashboard.latest_export" :button-class="themeOutlineButtonClass" @start="startExport"></export-panel>
                <div class="d-grid gap-2 mt-3">
                  <a class="btn" :class="themeOutlineButtonClass" href="/api/student/report?format=html" download>Download HTML report</a>
                  <a class="btn" :class="themeOutlineButtonClass" href="/api/student/report?format=pdf" download>Download PDF report</a>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="user && user.role === 'admin'" class="row g-4">
          <div class="col-12">
            <div class="card border-0 shadow-sm h-100">
              <div class="card-body">
                <h2 class="h5 fw-normal mb-1">Company placement analytics</h2>
                <p class="text-secondary mb-3">
                  Compare applied, shortlisted, placed, and rejected records by company, with the overall distribution alongside.
                </p>
                <div class="row g-3 mt-1">
                  <div class="col-lg-8">
                    <div class="card border p-3 h-100"><canvas id="adminCompanyBarChart"></canvas></div>
                  </div>
                  <div class="col-lg-4">
                    <div class="card border p-3 h-100"><canvas id="adminOverallDoughnutChart"></canvas></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
`;
