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
                    <div class="card border-0 bg-light-subtle shadow-sm h-100">
                      <div class="card-body">
                        <div class="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
                          <h3 class="h6 fw-semibold mb-0">Applications by company</h3>
                          <div class="d-flex flex-wrap gap-2 small">
                            <span v-for="status in dashboard.company_analytics?.statuses || []" :key="status" class="badge border fw-normal" :class="statusBadgeClass(status)">
                              {{ statusLabel(status) }}
                            </span>
                          </div>
                        </div>
                        <div v-if="companyAnalyticsRows().length" class="table-responsive">
                          <table class="table table-sm align-middle mb-0">
                            <thead class="table-light">
                              <tr>
                                <th scope="col">Company</th>
                                <th scope="col">Status spread</th>
                                <th scope="col" class="text-end">Total</th>
                              </tr>
                            </thead>
                            <tbody>
                              <tr v-for="row in companyAnalyticsRows()" :key="row.label">
                                <th scope="row" class="fw-semibold text-nowrap">{{ row.label }}</th>
                                <td>
                                  <div class="d-grid gap-2">
                                    <div v-for="item in row.items" :key="row.label + item.status" class="row g-2 align-items-center">
                                      <div class="col-4 col-md-3 small text-secondary">{{ statusLabel(item.status) }}</div>
                                      <div class="col">
                                        <div class="progress bg-white border" role="progressbar" :aria-label="row.label + ' ' + statusLabel(item.status)" :aria-valuenow="item.value" aria-valuemin="0" :aria-valuemax="adminAnalyticsMax()">
                                          <div class="progress-bar" :class="[statusProgressClass(item.status), widthClass(item.value, adminAnalyticsMax())]"></div>
                                        </div>
                                      </div>
                                      <div class="col-auto small fw-semibold">{{ item.value }}</div>
                                    </div>
                                  </div>
                                </td>
                                <td class="text-end fw-semibold">{{ row.total }}</td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                        <p v-else class="text-secondary mb-0">No company placement records yet.</p>
                      </div>
                    </div>
                  </div>
                  <div class="col-lg-4">
                    <div class="card border-0 bg-light-subtle shadow-sm h-100">
                      <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start gap-3 mb-3">
                          <div>
                            <h3 class="h6 fw-semibold mb-1">Overall application record</h3>
                            <p class="small text-secondary mb-0">{{ adminOverallTotal() }} applications</p>
                          </div>
                        </div>
                        <div v-if="adminOverallRows().length" class="d-grid gap-3">
                          <div v-for="item in adminOverallRows()" :key="item.status">
                            <div class="d-flex justify-content-between align-items-center gap-2 mb-1">
                              <span class="badge border fw-normal" :class="statusBadgeClass(item.status)">{{ statusLabel(item.status) }}</span>
                              <span class="small text-secondary">{{ item.value }} · {{ item.percent }}%</span>
                            </div>
                            <div class="progress bg-white border" role="progressbar" :aria-label="statusLabel(item.status)" :aria-valuenow="item.value" aria-valuemin="0" :aria-valuemax="adminOverallTotal()">
                              <div class="progress-bar" :class="[statusProgressClass(item.status), widthClass(item.value, adminOverallTotal())]"></div>
                            </div>
                          </div>
                        </div>
                        <p v-else class="text-secondary mb-0">No application records yet.</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
`;
