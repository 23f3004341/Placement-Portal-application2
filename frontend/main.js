const { createApp, nextTick } = Vue;
const Chart = window.Chart;


const App = {
  name: "App",
  template: window.AppTemplate,
  components: {
    StatusBadge,
    ListHeader,
    ExportPanel,
    DriveTable,
    ApplicationTable,
  },
  data() {
    return {
      page: "home",
      user: null,
      loading: false,
      alert: { message: "", type: "info", progress: 100 },
      alertTimer: null,
      alertProgressTimer: null,
      hoveredNav: "",
      loginPasswordVisible: false,
      studentPasswordVisible: false,
      studentConfirmPasswordVisible: false,
      companyPasswordVisible: false,
      companyConfirmPasswordVisible: false,
      publicStats: {
        totals: {},
        trends: { labels: [], values: [] },
        funnel: { labels: [], values: [] },
        skills: { labels: [], values: [] },
      },
      charts: [],
      dashboard: { metrics: {} },
      dashboardChartVersion: 0,
      dashboardRefreshTimer: null,
      search: "",
      companies: [],
      selectedAdminCompany: null,
      students: [],
      selectedAdminStudent: null,
      editingStudentId: null,
      studentEditForm: {},
      drives: [],
      selectedAdminDrive: null,
      applications: [],
      eligibleOnly: false,
      exportPollTimer: null,
      mailhogUrl: "http://127.0.0.1:8025",
      loginForm: { role: "student", email: "", password: "" },
      registerRole: "student",
      degreeOptions: [
        "B.Tech",
        "M.Tech",
        "B.Sc",
        "M.Sc",
        "BCA",
        "MCA",
        "MBA",
        "BBA",
        "B.Com",
        "M.Com",
        "BA",
        "MA",
        "Diploma",
      ],
      branchOptions: [
        "Computer Science",
        "Information Technology",
        "Electronics and Communication",
        "Electrical Engineering",
        "Mechanical Engineering",
        "Civil Engineering",
        "Chemical Engineering",
        "Artificial Intelligence",
        "Data Science",
        "Cybersecurity",
        "Business Administration",
        "Commerce",
        "Mathematics",
        "Physics",
        "General",
      ],
      genderOptions: ["Female", "Male", "Other", "Prefer not to say"],
      studentRegister: {
        first_name: "",
        middle_name: "",
        last_name: "",
        email: "",
        password: "",
        confirm_password: "",
        contact: "",
        gender: "",
        dob: "",
        address_line1: "",
        address_line2: "",
        landmark: "",
        pincode: "",
        city: "",
        state: "",
        country: "India",
        course: "",
        branch: "",
        graduation_year: new Date().getFullYear() + 1,
        cgpa: "",
        experience: "",
      },
      companyRegister: {
        company_name: "",
        industry: "",
        email: "",
        password: "",
        confirm_password: "",
        hr_first_name: "",
        hr_middle_name: "",
        hr_last_name: "",
        hr_email: "",
        hr_phone: "",
        website: "",
        headquarters: "",
        address_line1: "",
        address_line2: "",
        landmark: "",
        pincode: "",
        city: "",
        state: "",
        country: "India",
        description: "",
      },
      pincodeLoading: false,
      lastPincodeLookup: { student: "", company: "" },
      pincodeMessage: { student: "", company: "" },
      showDriveForm: false,
      driveForm: {},
      studentProfile: { user: {} },
      companyProfile: {},
    };
  },
  computed: {
    roleTitle() {
      return this.user
        ? this.user.role.charAt(0).toUpperCase() + this.user.role.slice(1)
        : "";
    },
    roleNavClass() {
      if (!this.user) return "bg-body-tertiary";
      return {
        student: "bg-success-subtle",
        company: "bg-warning-subtle",
        admin: "bg-danger-subtle",
      }[this.user.role] || "bg-body-tertiary";
    },
    roleShellClass() {
      if (!this.user) return "";
      return {
        student: "bg-success-subtle",
        company: "bg-warning-subtle",
        admin: "bg-danger-subtle",
      }[this.user.role] || "";
    },
    themeButtonClass() {
      if (!this.user) return "btn-secondary";
      return {
        student: "btn-success",
        company: "btn-secondary",
        admin: "btn-secondary",
      }[this.user.role] || "btn-secondary";
    },
    themeOutlineButtonClass() {
      if (!this.user) return "btn-outline-secondary";
      return {
        student: "btn-outline-success",
        company: "btn-outline-secondary",
        admin: "btn-outline-secondary",
      }[this.user.role] || "btn-outline-secondary";
    },
    themeTextClass() {
      if (!this.user) return "text-secondary";
      return {
        student: "text-success-emphasis",
        company: "text-warning-emphasis",
        admin: "text-danger-emphasis",
      }[this.user.role] || "text-secondary";
    },
    themeBorderClass() {
      if (!this.user) return "border-secondary";
      return {
        student: "border-success",
        company: "border-warning",
        admin: "border-secondary",
      }[this.user.role] || "border-secondary";
    },
    today() {
      return new Date().toISOString().slice(0, 10);
    },
  },
  async mounted() {
    window.addEventListener("hashchange", () => this.route());
    await this.loadMailhogConfig();
    await this.restoreSession();
    await this.route();
  },
  beforeUnmount() {
    if (this.dashboardRefreshTimer) clearTimeout(this.dashboardRefreshTimer);
    if (this.exportPollTimer) clearTimeout(this.exportPollTimer);
    if (this.alertTimer) clearTimeout(this.alertTimer);
    if (this.alertProgressTimer) clearInterval(this.alertProgressTimer);
  },
  methods: {
    navItemClass(target) {
      const isWarm = this.hoveredNav === target || this.page === target;
      if (!isWarm || !this.user) return "";
      return {
        student: "bg-success bg-gradient text-white border rounded px-3 shadow-sm",
        company: "bg-warning bg-gradient text-dark border rounded px-3 shadow-sm",
        admin: "bg-danger bg-gradient text-white border rounded px-3 shadow-sm",
      }[this.user.role] || "bg-light rounded px-3";
    },
    notify(message, type = "success") {
      if (this.alertTimer) clearTimeout(this.alertTimer);
      if (this.alertProgressTimer) clearInterval(this.alertProgressTimer);
      this.alert = { message, type, progress: 100 };
      window.scrollTo({ top: 0, behavior: "smooth" });
      const progressDuration = 1500;
      const visibleDuration = 2000;
      const startedAt = Date.now();
      this.alertProgressTimer = setInterval(() => {
        const elapsed = Date.now() - startedAt;
        this.alert.progress = Math.max(0, 100 - (elapsed / progressDuration) * 100);
        if (this.alert.progress <= 0 && this.alertProgressTimer) {
          clearInterval(this.alertProgressTimer);
          this.alertProgressTimer = null;
        }
      }, 40);
      this.alertTimer = setTimeout(() => {
        this.alert.message = "";
        this.alertTimer = null;
        if (this.alertProgressTimer) {
          clearInterval(this.alertProgressTimer);
          this.alertProgressTimer = null;
        }
      }, visibleDuration);
    },
    dismissAlert() {
      if (this.alertTimer) clearTimeout(this.alertTimer);
      if (this.alertProgressTimer) clearInterval(this.alertProgressTimer);
      this.alertTimer = null;
      this.alertProgressTimer = null;
      this.alert = { message: "", type: "info", progress: 100 };
    },
    async api(path, options = {}) {
      return window.apiRequest(path, options);
    },
    async withLoading(action) {
      this.loading = true;
      try {
        return await action();
      } catch (error) {
        this.notify(error.message, "danger");
        throw error;
      } finally {
        this.loading = false;
      }
    },
    async loadMailhogConfig() {
      try {
        const result = await this.api("/api/mailhog");
        this.mailhogUrl = result.data.url || this.mailhogUrl;
      } catch (error) {
        this.mailhogUrl = this.mailhogUrl || "http://127.0.0.1:8025";
      }
    },
    async openMailhog() {
      await this.loadMailhogConfig();
      window.open(
        this.mailhogUrl || "http://127.0.0.1:8025",
        "_blank",
        "noopener"
      );
    },
    async restoreSession() {
      const result = await this.api("/api/auth/me");
      this.user = result.data.user;
    },
    go(page) {
      location.hash = page;
    },
    async route() {
      if (this.dashboardRefreshTimer) {
        clearTimeout(this.dashboardRefreshTimer);
        this.dashboardRefreshTimer = null;
      }
      const requested = window.resolvePage(location.hash, this.user);
      this.page = requested;
      this.search = "";
      this.selectedAdminCompany = null;
      this.selectedAdminDrive = null;
      await this.loadPage();
    },
    async loadPage() {
      const loaders = {
        home: this.loadPublicStats,
        analytics: this.loadPublicStats,
        dashboard: this.loadDashboard,
        "admin-companies": this.loadAdminCompanies,
        "admin-students": this.loadAdminStudents,
        "admin-drives": this.loadAdminDrives,
        "admin-applications": this.loadAdminApplications,
        "company-drives": this.loadCompanyDrives,
        "company-applications": this.loadCompanyApplications,
        "student-drives": this.loadStudentDrives,
        "student-applications": this.loadStudentApplications,
        profile: this.loadProfile,
      };
      if (loaders[this.page])
        await this.withLoading(loaders[this.page].bind(this)).catch(() => {});
    },
    async login() {
      await this.withLoading(async () => {
        const result = await this.api("/api/auth/login", {
          method: "POST",
          body: this.loginForm,
        });
        this.user = result.data.user;
        this.loginForm.password = "";
        this.notify(result.message);
        this.go("dashboard");
      }).catch(() => {});
    },
    async logout() {
      await this.api("/api/auth/logout", { method: "POST" });
      this.user = null;
      this.dashboard = { metrics: {} };
      if (this.exportPollTimer) clearTimeout(this.exportPollTimer);
      this.exportPollTimer = null;
      this.notify("Logged out.", "info");
      this.go("home");
    },
    async registerStudent() {
      if (
        this.studentRegister.password !== this.studentRegister.confirm_password
      )
        return this.notify("Student passwords do not match.", "warning");
      await this.withLoading(async () => {
        const data = new FormData();
        Object.entries(this.studentRegister).forEach(([key, value]) =>
          data.append(key, value ?? "")
        );
        const file = this.$refs.studentResume?.files[0];
        if (file) data.append("resume", file);
        const result = await this.api("/api/auth/register/student", {
          method: "POST",
          body: data,
        });
        this.notify(result.message);
        this.loginForm.email = this.studentRegister.email;
        this.loginForm.role = "student";
        this.go("login");
      }).catch(() => {});
    },
    async registerCompany() {
      if (
        this.companyRegister.password !== this.companyRegister.confirm_password
      )
        return this.notify("Company passwords do not match.", "warning");
      await this.withLoading(async () => {
        const result = await this.api("/api/auth/register/company", {
          method: "POST",
          body: this.companyRegister,
        });
        this.notify(result.message);
        this.loginForm.email = this.companyRegister.email;
        this.loginForm.role = "company";
        this.go("login");
      }).catch(() => {});
    },
    digitsOnly(form, field, length = null) {
      let value = String(form[field] || "").replace(/\D/g, "");
      if (length) value = value.slice(0, length);
      form[field] = value;
    },
    async lookupPincodeDirect(pincode) {
      const response = await fetch(
        `https://api.postalpincode.in/pincode/${pincode}`
      );
      const payload = await response.json();
      if (
        !Array.isArray(payload) ||
        payload[0]?.Status !== "Success" ||
        !payload[0]?.PostOffice?.length
      ) {
        throw new Error("No city or state was found for this pincode.");
      }
      const postOffice = payload[0].PostOffice[0];
      return {
        city: postOffice.District || postOffice.Name || "",
        state: postOffice.State || "",
        country: postOffice.Country || "India",
      };
    },
    async lookupPincode(form) {
      this.digitsOnly(form, "pincode", 6);
      const formKey =
        form === this.studentRegister || form === this.studentProfile
          ? "student"
          : "company";
      if (form.pincode.length !== 6) {
        this.lastPincodeLookup[formKey] = "";
        this.pincodeMessage[formKey] = "";
        return;
      }
      if (this.lastPincodeLookup[formKey] === form.pincode) return;
      this.lastPincodeLookup[formKey] = form.pincode;
      this.pincodeMessage[formKey] = "";
      this.pincodeLoading = true;
      try {
        const result = await this.api(`/api/public/pincode/${form.pincode}`);
        form.city = result.data.city;
        form.state = result.data.state;
        form.country = result.data.country || "India";
        this.pincodeMessage[formKey] = "City and state filled automatically.";
      } catch (error) {
        if (error.status === 502) {
          try {
            const result = await this.lookupPincodeDirect(form.pincode);
            form.city = result.city;
            form.state = result.state;
            form.country = result.country || "India";
            this.pincodeMessage[formKey] =
              "City and state filled automatically.";
            return;
          } catch (_fallbackError) {
            this.pincodeMessage[formKey] =
              "Auto-fill is unavailable right now. Please retry with a valid pincode.";
            return;
          }
        }
        this.pincodeMessage[formKey] = error.message;
      } finally {
        this.pincodeLoading = false;
      }
    },
    async loadPublicStats() {
      const result = await this.api("/api/public/stats");
      this.publicStats = result.data;
      await nextTick();
      this.renderCharts();
    },
    renderCharts() {
      this.charts.forEach((chart) => chart.destroy());
      this.charts = [];
      const make = (id, config) => {
        const el = document.getElementById(id);
        if (el) this.charts.push(new Chart(el, config));
      };
      const base = { responsive: true, maintainAspectRatio: false };
      make("trendChart", {
        type: "line",
        data: {
          labels: this.publicStats.trends.labels,
          datasets: [
            {
              label: "Placements",
              data: this.publicStats.trends.values,
              borderColor: "#2563eb",
              backgroundColor: "rgba(37,99,235,.15)",
              fill: true,
              tension: 0.3,
            },
          ],
        },
        options: base,
      });
      make("funnelChart", {
        type: "doughnut",
        data: {
          labels: this.publicStats.funnel.labels,
          datasets: [
            {
              data: this.publicStats.funnel.values,
              backgroundColor: [
                "#64748b",
                "#f59e0b",
                "#3b82f6",
                "#22c55e",
                "#ef4444",
              ],
            },
          ],
        },
        options: base,
      });
      make("skillsChart", {
        type: "bar",
        data: {
          labels: this.publicStats.skills.labels,
          datasets: [
            {
              label: "Approved job mentions",
              data: this.publicStats.skills.values,
              backgroundColor: "#7c3aed",
            },
          ],
        },
        options: {
          ...base,
          indexAxis: "y",
          plugins: { legend: { display: false } },
        },
      });
    },
    async loadDashboard() {
      if (!this.user) return;
      const result = await this.api(`/api/${this.user.role}/dashboard`);
      this.dashboard = result.data;
      if (["admin", "company"].includes(this.user.role)) this.dashboardChartVersion = Date.now();
      await nextTick();
      this.renderDashboardCharts();
      if (["admin", "company"].includes(this.user.role) && this.page === "dashboard") {
        if (this.dashboardRefreshTimer) clearTimeout(this.dashboardRefreshTimer);
        this.dashboardRefreshTimer = setTimeout(() => this.loadDashboard(), 30000);
      }
    },
    renderDashboardCharts() {
      this.charts.forEach((chart) => chart.destroy());
      this.charts = [];
      if (this.user?.role === "admin" && this.dashboard.company_analytics) {
        const analytics = this.dashboard.company_analytics;
        const palette = ["#9aabba", "#c9b48b", "#80a995", "#bc898f"];
        const labels = { applied: "Applied", shortlisted: "Shortlisted", placed: "Placed", rejected: "Rejected" };
        const barEl = document.getElementById("adminCompanyBarChart");
        const doughnutEl = document.getElementById("adminOverallDoughnutChart");
        const overallTotal = analytics.statuses.reduce((total, status) => total + Number(analytics.overall[status] || 0), 0);
        const centerTotalPlugin = {
          id: "centerTotal",
          afterDraw(chart) {
            const { ctx, chartArea } = chart;
            if (!chartArea) return;
            const x = (chartArea.left + chartArea.right) / 2;
            const y = (chartArea.top + chartArea.bottom) / 2;
            ctx.save();
            ctx.textAlign = "center"; ctx.textBaseline = "middle";
            ctx.fillStyle = "#343a40"; ctx.font = "600 26px system-ui"; ctx.fillText(String(overallTotal), x, y - 7);
            ctx.fillStyle = "#6c757d"; ctx.font = "12px system-ui"; ctx.fillText("applications", x, y + 17);
            ctx.restore();
          },
        };
        const commonLegend = {
          position: "bottom",
          labels: { usePointStyle: true, pointStyle: "rectRounded", boxWidth: 10, boxHeight: 10, padding: 18, color: "#4f555b", font: { size: 12 } },
        };
        if (barEl) this.charts.push(new Chart(barEl, {
          type: "bar",
          data: {
            labels: analytics.labels,
            datasets: analytics.statuses.map((status, index) => ({
              label: labels[status], data: analytics.series[status], backgroundColor: palette[index],
              borderColor: palette[index], borderWidth: 1, borderRadius: 7, borderSkipped: false,
              maxBarThickness: 42, categoryPercentage: .72, barPercentage: .82,
            })),
          },
          options: {
            responsive: true, maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: { legend: commonLegend, title: { display: true, text: "Applications by company", color: "#3f464d", font: { size: 15, weight: "500" }, padding: { bottom: 18 } }, tooltip: { padding: 12, cornerRadius: 8 } },
            scales: {
              x: { grid: { display: false }, ticks: { color: "#555d64", font: { size: 12 } } },
              y: { beginAtZero: true, suggestedMax: 3, ticks: { precision: 0, stepSize: 1, color: "#687078" }, grid: { color: "rgba(90, 98, 105, .1)" }, border: { display: false } },
            },
          },
        }));
        if (doughnutEl) this.charts.push(new Chart(doughnutEl, {
          type: "doughnut",
          plugins: [centerTotalPlugin],
          data: {
            labels: analytics.statuses.map((status) => labels[status]),
            datasets: [{ data: analytics.statuses.map((status) => analytics.overall[status]), backgroundColor: palette, borderColor: "#fff", borderWidth: 3, hoverOffset: 7 }],
          },
          options: {
            responsive: true, maintainAspectRatio: false, cutout: "64%",
            plugins: { legend: commonLegend, title: { display: true, text: "Overall application record", color: "#3f464d", font: { size: 15, weight: "500" }, padding: { bottom: 18 } }, tooltip: { padding: 12, cornerRadius: 8 } },
          },
        }));
        return;
      }
      const el = document.getElementById("adminPlacementChart");
      if (!el || !this.dashboard.placement_chart) return;
      this.charts.push(
        new Chart(el, {
          type: "bar",
          data: {
            labels: this.dashboard.placement_chart.labels,
            datasets: [
              {
                label: "Placements",
                data: this.dashboard.placement_chart.values,
                backgroundColor: "#7c3aed",
                borderRadius: 8,
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
          },
        })
      );
    },
    async pollExportStatus(exportId) {
      if (this.exportPollTimer) clearTimeout(this.exportPollTimer);
      const check = async () => {
        if (!this.user || this.user.role !== "student")
          return;
        try {
          const result = await this.api(`/api/${this.user.role}/export`);
          const latest = result.data;
          if (!latest || latest.id !== exportId) return;
          this.dashboard.latest_export = latest;
          if (latest.status === "completed") {
            this.notify("CSV export is ready to download.");
            return;
          }
          if (latest.status === "failed") {
            this.notify(latest.message || "CSV export failed.", "danger");
            return;
          }
          this.exportPollTimer = setTimeout(check, 4000);
        } catch (_error) {
          this.exportPollTimer = setTimeout(check, 8000);
        }
      };
      this.exportPollTimer = setTimeout(check, 4000);
    },
    async loadAdminCompanies() {
      const r = await this.api(
        `/api/admin/companies?q=${encodeURIComponent(this.search)}`
      );
      this.companies = r.data;
      if (this.selectedAdminCompany) {
        this.selectedAdminCompany =
          this.companies.find((company) => company.id === this.selectedAdminCompany.id) || null;
      }
    },
    async loadAdminStudents() {
      const r = await this.api(
        `/api/admin/students?q=${encodeURIComponent(this.search)}`
      );
      this.students = r.data;
      if (this.selectedAdminStudent) this.selectedAdminStudent = this.students.find((s) => s.id === this.selectedAdminStudent.id) || null;
    },
    companyApprovalLabel(company) {
      if (company.user.approved && company.user.active) return "approved";
      if (company.user.approved && !company.user.active) return "blacklisted";
      if (!company.user.approved && !company.user.active) return "rejected";
      return "pending";
    },
    startStudentEdit(student) {
      this.editingStudentId = student.id;
      this.studentEditForm = {
        name: student.user.name || "",
        email: student.user.email || "",
        contact: student.user.contact || "",
        roll_number: student.roll_number || "",
        course: student.course || "",
        branch: student.branch || "",
        graduation_year: student.graduation_year || "",
        cgpa: student.cgpa ?? "",
      };
    },
    cancelStudentEdit() {
      this.editingStudentId = null;
      this.studentEditForm = {};
    },
    async saveStudentEdit() {
      if (!this.editingStudentId) return;
      await this.withLoading(async () => {
        const r = await this.api(`/api/admin/students/${this.editingStudentId}`, {
          method: "PATCH",
          body: this.studentEditForm,
        });
        this.notify(r.message);
        this.cancelStudentEdit();
        await this.loadAdminStudents();
      }).catch(() => {});
    },
    async loadAdminDrives() {
      const r = await this.api(
        `/api/admin/drives?q=${encodeURIComponent(this.search)}`
      );
      this.drives = r.data;
      if (this.selectedAdminDrive) {
        this.selectedAdminDrive =
          this.drives.find((drive) => drive.id === this.selectedAdminDrive.id) || null;
      }
    },
    async loadAdminApplications() {
      const r = await this.api("/api/admin/applications");
      this.applications = r.data;
    },
    async adminStatus(type, id, action) {
      const labels = {
        approve: "Approve",
        blacklist: "Blacklist",
        unblacklist: "Unblacklist",
        activate: "Activate",
        reject: "Reject",
        deactivate: "Deactivate"
      };
      if (!confirm(`${labels[action] || action} this record?`)) return;
      await this.withLoading(async () => {
        const r = await this.api(`/api/admin/${type}/${id}/status`, {
          method: "PATCH",
          body: { action },
        });
        this.notify(r.message);
        await this.loadPage();
      }).catch(() => {});
    },
    viewAdminCompany(company) {
      this.selectedAdminCompany = company;
    },
    viewAdminStudent(student) {
      this.selectedAdminStudent = student;
    },
    viewAdminDrive(drive) {
      this.selectedAdminDrive = drive;
    },
    moneyLabel(value, unit) {
      if (value === null || value === undefined || value === "") return "Not disclosed";
      const unitLabel = { lpa: "LPA", k_month: "K/month" }[unit] || unit || "";
      return `${Number(value).toLocaleString("en-IN")} ${unitLabel}`.trim();
    },
    titleCase(value) {
      return String(value || "")
        .replace(/[_-]+/g, " ")
        .replace(/\b\w/g, (letter) => letter.toUpperCase());
    },
    async adminDelete(type, id) {
      if (!confirm("Delete this record permanently?")) return;
      await this.withLoading(async () => {
        const r = await this.api(`/api/admin/${type}/${id}`, {
          method: "DELETE",
        });
        this.notify(r.message);
        await this.loadPage();
      }).catch(() => {});
    },
    async adminDriveAction(drive, action) {
      if (!confirm(`${action} ${drive.title}?`)) return;
      await this.withLoading(async () => {
        const url = `/api/admin/drives/${drive.id}${
          action === "delete" ? "" : "/status"
        }`;
        const r = await this.api(
          url,
          action === "delete"
            ? { method: "DELETE" }
            : { method: "PATCH", body: { action } }
        );
        this.notify(r.message);
        await this.loadAdminDrives();
      }).catch(() => {});
    },
    csvToList(value) {
      return (value || "")
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);
    },
    resetDriveForm() {
      this.driveForm = {
        id: null,
        title: "",
        job_type: "full-time",
        deadline: "",
        location: "",
        salary: "",
        salary_unit: "lpa",
        openings: 1,
        min_cgpa: "",
        eligible_degrees: "",
        eligible_branches: "",
        eligible_degrees_list: [],
        eligible_branches_list: [],
        eligible_years: "",
        skills_required: "",
        experience_required: "",
        description: "",
      };
    },
    async loadCompanyDrives() {
      const r = await this.api("/api/company/dashboard");
      this.dashboard = r.data;
      this.drives = r.data.drives;
      this.resetDriveForm();
    },
    editDrive(drive) {
      this.driveForm = {
        ...drive,
        deadline: drive.deadline || "",
        eligible_degrees_list: this.csvToList(drive.eligible_degrees),
        eligible_branches_list: this.csvToList(drive.eligible_branches),
      };
      this.showDriveForm = true;
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
    async saveDrive() {
      await this.withLoading(async () => {
        const editing = !!this.driveForm.id;
        const payload = {
          ...this.driveForm,
          eligible_degrees: (this.driveForm.eligible_degrees_list || []).join(
            ", "
          ),
          eligible_branches: (this.driveForm.eligible_branches_list || []).join(
            ", "
          ),
        };
        delete payload.eligible_degrees_list;
        delete payload.eligible_branches_list;
        const r = await this.api(
          editing
            ? `/api/company/drives/${this.driveForm.id}`
            : "/api/company/drives",
          { method: editing ? "PATCH" : "POST", body: payload }
        );
        this.notify(r.message);
        this.showDriveForm = false;
        await this.loadCompanyDrives();
      }).catch(() => {});
    },
    async companyDriveAction(drive, action) {
      if (!confirm(`${action} ${drive.title}?`)) return;
      await this.withLoading(async () => {
        const r = await this.api(`/api/company/drives/${drive.id}/close`, {
          method: "PATCH",
        });
        this.notify(r.message);
        await this.loadCompanyDrives();
      }).catch(() => {});
    },
    async loadCompanyApplications() {
      const r = await this.api("/api/company/applications");
      const placedApplicationByStudentCompany = {};
      r.data.forEach((application) => {
        const studentId = application.student?.id;
        const companyId = application.drive?.company_id || application.drive?.company;
        const isPlaced = application.status === "placed";
        if (studentId && companyId && isPlaced) {
          placedApplicationByStudentCompany[`${studentId}:${companyId}`] = application.id;
        }
      });
      this.applications = r.data.map((a) => {
        const companyId = a.drive?.company_id || a.drive?.company;
        const placedApplicationId =
          placedApplicationByStudentCompany[`${a.student?.id}:${companyId}`];
        return {
          ...a,
          already_placed_elsewhere:
            !!(placedApplicationId && placedApplicationId !== a.id),
          interviews: a.interviews.map((i) => ({
            ...i,
            nextFeedback: i.feedback,
            nextResult: i.result,
          })),
          nextStatus: ["shortlisted", "interview", "rejected", "placed"].includes(
            a.status
          )
            ? a.status
            : "shortlisted",
          nextFeedback: a.feedback,
          interviewAt: "",
          interviewLocation: "",
        };
      });
    },
    async updateApplication(application) {
      await this.withLoading(async () => {
        const r = await this.api(
          `/api/company/applications/${application.id}`,
          {
            method: "PATCH",
            body: {
              status: application.nextStatus,
              feedback: application.nextFeedback,
            },
          }
        );
        this.notify(r.message);
        await this.loadCompanyApplications();
      }).catch(() => {});
    },
    async scheduleInterview(application) {
      if (!application.interviewAt)
        return this.notify("Choose an interview date and time.", "warning");
      await this.withLoading(async () => {
        const r = await this.api(
          `/api/company/applications/${application.id}/interviews`,
          {
            method: "POST",
            body: {
              scheduled_at: application.interviewAt,
              mode: "online",
              location_or_link: application.interviewLocation,
            },
          }
        );
        this.notify(r.message);
        await this.loadCompanyApplications();
      }).catch(() => {});
    },
    async completeInterview(interview) {
      await this.withLoading(async () => {
        const r = await this.api(`/api/company/interviews/${interview.id}`, {
          method: "PATCH",
          body: {
            feedback: interview.nextFeedback,
            result: interview.nextResult,
          },
        });
        this.notify(r.message);
        await this.loadCompanyApplications();
      }).catch(() => {});
    },
    async loadStudentDrives() {
      const r = await this.api(
        `/api/student/drives?q=${encodeURIComponent(this.search)}&eligible=${
          this.eligibleOnly ? 1 : 0
        }`
      );
      this.drives = r.data;
    },
    async applyDrive(drive) {
      await this.withLoading(async () => {
        const r = await this.api(`/api/student/drives/${drive.id}/apply`, {
          method: "POST",
          body: {},
        });
        this.notify(r.message);
        await this.loadStudentDrives();
      }).catch(() => {});
    },
    async loadStudentApplications() {
      const r = await this.api("/api/student/applications");
      this.applications = r.data;
    },
    async withdrawApplication(application) {
      if (!confirm("Withdraw this application?")) return;
      await this.withLoading(async () => {
        const r = await this.api(
          `/api/student/applications/${application.id}/withdraw`,
          { method: "PATCH" }
        );
        this.notify(r.message);
        await this.loadStudentApplications();
      }).catch(() => {});
    },
    async loadProfile() {
      if (!this.user) return;
      const r = await this.api(`/api/${this.user.role}/dashboard`);
      this.dashboard = r.data;
      if (this.user.role === "student") {
        this.studentProfile = JSON.parse(JSON.stringify(r.data.student));
        const user = this.studentProfile.user || {};
        const parts = (user.name || "").trim().split(/\s+/).filter(Boolean);
        user.first_name = user.first_name || parts.shift() || "";
        user.last_name = user.last_name || parts.pop() || "";
        user.middle_name = user.middle_name || parts.join(" ");
        this.studentProfile.user = user;
        this.studentProfile.address_line1 =
          this.studentProfile.address_line1 || user.address || "";
        this.studentProfile.address_line2 =
          this.studentProfile.address_line2 || "";
        this.studentProfile.landmark = this.studentProfile.landmark || "";
        this.studentProfile.pincode = this.studentProfile.pincode || "";
        this.studentProfile.city = this.studentProfile.city || "";
        this.studentProfile.state = this.studentProfile.state || "";
        this.studentProfile.country = this.studentProfile.country || "India";
      } else this.companyProfile = JSON.parse(JSON.stringify(r.data.company));
    },
    async saveStudentProfile() {
      await this.withLoading(async () => {
        const data = new FormData();
        const s = this.studentProfile;
        [
          "course",
          "branch",
          "graduation_year",
          "cgpa",
          "experience",
          "address_line1",
          "address_line2",
          "landmark",
          "pincode",
          "city",
          "state",
          "country",
        ].forEach((k) => data.append(k, s[k] ?? ""));
        [
          "first_name",
          "middle_name",
          "last_name",
          "email",
          "contact",
          "gender",
          "dob",
        ].forEach((k) => data.append(k, s.user?.[k] ?? ""));
        const file = this.$refs.profileResume?.files[0];
        if (file) data.append("resume", file);
        const r = await this.api("/api/student/profile", {
          method: "PATCH",
          body: data,
        });
        this.studentProfile = r.data;
        this.user.name = r.data.user.name;
        this.user.email = r.data.user.email;
        this.notify(r.message);
        await this.loadProfile();
      }).catch(() => {});
    },
    async cancelProfileChanges() {
      await this.withLoading(async () => {
        await this.loadProfile();
        if (this.$refs.profileResume) this.$refs.profileResume.value = "";
      }).catch(() => {});
    },
    async saveCompanyProfile() {
      await this.withLoading(async () => {
        const r = await this.api("/api/company/profile", {
          method: "PATCH",
          body: this.companyProfile,
        });
        this.companyProfile = r.data;
        this.user.name = r.data.name;
        this.notify(r.message);
      }).catch(() => {});
    },
    async startExport() {
      if (!this.user || this.user.role !== "student") return;
      await this.withLoading(async () => {
        const r = await this.api("/api/student/export", {
          method: "POST",
        });
        this.notify(r.message);
        await this.loadDashboard();
        if (r.data?.id) await this.pollExportStatus(r.data.id);
      }).catch(() => {});
    },
    formatDate(value) {
      return value ? new Date(value).toLocaleString() : "-";
    },
  },
};

createApp(App).mount("#app");
