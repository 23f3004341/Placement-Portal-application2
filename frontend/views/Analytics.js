window.AnalyticsView = `
      <section v-else-if="page === 'analytics'">
        <div
          class="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-4"
        >
          <div>
            <h1 class="h3 mb-1">Public Placement Analytics</h1>
            <p class="text-secondary mb-0">
              Aggregated statistics only—no student-level information.
            </p>
          </div>
          <button class="btn btn-outline-secondary" @click="go('home')">
            Back to home
          </button>
        </div>
        <div class="row g-3">
          <div class="col-12 col-lg-6">
            <div class="card shadow-sm border-0">
              <div class="card-body">
                <h2 class="h5">Monthly placement trend</h2>
                <div v-if="metricRows('trends').length" class="d-grid gap-3 mt-3">
                  <div v-for="item in metricRows('trends')" :key="item.label">
                    <div class="d-flex justify-content-between align-items-center gap-2 mb-1">
                      <span class="small text-secondary">{{ item.label }}</span>
                      <span class="small fw-semibold">{{ item.value }}</span>
                    </div>
                    <div class="progress bg-light border" role="progressbar" :aria-label="'Placements in ' + item.label" :aria-valuenow="item.value" aria-valuemin="0" :aria-valuemax="metricMax('trends')">
                      <div class="progress-bar bg-success-subtle text-success-emphasis" :class="widthClass(item.value, metricMax('trends'))"></div>
                    </div>
                  </div>
                </div>
                <p v-else class="text-secondary mb-0 mt-3">No placement trend records yet.</p>
              </div>
            </div>
          </div>
          <div class="col-12 col-lg-6">
            <div class="card shadow-sm border-0">
              <div class="card-body">
                <h2 class="h5">Application funnel</h2>
                <div v-if="metricRows('funnel').length" class="d-grid gap-3 mt-3">
                  <div v-for="item in metricRows('funnel')" :key="item.label">
                    <div class="d-flex justify-content-between align-items-center gap-2 mb-1">
                      <span class="badge border fw-normal" :class="statusBadgeClass(item.label.toLowerCase())">{{ item.label }}</span>
                      <span class="small text-secondary">{{ item.value }} · {{ metricPercent(item.value, metricTotal('funnel')) }}%</span>
                    </div>
                    <div class="progress bg-light border" role="progressbar" :aria-label="item.label" :aria-valuenow="item.value" aria-valuemin="0" :aria-valuemax="metricTotal('funnel')">
                      <div class="progress-bar" :class="[statusProgressClass(item.label.toLowerCase()), widthClass(item.value, metricTotal('funnel'))]"></div>
                    </div>
                  </div>
                </div>
                <p v-else class="text-secondary mb-0 mt-3">No application records yet.</p>
              </div>
            </div>
          </div>
          <div class="col-12">
            <div class="card shadow-sm border-0">
              <div class="card-body">
                <h2 class="h5">Job demand by skills</h2>
                <div v-if="metricRows('skills').length" class="table-responsive mt-3">
                  <table class="table align-middle mb-0">
                    <thead class="table-light">
                      <tr>
                        <th scope="col">Skill</th>
                        <th scope="col">Demand</th>
                        <th scope="col" class="text-end">Mentions</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="item in metricRows('skills')" :key="item.label">
                        <th scope="row" class="fw-semibold">{{ item.label }}</th>
                        <td>
                          <div class="progress bg-light border" role="progressbar" :aria-label="item.label" :aria-valuenow="item.value" aria-valuemin="0" :aria-valuemax="metricMax('skills')">
                            <div class="progress-bar bg-secondary-subtle text-secondary-emphasis" :class="widthClass(item.value, metricMax('skills'))"></div>
                          </div>
                        </td>
                        <td class="text-end fw-semibold">{{ item.value }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <p v-else class="text-secondary mb-0 mt-3">No approved skill demand records yet.</p>
              </div>
            </div>
          </div>
        </div>
      </section>
`;
