window.AdminCompaniesView = `
      <section v-else-if="page === 'admin-companies'">
        <list-header
          title="Companies"
          placeholder="Search name or industry"
          v-model="search"
          :button-class="themeButtonClass"
          :eyebrow-class="themeTextClass"
          @search="loadAdminCompanies"
        ></list-header>
        <div
          v-if="selectedAdminCompany"
          class="card border-0 shadow-sm mb-4"
        >
          <div class="card-body p-4">
            <div
              class="d-flex flex-wrap justify-content-between align-items-start gap-3 mb-4"
            >
              <div>
                <p class="fw-semibold text-uppercase small mb-1" :class="themeTextClass">
                  Company approval review
                </p>
                <h2 class="h4 mb-1">{{ selectedAdminCompany.name }}</h2>
                <div class="d-flex flex-wrap gap-2">
                  <status-badge
                    :value="companyApprovalLabel(selectedAdminCompany)"
                  ></status-badge>
                  <status-badge
                    :value="selectedAdminCompany.user.active ? 'active' : 'inactive'"
                  ></status-badge>
                </div>
              </div>
              <button
                class="btn btn-outline-secondary btn-sm"
                @click="selectedAdminCompany = null"
              >
                Back to list
              </button>
            </div>

            <div class="row g-4">
              <div class="col-lg-6">
                <h3 class="h6 text-secondary text-uppercase">Company details</h3>
                <dl class="row mb-0">
                  <dt class="col-sm-4">Company email</dt>
                  <dd class="col-sm-8">{{ selectedAdminCompany.user.email }}</dd>
                  <dt class="col-sm-4">Industry</dt>
                  <dd class="col-sm-8">{{ selectedAdminCompany.industry || "-" }}</dd>
                  <dt class="col-sm-4">Website</dt>
                  <dd class="col-sm-8">
                    <a
                      v-if="selectedAdminCompany.website"
                      :href="selectedAdminCompany.website"
                      target="_blank"
                      rel="noopener"
                    >
                      {{ selectedAdminCompany.website }}
                    </a>
                    <span v-else>-</span>
                  </dd>
                  <dt class="col-sm-4">Headquarters</dt>
                  <dd class="col-sm-8">{{ selectedAdminCompany.headquarters || "-" }}</dd>
                  <dt class="col-sm-4">Address</dt>
                  <dd class="col-sm-8 text-break">
                    {{ selectedAdminCompany.user.address || "-" }}
                  </dd>
                </dl>
              </div>
              <div class="col-lg-6">
                <h3 class="h6 text-secondary text-uppercase">HR contact</h3>
                <dl class="row mb-0">
                  <dt class="col-sm-4">HR name</dt>
                  <dd class="col-sm-8">{{ selectedAdminCompany.hr_name || "-" }}</dd>
                  <dt class="col-sm-4">HR email</dt>
                  <dd class="col-sm-8">{{ selectedAdminCompany.hr_email || "-" }}</dd>
                  <dt class="col-sm-4">HR phone</dt>
                  <dd class="col-sm-8">{{ selectedAdminCompany.hr_phone || "-" }}</dd>
                  <dt class="col-sm-4">Description</dt>
                  <dd class="col-sm-8 text-break">
                    {{ selectedAdminCompany.description || "-" }}
                  </dd>
                </dl>
              </div>
            </div>

            <div class="d-flex flex-wrap gap-2 mt-4 pt-3 border-top">
              <button
                v-if="!selectedAdminCompany.user.approved"
                class="btn btn-success"
                @click="adminStatus('companies', selectedAdminCompany.id, 'approve')"
              >
                Approve company
              </button>
              <button
                v-if="!selectedAdminCompany.user.approved && selectedAdminCompany.user.active"
                class="btn btn-outline-danger"
                @click="adminStatus('companies', selectedAdminCompany.id, 'reject')"
              >
                Reject company
              </button>
              <button
                v-if="selectedAdminCompany.user.approved"
                class="btn btn-outline-warning"
                @click="
                  adminStatus(
                    'companies',
                    selectedAdminCompany.id,
                    selectedAdminCompany.user.active ? 'blacklist' : 'unblacklist'
                  )
                "
              >
                {{
                  selectedAdminCompany.user.active ? "Blacklist" : "Unblacklist"
                }}
              </button>
            </div>
          </div>
        </div>
        <div class="table-responsive card shadow-sm border-0 rounded-4 overflow-hidden">
          <table class="table table-hover align-middle mb-0">
            <thead>
              <tr>
                <th class="p-3">Company</th>
                <th class="p-3">Industry</th>
                <th class="p-3">Approval</th>
                <th class="p-3">Account</th>
                <th class="p-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!companies.length"><td colspan="5" class="text-center text-secondary py-5">No companies found.</td></tr>
              <tr v-for="c in companies">
                <td class="p-3">
                  {{ c.name }}<br /><small>{{ c.user.email }}</small>
                </td>
                <td class="p-3">{{ c.industry || "-" }}</td>
                <td class="p-3">
                  <status-badge :value="companyApprovalLabel(c)"></status-badge>
                </td>
                <td class="p-3">
                  <status-badge :value="c.user.active ? 'active' : 'inactive'"></status-badge>
                </td>
                <td class="p-3">
                  <div class="d-flex flex-wrap gap-1">
                    <button
                      class="btn btn-sm btn-outline-secondary"
                      @click="viewAdminCompany(c)"
                    >
                      View details</button
                    ><button
                      v-if="c.user.approved"
                      class="btn btn-outline-warning btn-sm"
                      @click="
                        adminStatus(
                          'companies',
                          c.id,
                          c.user.active ? 'blacklist' : 'unblacklist'
                        )
                      "
                    >
                      {{ c.user.active ? "Blacklist" : "Unblacklist" }}</button
                    ><button
                      class="btn btn-outline-danger btn-sm"
                      @click="adminDelete('companies', c.id)"
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
`;
