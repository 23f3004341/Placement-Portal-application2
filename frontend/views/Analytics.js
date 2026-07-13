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
                <div class="ratio ratio-4x3"><canvas id="trendChart"></canvas></div>
              </div>
            </div>
          </div>
          <div class="col-12 col-lg-6">
            <div class="card shadow-sm border-0">
              <div class="card-body">
                <h2 class="h5">Application funnel</h2>
                <div class="ratio ratio-4x3"><canvas id="funnelChart"></canvas></div>
              </div>
            </div>
          </div>
          <div class="col-12">
            <div class="card shadow-sm border-0">
              <div class="card-body">
                <h2 class="h5">Job demand by skills</h2>
                <div class="ratio ratio-4x3"><canvas id="skillsChart"></canvas></div>
              </div>
            </div>
          </div>
        </div>
      </section>
`;
